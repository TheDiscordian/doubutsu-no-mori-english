"""Build an experimental V3 object-loader cartridge, without enabling move-ins."""
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib

from aflib import (CODE_RAM, CODE_VROM, apply_ups, by_vrom, fix_checksum, make_ups,
                   replace_dma, sha256, u32, verified_rom)
from apply_translation import write_new
from toolchain import IMAGE
from v3_import_catalog import ROOT, read_donor
from v3_villager_art import build_art
import v3_storage

BASE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
MODULE, MODULE_RAM = 0x02800000, 0x801948E0
STARTUP, CONFIG, STATE, STARTUP_END = 0x6000, 0x63E0, 0x63F0, 0x6400
BLOB, BLOB_RAM, BLOB_SIZE, TABLE_OFFSET = v3_storage.START, 0x80460000, 0x2000, 0x1000
OBJECT_TABLE, OBJECT_COUNT, CAPACITY = 0x8010DDD0, 410, 430
STARTUP_CALL, ORIGINAL_CALL = 0x800D65D0, 0x0C0275B4
TEXTURE_BASE, TEXTURE_STRIDE = 0x03F10000, 0x2000
SOURCE_FILES = ('tools/v3_asset_loader.py', 'overlays/v3/startup.c', 'overlays/v3/startup.ld',
                'overlays/v3/asset.c', 'overlays/v3/asset.ld', 'tools/v3_villager_art.py',
                'tools/v3_import_catalog.py', 'tools/aflib.py') + v3_storage.SOURCES


def texture_slot(donor_index):
    """Fixed English-donor slots, independent of the chosen subset or its order."""
    if not 216 <= donor_index < 236:
        raise ValueError('Not a new named English-donor villager')
    slot = donor_index - 216
    return OBJECT_COUNT + slot, TEXTURE_BASE + slot * TEXTURE_STRIDE


def compile_part(part, out, extra_sources=(), defines=(), primary_source=None):
    out.mkdir(parents=True, exist_ok=False)
    docker = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
              '-v', f'{ROOT}:/source:ro', '-v', f'{out.resolve()}:/out', '-w', '/out', '--entrypoint']
    def run(tool, *args):
        return subprocess.run(docker + ['/n64_toolchain/bin/mips64-elf-' + tool, IMAGE, *args],
                              check=True, capture_output=True, text=True, timeout=60).stdout
    flags = ['-c', '-Os', '-EB', '-mabi=32', '-march=vr4300', '-mfix4300', '-G0',
             '-mno-abicalls', '-fno-pic', '-ffreestanding', '-fno-builtin', '-fno-common',
             '-fno-stack-protector', '-ffunction-sections', '-fdata-sections', '-fstack-usage',
             '-Wall', '-Wextra', '-Werror']
    flags += ['-D' + define for define in defines]
    if part in ('catalogue', 'hra', 'feng_shui', 'campsite_manager', 'camper_greeting', 'camper_trade'):
        flags += ['-fno-merge-constants', '-mno-explicit-relocs', '-mno-split-addresses']
    objects = []
    for i, source in enumerate((primary_source or f'overlays/v3/{part}.c', *extra_sources)):
        obj = 'code.o' if i == 0 else f'extra{i}.o'
        run('gcc', *flags, f'/source/{source}', '-o', obj)
        objects.append(obj)
    run('ld', '-EB', *(['--emit-relocs'] if part in ('catalogue', 'hra', 'feng_shui', 'campsite_manager', 'camper_greeting', 'camper_trade') else []),
        '-T', f'/source/overlays/v3/{part}.ld', '-o', 'code.elf', *objects)
    if run('nm', '--undefined-only', 'code.elf').strip():
        raise ValueError('Unresolved V3 loader symbol')
    symbols = {name: int(address, 16) for address, kind, name in
               (line.split() for line in run('nm', '--defined-only', 'code.elf').splitlines())}
    run('objcopy', '-O', 'binary', '-j', '.text', '-j', '.rodata', 'code.elf', 'code.bin')
    code = (out / 'code.bin').read_bytes()
    entry, expected = {'startup': ('af_v3_startup', MODULE_RAM + STARTUP),
                       'accessory': ('af_v3_accessory_draw', 0x80473100),
                       'melody_expanded': ('af_v3_melody_start', 0x80473500),
                       'clothing_roster': ('af_v3_roster_clothing_record', 0x80473A00),
                       'town_eligible': ('af_v3_town_eligible', 0x80473E40),
                       'display_roster': ('af_v3_all_display_clothing_index', 0x80466380),
                       'house_markers': ('af_v3_house_marker_v1', 0x80461F80),
                       'asset': ('af_v3_asset_init', BLOB_RAM + 0x100),
                       'villager': ('af_v3_load_name', BLOB_RAM + 0x4000),
                       'villager_readers': ('af_v3_mail_source_name', BLOB_RAM + 0x5400),
                       'villager_selection': ('af_v3_unseen_personality', BLOB_RAM + 0x3400),
                       'villager_rewards': ('af_v3_house_reward', BLOB_RAM + 0x3A00),
                       'furniture': ('af_v3_furniture_import_profile', BLOB_RAM + 0x5000),
                       'furniture_tables': ('af_v3_furniture_tables_init', BLOB_RAM + 0xA000),
                       'furniture_expanded': ('af_v3_furniture_import_profile', BLOB_RAM + 0x5800),
                       'clothing_display': ('af_v3_display_clothing_index', BLOB_RAM + 0x6200),
                       'display_items': ('af_v3_display_pocket_item', BLOB_RAM + 0x6C00),
                       'display_conversion': ('af_v3_room_display_item', BLOB_RAM + 0x6270),
                       'items': ('af_v3_item_name', BLOB_RAM + 0x7300),
                       'items_large': ('af_v3_item_name_extended', 0x80483000),
                       'tent_model': ('af_v3_tent_model_ct', 0x80483400),
                       'palette_fade': ('af_v3_tent_model_ct', 0x80483400),
                       'fire': ('af_v3_campfire_ct', 0x80483800),
                       'furniture_behaviours': ('af_v3_furniture_action_sound', 0x80483D00),
                       'furniture_rewards': ('af_v3_furniture_reward_goods', 0x80474BC0),
                       'campsite_scene': ('af_v3_campsite_scene_status', 0x804A0100),
                       'campsite_exterior': ('af_v3_campsite_actor_descriptor', 0x804A0360),
                       'campsite_event': ('af_v3_campsite_schedule', 0x804A2100),
                       'campsite_calendar': ('af_v3_campsite_today_init', 0x804A2740),
                       'camper': ('af_v3_camper_register', 0x804A2D00),
                       'camper_reader': ('af_v3_camper_npc_info', 0x804A29A0),
                       'campsite_placement': ('af_v3_tent_set_class', 0x804A2A70),
                       'campsite_manager': ('af_v3_camper_event_start', 0x80964DA0),
                       'camper_movein': ('af_v3_camper_movein_candidate', BLOB_RAM + 0x3EE0),
                       'camper_quest': ('af_v3_camper_profile', 0x804A2EC0),
                       'camper_greeting': ('af_v3_camper_greeting', 0x8092DAE0),
                       'camper_trade': ('af_v3_camper_pocket', 0x80922370),
                       'camper_gift': ('af_v3_camper_gift', 0x804A2F30),
                       'campsite_environment': ('af_v3_campsite_floor', 0x804A2F54),
                       'tent_lamp': ('af_v3_lamp_ct', 0x8046E000),
                       'equipment_resources': ('af_v3_equipment_pointer', 0x804A3000),
                       'player_actions': ('af_v3_player_action_v0', 0x804A5000),
                       'tool_motion': ('af_v3_tool_action_setup', 0x804A5A50),
                       'tool_effects': ('af_v3_shovel_call', 0x804B2000),
                       'held_items': ('af_v3_held_item_name', 0x804A6000),
                       'held_presents': ('af_v3_present_pocket', 0x804B4000),
                       'held_present_names': ('af_v3_present_legacy_name', 0x804B4480),
                       'player_faces': ('af_v3_player_eye_sequence', 0x804B4540),
                       'player_reward_messages': ('af_v3_reward_message_id', 0x804B2280),
                       'player_rewards': ('af_v3_reward_bgm', 0x804B3880),
                       'held_rigs': ('af_v3_held_setup', 0x804B0000),
                       'room_rigs': ('af_v3_room_rig_ct', 0x804B1800),
                       'held_collection': ('af_v3_held_catalogue_record', 0x804AFA00),
                       'inventory_equipment': ('af_v3_inventory_item_kind', 0x804A9000),
                       'inventory_aux': ('af_v3_inventory_bobber', 0x804B2180),
                       'item_categories': ('af_v3_equipment_category', 0x804AA000),
                       'ground_categories': ('af_v3_ground_prepare', 0x804AD000),
                       'event_acquisition': ('af_v3_event_stock_construct', 0x804AE000),
                       'event_menu': ('af_v3_event_menu_start', 0x804AF000),
                       'room': ('af_v3_room_value', BLOB_RAM + 0x8000),
                       'identity': ('af_v3_identity_item', BLOB_RAM + 0x9D00),
                       'fields': ('af_v3_field_shop', BLOB_RAM + 0xA400),
                       'menu': ('af_v3_menu_type_80872bb0', BLOB_RAM + 0xA800),
                       'icon': ('af_v3_furniture_icon_type', BLOB_RAM + 0xAB00),
                       'ground': ('af_v3_ground_type_8090f888', BLOB_RAM + 0xAE00),
                       'pockets': ('af_v3_pocket_index', BLOB_RAM + 0xB200),
                       'save_codec': ('af_v3_save_check', BLOB_RAM + 0xB400),
                       'save_clothing': ('af_v3_save_check_extended', BLOB_RAM + 0xD000),
                       'clothing_menu': ('af_v3_room_value_clothing', BLOB_RAM + 0x3C30),
                       'shop_mannequin': ('af_v3_mannequin_80959320', BLOB_RAM + 0x4C00),
                       'save_runtime': ('af_v3_save_reset', BLOB_RAM + 0x9200),
                       'collection': ('af_v3_catalogue_record', BLOB_RAM + 0x99C0),
                       'catalogue': ('af_v3_catalogue_bit', 0x808B32B0),
                       'shops': ('af_v3_shop_category', BLOB_RAM + 0x9C00),
                       'shop_actors': ('af_v3_shop_type_809cacbc', BLOB_RAM + 0x7600),
                       'shop_floor': ('af_v3_shop_floor_80953e54', BLOB_RAM + 0x7C00),
                       'hra': ('af_v3_hra_remaining', 0x80929C30),
                       'feng_shui': ('af_v3_feng_range', 0x80931780)}[part]
    if symbols[entry] != expected:
        raise ValueError('V3 linker moved the public entry')
    write_new(out / 'code.asm', run('objdump', '-d', 'code.elf').encode())
    report = {'bytes': len(code), 'sha256': sha256(code), 'symbols': symbols,
              'toolchain': IMAGE, 'flags': flags,
              'stack_usage': ''.join(p.read_text() for p in sorted(out.glob('*.su')))}
    if part == 'villager':
        run('objcopy', '-O', 'binary', '-j', '.defaults', 'code.elf', 'defaults.bin')
        defaults = (out / 'defaults.bin').read_bytes()
        report['default_extension'] = {'ram': 0x804632E0, 'bytes': len(defaults),
                                       'sha256': sha256(defaults)}
    if part in ('catalogue', 'hra', 'feng_shui', 'campsite_manager', 'camper_greeting', 'camper_trade'):
        report['elf_relocations'] = run('readelf', '-rW', 'code.elf')
    return code, report


