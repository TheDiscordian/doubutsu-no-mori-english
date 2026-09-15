"""Convert the complete GC summer campsite scenery, without enabling an event.

The enterable tent and its scene lantern are not the collectible tent/lantern.
Keep every source vertex, texture, material, and dynamic segment dependency.
"""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import struct

from aflib import sha256
from apply_translation import write_new
from gc_names import rel_sections
from map_artwork import compile_commands
from stall_model_source import packed
from title_assets import model_texture_shape, pack4, untile
from toolchain import IMAGE
from v3_camping_actor_art import exact_symbol
from v3_furniture_art import SEGMENT, verify_sources
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import data_pointers, native_palette, normalise_vertex_flags


@dataclass(frozen=True)
class Scenery:
    key: str
    palettes: tuple
    textures: tuple
    vertex: str
    count: int
    model: str
    model_size: int
    triangles: int


PARTS = (
    Scenery('exterior', ('obj_s_tent_mat_pal', 'obj_s_tent_main_pal'),
        (('obj_s_tent_mat', 32, 16, 'ci4'), ('obj_s_tent_wall1', 32, 64, 'ci4'),
         ('obj_s_tent_wall2', 64, 64, 'ci4'), ('obj_s_tent_wall3', 32, 64, 'ci4')),
        'obj_s_tent_v', 105, 'obj_s_tent_model', 0x190, 61),
    Scenery('shadow', (), (('obj_s_tent_shadow', 16, 16, 'i4'),),
        'obj_s_tent_shadow_v', 28, 'obj_s_tent_shadow_modelT', 0x68, 16),
    Scenery('interior', ('rom_tent_box_pal', 'rom_tent_can_pal',
        'rom_tent_mono1_pal', 'rom_tent_gas_pal'),
        (('rom_tent_enter', 64, 32, 'ci4'), ('rom_tent_floor', 64, 64, 'ci4'),
         ('rom_tent_wall1', 64, 64, 'ci4'), ('rom_tent_wall2', 64, 64, 'ci4'),
         ('rom_tent_bou', 8, 8, 'ci4'), ('rom_tent_mono1', 64, 64, 'ci4'),
         ('rom_tent_can', 16, 32, 'ci4'), ('rom_tent_conpas', 16, 16, 'ci4'),
         ('rom_tent_box', 32, 64, 'ci4'), ('rom_tent_kage_m', 16, 16, 'i4'),
         ('rom_tent_gas', 16, 64, 'ci4'), ('rom_tent_kage_s', 16, 16, 'i4'),
         ('rom_tent_kage_b', 32, 16, 'i4')),
        'rom_tent_v', 349, 'rom_tent_model', 0x448, 267),
    Scenery('lantern', ('obj_tent_lamp1_rgb_ci4_pal', 'obj_tent_lamp2_rgb_ci4_pal'),
        (('obj_tent_lamp1', 32, 64, 'ci4'), ('obj_tent_lamp2_rgb_ci4', 32, 64, 'ci4')),
        'obj_tent_lamp_v', 45, 'obj_tent_lamp_model', 0xA0, 25),
)
SHADE_COMBINE = (0xFC127E60, 0xFFFFF3F8)
SHADOW_COMBINE = (0xFCFF9DFF, 0xFFFDFE38)
WINDOW_COMBINE = (0xFC11FFFF, 0xFFFFF238)
LAMP_COMBINE = (0xFC277E04, 0x1FFCF3F8)
SHADOW_FLAGS = bytes.fromhex('00000000000001010001010000010100000101000001010000010100')


