"""Build the full native campsite scene/field packet and runtime adapters.

Keep original scene and field records. These outputs still need cartridge,
event, camper identity/conversation, lighting, and ordinary gameplay integration.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from apply_translation import write_new
from gc_names import rel_sections
from v3_asset_loader import compile_part
from v3_camping_actor_art import exact_symbol
from v3_furniture_art import verify_sources
from v3_import_catalog import ROOT, REL_SHA, SYMBOLS_SHA
from v3_villager_art import data_pointers

BASE = ROOT / 'build/v3-fire-runtime-02/animal-forest-v3-asset-loader.z64'
BASE_SHA = 'e2a8ddfb41b7ad7d111cf666dc4b4706046d6edff1fe88968e925603a9345ad5'
ART = ROOT / 'build/v3-campsite-art-01'
ART_SHA = 'e34166e906e8ba9edc35a14468a473222adb9005844b4a6988e012255fe30529'
FG_SHA = '287dc0506d7b623ba6b98f3ed4463d87482fccd4c070347899a32d65e412333b'
SCENE, DONOR_SCENE, FIELD_ID = 35, 51, 0x3012
SCENE_VROM, ACTORS_VROM, FIELD_VROM = 0x02480000, 0x02480100, 0x02480200
INTERIOR_VROM, LANTERN_VROM, EXTERIOR_VROM, SHADOW_VROM = 0x02484000, 0x02489000, 0x0248A000, 0x0248C000
CODE_ADDRESS, DATA_ADDRESS, DATA_SIZE = 0x804A0100, 0x804A1000, 0x1000
NATIVE_FIELDS, FIELD_BYTES, OLD_SCENES = 0x01148000, 0x88, 35


def prepare(native, current, rel, symbols, foreground, art_report):
    verified_rom(native)
    verify_sources(rel, symbols)
    if sha256(current) != BASE_SHA or sha256(foreground) != FG_SHA or sha256(art_report) != ART_SHA:
        raise ValueError('Changed current cartridge, complete donor foreground, or scenery report')
    report = json.loads(art_report)
    if (report['runtime_installed'] or len(report['objects']) != 4
            or report['source_rel_sha256'] != REL_SHA or report['source_symbols_sha256'] != SYMBOLS_SHA):
        raise ValueError('Unexpected campsite scenery contract')
    art = {p['part']: p for p in report['objects']}
    original_files, files = by_vrom(native), by_vrom(current)
    code = files[CODE_VROM].extract(current)
    original_code = original_files[CODE_VROM].extract(native)
    base, text = rel_sections(rel)[5][0], symbols.decode()

    def donor(name, size):
        at = exact_symbol(text, name, size)
        return at, rel[base + at:base + at + size]

    # Controller profile IDs and the 16-/20-byte native actor/door layouts agree
    # with these actual donor records, not an assumption about every GC profile.
    scene_at, scene = donor('tent_info', 56)
    player_at, player = donor('TENT_player_data', 16)
    ctrl_at, controls = donor('TENT_ctrl_actor_data', 22)
    door_at, door = donor('TENT_door_data', 20)
    native_igloo = files[0x018E7000].extract(current)
    if (native_igloo != original_files[0x018E7000].extract(native)
            or controls != native_igloo[0x48:0x5E] or door != native_igloo[0x60:0x74]
            or player.hex() != '00000078000000640000000000000000'
            or scene != bytes.fromhex('090000000000000004010000000000000001000000000000'
                '0803000000000000010b00000000000005010100a00003010a00000000000000')
            or data_pointers(rel, scene_at, 56) !=
                {scene_at + 12: door_at, scene_at + 20: player_at, scene_at + 36: ctrl_at}
            or any(data_pointers(rel, a, len(r)) for a, r in ((player_at, player), (ctrl_at, controls), (door_at, door)))):
        raise ValueError('Changed complete donor/native scene or controller layouts')
    native_scene = bytearray(native_igloo)
    native_scene[0x38:0x48] = player
    # Retain native segment-2 pointers, complete door/controller records, and padding.

    fdd_at, fdd = donor('data_fdd', 0x2150)
    gc_row_at = fdd_at + DONOR_SCENE * 0xA4
    gc_row = fdd[DONOR_SCENE * 0xA4:(DONOR_SCENE + 1) * 0xA4]
    actors_at, actors = donor('tent_actable', 48)
    expected_actors = bytes.fromhex('d08f000000000000000000000303ff000000000000000000'
                                  'ffff00000000000000000000000000000000000000000000')
    if (gc_row != bytes.fromhex('3012010105bc') + bytes(0xA4 - 6)
            or data_pointers(rel, gc_row_at, 0xA4) != {gc_row_at + 0x90: actors_at}
            or actors != expected_actors or data_pointers(rel, actors_at, 48)):
        raise ValueError('Changed complete campsite field or camper placement')
    # The donor has 70 combination slots; native has 56. Only the first is used
    # in this one-acre room; every omitted slot must be zero.
    fields = files[NATIVE_FIELDS].extract(current)
    if fields != original_files[NATIVE_FIELDS].extract(native) or len(fields) != 0x12A0 or any(fields[35 * 0x88:]):
        raise ValueError('Changed original 35 native field records or padding')
    row = bytearray(FIELD_BYTES)
    row[:0x74] = gc_row[:0x74]
    struct.pack_into('>5I', row, 0x74, 0x02000000, ACTORS_VROM, ACTORS_VROM + 48,
                     0x02000000, 0x02000030)
    new_fields = fields[:35 * FIELD_BYTES] + row

    combo_at, combinations = donor('data_combi_table', 0x8A0)
    combo = combinations[367 * 6:368 * 6]
    if combo != bytes.fromhex('00f30199ff00') or data_pointers(rel, combo_at + 367 * 6, 6):
        raise ValueError('Changed campsite background/foreground identity')
    bg_at, bg_all = donor('data_bgd', 0x4D7EC)
    matches = [(bg_at + i, bg_all[i:i + 0x434]) for i in range(0, len(bg_all), 0x434)
               if struct.unpack_from('>H', bg_all, i)[0] == 0xF3]
    if len(matches) != 1:
        raise ValueError('Missing or ambiguous complete campsite background')
    bg_at, bg = matches[0]
    if (sha256(bg) != '4b41d06a3ca262a0f9230de76b5bcadc84c474c6ba90efede147884e5a976c0f'
            or data_pointers(rel, bg_at, 0x434) != {bg_at + 4: 0xAB7698, bg_at + 8: 0xAB7690}
            or bg[:28] != bytes.fromhex('00f30000') + bytes(24) or any(bg[0x41C:])):
        raise ValueError('Changed collision, sound sources, or complete background pointers')
    # All five height fields match within each donor cell. Native and GC name
    # the last two corners differently; equality makes this mapping unambiguous.
    collision = tuple(v[0] for v in struct.iter_unpack('>I', bg[28:0x41C]))
    if (len(collision) != 256 or set(collision) != {0x10842108, 0x18C63188, 0x1CE739C8, 0x7FFFFFC8}
            or any(len({word >> shift & 31 for shift in (26, 21, 16, 11, 6)}) != 1
                   or word & 63 != 8 for word in collision)):
        raise ValueError('Campsite collision needs an explicit native attribute/corner conversion')
    backgrounds = original_files[0x0114A000].extract(native)
    if any(struct.unpack_from('>H', backgrounds, i)[0] == 0xF3
           for i in range(0, len(backgrounds) - 0x433, 0x434)):
        raise ValueError('Campsite background would replace a native identity')
    fg_matches = [foreground[i:i + 518] for i in range(0, len(foreground), 518)
                  if struct.unpack_from('>H', foreground, i)[0] == 0x199]
    if len(fg_matches) != 1 or sha256(fg_matches[0]) != 'c381e32bdd6b6e2cb7e919bc22121f28ab189c02ade1ebf395616b604869b306':
        raise ValueError('Changed complete campsite foreground')
    fg = fg_matches[0]
    cells = [v[0] for v in struct.iter_unpack('>H', fg[2:514])]
    if set(cells) != {0xFFFE, 0xFFFF, 0x4080} or [i for i, v in enumerate(cells) if v == 0x4080] != [98, 99]:
        raise ValueError('Campsite contains an unmapped foreground item')

    packet = bytearray(DATA_SIZE)
    struct.pack_into('>IIIHH', packet, 0, 0x41464350, 1, DATA_SIZE, SCENE, DONOR_SCENE)
    struct.pack_into('>II', packet, 0x20, SCENE_VROM, SCENE_VROM + len(native_scene))
    converted_bg = bytearray(bg)
    struct.pack_into('>II', converted_bg, 4, 0x06000000 + art['interior']['model']['native_offset'],
                     0x06000000 + art['interior']['empty_model_offset'])
    struct.pack_into('>II', converted_bg, 20, INTERIOR_VROM, INTERIOR_VROM + art['interior']['object_bytes'])
    packet[0x40:0x474] = converted_bg
    packet[0x480:0x480 + len(fg)] = fg
    packet[0x700:0x788] = row
    packet[-16:] = bytes.fromhex('AFCA5EED') * 4
    status_at = 0x8010EAA0 - CODE_RAM
    status_bytes = 35 * 20
    if code[status_at:status_at + status_bytes] != original_code[status_at:status_at + status_bytes]:
        raise ValueError('Changed original native scene descriptors')
    return {'scene.bin': bytes(native_scene), 'actors.bin': actors, 'fields.bin': bytes(new_fields),
            'packet.bin': bytes(packet)}, {'scene': SCENE, 'donor_scene': DONOR_SCENE,
        'field_id': '3012', 'background_id': '00F3', 'foreground_id': '0199', 'camper_mask_id': 'D08F',
        'native_fields_sha256': sha256(fields), 'native_scene_table_sha256': sha256(code[status_at:status_at + status_bytes]),
        'donor_background_sha256': sha256(bg), 'donor_foreground_sha256': sha256(fg),
        'source_fg_sha256': FG_SHA, 'collision_cells': 256, 'exit_cells': [98, 99],
        'native_existing_scenes': 35, 'native_scenes_with_addition': 36,
        'scene_buffer_bytes': 0xA000, 'scene_model_bytes': art['interior']['object_bytes']}


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
    current = BASE.read_bytes()
    rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    fg = (ROOT / 'build/gamecube/files/forest_1st.arc.unpacked/data/fgdata.bin').read_bytes()
    parts, details = prepare(native, current, rel, symbols, fg, (ART / 'art.json').read_bytes())
    output.mkdir(parents=True)
    code, compiled = compile_part('campsite_scene', output / 'code')
    for name, data in parts.items():
        write_new(output / name, data)
    report = {'format': 'AFV3-CAMPSITE-SCENE-1', 'code': compiled, 'native_contract': details,
        'source_cartridge_sha256': BASE_SHA, 'source_rel_sha256': REL_SHA,
        'source_symbols_sha256': SYMBOLS_SHA, 'art_report_sha256': ART_SHA,
        'parts': {name: {'bytes': len(data), 'sha256': sha256(data)} for name, data in parts.items()},
        'code_ram': CODE_ADDRESS, 'packet_ram': DATA_ADDRESS, 'packet_bytes': DATA_SIZE,
        'scene_vrom': SCENE_VROM, 'actors_vrom': ACTORS_VROM, 'fields_vrom': FIELD_VROM,
        'runtime_installed': False, 'acquisition_installed': False, 'web_patcher_enabled': False}
    write_new(output / 'scene.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = build(args.output)
    print(json.dumps({'code_bytes': result['code']['bytes'], 'parts': result['parts']}, indent=2))