def compose(native, base, changes, added, *, resized=(), relocated=None):
    """Preserve current DMA identities and startup copies while adding new files."""
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('V3 composition requires exact stable V2-11')
    current, original = by_vrom(base), by_vrom(native)
    relocated = relocated or {}
    scoring_moves = {0x0081D9D0: 0x03F40000, 0x00821740: 0x03F48000}
    all_moves = {**scoring_moves, 0x00827DE0: 0x03F50000, 0x00828C00: 0x03F54000}
    from v3_speed_bag_sound_runtime import RELOCATIONS as sound_moves
    from v3_villager_houses import FOREGROUND, EXPANDED_FOREGROUND
    if (relocated not in ({}, scoring_moves, all_moves, {**all_moves, **sound_moves},
                         {**all_moves, **sound_moves, FOREGROUND: EXPANDED_FOREGROUND})
            or not set(relocated) <= set(resized) or set(relocated.values()) & (set(current) | set(added))):
        raise ValueError('Unreviewed V3 resource relocation')
    if not changes and not added and not relocated:
        return base
    if not set(changes) <= set(current) or set(added) & set(current):
        raise ValueError('Unknown change or colliding V3 addition')
    if not set(resized) <= set(changes) or not set(resized) <= {
            0x03970000, 0x03980000, 0x03200000, 0x011E6000, 0x011E5000, 0xE02000, 0x11AB000, *relocated}:
        raise ValueError('Unreviewed V3 resource resize')
    if any((len(data) != current[v].size and v not in resized) or v in (0x1060, 0x19D40)
           for v, data in changes.items()):
        raise ValueError('Unexpected resize or boot change in V3 asset batch')
    original_by_index = {e.index: e for e in original.values()}
    if not set(original_by_index) <= {e.index for e in current.values()}:
        raise ValueError('V2 has lost an original DMA identity')
    replacements, moves, additions = {}, {}, dict(added)
    for v, entry in current.items():
        data = changes.get(v, entry.extract(base))
        old = original_by_index.get(entry.index)
        if old is None:
            additions[v] = data
        elif v != 0x19D40:
            target = relocated.get(v, v)
            if target != old.vstart or len(data) != old.size:
                moves[old.vstart] = target
            if data != old.extract(native) or old.vstart in moves:
                replacements[old.vstart] = data
    # VROM addresses need not be sorted in the native directory. Preserve all
    # existing appended row identities before allocating the new V3 rows.
    addition_order = [v for v, entry in sorted(current.items(), key=lambda pair: pair[1].index)
                      if entry.index not in original_by_index] + sorted(added)
    image = bytearray(replace_dma(native, replacements, moves, additions,
                                  addition_order=addition_order))
    boot = original[0x1060]
    boot_data = current[0x1060].extract(base)
    if base[boot.pstart:boot.pstart + boot.size] != boot_data:
        raise ValueError('V2 physical and virtual startup copies disagree')
    image[boot.pstart:boot.pstart + boot.size] = boot_data
    fix_checksum(image)
    image = bytes(image)
    installed = by_vrom(image)
    if set(installed) != (set(current) - set(relocated)) | set(relocated.values()) | set(added):
        raise ValueError('V3 composition loses DMA resources')
    for v, before in current.items():
        target = relocated.get(v, v)
        actual, expected = installed[target].extract(image), changes.get(v, before.extract(base))
        if v == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if installed[target].index != before.index or actual != expected:
            raise ValueError(f'V3 composition changes an unrelated resource: {v:08X}')
    if any(installed[v].extract(image) != data for v, data in added.items()):
        raise ValueError('V3 composition does not retain complete added data')
    return image


