"""Convert complete campfire, bonfire, and light-switching tent-model assets.

Keep the real rigs, two-texture flame effects, palette endpoints, and callback
dependencies. This converter does not install or pretend to supply behaviours.
"""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import sha256
from apply_translation import write_new
from gc_names import rel_sections, symbol_data
from item_identity_sheet import SHEET_SHA, sheet_rows
from map_artwork import compile_commands
from title_assets import pack4, untile
from toolchain import IMAGE
from v3_furniture_art import SEGMENT, command_source, parse_model, verify_sources
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import data_pointers, native_palette, normalise_vertex_flags, symbol_span


@dataclass(frozen=True)
class CampingActor:
    item: int
    name: str
    stem: str
    profile: str
    callback: str
    palettes: tuple
    textures: tuple
    vertices: int
    models: tuple
    scalar_hex: str
    price: int
    feng: int
    catalogue_position: int
    preview_mode: int
    preview_hex: str


ACTORS = (
    CampingActor(0x335C, 'campfire', 'int_ike_tent_fire01', 'iam_ike_tent_fire01', 'fITF',
        (('int_sum_ayu_pal', 0x849D60), ('int_ike_tent_fire01_pal', 0x849D80),
         ('int_ike_kama_danro01_pal', 0x849DA0)),
        (('act_mus_ayu_body_txt', 48, 32, 'ci4', 0x849DC0),
         ('int_ike_tent_fire01_pole1_tex_txt', 32, 8, 'ci4', None),
         ('int_ike_tent_fire01_tree2_tex_txt', 16, 16, 'ci4', None),
         ('int_ike_tent_fire01_tree1_tex_txt', 16, 16, 'ci4', None),
         ('int_ike_kama_danrotree1_tex_txt', 16, 16, 'ci4', 0x84A240),
         ('int_ike_tent_fire01_fire_pic_i4', 32, 32, 'i4', None),
         ('int_ike_tent_fire01_fire2_pic_i4', 32, 64, 'i4', None)),
        126, (('body', 'int_ike_tent_firetree_model', 0x378), ('flame', 'int_ike_fire_model', 0x70)),
        '422400003c23d70a0400000000000000', 1360, 0, 464, 0, '3f666666c0400000'),
    CampingActor(0x3360, 'bonfire', 'int_ike_tent_fire02', 'iam_ike_tent_fire02', 'fITF02',
        (('int_ike_tent_fire02_pal', None),),
        (('int_ike_tent_fire02_tree3_tex_txt', 16, 16, 'ci4', None),
         ('int_ike_tent_fire02_tree2_tex_txt', 16, 16, 'ci4', None),
         ('int_ike_tent_fire02_tree5_tex_txt', 32, 8, 'ci4', None),
         ('int_ike_tent_fire02_tree1_tex_txt', 32, 8, 'ci4', None),
         ('int_ike_tent_fire02_f2_4i4_pic_i4', 32, 64, 'i4', None),
         ('int_ike_tent_fire02_tex_4i4_pic_i4', 64, 32, 'i4', None)),
        99, (('body', 'int_ike_tent_firetree02_model', 0x270), ('flame', 'int_ike_fire1_model', 0x78)),
        '422400003c23d70a0505000000000000', 2240, 0, 463, 19, '3f5c28f6c0400000'),
    CampingActor(0x336C, 'tent model', 'int_tak_tent', 'iam_tak_tent', 'fTTnt',
        (('int_tak_tent_pal', None), ('int_tak_tent_on_pal', None), ('int_tak_tent_off_pal', None)),
        (('int_tak_tent_1_tex', 16, 64, 'ci4', None), ('int_tak_tent_2_tex', 16, 16, 'ci4', None)),
        151, (('green', 'int_tak_tent_green_on_model', 0x58), ('body', 'int_tak_tent_body_onT_model', 0x68),
              ('detail', 'int_tak_tent_etc_onT_model', 0x110), ('light', 'int_tak_tent_light_offT_model', 0x60)),
        '417b33333c23d70a0400000000008000', 2550, 0x100, 553, 0, '3f666666c0400000'),
)


def exact_symbol(symbols, name, size, address=None):
    rows = [(int(at, 16), int(n, 16)) for at, n in re.findall(
        r'^' + re.escape(name) + r' = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', symbols, re.M)]
    if address is not None:
        rows = [row for row in rows if row[0] == address]
    if len(rows) != 1 or rows[0][1] != size:
        raise ValueError('Changed or ambiguous complete camping source: ' + name)
    return rows[0][0]


