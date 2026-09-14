"""Convert reviewed static GC furniture into self-contained native N64 objects.

This builds local assets, not selectable or playable imports. Furniture loading,
item IDs, acquisition, placement, and saved-item readers are separate runtime work.
"""
import argparse
from dataclasses import dataclass
import json
from pathlib import Path
import re
import struct

from aflib import sha256
from gc_names import rel_sections
from map_artwork import compile_commands
from stall_model_source import packed
from title_assets import model_texture_shape, pack4, untile
from toolchain import IMAGE
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import data_pointers, native_palette, normalise_vertex_flags, symbol_span

SEGMENT = 0x06000000
CONVERTER_VERSION = 1


@dataclass(frozen=True)
class Pilot:
    key: str
    item: int
    name: str
    stem: str
    profile: str
    textures: tuple
    lighting_map: int


PILOTS = (
    Pilot('haz-mat-barrel', 0x3224, 'haz-mat barrel', 'int_iku_hazardous',
          'iam_iku_hazardous_top', (('mark', 32, 32), ('top', 32, 32), ('yoko', 64, 32)), 1),
    Pilot('oil-drum', 0x32B8, 'oil drum', 'int_iku_orange', 'iam_iku_orange',
          (('b', 32, 32), ('a', 32, 32), ('c', 64, 32)), 0),
)


def verify_sources(rel, symbols):
    if sha256(rel) != REL_SHA or sha256(symbols) != SYMBOLS_SHA:
        raise ValueError('Furniture conversion requires the pinned English donor and symbols')


def scalar_profile(pilot):
    # Height, scale, 1x1 shape, collision kind, rotation, lighting, contact,
    # padding, and interaction. No rig, texture animation, or callback table.
    return struct.pack('>ff6BH', 18.0, 0.01, 4, 0, 0, pilot.lighting_map, 0, 0, 0)