def build(native, base, rel, symbols, out, *, npc_draw=False, audio_donor=None, text_donor=None,
          furniture=False, furniture_items=False, furniture_room=False, furniture_fields=False,
          furniture_menu=False, furniture_icon=False, furniture_ground=False, furniture_pockets=False,
          save_codec=False, save_runtime=False, collection=False, catalogue=False, shops=False,
          shop_actors=False, shop_floor=False, hra=False, feng_shui=False, houses=False,
          villager_readers=False, villager_selection=False, villager_rewards=False, clothing=False,
          speed_bag_sound=False, speed_bag=False):
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('Asset loader requires exact stable V2-11')
    import v3_npc_draw
    import v3_audio_runtime
    import v3_villager_text
    import v3_furniture_runtime
    import v3_furniture_items
    import v3_furniture_room
    import v3_furniture_fields
    import v3_furniture_menu
    import v3_furniture_identity
    import v3_furniture_icon
    import v3_furniture_ground
    import v3_furniture_pockets
    import v3_save_codec
    import v3_save_runtime
    import v3_collection
    import v3_catalogue
    import v3_shops
    import v3_shop_actors
    import v3_shop_floor
    import v3_hra
    import v3_feng_shui
    import v3_villager_houses
    import v3_villager_readers
    import v3_villager_selection
    import v3_villager_rewards
    import v3_clothing
    import v3_npc_clothing
    import v3_player_clothing
    import v3_save_clothing
    import v3_clothing_items
    import v3_clothing_menu
    import v3_clothing_wear
    import v3_clothing_stock
    import v3_shop_mannequin
    import v3_clothing_shop_floor
    import v3_furniture_tables
    import v3_clothing_display
    import v3_display_items
    import v3_display_conversion
    import v3_clothing_catalogue
    import v3_speed_bag_sound_runtime
    import v3_speed_bag_runtime
    import v3_hra_mail
    if speed_bag and not speed_bag_sound:
        raise ValueError('Speed-bag callbacks require their complete installed sound')
    if speed_bag_sound and not clothing:
        raise ValueError('Speed-bag sound requires the current complete V3 foundation')
    if clothing and not villager_rewards:
        raise ValueError('Clothing resources require the current complete villager foundation')
    if villager_rewards and not villager_selection:
        raise ValueError('House rewards require the complete selection/house foundation')
    if villager_selection and not villager_readers:
        raise ValueError('Villager selection requires the complete secondary name readers')
    if villager_readers and not houses:
        raise ValueError('Villager reader integration requires the current house foundation')
    if houses and not feng_shui:
        raise ValueError('Villager houses require the current furniture/scoring foundation')
    if feng_shui and not hra:
        raise ValueError('Feng shui imports require the current HRA foundation')
    if hra and not shop_floor:
        raise ValueError('HRA imports require the current shop-floor foundation')
    if shop_floor and not shop_actors:
        raise ValueError('Shop floor imports require shop interaction support')
    if shop_actors and not shops:
        raise ValueError('Shop interaction imports require native stock and catalogue support')
    if shops and not catalogue:
        raise ValueError('Ordinary import stock requires catalogue and persistence support')
    if catalogue and not collection:
        raise ValueError('Catalogue imports require persistent native collection')
    if collection and not save_runtime:
        raise ValueError('Collection requires actual save/profile state')
    if save_runtime and not save_codec:
        raise ValueError('Save runtime requires the checked save codec')
    if save_codec and not furniture_pockets:
        raise ValueError('Save-codec variant requires the current pocket integration baseline')
    if furniture_pockets and not furniture_ground:
        raise ValueError('Pocket variant requires installed furniture ground integration')
    if furniture_ground and not furniture_icon:
        raise ValueError('Ground variant requires installed furniture icon integration')
    if furniture_icon and not furniture_menu:
        raise ValueError('Icon variant requires installed furniture menu integration')
    if furniture_menu and not furniture_fields:
        raise ValueError('Menu variant requires installed shared grid integration')
    if furniture_fields and not furniture_room:
        raise ValueError('Field variant requires installed room integration')
    if furniture_room and not furniture_items:
        raise ValueError('Room variant requires installed shared item metadata readers')
    if furniture_items and not furniture:
        raise ValueError('Item metadata variant requires installed furniture models/profiles')
    if furniture and text_donor is None:
        raise ValueError('Furniture variant requires the current villager/text baseline')
    if text_donor is not None and audio_donor is None:
        raise ValueError('Villager text variant requires installed pilot artwork and audio')
    if audio_donor is not None:
        npc_draw = True
    source_files = (SOURCE_FILES + (v3_npc_draw.SOURCE_FILES if npc_draw else ())
                    + (v3_audio_runtime.SOURCES if audio_donor is not None else ())
                    + (v3_villager_text.SOURCES if text_donor is not None else ())
                    + (v3_furniture_runtime.SOURCE_FILES if furniture else ())
                    + (v3_furniture_items.SOURCES if furniture_items else ())
                    + (v3_furniture_room.SOURCES if furniture_room else ())
                    + (v3_furniture_fields.SOURCES if furniture_fields else ())
                    + (v3_furniture_menu.SOURCES if furniture_menu else ())
                    + (v3_furniture_identity.SOURCES if furniture_menu else ())
                    + (v3_furniture_icon.SOURCES if furniture_icon else ())
                    + (v3_furniture_ground.SOURCES if furniture_ground else ())
                    + (v3_furniture_pockets.SOURCES if furniture_pockets else ())
                    + (v3_save_codec.SOURCES if save_codec else ())
                    + (v3_save_runtime.SOURCES if save_runtime else ())
                    + (v3_collection.SOURCES if collection else ())
                    + (v3_catalogue.SOURCES if catalogue else ())
                    + (v3_shops.SOURCES if shops else ())
                    + (v3_shop_actors.SOURCES if shop_actors else ())
                    + (v3_shop_floor.SOURCES if shop_floor else ())
                    + (v3_hra.SOURCES if hra else ())
                    + (v3_feng_shui.SOURCES if feng_shui else ())
                    + (v3_villager_houses.SOURCES if houses else ())
                    + (v3_villager_readers.SOURCES if villager_readers else ())
                    + (v3_villager_selection.SOURCES if villager_selection else ())
                    + (v3_villager_rewards.SOURCES if villager_rewards else ())
                    + (v3_clothing.SOURCES + v3_npc_clothing.SOURCES + v3_player_clothing.SOURCES
                       + v3_save_clothing.SOURCES + v3_clothing_items.SOURCES + v3_clothing_menu.SOURCES
                       + v3_clothing_wear.SOURCES + v3_clothing_stock.SOURCES + v3_shop_mannequin.SOURCES
                       + v3_clothing_shop_floor.SOURCES + v3_furniture_tables.SOURCES
                       + v3_clothing_display.SOURCES + v3_display_items.SOURCES + v3_display_conversion.SOURCES
                       + v3_clothing_catalogue.SOURCES
                       if clothing else ())
                    + (v3_speed_bag_sound_runtime.SOURCES if speed_bag_sound else ())
                    + (v3_speed_bag_runtime.SOURCES+v3_hra_mail.SOURCES if speed_bag else ()))
    sources = {p: sha256((ROOT / p).read_bytes()) for p in source_files}
    blob_size, abi = (v3_npc_draw.BLOB_SIZE, v3_npc_draw.ABI) if npc_draw else (BLOB_SIZE, 1)
    if audio_donor is not None:
        abi = v3_audio_runtime.ABI
    if text_donor is not None:
        blob_size, abi = v3_villager_text.BLOB_SIZE, v3_villager_text.ABI
    if furniture:
        blob_size, abi = v3_furniture_runtime.BLOB_SIZE, v3_furniture_runtime.ABI
    if furniture_items:
        abi = v3_furniture_items.ABI
    staging_size = blob_size
    if furniture_room:
        blob_size, abi = v3_furniture_room.BLOB_SIZE, v3_furniture_room.ABI
    if furniture_fields:
        abi = v3_furniture_fields.ABI
    if furniture_menu:
        abi = v3_furniture_menu.ABI
    if furniture_icon:
        abi = v3_furniture_icon.ABI
    if furniture_ground:
        abi = v3_furniture_ground.ABI
    if furniture_pockets:
        abi = v3_furniture_pockets.ABI
    if save_codec:
        abi = v3_save_codec.ABI
    if save_runtime:
        abi = v3_save_runtime.ABI
    if collection:
        abi = v3_collection.ABI
    if shops:
        abi = v3_shops.ABI
    if shop_actors:
        abi = v3_shop_actors.ABI
    if shop_floor:
        abi = v3_shop_floor.ABI
    if hra:
        abi = v3_hra.ABI
    if feng_shui:
        abi = v3_feng_shui.ABI
    if furniture_menu:
        abi = max(abi, v3_furniture_menu.ABI, v3_furniture_identity.ABI)
    if houses:
        abi = max(abi, v3_villager_houses.ABI)
    if villager_readers:
        abi = max(abi, v3_villager_readers.ABI)
    if villager_selection:
        abi = max(abi, v3_villager_selection.ABI)
    if villager_rewards:
        abi = max(abi, v3_villager_rewards.ABI)
    if npc_draw:
        abi = max(abi, v3_npc_draw.STREAMING_ABI)
    if clothing:
        abi = max(abi, v3_clothing.ABI, v3_npc_clothing.ABI, v3_player_clothing.ABI,
                  v3_save_clothing.ABI, v3_clothing_items.ABI, v3_collection.CLOTHING_ABI,
                  v3_clothing_menu.ABI, v3_clothing_wear.ABI, v3_shops.CLOTHING_ABI,
                  v3_clothing_stock.ABI, v3_shop_mannequin.ABI, v3_clothing_shop_floor.ABI,
                  v3_furniture_tables.ABI, v3_clothing_display.ABI, v3_display_items.ABI,
                  v3_display_conversion.ABI, v3_clothing_catalogue.ABI)
    if speed_bag_sound:
        abi = max(abi, v3_speed_bag_sound_runtime.ABI)
    if speed_bag:
        abi = max(abi, v3_speed_bag_runtime.ABI, v3_villager_houses.PUNCHY_ABI)
    artifacts, art = build_art(native, rel, symbols)
    files, originals = by_vrom(base), by_vrom(native)
    code = bytearray(files[CODE_VROM].extract(base))
    module = bytearray(files[MODULE].extract(base))
    if (len(module) != 0x8000 or any(module[STARTUP:STARTUP_END])
            or u32(module, 12) != STARTUP or u32(code, STARTUP_CALL - CODE_RAM) != ORIGINAL_CALL):
        raise ValueError('Changed resident diagnostic space or existing startup chain')
    object_at = 0x800C5AA0 - CODE_RAM
    if code[object_at:object_at + 144] != originals[CODE_VROM].extract(native)[object_at:object_at + 144]:
        raise ValueError('Object loader is no longer the reviewed native function')
    table_at = OBJECT_TABLE - CODE_RAM
    table = bytes(code[table_at:table_at + OBJECT_COUNT * 8])
    for start, end in struct.iter_unpack('>II', table):
        if start == end == 0:
            continue
        if start not in files or end != files[start].vend:
            raise ValueError('Existing object bank does not match its current DMA resource')
    startup_defines = (f'AF_V3_BLOB_SIZE={blob_size}', f'AF_V3_ABI={abi}') if npc_draw else ()
    if save_runtime:
        startup_defines += ('AF_V3_SAVE_RUNTIME=1',)
    clothing_defines = ('AF_V3_CLOTHING_PROFILE=1',) if clothing else ()
    speed_bag_defines = ('AF_V3_SPEED_BAG=1',) if speed_bag else ()
    startup_defines += clothing_defines
    table_defines = ('AF_V3_FURNITURE_TABLES=1',) if clothing else ()
    startup_defines += table_defines
    startup, startup_report = compile_part('startup', out / 'startup', defines=startup_defines)
    extra_sources = ('overlays/v3/npc_draw.c', 'overlays/v3/npc_voice.S') if npc_draw else ()
    if audio_donor is not None:
        extra_sources += ('overlays/v3/melody.c',)
    if clothing:
        extra_sources += ('overlays/v3/clothing.c', 'overlays/v3/npc_clothing.c', 'overlays/v3/player_clothing.c',
                          'overlays/v3/clothing_stock.c', 'overlays/v3/clothing_stock.S')
    helper, helper_report = compile_part('asset', out / 'asset', extra_sources=extra_sources)
    if len(startup) > CONFIG - STARTUP or len(helper) > TABLE_OFFSET - 0x100:
        raise ValueError('V3 code exceeds its owned reservation')
    blob = bytearray(staging_size)
    struct.pack_into('>5I', blob, 0, 0x41465633, abi, blob_size, CAPACITY, OBJECT_COUNT)
    blob[0x100:0x100 + len(helper)] = helper
    blob[TABLE_OFFSET:TABLE_OFFSET + len(table)] = table
    struct.pack_into('>4I', blob, staging_size - 16, *([0xAF33C0DE] * 4))
    additions, imports = {}, []
    for row in art['villagers']:
        index = int(row['id'].rsplit('/', 1)[-1], 16)
        bank, vrom = texture_slot(index)
        texture = artifacts[row['texture_file']]
        struct.pack_into('>II', blob, TABLE_OFFSET + bank * 8, vrom, vrom + len(texture))
        additions[vrom] = texture
        imports.append({'id': row['id'], 'name': row['name'], 'object_bank': bank,
                        'texture_vrom': f'{vrom:08X}', 'texture_sha256': sha256(texture),
                        'playable': False, 'draw_record_installed': npc_draw})
    draw_changes, draw_report = {}, None
    if npc_draw:
        records, draw_imports = v3_npc_draw.draw_records(native, rel, symbols, art)
        at = v3_npc_draw.DRAW_OFFSET
        if at + len(records) > blob_size - 16:
            raise ValueError('V3 draw records exceed their owned reservation')
        blob[at:at + len(records)] = records
        draw_changes, owner_report = v3_npc_draw.patch_owners(native, base, helper_report['symbols'])
        draw_report = {'imports': draw_imports, 'owners': owner_report,
                       'record_offset': at, 'record_stride': v3_npc_draw.STRIDE}
    audio_report = (v3_audio_runtime.install(native, code, blob, helper_report['symbols'], audio_donor)
                    if audio_donor is not None else None)
    text_report = None
    outfit_defines = ((f'AF_V3_IMPORTED_OUTFIT_SOURCE=0x{helper_report["symbols"]["af_v3_clothing_source"]:08X}u',)
                      if speed_bag else ())
    if text_donor is not None:
        text_code, text_code_report = compile_part('villager', out / 'villager', defines=outfit_defines)
        text_limit = v3_furniture_runtime.CODE if furniture else blob_size - 16
        if furniture_items:
            text_limit = v3_furniture_items.BRIDGE
        if len(text_code) > text_limit - v3_villager_text.CODE:
            raise ValueError('Villager text code exceeds its reservation')
        blob[v3_villager_text.CODE:v3_villager_text.CODE + len(text_code)] = text_code
        text_report = v3_villager_text.install(native, code, module, blob,
            text_code_report['symbols'], *text_donor, symbols)
        text_report['code'] = text_code_report
        if speed_bag:
            defaults = (out / 'villager/defaults.bin').read_bytes()
            if (not 0 < len(defaults) <= 0x120 or any(blob[0x32E0:0x3400])
                    or len(text_code) > 0x600):
                raise ValueError('Imported defaults overlap melody, selection, or item bridges')
            blob[0x32E0:0x32E0+len(defaults)] = defaults
    furniture_changes, furniture_report = {}, None
    if furniture:
        furniture_code, furniture_code_report = compile_part('furniture', out / 'furniture',
            extra_sources=('overlays/v3/furniture_entry.S',))
        if len(furniture_code) > v3_furniture_runtime.PROFILES - v3_furniture_runtime.CODE:
            raise ValueError('Furniture code exceeds its reservation')
        blob[v3_furniture_runtime.CODE:v3_furniture_runtime.CODE + len(furniture_code)] = furniture_code
        furniture_changes, furniture_added, furniture_report = v3_furniture_runtime.install(
            native, base, blob, rel, symbols, furniture_code_report['symbols'], out / 'furniture-art',
            object_vrom_offset=v3_furniture_room.MODEL_SHIFT if furniture_room else 0)
        furniture_report['code'] = furniture_code_report
        if set(furniture_added) & set(additions) or set(furniture_changes) & set(draw_changes):
            raise ValueError('Furniture composition collides with a villager resource')
        additions.update(furniture_added)
    items_report = None
    if furniture_items:
        item_code, item_code_report = compile_part('items', out / 'items', defines=speed_bag_defines)
        if len(item_code) > staging_size - 16 - v3_furniture_items.CODE:
            raise ValueError('Furniture item helpers exceed their reservation')
        blob[v3_furniture_items.CODE:v3_furniture_items.CODE + len(item_code)] = item_code
        items_report = v3_furniture_items.install(code, module, blob,
            item_code_report['symbols'], rel, symbols)
        items_report['code'] = item_code_report
    room_report = None
    if furniture_room:
        rows = v3_furniture_room.inspect(furniture_changes[v3_furniture_runtime.VROM],
                                        furniture_changes[v3_furniture_runtime.RELOC])
        generated = out / 'room-hooks.S'
        write_new(generated, v3_furniture_room.assembly(rows).encode())
        room_code, room_code_report = compile_part('room', out / 'room',
            extra_sources=('overlays/v3/room_entry.S', str(generated.relative_to(ROOT))))
        room_report = v3_furniture_room.install(furniture_changes, blob, rows,
                                               room_code, room_code_report['symbols'])
        room_report['code'] = room_code_report
        room_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
    fields_report = None
    if furniture_fields:
        rows = v3_furniture_fields.inspect(code)
        generated = out / 'field-hooks.S'
        write_new(generated, v3_furniture_fields.hook_assembly(rows).encode())
        fields_code, fields_code_report = compile_part('fields', out / 'fields',
            extra_sources=(str(generated.relative_to(ROOT)),))
        fields_report = v3_furniture_fields.install(code, blob, rows, fields_code,
            fields_code_report['symbols'], room_code_report['symbols'], rel, symbols)
        fields_report['code'] = fields_code_report
        fields_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
    menu_changes, menu_report = {}, None
    if furniture_menu:
        rows = v3_furniture_menu.inspect(code, files[v3_furniture_menu.ROOT_VROM].extract(base),
            files[v3_furniture_menu.VROM].extract(base), files[v3_furniture_menu.RELOC].extract(base))
        generated = out / 'menu-hooks.S'
        write_new(generated, v3_furniture_menu.assembly(rows).encode())
        menu_code, menu_code_report = compile_part('menu', out / 'menu',
            primary_source=str(generated.relative_to(ROOT)))
        menu_changes, menu_report = v3_furniture_menu.install(base, code, blob, rows, menu_code,
            menu_code_report['symbols'], room_code_report['symbols'])
        menu_report['code'] = menu_code_report
        menu_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        if set(menu_changes) & (set(draw_changes) | set(furniture_changes)):
            raise ValueError('Menu composition overlaps another changed owner')
    icon_changes, icon_report = {}, None
    if furniture_icon:
        generated = out / 'icon-hooks.S'
        write_new(generated, v3_furniture_icon.assembly().encode())
        icon_code, icon_code_report = compile_part('icon', out / 'icon',
            primary_source=str(generated.relative_to(ROOT)))
        icon_changes, icon_report = v3_furniture_icon.install(base, code, blob, icon_code,
            icon_code_report['symbols'], room_code_report['symbols'])
        icon_report['code'] = icon_code_report
        icon_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        if set(icon_changes) & (set(draw_changes) | set(furniture_changes) | set(menu_changes)):
            raise ValueError('Icon composition overlaps another changed owner')
    ground_changes, ground_report = {}, None
    if furniture_ground:
        generated = out / 'ground-hooks.S'
        write_new(generated, v3_furniture_ground.assembly().encode())
        ground_code, ground_code_report = compile_part('ground', out / 'ground',
            primary_source=str(generated.relative_to(ROOT)))
        ground_changes, ground_report = v3_furniture_ground.install(base, code, blob, ground_code,
            ground_code_report['symbols'], room_code_report['symbols'])
        ground_report['code'] = ground_code_report
        ground_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        if set(ground_changes) & (set(draw_changes) | set(furniture_changes) | set(menu_changes) | set(icon_changes)):
            raise ValueError('Ground composition overlaps another changed owner')
    pockets_report = None
    if furniture_pockets:
        pockets_code, pockets_code_report = compile_part('pockets', out / 'pockets')
        pockets_report = v3_furniture_pockets.install(code, blob, pockets_code,
            pockets_code_report['symbols'], room_code_report['symbols'])
        pockets_report['code'] = pockets_code_report
    save_report = None
    gameplay_imports = (furniture_report['imports'] +
        ([{'item_id': '3350', 'runtime_index': 1236}] if speed_bag else [])) if furniture else []
    if clothing:
        clothing_resource, clothing_record, clothing_row = v3_clothing.convert(
            native, text_donor[1], rel, symbols)
    if save_codec:
        save_code, save_code_report = compile_part('save_codec', out / 'save_codec')
        save_report = v3_save_codec.install(blob, save_code, save_code_report['symbols'], pockets_code_report)
        save_report['code'] = save_code_report
    save_runtime_report = None
    if save_runtime:
        runtime_code, runtime_report = compile_part('save_runtime', out / 'save_runtime', defines=clothing_defines)
        save_runtime_report = v3_save_runtime.install(native, base, code, blob, runtime_code,
            runtime_report['symbols'], save_code_report, room_code_report,
            draw_report['imports'], gameplay_imports +
            ([v3_clothing_display.profile_dependency()] if clothing else []),
            [clothing_row] if clothing else None)
        save_runtime_report['code'] = runtime_report
    collection_report = None
    if collection:
        collection_code, collection_code_report = compile_part('collection', out / 'collection', defines=clothing_defines)
        collection_report = v3_collection.install(code, blob, collection_code,
            collection_code_report['symbols'], runtime_report, save_code_report, furniture_code_report,
            item_readers=item_code_report if clothing else None)
        collection_report['code'] = collection_code_report
    catalogue_changes, catalogue_report = {}, None
    if catalogue:
        ordering, catalogue_records = v3_catalogue.table(base, rel, symbols, gameplay_imports)
        table_path = out / 'catalogue-order.bin'
        write_new(table_path, ordering)
        generated = out / 'catalogue-order.S'
        catalogue_assembly = ('.section .rodata.catalogue_order\n.balign 4\n'
            '.globl af_v3_catalogue_order\naf_v3_catalogue_order:\n'
            f'.incbin "/source/{table_path.relative_to(ROOT)}"\n')
        clothing_catalogue = v3_clothing_catalogue.table(base, rel, symbols) if clothing else None
        if clothing_catalogue is not None:
            clothing_path = out/'catalogue-clothing-order.bin'
            write_new(clothing_path, clothing_catalogue[0])
            catalogue_assembly += ('.section .rodata.catalogue_clothing\n.balign 4\n'
                '.globl af_v3_catalogue_clothing_order\naf_v3_catalogue_clothing_order:\n'
                f'.incbin "/source/{clothing_path.relative_to(ROOT)}"\n')
        write_new(generated, catalogue_assembly.encode())
        catalogue_code, catalogue_code_report = compile_part('catalogue', out / 'catalogue',
            extra_sources=('overlays/v3/catalogue_bridge.S', str(generated.relative_to(ROOT))),
            defines=table_defines+(('AF_V3_CLOTHING_CATALOGUE=1',) if clothing else ()))
        catalogue_changes, catalogue_report = v3_catalogue.install(base,
            icon_changes[v3_catalogue.PARENT], catalogue_code, catalogue_code_report,
            ordering, catalogue_records, collection_code_report, runtime_report, room_code_report,
            clothing=clothing_catalogue)
        catalogue_report['code'] = catalogue_code_report
    shop_changes, shop_report = {}, None
    if shops:
        shop_code, shop_code_report = compile_part('shops', out / 'shops',
            defines=('AF_V3_CLOTHING_PROFILE',) if clothing else ())
        shop_changes, shop_report = v3_shops.install(base, code, blob, shop_code, shop_code_report,
            collection_code_report, furniture_code_report, rel, symbols, gameplay_imports,
            clothing_items=item_code_report if clothing else None)
        shop_report['code'] = shop_code_report
    shop_actor_changes, shop_actor_report = {}, None
    if shop_actors:
        rows = v3_shop_actors.inspect(base, code)
        generated = out / 'shop-actor-hooks.S'
        write_new(generated, v3_shop_actors.assembly(rows).encode())
        actor_code, actor_code_report = compile_part('shop_actors', out / 'shop_actors',
            primary_source=str(generated.relative_to(ROOT)))
        shop_actor_changes, shop_actor_report = v3_shop_actors.install(base, code, blob, rows,
            actor_code, actor_code_report['symbols'], item_code_report, room_code_report)
        shop_actor_report['code'] = actor_code_report
        shop_actor_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        if set(shop_actor_changes) & (set(draw_changes) | set(furniture_changes) | set(menu_changes)
                | set(icon_changes) | set(ground_changes) | set(catalogue_changes) | set(shop_changes)):
            raise ValueError('Shop actor composition overlaps another changed owner')
    shop_floor_changes, shop_floor_report = {}, None
    if shop_floor:
        rows = v3_shop_floor.inspect(base, code)
        generated = out / 'shop-floor-hooks.S'
        clothing_floor_rows = v3_clothing_shop_floor.inspect(base, code) if clothing else []
        write_new(generated, (v3_shop_floor.assembly(rows)
            + (v3_clothing_shop_floor.assembly(clothing_floor_rows) if clothing else '')).encode())
        floor_code, floor_code_report = compile_part('shop_floor', out / 'shop_floor',
            primary_source=str(generated.relative_to(ROOT)))
        shop_floor_changes, shop_floor_report = v3_shop_floor.install(base, code, blob, rows,
            floor_code, floor_code_report['symbols'], actor_code_report, room_code_report)
        shop_floor_report['code'] = floor_code_report
        if clothing:
            shop_floor_changes[v3_shop_floor.VROM], shop_floor_report['clothing'] = v3_clothing_shop_floor.install(
                shop_floor_changes[v3_shop_floor.VROM], blob, clothing_floor_rows, floor_code_report, shop_floor_report)
            shop_floor_report['output_sha256'] = shop_floor_report['clothing']['output_sha256']
        shop_floor_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        if set(shop_floor_changes) & (set(draw_changes) | set(furniture_changes) | set(menu_changes)
                | set(icon_changes) | set(ground_changes) | set(catalogue_changes)
                | set(shop_changes) | set(shop_actor_changes)):
            raise ValueError('Shop floor composition overlaps another changed owner')
    hra_changes, hra_report, relocated = {}, None, {}
    if hra:
        metadata, records = v3_hra.table(base, rel, symbols, furniture_report['imports'],
            v3_clothing_display.profile_dependency() if clothing else None, speed_bag=speed_bag)
        series_resources = v3_hra.v3_hra_series.prepare(base, rel, symbols) if speed_bag else None
        metadata_path, generated = out / 'hra-metadata.bin', out / 'hra-hooks.S'
        write_new(metadata_path, metadata)
        rows = v3_hra.inspect(base)
        write_new(generated, (v3_hra.assembly(rows) + '.section .rodata.hra_table\n.balign 4\n'
            '.globl af_v3_hra_table\naf_v3_hra_table:\n'
            f'.incbin "/source/{metadata_path.relative_to(ROOT)}"\n'
            + (v3_hra.v3_hra_series.assembly(series_resources) if series_resources else '')).encode())
        hra_code, hra_compiled = compile_part('hra', out / 'hra',
            extra_sources=(str(generated.relative_to(ROOT)),), defines=table_defines+speed_bag_defines)
        hra_changes, hra_report = v3_hra.install(base, code, hra_code, hra_compiled, metadata, records, rows, series_resources)
        hra_report['code'] = hra_compiled
        hra_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        relocated = {v3_hra.VROM: v3_hra.NEW_VROM, v3_hra.RELOC: v3_hra.NEW_RELOC}
    feng_changes, feng_report = {}, None
    if feng_shui:
        metadata, records = v3_feng_shui.table(base, rel, symbols, gameplay_imports,
            v3_clothing_display.profile_dependency() if clothing else None)
        metadata_path, generated = out / 'feng-metadata.bin', out / 'feng-hooks.S'
        write_new(metadata_path, metadata)
        write_new(generated, (v3_feng_shui.assembly() + '.section .rodata.feng_table\n.balign 4\n'
            '.globl af_v3_feng_table\naf_v3_feng_table:\n'
            f'.incbin "/source/{metadata_path.relative_to(ROOT)}"\n').encode())
        feng_code, feng_compiled = compile_part('feng_shui', out / 'feng_shui',
            primary_source=str(generated.relative_to(ROOT)))
        feng_changes, feng_report = v3_feng_shui.install(base, code, feng_code, feng_compiled, metadata, records)
        feng_report['code'] = feng_compiled
        feng_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        relocated.update({v3_feng_shui.VROM: v3_feng_shui.NEW_VROM, v3_feng_shui.RELOC: v3_feng_shui.NEW_RELOC})
    identity_report = None
    if furniture_menu:
        rows = v3_furniture_identity.inspect(furniture_changes[v3_furniture_runtime.VROM],
                                              furniture_changes[v3_furniture_runtime.RELOC])
        generated, entry = out / 'identity-hooks.S', out / 'identity-entry.S'
        write_new(generated, v3_furniture_identity.assembly(rows).encode())
        write_new(entry, (ROOT / 'overlays/v3/room_entry.S').read_text().replace(
            'af_v3_room_query', 'af_v3_identity_query').replace(
            'af_v3_room_value', 'af_v3_identity_item').encode())
        identity_code, identity_compiled = compile_part('identity', out / 'identity',
            extra_sources=(str(entry.relative_to(ROOT)), str(generated.relative_to(ROOT))))
        identity_report = v3_furniture_identity.install(furniture_changes, blob, rows,
            identity_code, identity_compiled['symbols'], furniture_code_report['symbols'])
        identity_report['code'] = identity_compiled
        identity_report['generated_hooks_sha256'] = sha256(generated.read_bytes())
        identity_report['generated_entry_sha256'] = sha256(entry.read_bytes())
    house_changes, house_report = {}, None
    if houses:
        house_changes, house_report = v3_villager_houses.install(native, base, code,
            text_donor[0], symbols, {'imports': gameplay_imports}, punchy=speed_bag)
        relocated.update({int(v, 16): int(t, 16) for v, t in house_report['relocations'].items()})
    if speed_bag:
        from v3_villager_defaults import imported_outfit
        text_report['imported_outfit'] = imported_outfit(blob, text_report,
            clothing_resource, clothing_record, clothing_row)
    reader_changes, reader_report = {}, None
    if villager_readers:
        reader_code, reader_compiled = compile_part('villager_readers', out / 'villager_readers')
        reader_changes, reader_report = v3_villager_readers.install(base,
            {CODE_VROM: bytes(code), MODULE: bytes(module), **menu_changes}, blob,
            reader_code, reader_compiled['symbols'])
        code, module = (bytearray(reader_changes.pop(v)) for v in (CODE_VROM, MODULE))
        reader_report['code'] = reader_compiled
    selection_report = None
    if villager_selection:
        selection_code, selection_compiled = compile_part('villager_selection', out / 'villager_selection',
            defines=((f'AF_V3_OUTFIT_READY=0x{text_code_report["symbols"]["outfit_ready"]:08X}u',)
                     if speed_bag else ()))
        selection_report = v3_villager_selection.install(native, code, blob,
            selection_code, selection_compiled['symbols'], text_report, house_report)
        selection_report['code'] = selection_compiled
    reward_report = None
    if villager_rewards:
        reward_code, reward_compiled = compile_part('villager_rewards', out / 'villager_rewards')
        reward_report = v3_villager_rewards.install(code, blob, reward_code, reward_compiled['symbols'])
        reward_report['code'] = reward_compiled
    clothing_report, clothing_wear_changes, clothing_stock_changes = None, {}, {}
    mannequin_changes = {}
    if clothing:
        clothing_report = v3_clothing.install(code, blob, helper_report['symbols'],
            clothing_resource, clothing_record)
        clothing_report['punchy_defaults_enabled'] = speed_bag
        clothing_report['imports'] = [clothing_row]
        draw_changes, clothing_owners = v3_npc_clothing.patch_owners(
            native, draw_changes, helper_report['symbols'])
        clothing_report['owners'] = clothing_owners
        clothing_report['npc_streaming_clothes_installed'] = True
        clothing_report['player_readers'] = v3_player_clothing.install(code, helper_report['symbols'])
        extended_code, extended_compiled = compile_part('save_clothing', out/'save_clothing',
            defines=v3_save_clothing.DEFINES+v3_clothing_items.DEFINES+speed_bag_defines,
            primary_source='overlays/v3/save_codec.c', extra_sources=('overlays/v3/items.c',))
        extended_resource, extended_report = v3_save_clothing.install(
            blob, extended_code, extended_compiled, save_code_report, save_runtime_report)
        extended_report['code'] = extended_compiled
        clothing_report['save_extension'] = extended_report
        clothing_report['item_readers'] = v3_clothing_items.install(
            blob, extended_compiled, item_code_report, helper_report)
        # The name-reader pass also edits tag. Compose on that final owner,
        # otherwise its later merge would silently discard clothing hooks.
        clothing_tag = reader_changes[v3_furniture_menu.VROM]
        clothing_tag_owner = next(row for row in reader_report['owners']
                                  if row['vrom'] == f'{v3_furniture_menu.VROM:08X}')
        clothing_reloc = files[v3_furniture_menu.RELOC].extract(base)
        clothing_sites = v3_clothing_menu.inspect(clothing_tag, clothing_reloc, clothing_tag_owner)
        clothing_entries = out/'clothing-menu-hooks.S'
        write_new(clothing_entries, (v3_clothing_menu.assembly(clothing_sites)+v3_clothing_wear.assembly()).encode())
        clothing_menu_code, clothing_menu_compiled = compile_part('clothing_menu', out/'clothing_menu',
            defines=('AF_V3_CLOTHING_PROFILE', 'af_v3_room_value=af_v3_room_value_clothing'),
            primary_source='overlays/v3/room.c', extra_sources=(str(clothing_entries.relative_to(ROOT)),))
        reader_changes[v3_furniture_menu.VROM], clothing_report['menu'] = v3_clothing_menu.install(
            blob, clothing_menu_code, clothing_menu_compiled, clothing_tag, clothing_reloc,
            clothing_tag_owner, room_code_report, item_code_report, reward_compiled)
        clothing_tag_owner['before_clothing_sha256'] = clothing_tag_owner['output_sha256']
        clothing_tag_owner['output_sha256'] = sha256(reader_changes[v3_furniture_menu.VROM])
        menu_report['before_villager_readers_sha256'] = menu_report['output_sha256']
        menu_report['before_clothing_sha256'] = sha256(clothing_tag)
        menu_report['output_sha256'] = clothing_tag_owner['output_sha256']
        clothing_wear_changes, clothing_report['wearing'] = v3_clothing_wear.install(base, clothing_menu_compiled)
        clothing_stock_changes, clothing_report['stock'] = v3_clothing_stock.install(
            base, code, helper, helper_report, rel, symbols, clothing_report['imports'])
        for owner in shop_report['retained_owners']:
            if owner['start'] == 0x800BFCF0:
                owner['before_clothing_stock_sha256'] = owner['sha256']
                owner['sha256'] = sha256(code[owner['start']-CODE_RAM:owner['end']-CODE_RAM])
        mannequin_rows = v3_shop_mannequin.inspect(base)[2]
        mannequin_source = out/'shop-mannequin.S'
        write_new(mannequin_source, v3_shop_mannequin.assembly(mannequin_rows).encode())
        mannequin_code, mannequin_compiled = compile_part('shop_mannequin', out/'shop_mannequin',
            primary_source=str(mannequin_source.relative_to(ROOT)))
        mannequin_changes, clothing_report['mannequin'] = v3_shop_mannequin.install(
            base, blob, mannequin_code, mannequin_compiled, room_report['code'], selection_report)
        expanded_code, expanded_compiled = compile_part('furniture_expanded', out/'furniture-expanded',
            primary_source='overlays/v3/furniture.c',
            extra_sources=('overlays/v3/furniture_entry.S',),
            defines=table_defines+('AF_V3_CLOTHING_DISPLAY=1',)+speed_bag_defines)
        table_entries = v3_furniture_tables.install_helper(blob, expanded_code, expanded_compiled,
                                                          furniture_code_report)
        table_code, table_compiled = compile_part('furniture_tables', out/'furniture_tables',
            defines=('AF_V3_CLOTHING_DISPLAY=1',))
        furniture_changes[v3_furniture_runtime.VROM], table_report = v3_furniture_tables.install(
            furniture_changes[v3_furniture_runtime.VROM], furniture_changes[v3_furniture_runtime.RELOC],
            blob, table_code, table_compiled,
            {**furniture_report['owner'], 'room_relocation_sha256': room_report['relocation_sha256']})
        table_report['expanded_code'] = expanded_compiled
        table_report['public_entries'] = table_entries
        furniture_report['expanded_tables'] = table_report
        furniture_report.update({key: table_report[key] for key in
            ('capacity', 'profile_table_ram', 'bank_index_ram')})
        furniture_report['mutable_ranges'] = []
        furniture_report['external_mutable_ranges'] = [
            [v3_furniture_tables.PROFILES, v3_furniture_tables.PROFILES+v3_furniture_tables.CAPACITY*4],
            [v3_furniture_tables.INDICES, v3_furniture_tables.INDICES+v3_furniture_tables.CAPACITY]]
        display_code, display_compiled = compile_part('clothing_display', out/'clothing_display')
        clothing_report['display'] = v3_clothing_display.install(native, base, blob,
            display_code, display_compiled, item_code_report, save_runtime_report)
        furniture_report['display_imports'] = clothing_report['display']['imports']
        display_item_code, display_item_compiled = compile_part('display_items', out/'display_items')
        clothing_report['display']['readers'] = v3_display_items.install(blob,
            display_item_code, display_item_compiled, clothing_report['item_readers'],
            extended_compiled, collection_report)
        conversion_code, conversion_compiled = compile_part('display_conversion', out/'display_conversion')
        clothing_report['display']['conversion'] = v3_display_conversion.install(code, blob,
            conversion_code, conversion_compiled, clothing_report['display'],
            clothing_report['display']['readers'])
        clothing_report['display']['global_placement_enabled'] = True
        clothing_report['imports'][0]['save_profile_installed'] = True
        save_report.update({'base_codec_format_version': 1, 'format_version': 2,
            'registry_version': 2, 'work_state_bytes': v3_save_clothing.STATE,
            'extended_entry_dispatch': 'clothing.save_extension.public_entries'})
        for owner in draw_report['owners']:
            owner['before_clothing_sha256'] = owner['patched_sha256']
            owner['patched_sha256'] = sha256(draw_changes[int(owner['vrom'], 16)])
    speed_bag_report = None
    if speed_bag:
        reader_changes[v3_hra_mail.VROM], hra_mail_report = v3_hra_mail.install(
            reader_changes[v3_hra_mail.VROM], module, rel, symbols)
        hra_report['score_letters'] = hra_mail_report
        hra_report['series']['boxing']['score_letter_name_installed'] = True
        if (not all(any(row['item_id']=='3350' for row in owner['imports'])
                    for owner in (hra_report,feng_report,catalogue_report,shop_report))
                or not bytes.fromhex(save_runtime_report['profile_hex'])[58] & 16):
            raise ValueError('Speed-bag gameplay lacks a complete installed dependency')
        speed_bag_asset, speed_bag_report = v3_speed_bag_runtime.install(
            native, code, blob, rel, symbols, out/'speed-bag', gameplay=True)
        speed_bag_report.update({'saved_profile_included': True,
            'catalogue_row_installed': True, 'shop_stock_installed': True,
            'hra_score_letter_name_installed': True, 'feng_shui_installed': True})
        speed_bag_report['punchy_house_installed'] = house_report['installed_villagers'] == ['E0EA', 'E0ED']
        speed_bag_report['pending'] = ['ordinary acquisition/interaction and persistence',
                                     'ordinary Punchy gameplay and house visits']
        furniture_added[int(speed_bag_report['object_vrom'], 16)] = speed_bag_asset
        additions[int(speed_bag_report['object_vrom'], 16)] = speed_bag_asset
    if len(blob) != blob_size:
        raise ValueError('V3 resident payload differs from startup reservation')
    module[STARTUP:STARTUP + len(startup)] = startup
    struct.pack_into('>4I', module, CONFIG, BLOB, blob_size, zlib.crc32(blob), abi)
    struct.pack_into('>I', code, STARTUP_CALL - CODE_RAM,
                     0x0C000000 | ((MODULE_RAM + STARTUP) >> 2 & 0x3FFFFFF))
    # The native DMA directory has no spare row after the two pilot texture
    # banks. Furniture occupies ROM-only tail slots in the existing V3 file;
    # startup still loads/checks exactly blob_size bytes into its RAM reservation.
    resources = {}
    if furniture:
        for vrom, data in sorted(furniture_added.items()):
            resources[vrom] = data
            del additions[vrom]
    if clothing:
        for vrom, data in ((int(clothing_row['vrom'], 16), clothing_resource),
                           (v3_save_clothing.VROM, extended_resource)):
            if vrom in resources:
                raise ValueError('Duplicate V3 storage resource')
            resources[vrom] = data
    blob_file = v3_storage.pack(blob, resources, files)
    additions[BLOB] = blob_file
    sound_changes, sound_report = {}, None
    if speed_bag_sound:
        for vrom in v3_speed_bag_sound_runtime.RELOCATIONS:
            if files[vrom].extract(base) != originals[vrom].extract(native):
                raise ValueError('Stable audio resources changed before the V3 append')
        sound_changes, sound_report = v3_speed_bag_sound_runtime.prepare(native, code, audio_donor)
        sound_report['furniture_callback_installed'] = speed_bag
        relocated.update(v3_speed_bag_sound_runtime.RELOCATIONS)
    changes = {CODE_VROM: bytes(code), MODULE: bytes(module), **draw_changes,
               **furniture_changes, **menu_changes, **icon_changes, **ground_changes,
               **catalogue_changes, **shop_changes, **shop_actor_changes, **shop_floor_changes,
               **hra_changes, **feng_changes, **house_changes, **reader_changes, **clothing_wear_changes,
               **clothing_stock_changes, **mannequin_changes, **sound_changes}
    resized = (((v3_catalogue.VROM, v3_catalogue.RELOC) if catalogue else ())
               + ((v3_hra_mail.VROM,) if speed_bag else ())
               + ((v3_shops.VROM,) if shops else ()) + ((v3_clothing_stock.VROM,) if clothing else ()) + tuple(relocated)
               + ((v3_villager_houses.HOUSE, v3_villager_houses.FOREGROUND) if houses else ()))
    image = compose(native, base, changes, additions, resized=resized, relocated=relocated)
    if speed_bag_sound:
        # Physical placement is known only after composition. The second pass
        # changes six same-sized instructions, never audio file sizes or order.
        v3_speed_bag_sound_runtime.bind_physical(native, code, image, sound_report)
        changes[CODE_VROM] = bytes(code)
        image = compose(native, base, changes, additions, resized=resized, relocated=relocated)
        placed = by_vrom(image)
        for row in sound_report['files'].values():
            if placed[row['vrom']].pstart != row['physical_rom']:
                raise ValueError('Audio physical locations changed during final binding')
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('V3 asset patch reconstruction failed')
    if sources != {p: sha256((ROOT / p).read_bytes()) for p in source_files}:
        raise ValueError('V3 sources changed during construction')
    label = ('V3 speed-bag furniture integration 01' if speed_bag else
             'V3 speed-bag native sound 01' if speed_bag_sound else
             'V3 expanded furniture tables 01' if clothing else
             'V3 villager house rewards integration 01' if villager_rewards else
             'V3 villager selection integration 01' if villager_selection else
             'V3 villager secondary readers development 01' if villager_readers else
             'V3 villager house development 01' if houses else
             'V3 imported room scoring development 01' if feng_shui else
             'V3 imported HRA scoring development 01' if hra else
             'V3 imported shop floor development 01' if shop_floor else
             'V3 imported shop interactions development 01' if shop_actors else
             'V3 imported shop stock development 01' if shops else
             'V3 imported catalogue development 01' if catalogue else
             'V3 item collection integration development 01' if collection else
             'V3 FlashRAM integration development 01' if save_runtime else
             'V3 save-codec foundation development 01' if save_codec else
             'V3 furniture pocket integration development 01' if furniture_pockets else
             'V3 furniture ground integration development 01' if furniture_ground else
             'V3 furniture icon integration development 01' if furniture_icon else
             'V3 furniture menu integration development 01' if furniture_menu else
             'V3 furniture field integration development 01' if furniture_fields else
             'V3 furniture room integration development 01' if furniture_room else
             'V3 furniture item readers development 01' if furniture_items else
             'V3 furniture loader development 01' if furniture else
             'V3 villager defaults development 01' if text_donor is not None else
             'V3 villager audio development 02' if audio_donor is not None else
             'V3 NPC draw development 02' if npc_draw else 'V3 asset-loader development 02')
    return image, patch, {'build': label,
        'baseline_sha256': BASE_SHA, 'npc_draw': draw_report, 'villager_audio': audio_report,
        'speed_bag_sound': sound_report,
        'speed_bag': speed_bag_report,
        'storage': {'vrom': BLOB, 'limit': v3_storage.END, 'bytes': len(blob_file)},
        'villager_text': text_report, 'furniture': furniture_report, 'furniture_items': items_report,
        'furniture_room': room_report,
        'furniture_identity': identity_report,
        'furniture_fields': fields_report,
        'furniture_menu': menu_report,
        'furniture_icon': icon_report,
        'furniture_ground': ground_report,
        'furniture_pockets': pockets_report,
        'save_codec': save_report,
        'save_runtime': save_runtime_report,
        'collection': collection_report,
        'catalogue': catalogue_report,
        'shops': shop_report,
        'shop_actors': shop_actor_report,
        'shop_floor': shop_floor_report,
        'hra': hra_report,
        'feng_shui': feng_report,
        'villager_houses': house_report,
        'villager_readers': reader_report,
        'villager_selection': selection_report,
        'villager_rewards': reward_report,
        'clothing': clothing_report,
        'resized_resources': [f'{v:08X}' for v in resized],
        'relocated_resources': {f'{v:08X}': f'{target:08X}' for v, target in relocated.items()},
        'source_sha256': sha256(native), 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'sources': sources, 'startup': startup_report, 'asset': helper_report,
        'blob_sha256': sha256(blob), 'resident_blob_bytes': blob_size,
        'blob_file_bytes': len(blob_file), 'original_object_table_sha256': sha256(table),
        'object_capacity': CAPACITY, 'imports': imports, 'rom_bytes': len(image),
        'resident_startup_range': ['8019A8E0', '8019ACE0'],
        'expansion_data_range': ['80460000', f'{BLOB_RAM + blob_size:08X}'], 'ordinary_heap_growth': 0,
        'expansion_state_range': ['8046C000', f'{v3_save_runtime.STATE_RAM+save_runtime_report["state_bytes"]:08X}'] if save_runtime else None,
        'save_temporary_buffer_bytes': 0x10000 if save_runtime else None,
        'required_ram_bytes': 0x800000, 'saved_layout_changed': save_runtime,
        'saved_format_changed': text_report is not None,
        'imported_default_key_format': 'V3-only four-byte reference' if text_report else None,
        'new_villager_ids_enabled': False, 'native_test': 'pending', 'hardware_test': 'not performed',
        'save_warning': ('Experimental V3 saves require this save format and compatible imports. '
                         'Do not load them in V2 or older V3 builds. Keep backups; removing required '
                         'imports stops loading.' if save_runtime else
                        'Development only; use disposable saves. Imported default references require V3 '
                         'and compatible profile metadata; do not load those saves in V2.' if text_report else
                         'Development loader only; use disposable saves. V3 import/profile compatibility is unverified.'),
        'added_resources': {f'{v:08X}': sha256(data) for v, data in additions.items()},
        'changed_resources': {f'{v:08X}': sha256(data) for v, data in changes.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--villager-houses', action='store_true', help='Include Cheri house data; move-ins remain disabled')
    p.add_argument('--villager-readers', action='store_true', help='Connect imported map, inventory, and mail names')
    p.add_argument('--villager-selection', action='store_true', help='Integrate subset-aware selection with imports disabled')
    p.add_argument('--villager-rewards', action='store_true', help='Include imported furniture in villager house gifts')
    p.add_argument('--clothing', action='store_true', help='Add the cherry-shirt resource and shared reader; gameplay is not enabled')
    p.add_argument('--speed-bag-sound', action='store_true', help='Install the actual speed-bag sound; furniture installation remains pending')
    p.add_argument('--speed-bag', action='store_true', help='Install the animated item and gameplay dependencies for private testing')
    p.add_argument('--npc-draw', action='store_true', help='Install experimental draw rows and voice-ID transport')
    p.add_argument('--villager-audio', action='store_true', help='Include pilot draw records and full-ID melody support')
    p.add_argument('--villager-text', action='store_true', help='Include pilot audio, names, phrases, and verified initial defaults')
    p.add_argument('--furniture', action='store_true', help='Include the current baseline and experimental static furniture loading')
    p.add_argument('--furniture-items', action='store_true', help='Include furniture loading and shared item metadata readers')
    p.add_argument('--furniture-room', action='store_true', help='Include selected furniture room range/index integration')
    p.add_argument('--furniture-fields', action='store_true', help='Include selected furniture shared grids and shop eligibility')
    p.add_argument('--furniture-menu', action='store_true', help='Include selected furniture action, transfer, and placement menus')
    p.add_argument('--furniture-icon', action='store_true', help='Include selected furniture inventory leaf icons')
    p.add_argument('--furniture-ground', action='store_true', help='Include selected furniture ground drawing and drop flags')
    p.add_argument('--furniture-pockets', action='store_true', help='Include imported furniture in inventory searches and counts')
    p.add_argument('--save-codec', action='store_true', help='Include checked save/profile codec; native saving is not changed')
    p.add_argument('--save-runtime', action='store_true', help='Enable V3 FlashRAM profiles and save/load integration; saves require V3')
    p.add_argument('--collection', action='store_true', help='Connect native item collection and player clearing to V3 catalogue state')
    p.add_argument('--catalogue', action='store_true', help='Include imported catalogue rows, model previews, and orderable prices')
    p.add_argument('--shops', action='store_true', help='Include selected furniture in native ordinary-stock tables and category queries')
    p.add_argument('--shop-actors', action='store_true', help='Connect imported furniture to all five native shop interaction actors')
    p.add_argument('--shop-floor', action='store_true', help='Connect imported stock to shop floor selection and sold-item removal')
    p.add_argument('--hra', action='store_true', help='Include imported furniture in native HRA scoring and recommendations')
    p.add_argument('--feng-shui', action='store_true', help='Include actual imported furniture colours in native feng shui scoring')
    args = p.parse_args()
    if args.speed_bag:
        args.speed_bag_sound = True
    if args.speed_bag_sound:
        args.clothing = True
    if args.clothing:
        args.villager_rewards = True
    if args.villager_rewards:
        args.villager_selection = True
    if args.villager_selection:
        args.villager_readers = True
    if args.villager_readers:
        args.villager_houses = True
    if args.villager_houses:
        args.feng_shui = True
    if args.feng_shui:
        args.hra = True
    if args.hra:
        args.shop_floor = True
    if args.shop_floor:
        args.shop_actors = True
    if args.shop_actors:
        args.shops = True
    if args.shops:
        args.catalogue = True
    if args.catalogue:
        args.collection = True
    if args.collection:
        args.save_runtime = True
    if args.save_runtime:
        args.save_codec = True
    if args.save_codec:
        args.furniture_pockets = True
    if args.furniture_pockets:
        args.furniture_ground = True
    if args.furniture_ground:
        args.furniture_icon = True
    if args.furniture_icon:
        args.furniture_menu = True
    if args.furniture_menu:
        args.furniture_fields = True
    if args.furniture_fields:
        args.furniture_room = True
    if args.furniture_room:
        args.furniture_items = True
    if args.furniture_items:
        args.furniture = True
    if args.furniture:
        args.villager_text = True
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'build') or out.exists():
        raise ValueError('Choose a fresh output directory inside ignored build/')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    from v3_villager_audio import read_audio_donor
    audio_donor = (read_audio_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
                   if args.villager_audio or args.villager_text else None)
    from v3_villager_text import read_text_donor
    text_donor = ((donor, read_text_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso'))
                  if args.villager_text else None)
    out.mkdir(parents=True)
    image, patch, report = build((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes(), donor['rel'],
        (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes(), out,
        npc_draw=args.npc_draw, audio_donor=audio_donor, text_donor=text_donor,
        furniture=args.furniture, furniture_items=args.furniture_items, furniture_room=args.furniture_room,
        furniture_fields=args.furniture_fields, furniture_menu=args.furniture_menu,
        furniture_icon=args.furniture_icon, furniture_ground=args.furniture_ground,
        furniture_pockets=args.furniture_pockets, save_codec=args.save_codec, save_runtime=args.save_runtime,
        collection=args.collection, catalogue=args.catalogue, shops=args.shops,
        shop_actors=args.shop_actors, shop_floor=args.shop_floor, hra=args.hra, feng_shui=args.feng_shui,
        houses=args.villager_houses, villager_readers=args.villager_readers,
        villager_selection=args.villager_selection, villager_rewards=args.villager_rewards,
        clothing=args.clothing, speed_bag_sound=args.speed_bag_sound, speed_bag=args.speed_bag)
    for name, data in {'animal-forest-v3-asset-loader.z64': image, 'asset-loader.ups': patch,
                      'build.json': (json.dumps(report, indent=2) + '\n').encode()}.items():
        write_new(out / name, data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