def identity_evidence(path):
    if sha256(path.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed camping identity worksheet')
    cells = list(sheet_rows(path, 'Items'))
    result = []
    for actor in ACTORS:
        matches = [(n, c) for n, c in cells if c.get('E') == f'{actor.item:04X}']
        if (len(matches) != 1 or matches[0][1].get('J') != actor.name
                or any(matches[0][1].get(k) != '-' for k in ('C', 'H', 'CG', 'CJ'))):
            raise ValueError('Camping actor has a conflicting native identity')
        result.append({'item_id': f'{actor.item:04X}', 'sheet_row': matches[0][0],
                       'native_id_name_and_artwork_absent': True})
    return result


def source_metadata(rel, symbols, actor):
    verify_sources(rel, symbols)
    text, sections = symbols.decode(), rel_sections(rel)
    base = sections[5][0]
    profile_at = exact_symbol(text, actor.profile, 52)
    func = exact_symbol(text, actor.callback + '_func', 20)
    profile = rel[base + profile_at:base + profile_at + 52]
    if (profile != bytes(32) + bytes.fromhex(actor.scalar_hex) + bytes(4)
            or data_pointers(rel, profile_at, 52) != {profile_at + 48: func}
            or rel[base + func:base + func + 20] != bytes(20)):
        raise ValueError('Changed complete camping profile or callback table')
    callbacks, targets = [], {}
    names = ('ct', 'mv', 'dw', 'dt') if actor.item == 0x336C else ('ct', 'mv', 'dw')
    for i, name in enumerate(names):
        symbol = actor.callback + '_' + name
        found = re.findall(r'^' + symbol + r' = \.text:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', text, re.M)
        if len(found) != 1:
            raise ValueError('Changed camping callback identity')
        at, size = (int(n, 16) for n in found[0])
        if at & 3 or not size or size & 3 or at + size > sections[1][1]:
            raise ValueError('Camping callback leaves donor code')
        targets[func + i * 4] = at
        callbacks.append({'symbol': symbol, 'text_offset': at, 'bytes': size,
            'source_sha256': sha256(rel[sections[1][0] + at:sections[1][0] + at + size])})
    if data_pointers(rel, func, 20, expected_section=1) != targets:
        raise ValueError('Camping callbacks differ from the actual profile')
    index = 1024 + (actor.item - 0x3000) // 4
    for at in (0x39FB4, 0x7B5B0):
        row = at + index * 4
        if data_pointers(rel, row, 4) != {row: profile_at}:
            raise ValueError('Camping quality-table identity changed')
    names = symbol_data(rel, text, 'ftrName2_table')
    name = names[(index - 1024) * 16:(index - 1023) * 16]
    prices = symbol_data(rel, text, 'ftr_price_table')
    catalogue = symbol_data(rel, text, 'mCL_furniture_list')
    found = [(n, mode) for n, (i, mode) in enumerate(struct.iter_unpack('>HH', catalogue)) if i == index]
    draw = symbol_data(rel, text, 'furniture_draw_data$436')
    groups = []
    list_names = re.findall(r'^(ftr_list\w*) =', text, re.M)
    if len(list_names) != 23 or len(set(list_names)) != 23:
        raise ValueError('Changed full acquisition-list inventory')
    for key in list_names:
        raw = symbol_data(rel, text, key)
        ids = struct.unpack('>' + str(len(raw) // 2) + 'H', raw)
        if not ids or ids[-1] != 0 or 0 in ids[:-1]:
            raise ValueError('Changed acquisition list or terminator')
        if actor.item in ids:
            groups.append((key, ids.count(actor.item)))
    if (name != actor.name.encode().ljust(16, b' ')
            or struct.unpack_from('>H', prices, index * 2)[0] != actor.price
            or found != [(actor.catalogue_position, actor.preview_mode)]
            or draw[actor.preview_mode * 8:actor.preview_mode * 8 + 8].hex() != actor.preview_hex
            or groups != [('ftr_listTent', 1)]
            or rel[base + 0x4FAFC + index * 4:base + 0x4FAFC + index * 4 + 4] != bytes.fromhex('d4052500')
            or struct.unpack_from('>H', rel, base + 0x4EBF0 + index * 2)[0] != actor.feng):
        raise ValueError('Changed camping gameplay metadata')
    return {'id': f'{DONOR}/item/{actor.item:04X}', 'item_id': f'{actor.item:04X}',
        'name': actor.name, 'donor_runtime_index': index, 'price': actor.price,
        'footprint': '2x2' if actor.item == 0x3360 else '1x1',
        'donor_profile_scalar_hex': actor.scalar_hex, 'profile_source_sha256': sha256(profile),
        'callbacks': callbacks, 'donor_list': 'ftr_listTent', 'catalogue_orderable': False,
        'catalogue_position': actor.catalogue_position, 'preview_mode': actor.preview_mode,
        'donor_preview_scalar_hex': actor.preview_hex, 'donor_hra_hex': 'd4052500',
        'donor_birth_category': 37, 'hra_points': 412, 'feng_hex': f'{actor.feng:04x}',
        'runtime_installed': False, 'selectable': False, 'behaviour_installed': False,
        'acquisition_installed': False}


def prepare(rel, symbols, actor):
    if actor not in ACTORS:
        raise ValueError('Unreviewed camping actor')
    details = source_metadata(rel, symbols, actor)
    text, base = symbols.decode(), rel_sections(rel)[5][0]
    body, resources, offsets = bytearray(), [], {}
    def source(name, size, address=None):
        at = exact_symbol(text, name, size, address)
        return at, rel[base + at:base + at + size]
    def append(name, size, convert, *, address=None, kind, alignment=32, **extra):
        at, raw = source(name, size, address)
        if data_pointers(rel, at, size) or at in offsets:
            raise ValueError('Pointer or duplicated raw camping resource')
        converted = convert(raw)
        if len(converted) != size:
            raise ValueError('Incomplete camping array conversion')
        body.extend(bytes(-len(body) % alignment))
        offset = len(body)
        offsets[at] = offset
        body.extend(converted)
        resources.append({'symbol': name, 'donor_offset': at, 'native_offset': offset,
            'bytes': size, 'kind': kind, 'source_sha256': sha256(raw),
            'output_sha256': sha256(converted), **extra})
        return at
    palettes = tuple(append(name, 32, native_palette, address=address, kind='rgba16')
                     for name, address in actor.palettes)
    textures, types = {}, {}
    for name, w, h, kind, address in actor.textures:
        at = append(name, w * h // 2, lambda b, w=w, h=h: pack4(untile(b, w, h, 4)),
                    address=address, kind=kind, width=w, height=h)
        textures[at], types[at] = (w, h), kind
    vertex = append(actor.stem + '_v', actor.vertices * 16,
                    lambda b: normalise_vertex_flags(b)[0], kind='vertices')
    rig = {}
    if actor.item != 0x336C:
        for label, prefix, suffix, size in (
                ('flags', 'cKF_ckcb_r_', '_tbl', 3), ('constants', 'cKF_c_', '_tbl', 24),
                ('animation', 'cKF_ba_r_', '', 20), ('joints', 'cKF_je_r_', '_tbl', 36),
                ('skeleton', 'cKF_bs_r_', '', 8)):
            name = prefix + actor.stem + suffix
            rig[label] = source(name, size)
            if label in ('flags', 'constants'):
                append(name, size, lambda b: b, kind=label, alignment=4)
        if (rig['flags'][1] != bytes(3) or rig['constants'][1].hex() != '0000000000000000000000000000fc7c0000000000000000'):
            raise ValueError('Changed constant fire pose or channel flags')
    models = {}
    for label, name, size in actor.models:
        at, raw = source(name, size)
        flame = label == 'flame'
        selected_textures = {at: shape for at, shape in textures.items() if types[at] == ('i4' if flame else 'ci4')}
        mode = ({'tent': True} if actor.item == 0x336C else
                {'fire_effect': 1 if actor.item == 0x335C else 2} if flame else {'campfire_body': True})
        models[label] = {'symbol': name, 'donor_offset': at, 'source_sha256': sha256(raw),
            'rows': parse_model(raw, at, data_pointers(rel, at, size),
                palettes[0] if actor.item == 0x336C else palettes, selected_textures,
                vertex, actor.vertices * 16, **mode)}
    if rig:
        animation_at, animation = rig['animation']
        if (animation != bytes(16) + struct.pack('>hh', -1, 101) or
                data_pointers(rel, animation_at, 20) !=
                {animation_at: rig['flags'][0], animation_at + 12: rig['constants'][0]}):
            raise ValueError('Changed fire animation header or null-track dependencies')
        joints_at, joints = rig['joints']
        height, flag = (800, 0) if actor.item == 0x335C else (2700, 1)
        expected = struct.pack('>IBB3hIBB3hIBB3h', 0, 1, 0, 0, 0, 0,
                               0, 1, 0, 0, height, 0, 0, 0, flag, 0, 0, 0)
        if (joints != expected or data_pointers(rel, joints_at, 36) !=
                {joints_at: models['body']['donor_offset'], joints_at + 24: models['flame']['donor_offset']}):
            raise ValueError('Changed complete fire hierarchy or draw flags')
        skeleton_at, skeleton = rig['skeleton']
        if (skeleton != bytes.fromhex('0302000000000000') or
                data_pointers(rel, skeleton_at, 8) != {skeleton_at + 4: joints_at}):
            raise ValueError('Changed three-joint/two-draw fire rig')
        details.update(frame_count=101, joints=3, displayed_joints=2,
            keyframe_tracks=0, constant_components=12, repeat_speed=0.5,
            billboard_joint=2, dynamic_scroll_segment='09000000',
            scroll_dimensions=[[32, 64], [32, 32] if actor.item == 0x335C else [64, 32]],
            scroll_velocity=[[0, -6], [0, 0]] if actor.item == 0x335C else [[0, -3], [-2, 0]],
            donor_loop_sound=0x5D if actor.item == 0x335C else 0x5C)
    else:
        details.update(dynamic_palette_segment='08000000', palette_entries=16,
            palette_fade_step=0.1, interaction_bits='8000',
            dynamic_palette_allocation_bytes=32, dynamic_palette_alignment=32,
            draw_order=['green', 'body', 'detail', 'light'], all_parts_opaque=True)
    return bytes(body), resources, offsets, models, rig, details


def finish(body, offsets, models, rig, compiled):
    if set(compiled) != set(models):
        raise ValueError('Missing complete camping model part')
    asset, mapped, records = bytearray(body), dict(offsets), []
    for label, model in models.items():
        code = compiled[label]
        if not code or len(code) % 8 or code[-8:] != struct.pack('>II', 0xDF000000, 0):
            raise ValueError('Invalid complete native camping model')
        asset.extend(bytes(-len(asset) % 8))
        at = len(asset)
        mapped[model['donor_offset']] = at
        asset.extend(code)
        records.append({'part': label, 'symbol': model['symbol'], 'native_offset': at,
            'bytes': len(code), 'source_sha256': model['source_sha256'], 'output_sha256': sha256(code),
            'triangles': sum(len(row.get('triangles', ())) for row in model['rows'])})
    headers, pointers = {}, []
    for label in ('animation', 'joints', 'skeleton') if rig else ():
        source_at, raw = rig[label]
        refs = ({0: rig['flags'][0], 12: rig['constants'][0]} if label == 'animation' else
                {0: models['body']['donor_offset'], 24: models['flame']['donor_offset']} if label == 'joints' else
                {4: rig['joints'][0]})
        fixed = bytearray(raw)
        asset.extend(bytes(-len(asset) % 4))
        at = len(asset)
        for offset, target in refs.items():
            if target not in mapped or not 0 <= mapped[target] < at or fixed[offset:offset + 4] != bytes(4):
                raise ValueError('Unbound camping model/rig pointer')
            struct.pack_into('>I', fixed, offset, SEGMENT + mapped[target])
            pointers.append({'offset': at + offset, 'target_offset': mapped[target]})
        mapped[source_at] = at
        asset.extend(fixed)
        headers[label] = {'native_offset': at, 'bytes': len(fixed),
            'source_sha256': sha256(raw), 'output_sha256': sha256(fixed)}
    asset.extend(bytes(-len(asset) % 16))
    if len(asset) > 0x2400:
        raise ValueError('Complete camping actor exceeds the current native furniture bank')
    return bytes(asset), records, headers, pointers


def build(rel, symbols, output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ output')
    verify_sources(rel, symbols)
    evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx')
    output.mkdir(parents=True)
    objects = []
    for actor in ACTORS:
        body, resources, offsets, models, rig, details = prepare(rel, symbols, actor)
        directory = output / actor.name.replace(' ', '-')
        directory.mkdir()
        source, sections = command_source(models, offsets)
        write_new(directory / 'commands.c', source.encode())
        compiled = compile_commands(directory / 'gbi', directory / 'commands.c', sections)
        asset, records, headers, pointers = finish(body, offsets, models, rig, compiled)
        file = actor.name.replace(' ', '-') + '.n64obj.bin'
        write_new(output / file, asset)
        objects.append({**details, 'object_file': file, 'object_bytes': len(asset), 'object_sha256': sha256(asset),
            'resources': resources, 'models': records, 'headers': headers, 'pointers': pointers,
            'segment': f'{SEGMENT:08X}', 'bank_capacity': 0x2400, 'command_source_sha256': sha256(source.encode())})
    report = {'format': 'AFV3-CAMPING-ACTOR-ART-1', 'converter_version': 1,
        'donor': DONOR, 'source_rel_sha256': REL_SHA, 'source_symbols_sha256': SYMBOLS_SHA,
        'compiler_image': IMAGE, 'objects': objects, 'identity_evidence': evidence,
        'runtime_installed': False, 'web_patcher_enabled': False,
        'pending': ['native callback and sound adapters', 'cartridge integration',
                    'summer-camper acquisition', 'ordinary interaction and persistence']}
    write_new(output / 'art.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    report = build(donor['rel'], symbols, args.output)
    print(json.dumps([{'name': row['name'], 'bytes': row['object_bytes'], 'sha256': row['object_sha256']}
                      for row in report['objects']], indent=2))
