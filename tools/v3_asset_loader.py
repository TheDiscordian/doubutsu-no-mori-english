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

BASE_SHA = '8bbd1955536a2a3ac9f76d6f323842f5ce25c037e1ff5fd3da9f28d6dfe20507'
MODULE, MODULE_RAM = 0x02800000, 0x801948E0
STARTUP, CONFIG, STATE, STARTUP_END = 0x6000, 0x63E0, 0x63F0, 0x6400
BLOB, BLOB_RAM, BLOB_SIZE, TABLE_OFFSET = 0x03F00000, 0x80460000, 0x2000, 0x1000
OBJECT_TABLE, OBJECT_COUNT, CAPACITY = 0x8010DDD0, 410, 430
STARTUP_CALL, ORIGINAL_CALL = 0x800D65D0, 0x0C0275B4
TEXTURE_BASE, TEXTURE_STRIDE = 0x03F10000, 0x2000
SOURCE_FILES = ('tools/v3_asset_loader.py', 'overlays/v3/startup.c', 'overlays/v3/startup.ld',
                'overlays/v3/asset.c', 'overlays/v3/asset.ld', 'tools/v3_villager_art.py',
                'tools/v3_import_catalog.py')


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
    objects = []
    for i, source in enumerate((primary_source or f'overlays/v3/{part}.c', *extra_sources)):
        obj = 'code.o' if i == 0 else f'extra{i}.o'
        run('gcc', *flags, f'/source/{source}', '-o', obj)
        objects.append(obj)
    run('ld', '-EB', '-T', f'/source/overlays/v3/{part}.ld', '-o', 'code.elf', *objects)
    if run('nm', '--undefined-only', 'code.elf').strip():
        raise ValueError('Unresolved V3 loader symbol')
    symbols = {name: int(address, 16) for address, kind, name in
               (line.split() for line in run('nm', '--defined-only', 'code.elf').splitlines())}
    run('objcopy', '-O', 'binary', '-j', '.text', '-j', '.rodata', 'code.elf', 'code.bin')
    code = (out / 'code.bin').read_bytes()
    entry, expected = {'startup': ('af_v3_startup', MODULE_RAM + STARTUP),
                       'asset': ('af_v3_asset_init', BLOB_RAM + 0x100),
                       'villager': ('af_v3_load_name', BLOB_RAM + 0x4000),
                       'furniture': ('af_v3_furniture_import_profile', BLOB_RAM + 0x5000),
                       'items': ('af_v3_item_name', BLOB_RAM + 0x7300),
                       'room': ('af_v3_room_value', BLOB_RAM + 0x8000),
                       'fields': ('af_v3_field_shop', BLOB_RAM + 0xA400),
                       'menu': ('af_v3_menu_type_80872bb0', BLOB_RAM + 0xA800),
                       'icon': ('af_v3_furniture_icon_type', BLOB_RAM + 0xAB00),
                       'ground': ('af_v3_ground_type_8090f888', BLOB_RAM + 0xAE00)}[part]
    if symbols[entry] != expected:
        raise ValueError('V3 linker moved the public entry')
    write_new(out / 'code.asm', run('objdump', '-d', 'code.elf').encode())
    return code, {'bytes': len(code), 'sha256': sha256(code), 'symbols': symbols,
                  'toolchain': IMAGE, 'flags': flags,
                  'stack_usage': ''.join(p.read_text() for p in sorted(out.glob('*.su')))}


def compose(native, base, changes, added):
    """Preserve current DMA identities and startup copies while adding new files."""
    verified_rom(native)
    if sha256(base) != BASE_SHA:
        raise ValueError('V3 composition requires exact stable V2-11')
    current, original = by_vrom(base), by_vrom(native)
    if not changes and not added:
        return base
    if not set(changes) <= set(current) or set(added) & set(current):
        raise ValueError('Unknown change or colliding V3 addition')
    if any(len(data) != current[v].size or v in (0x1060, 0x19D40) for v, data in changes.items()):
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
            if v != old.vstart or len(data) != old.size:
                moves[old.vstart] = v
            if data != old.extract(native) or old.vstart in moves:
                replacements[old.vstart] = data
    image = bytearray(replace_dma(native, replacements, moves, additions))
    boot = original[0x1060]
    boot_data = current[0x1060].extract(base)
    if base[boot.pstart:boot.pstart + boot.size] != boot_data:
        raise ValueError('V2 physical and virtual startup copies disagree')
    image[boot.pstart:boot.pstart + boot.size] = boot_data
    fix_checksum(image)
    image = bytes(image)
    installed = by_vrom(image)
    if set(installed) != set(current) | set(added):
        raise ValueError('V3 composition loses DMA resources')
    for v, before in current.items():
        actual, expected = installed[v].extract(image), changes.get(v, before.extract(base))
        if v == 0x19D40:
            actual, expected = actual[:16], expected[:16]
        if installed[v].index != before.index or actual != expected:
            raise ValueError(f'V3 composition changes an unrelated resource: {v:08X}')
    if any(installed[v].extract(image) != data for v, data in added.items()):
        raise ValueError('V3 composition does not retain complete added data')
    return image