def parse_model(raw, start, pointers, palette, textures, vertex, vertex_size):
    """Decode only the reviewed static CI4 command subset; never copy GX loads."""
    if not raw or len(raw) % 8:
        raise ValueError('Incomplete furniture display list')
    result, used = [], set()
    at, loaded, first_vertex, material, have_palette = 0, 0, 0, None, False
    while at < len(raw):
        a, b = struct.unpack_from('>II', raw, at)
        op = a >> 24
        row = {'words': (a, b), 'opcode': op}
        if op in (0xF0, 0xFD, 0x01):
            fixup = start + at + 4
            if b or fixup not in pointers:
                raise ValueError('Missing or nonzero furniture data relocation')
            row['target'] = pointers[fixup]
            used.add(fixup)
        if op == 0xD7:
            if (a, b) != (0xD7000002, 0):
                raise ValueError('Unsupported furniture texture scale')
        elif op == 0xF0:
            if a != 0xF08F4010 or row['target'] != palette:
                raise ValueError('Unsupported furniture palette load')
            have_palette = True
        elif op == 0xFD:
            shape = model_texture_shape(raw[at:at + 8])
            target = row['target']
            if (not have_palette or target not in textures or
                    shape != (*textures[target], 2, 0)):
                raise ValueError('Unsupported furniture CI4 texture or palette')
            # Consume the paired Dolphin tile command. These two models clamp
            # every material in both directions, with no coordinate shifts.
            if at + 16 > len(raw) or raw[at + 8:at + 16] != struct.pack('>II', 0xD2F0F000, 0):
                raise ValueError('Unsupported furniture wrap mode')
            row['shape'] = shape[:2]
            material = target
            at += 8
        elif op == 0x01:
            count = a >> 12 & 255
            offset = row['target'] - vertex
            if (not 1 <= count <= 32 or a != 0x01000000 | count << 12 | count << 1 or
                    offset < 0 or offset % 16 or offset + count * 16 > vertex_size):
                raise ValueError('Furniture vertex load escapes its array')
            loaded, first_vertex = count, offset // 16
            row.update(count=count, first_vertex=first_vertex)
        elif op == 0x0A:
            if not loaded or material is None:
                raise ValueError('Furniture triangles lack vertices or a material')
            count = (a >> 17 & 127) + 1
            size = (1 + (max(0, count - 3) + 3) // 4) * 8
            if at + size > len(raw):
                raise ValueError('Furniture triangles escape the display list')
            row['triangles'] = packed(raw[at:at + size], loaded)
            row['global_triangles'] = [tuple(v + first_vertex for v in t) for t in row['triangles']]
            row['material'] = material
            at += size - 8
        elif op == 0xFC:
            if (a, b) not in ((0xFC127E60, 0xFFFFF3F8), (0xFC11FE04, 0xFFFFF3F8)):
                raise ValueError('Unsupported furniture colour combiner')
        elif op == 0xE2:
            if a != 0xE200001C or b not in (0xC8113078, 0xC8104DD8):
                raise ValueError('Unsupported furniture render mode')
        elif op == 0xFA:
            if a not in (0xFA000080, 0xFA0000FF) or b != 0xFFFFFFFF:
                raise ValueError('Unsupported furniture primitive colour')
        elif op == 0xD9:
            if a != 0xD9000000 or b not in (0x230405, 0x230005):
                raise ValueError('Unsupported furniture geometry mode')
        elif op == 0xDF:
            if (a, b) != (0xDF000000, 0) or at + 8 != len(raw):
                raise ValueError('Invalid furniture display-list terminator')
        else:
            raise ValueError(f'Unsupported furniture graphics opcode {op:02X}')
        result.append(row)
        at += 8
    if result[-1]['opcode'] != 0xDF or not any('triangles' in r for r in result):
        raise ValueError('Furniture model lacks triangles or termination')
    if used != set(pointers):
        raise ValueError('Unaccounted furniture data relocation')
    return result


def prepare(rel, symbols_bytes, pilot):
    verify_sources(rel, symbols_bytes)
    if pilot not in PILOTS:
        raise ValueError('Unreviewed furniture pilot')
    symbols = symbols_bytes.decode()
    base = rel_sections(rel)[5][0]
    profile_at, profile_size = symbol_span(symbols, pilot.profile)
    index = 1024 + (pilot.item - 0x3000) // 4
    quality = re.findall(r'^furniture_quality = \.data:0x([0-9A-F]+);[^\n]* size:0x13C8 ', symbols, re.M)
    if sorted(int(a, 16) for a in quality) != [0x39FB4, 0x7B5B0]:
        raise ValueError('Changed donor furniture profile tables')
    for table in quality:
        entry = int(table, 16) + index * 4
        if data_pointers(rel, entry, 4) != {entry: profile_at}:
            raise ValueError('Furniture item does not resolve to its reviewed profile')
    profile_raw = rel[base + profile_at:base + profile_at + profile_size]
    if profile_raw != bytes(32) + scalar_profile(pilot) + bytes(4):
        raise ValueError('Furniture profile needs unported behaviour or changed dimensions')

    body = bytearray()
    resources, offsets, texture_shapes = [], {}, {}

    def add(name, size, convert):
        at, actual_size = symbol_span(symbols, name)
        if actual_size != size:
            raise ValueError('Changed furniture resource size')
        source = rel[base + at:base + at + size]
        converted = convert(source)
        if len(converted) != size:
            raise ValueError('Furniture resource changes its expected allocation')
        body.extend(bytes((-len(body)) % 32))
        offset = len(body)
        offsets[at] = offset
        body.extend(converted)
        resources.append({'symbol': name, 'donor_offset': at, 'native_offset': offset,
                          'bytes': size, 'source_sha256': sha256(source),
                          'output_sha256': sha256(converted)})
        return at

    pal = add(pilot.stem + '_pal', 32, native_palette)
    for suffix, w, h in pilot.textures:
        at = add(pilot.stem + '_' + suffix + '_tex_txt', w * h // 2,
                 lambda data, w=w, h=h: pack4(untile(data, w, h, 4)))
        texture_shapes[at] = (w, h)
    vertex = add(pilot.stem + '_v', 36 * 16, lambda data: normalise_vertex_flags(data)[0])
    # These are plain arrays, not containers of unconverted pointers.
    for resource in resources:
        if data_pointers(rel, resource['donor_offset'], resource['bytes']):
            raise ValueError('Unexpected relocation in furniture texels or vertices')
    models = {}
    profile_pointers = {}
    for label, suffix, slot, size in (('opaque', 'b', 0, 0x98), ('translucent', 'a', 8, 0x68)):
        name = pilot.stem + '_model_' + suffix + '_model'
        at, actual_size = symbol_span(symbols, name)
        if actual_size != size:
            raise ValueError('Changed furniture model size')
        raw = rel[base + at:base + at + size]
        pointers = data_pointers(rel, at, size)
        models[label] = {'symbol': name, 'donor_offset': at, 'source_sha256': sha256(raw),
                         'rows': parse_model(raw, at, pointers, pal, texture_shapes, vertex, 36 * 16)}
        profile_pointers[profile_at + slot] = at
    if data_pointers(rel, profile_at, profile_size) != profile_pointers:
        raise ValueError('Furniture profile has missing, extra, or unported dependencies')
    names_at, names_size = symbol_span(symbols, 'ftrName2_table')
    name_at = base + names_at + (pilot.item - 0x3000) // 4 * 16
    if names_size != 242 * 16 or rel[name_at:name_at + 16] != pilot.name.encode().ljust(16, b' '):
        raise ValueError('Furniture name and reviewed donor item identity disagree')
    return bytes(body), resources, offsets, models


def command_source(models, offsets):
    output = ['/* Generated from local donor data; not a distribution asset. */', '#include <PR/mbi.h>']
    sections = []
    for label, model in models.items():
        values, count = [], 0

        def emit(value, commands=1):
            nonlocal count
            values.append('    ' + value + ',')
            count += commands

        emit('gsDPPipeSync()')
        emit('gsDPSetTextureLUT(G_TT_RGBA16)')
        for row in model['rows']:
            op = row['opcode']
            if op == 0xD7:
                # GX zero means its normal scale; native zero collapses UVs.
                emit('gsSPTexture(0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_ON)')
            elif op == 0xF0:
                emit('gsDPPipeSync()')
                emit(f"gsDPLoadTLUT_pal16(15, 0x{SEGMENT + offsets[row['target']]:08X})", 6)
            elif op == 0xFD:
                w, h = row['shape']
                if w * h // 2 > 2048:
                    raise ValueError('Furniture texture exceeds CI4 TMEM capacity')
                emit('gsDPPipeSync()')
                emit(f"gsDPLoadTextureBlock_4b(0x{SEGMENT + offsets[row['target']]:08X}, "
                     f'G_IM_FMT_CI, {w}, {h}, 15, G_TX_CLAMP, G_TX_CLAMP, '
                     f'{w.bit_length() - 1}, {h.bit_length() - 1}, 0, 0)', 7)
            elif op == 0x01:
                # The donor pointer can address the middle of the vertex array.
                first = row['first_vertex']
                target = offsets[row['target'] - first * 16] + first * 16
                emit(f"gsSPVertex(0x{SEGMENT + target:08X}, {row['count']}, 0)")
            elif op == 0x0A:
                triangles = row['triangles']
                for i in range(0, len(triangles), 2):
                    if i + 1 < len(triangles):
                        args = (*triangles[i], 0, *triangles[i + 1], 0)
                        emit('gsSP2Triangles(' + ', '.join(map(str, args)) + ')')
                    else:
                        emit('gsSP1Triangle(' + ', '.join(map(str, (*triangles[i], 0))) + ')')
            elif op in (0xFC, 0xE2, 0xFA, 0xD9, 0xDF):
                # Only the explicitly decoded compatible F3DEX2 state/end
                # commands reach here; Dolphin loads and packed triangles do not.
                a, b = row['words']
                emit(f'{{{{0x{a:08X}, 0x{b:08X}}}}}')
            else:
                raise ValueError('Unconverted furniture command in native compiler input')
        output.append(f'const Gfx furniture_{label}[] __attribute__((section(".{label}"), aligned(8))) = {{')
        output.extend(values)
        output.append('};')
        sections.append((label, count * 8))
    return '\n'.join(output) + '\n', tuple(sections)


def native_profile(pilot, object_size, model_offsets, vrom_start):
    """Bind an installed object's verified VROM; this does not register an item."""
    if (pilot not in PILOTS or type(object_size) is not int or
            not 0 < object_size < 0x1000000 or object_size % 16 or
            type(vrom_start) is not int or not 0 < vrom_start <= 0x4000000 - object_size or
            vrom_start % 16 or set(model_offsets) != {'opaque', 'translucent'} or
            any(type(at) is not int or at < 0 or at % 8 or at + 8 > object_size for at in model_offsets.values())):
        raise ValueError('Furniture profile exceeds its native object bounds')
    words = (vrom_start, vrom_start + object_size, SEGMENT, SEGMENT + object_size,
             SEGMENT + model_offsets['opaque'], 0, SEGMENT + model_offsets['translucent'], 0, 0, 0, 0, 0)
    return struct.pack('>12I', *words) + scalar_profile(pilot) + bytes(4)


def build_objects(rel, symbols, out):
    verify_sources(rel, symbols)
    out.mkdir(parents=True, exist_ok=False)
    report = {'format': 'AFV3-FURNITURE-ART-1', 'converter_version': CONVERTER_VERSION,
              'donor': DONOR, 'source_rel_sha256': REL_SHA, 'source_symbols_sha256': SYMBOLS_SHA,
              'compiler_image': IMAGE, 'objects': [], 'runtime_installed': False,
              'status': 'converted_static_assets_not_playable_imports'}
    for pilot in PILOTS:
        body, resources, offsets, models = prepare(rel, symbols, pilot)
        source, sections = command_source(models, offsets)
        directory = out / pilot.key
        directory.mkdir()
        source_file = directory / 'commands.c'
        source_file.write_text(source)
        compiled = compile_commands(directory / 'gbi', source_file, sections)
        asset, destinations, model_report = bytearray(body), {}, []
        for label, model in models.items():
            asset.extend(bytes((-len(asset)) % 8))
            at = len(asset)
            destinations[label] = at
            asset.extend(compiled[label])
            model_report.append({'layer': label, 'symbol': model['symbol'],
                                 'source_sha256': model['source_sha256'], 'native_offset': at,
                                 'bytes': len(compiled[label]), 'output_sha256': sha256(compiled[label]),
                                 'triangles': sum(len(r.get('triangles', ())) for r in model['rows'])})
        asset.extend(bytes((-len(asset)) % 16))
        name = pilot.key + '.n64obj.bin'
        (out / name).write_bytes(asset)
        report['objects'].append({'id': f'{DONOR}/item/{pilot.item:04X}', 'name': pilot.name,
                                  'target_item_id': None, 'selectable': False, 'object_file': name,
                                  'object_bytes': len(asset), 'object_sha256': sha256(asset),
                                  'segment': f'{SEGMENT:08X}', 'resources': resources, 'models': model_report,
                                  'native_profile_scalar_hex': scalar_profile(pilot).hex(),
                                  'profile_symbol': pilot.profile, 'model_offsets': destinations,
                                  'command_source_sha256': sha256(source.encode())})
    (out / 'art.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh output directory; existing builds are preserved')
    report = build_objects(read_donor(args.disc)['rel'], args.symbols.read_bytes(), args.output.resolve())
    print(json.dumps({'output': str(args.output), 'objects': [
        {'name': r['name'], 'bytes': r['object_bytes'], 'sha256': r['object_sha256']} for r in report['objects']],
        'runtime_installed': False}, indent=2))


if __name__ == '__main__':
    main()