def parse_model(raw, start, pointers, part, palettes, textures, vertex):
    """Decode only the four reviewed source lists and their exact state families."""
    if part not in PARTS or len(raw) != part.model_size:
        raise ValueError('Unreviewed or incomplete campsite model')
    rows, used, loaded_palettes = [], set(), set()
    at, loaded, first, material, windows, image_count = 0, 0, 0, None, 0, 0
    combines = {'exterior': (SHADE_COMBINE, WINDOW_COMBINE),
        'shadow': (SHADOW_COMBINE,), 'interior': (SHADE_COMBINE, SHADOW_COMBINE),
        'lantern': (LAMP_COMBINE,)}[part.key]
    while at < len(raw):
        a, b = struct.unpack_from('>II', raw, at)
        op = a >> 24
        row = {'opcode': op, 'words': (a, b)}
        dynamic_vertex = part.key == 'shadow' and op == 1 and b == 0x08000000
        if op in (0xF0, 0xFD, 1) and not dynamic_vertex:
            fixup = start + at + 4
            if b != 0 or fixup not in pointers:
                raise ValueError('Missing campsite data relocation')
            row['target'] = pointers[fixup]
            used.add(fixup)
        if op == 0xD7:
            if (a, b) != (0xD7000002, 0):
                raise ValueError('Changed campsite texture scale')
        elif op == 0xF0:
            bank = a >> 16 & 15
            if (bank not in ((15, 14) if part.key == 'lantern' else (15,))
                    or a != 0xF0804010 | bank << 16 or row['target'] not in palettes
                    or part.key == 'lantern' and row['target'] != palettes[15 - bank]):
                raise ValueError('Changed campsite palette bank or resource')
            row['palette'] = bank
            loaded_palettes.add(bank)
        elif op == 0xFD:
            shape = model_texture_shape(raw[at:at + 8])
            if row['target'] not in textures:
                raise ValueError('Unbound campsite texture')
            w, h, kind = textures[row['target']]
            if shape != (w, h, 4 if kind == 'i4' else 2, 0) or at + 16 > len(raw):
                raise ValueError('Changed complete campsite texture shape')
            tile_a, tile_b = struct.unpack_from('>II', raw, at + 8)
            tile, bank = (image_count, 15 - image_count) if part.key == 'lantern' else (0, 15)
            if tile > 1:
                raise ValueError('Too many campsite lantern textures')
            wraps = (tile_a >> 10 & 3, tile_a >> 8 & 3)
            allowed = ((2, 0),) if part.key == 'lantern' else ((0, 0),) if part.key == 'shadow' else ((0, 0), (2, 0), (2, 2))
            expected = 0xD2F00000 | tile << 16 | bank << 12 | wraps[0] << 10 | wraps[1] << 8
            if tile_b or tile_a != expected or wraps not in allowed:
                raise ValueError('Changed campsite texture tile')
            if kind == 'ci4' and bank not in loaded_palettes:
                raise ValueError('Campsite texture has no loaded palette')
            row.update(shape=(w, h), kind=kind, tile=tile, palette=bank, wraps=wraps,
                       tmem=tile * 128)
            material = row['target']
            image_count += 1
            at += 8
        elif op == 1:
            count = a >> 12 & 255
            offset = 0 if dynamic_vertex else row['target'] - vertex
            if (not 1 <= count <= 32 or a != 0x01000000 | count << 12 | count << 1
                    or offset < 0 or offset % 16 or offset + count * 16 > part.count * 16
                    or part.key == 'shadow' and (not dynamic_vertex or count != part.count)):
                raise ValueError('Campsite vertex load leaves its complete array')
            loaded, first = count, offset // 16
            row.update(count=count, first=first)
            if dynamic_vertex:
                row['dynamic_vertex'] = 0x08000000
        elif op == 0x0A:
            count = (a >> 17 & 127) + 1
            size = (1 + (max(0, count - 3) + 3) // 4) * 8
            if not loaded or material is None or at + size > len(raw):
                raise ValueError('Incomplete campsite triangles or draw state')
            row['triangles'] = packed(raw[at:at + size], loaded)
            row['global_triangles'] = [tuple(i + first for i in t) for t in row['triangles']]
            at += size - 8
        elif op == 0xFC:
            if (a, b) not in combines:
                raise ValueError('Changed campsite colour combiner')
        elif op == 0xE2:
            allowed = (0xC8113078,) if part.key in ('exterior', 'lantern') else (0xC8104DD8,) if part.key == 'shadow' else (0xC8113078, 0xC8104DD8)
            if a != 0xE200001C or b not in allowed:
                raise ValueError('Changed campsite render mode')
        elif op == 0xFA:
            if (a, b) not in (((0xFA000080, 0xFFFFFFFF), (0xFA000078, 0x280028FF))
                    if part.key == 'interior' else ((0xFA000080, 0xFFFFFFFF),)
                    if part.key == 'exterior' else ()):
                raise ValueError('Changed campsite primitive colour')
        elif op == 0xD9:
            if a != 0xD9000000 or b not in ((0x230405, 0x210405) if part.key == 'exterior' else (0x210405,)):
                raise ValueError('Changed campsite geometry mode')
        elif op == 0xDE:
            if part.key != 'exterior' or windows or (a, b) != (0xDE000000, 0x08000000):
                raise ValueError('Unbound campsite dynamic display list')
            windows += 1
        elif op == 0xDF:
            if (a, b) != (0xDF000000, 0) or at + 8 != len(raw):
                raise ValueError('Changed campsite terminator')
        else:
            raise ValueError(f'Unsupported campsite graphics opcode {op:02X}')
        rows.append(row)
        at += 8
    if (not rows or rows[-1]['opcode'] != 0xDF or used != set(pointers)
            or windows != (part.key == 'exterior')
            or sum(len(r.get('triangles', ())) for r in rows) != part.triangles
            or part.key == 'lantern' and image_count != 2):
        raise ValueError('Incomplete campsite geometry or dependencies')
    return rows


def prepare(rel, symbols, part):
    verify_sources(rel, symbols)
    if part not in PARTS:
        raise ValueError('Unreviewed campsite scenery')
    text, base = symbols.decode(), rel_sections(rel)[5][0]
    body, resources, offsets = bytearray(), [], {}

    def append(name, size, kind, transform, **extra):
        at = exact_symbol(text, name, size)
        raw = rel[base + at:base + at + size]
        if len(raw) != size or data_pointers(rel, at, size) or at in offsets:
            raise ValueError('Incomplete, repeated, or relocated campsite array')
        converted = transform(raw)
        if len(converted) != size:
            raise ValueError('Campsite conversion loses source data')
        body.extend(bytes(-len(body) % 32))
        dst = offsets[at] = len(body)
        body.extend(converted)
        resources.append({'symbol': name, 'donor_offset': at, 'native_offset': dst,
            'bytes': size, 'kind': kind, 'source_sha256': sha256(raw),
            'output_sha256': sha256(converted), **extra})
        return at

    palettes = tuple(append(name, 32, 'rgba16', native_palette) for name in part.palettes)
    textures = {append(name, w * h // 2, kind,
        lambda b, w=w, h=h: pack4(untile(b, w, h, 4)), width=w, height=h): (w, h, kind)
        for name, w, h, kind in part.textures}
    vertex = append(part.vertex, part.count * 16, 'vertices', lambda b: normalise_vertex_flags(b)[0])
    if part.key == 'shadow':
        def flags(raw):
            if raw != SHADOW_FLAGS:
                raise ValueError('Changed campsite projected-shadow fixed vertices')
            return raw
        flags_at = append('aTnt_shadow_vtx_fix_flg_table', 28, 'shadow_flags', flags)
        descriptor = exact_symbol(text, 'aTnt_shadow_data', 20)
        model_at = exact_symbol(text, part.model, part.model_size)
        if (rel[base + descriptor:base + descriptor + 20] != struct.pack('>IIfII', 28, 0, 60.0, 0, 0)
                or data_pointers(rel, descriptor, 20) !=
                {descriptor + 4: flags_at, descriptor + 12: vertex, descriptor + 16: model_at}):
            raise ValueError('Changed complete projected-shadow descriptor')
    start = exact_symbol(text, part.model, part.model_size)
    raw = rel[base + start:base + start + part.model_size]
    rows = parse_model(raw, start, data_pointers(rel, start, part.model_size), part, palettes, textures, vertex)
    model = {'symbol': part.model, 'donor_offset': start, 'source_sha256': sha256(raw), 'rows': rows}
    if part.key == 'interior':
        empty = exact_symbol(text, 'rom_tent_modelT', 8)
        if rel[base + empty:base + empty + 8] != struct.pack('>II', 0xDF000000, 0) or data_pointers(rel, empty, 8):
            raise ValueError('Campsite gains an unconverted translucent room model')
    return bytes(body), resources, offsets, model


def command_source(part, offsets, model):
    """Compile complete native materials, including two CI4 tiles and mixed LUTs."""
    values, count, current_lut = [], 0, None

    def emit(value, commands=1):
        nonlocal count
        values.append('    ' + value + ',')
        count += commands

    emit('gsDPPipeSync()')
    for row in model['rows']:
        op = row['opcode']
        if op == 0xD7:
            emit('gsSPTexture(0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_ON)')
        elif op == 0xF0:
            emit('gsDPPipeSync()')
            emit(f"gsDPLoadTLUT_pal16({row['palette']}, 0x{SEGMENT + offsets[row['target']]:08X})", 6)
        elif op == 0xFD:
            w, h = row['shape']
            kind, tile, bank, tmem = (row[k] for k in ('kind', 'tile', 'palette', 'tmem'))
            # Two 1024-byte lantern textures fit below the native TLUT. A single
            # CI4 texture may occupy all 2048 bytes below it. I4 shadows are small.
            if not 0 < w * h // 2 <= 2048 or tmem * 8 + w * h // 2 > 2048:
                raise ValueError('Campsite texture exceeds its native TMEM allocation')
            emit('gsDPPipeSync()')
            lut = 'G_TT_NONE' if kind == 'i4' else 'G_TT_RGBA16'
            if current_lut != lut:
                emit(f'gsDPSetTextureLUT({lut})')
                current_lut = lut
            wrap_names = {0: 'G_TX_CLAMP', 2: 'G_TX_MIRROR | G_TX_WRAP'}
            wraps = [wrap_names[n] for n in row['wraps']]
            if w & (w - 1) or h & (h - 1):
                raise ValueError('Unreviewed campsite non-power-of-two texture')
            masks = w.bit_length() - 1, h.bit_length() - 1
            fmt, bank = ('G_IM_FMT_I', 0) if kind == 'i4' else ('G_IM_FMT_CI', bank)
            address = SEGMENT + offsets[row['target']]
            if part.key == 'lantern':
                emit(f'gsDPLoadMultiBlock_4b(0x{address:08X}, {tmem}, {tile}, {fmt}, {w}, {h}, {bank}, '
                     f'{wraps[0]}, {wraps[1]}, {masks[0]}, {masks[1]}, 0, 0)', 7)
            else:
                tiled = w % 16 != 0
                macro = 'gsDPLoadTextureTile_4b' if tiled else 'gsDPLoadTextureBlock_4b'
                rect = f'0, 0, {w - 1}, {h - 1}, ' if tiled else ''
                emit(f'{macro}(0x{address:08X}, {fmt}, {w}, {h}, {rect}{bank}, '
                     f'{wraps[0]}, {wraps[1]}, {masks[0]}, {masks[1]}, 0, 0)', 7)
        elif op == 1:
            address = row.get('dynamic_vertex')
            if address is None:
                first = row['first']
                address = SEGMENT + offsets[row['target'] - first * 16] + first * 16
            emit(f"gsSPVertex(0x{address:08X}, {row['count']}, 0)")
        elif op == 0x0A:
            triangles = row['triangles']
            for i in range(0, len(triangles), 2):
                args = (*triangles[i], 0)
                if i + 1 < len(triangles):
                    args += (*triangles[i + 1], 0)
                emit(('gsSP2Triangles(' if len(args) == 8 else 'gsSP1Triangle(') + ', '.join(map(str, args)) + ')')
        elif op == 0xDE:
            emit('gsSPDisplayList(0x08000000)')
        elif op in (0xFC, 0xE2, 0xFA, 0xD9, 0xDF):
            a, b = row['words']
            emit(f'{{{{0x{a:08X}, 0x{b:08X}}}}}')
        else:
            raise ValueError('Unconverted campsite command reaches the compiler')
    source = ['/* Generated from local donor data; not a distribution asset. */',
        '#include <PR/mbi.h>',
        'const Gfx campsite_model[] __attribute__((section(".model"), aligned(8))) = {',
        *values, '};']
    return '\n'.join(source) + '\n', (('model', count * 8),)


def build(rel, symbols, output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    # Decode every source before creating output or starting the compiler.
    prepared = [prepare(rel, symbols, part) for part in PARTS]
    output.mkdir(parents=True)
    objects = []
    for part, (body, resources, offsets, model) in zip(PARTS, prepared, strict=True):
        directory = output / part.key
        directory.mkdir()
        source, sections = command_source(part, offsets, model)
        write_new(directory / 'commands.c', source.encode())
        code = compile_commands(directory / 'gbi', directory / 'commands.c', sections)['model']
        if len(code) % 8 or code[-8:] != struct.pack('>II', 0xDF000000, 0):
            raise ValueError('Invalid native campsite display list')
        asset = bytearray(body)
        asset.extend(bytes(-len(asset) % 8))
        at = len(asset)
        asset.extend(code)
        empty = None
        if part.key == 'interior':
            empty = len(asset)
            asset.extend(struct.pack('>II', 0xDF000000, 0))
        asset.extend(bytes(-len(asset) % 16))
        file = part.key + '.n64scene.bin'
        write_new(output / file, asset)
        objects.append({'part': part.key, 'object_file': file, 'object_bytes': len(asset),
            'object_sha256': sha256(asset), 'segment': f'{SEGMENT:08X}', 'resources': resources,
            'model': {k: v for k, v in model.items() if k != 'rows'} | {
                'native_offset': at, 'bytes': len(code), 'output_sha256': sha256(code),
                'triangles': part.triangles}, 'empty_model_offset': empty,
            'command_source_sha256': sha256(source.encode()),
            'dynamic_dependencies': ({'08000000': 'frame-owned window colour display list'}
                if part.key == 'exterior' else {'08000000': '28 frame-owned projected shadow vertices'}
                if part.key == 'shadow' else {}),
            'runtime_installed': False})
    report = {'format': 'AFV3-CAMPSITE-ART-1', 'converter_version': 1, 'donor': DONOR,
        'source_rel_sha256': REL_SHA, 'source_symbols_sha256': SYMBOLS_SHA, 'compiler_image': IMAGE,
        'objects': objects, 'runtime_installed': False, 'web_patcher_enabled': False,
        'pending': ['native scene and exterior actor', 'event schedule and camper identity',
            'camper English conversations and reward selection', 'scene lighting and collision',
            'ordinary gameplay and persistence']}
    write_new(output / 'art.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    report = build(donor['rel'], symbols, args.output)
    print(json.dumps([{k: row[k] for k in ('part', 'object_bytes', 'object_sha256')}
                      for row in report['objects']], indent=2))