def build(native, base, rel, symbols, out, *, npc_draw=False, audio_donor=None, text_donor=None,
          furniture=False, furniture_items=False, furniture_room=False, furniture_fields=False,
          furniture_menu=False, furniture_icon=False, furniture_ground=False):
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
    import v3_furniture_icon
    import v3_furniture_ground
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
                    + (v3_furniture_icon.SOURCES if furniture_icon else ())
                    + (v3_furniture_ground.SOURCES if furniture_ground else ()))
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
    startup, startup_report = compile_part('startup', out / 'startup',
        defines=(f'AF_V3_BLOB_SIZE={blob_size}', f'AF_V3_ABI={abi}') if npc_draw else ())
    extra_sources = ('overlays/v3/npc_draw.c', 'overlays/v3/npc_voice.S') if npc_draw else ()
    if audio_donor is not None:
        extra_sources += ('overlays/v3/melody.c',)
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
    if text_donor is not None:
        text_code, text_code_report = compile_part('villager', out / 'villager')
        text_limit = v3_furniture_runtime.CODE if furniture else blob_size - 16
        if furniture_items:
            text_limit = v3_furniture_items.BRIDGE
        if len(text_code) > text_limit - v3_villager_text.CODE:
            raise ValueError('Villager text code exceeds its reservation')
        blob[v3_villager_text.CODE:v3_villager_text.CODE + len(text_code)] = text_code
        text_report = v3_villager_text.install(native, code, module, blob,
            text_code_report['symbols'], *text_donor, symbols)
        text_report['code'] = text_code_report
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
        item_code, item_code_report = compile_part('items', out / 'items')
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
    if len(blob) != blob_size:
        raise ValueError('V3 resident payload differs from startup reservation')
    module[STARTUP:STARTUP + len(startup)] = startup
    struct.pack_into('>4I', module, CONFIG, BLOB, blob_size, zlib.crc32(blob), abi)
    struct.pack_into('>I', code, STARTUP_CALL - CODE_RAM,
                     0x0C000000 | ((MODULE_RAM + STARTUP) >> 2 & 0x3FFFFFF))
    # The native DMA directory has no spare row after the two pilot texture
    # banks. Furniture occupies ROM-only tail slots in the existing V3 file;
    # startup still loads/checks exactly blob_size bytes into its RAM reservation.
    blob_file = bytearray(blob)
    if furniture:
        for vrom, data in sorted(furniture_added.items()):
            offset = vrom - BLOB
            if offset < len(blob_file) or vrom + len(data) > TEXTURE_BASE:
                raise ValueError('Furniture ROM tail overlaps resident or villager data')
            blob_file.extend(bytes(offset - len(blob_file)))
            blob_file.extend(data)
            del additions[vrom]
    additions[BLOB] = bytes(blob_file)
    changes = {CODE_VROM: bytes(code), MODULE: bytes(module), **draw_changes,
               **furniture_changes, **menu_changes, **icon_changes, **ground_changes}
    image = compose(native, base, changes, additions)
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image:
        raise ValueError('V3 asset patch reconstruction failed')
    if sources != {p: sha256((ROOT / p).read_bytes()) for p in source_files}:
        raise ValueError('V3 sources changed during construction')
    label = ('V3 furniture ground integration development 01' if furniture_ground else
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
        'villager_text': text_report, 'furniture': furniture_report, 'furniture_items': items_report,
        'furniture_room': room_report,
        'furniture_fields': fields_report,
        'furniture_menu': menu_report,
        'furniture_icon': icon_report,
        'furniture_ground': ground_report,
        'source_sha256': sha256(native), 'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'sources': sources, 'startup': startup_report, 'asset': helper_report,
        'blob_sha256': sha256(blob), 'resident_blob_bytes': blob_size,
        'blob_file_bytes': len(blob_file), 'original_object_table_sha256': sha256(table),
        'object_capacity': CAPACITY, 'imports': imports, 'rom_bytes': len(image),
        'resident_startup_range': ['8019A8E0', '8019ACE0'],
        'expansion_data_range': ['80460000', f'{BLOB_RAM + blob_size:08X}'], 'ordinary_heap_growth': 0,
        'required_ram_bytes': 0x800000, 'saved_layout_changed': False,
        'saved_format_changed': text_report is not None,
        'imported_default_key_format': 'V3-only four-byte reference' if text_report else None,
        'new_villager_ids_enabled': False, 'native_test': 'pending', 'hardware_test': 'not performed',
        'save_warning': ('Development only; use disposable saves. Imported default references require V3 '
                         'and compatible profile metadata; do not load those saves in V2.' if text_report else
                         'Development loader only; use disposable saves. V3 import/profile compatibility is unverified.'),
        'added_resources': {f'{v:08X}': sha256(data) for v, data in additions.items()},
        'changed_resources': {f'{v:08X}': sha256(data) for v, data in changes.items()}}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
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
    args = p.parse_args()
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
        furniture_icon=args.furniture_icon, furniture_ground=args.furniture_ground)
    for name, data in {'animal-forest-v3-asset-loader.z64': image, 'asset-loader.ups': patch,
                      'build.json': (json.dumps(report, indent=2) + '\n').encode()}.items():
        write_new(out / name, data)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
