"""Convert every GAFE01-r0 islander accessory into a separate native object."""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import sha256, u32
from gc_names import rel_sections, symbol_data
from map_artwork import compile_commands
from title_assets import model_texture_shape, pack4, untile
from toolchain import IMAGE
from v3_furniture_art import SEGMENT, command_source, parse_model, verify_sources
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import (DRAW_STRIDE, data_pointers, native_palette,
                             normalise_vertex_flags, symbol_span)

ACCESSORIES = ('anrium1', 'bag1', 'bag2', 'biscus1', 'biscus2', 'biscus3', 'biscus4',
               'hasu1', 'hat1', 'hat2', 'hat3', 'rei1', 'rei2', 'zinnia1', 'zinnia2', 'cobra1')
PROFILE_TABLE = 'profile_table$395'
PROFILE_TABLE_SHA = '0a54d36b4eda12e5c0c22c2ede016dbcc082060c63e6a0d96c0a9e31f23e9c98'
VERIFIED_ART_SHA = 'a721b129f98959916d0d7cd6c73c9d60d8e2db9f815fcd832f4dfe3b3cac808c'


def load_objects(directory, rel, symbols):
    """Reuse the source-bound, compiled batch without trusting an edited receipt."""
    verify_sources(rel, symbols)
    receipt = (directory/'art.json').read_bytes()
    if sha256(receipt) != VERIFIED_ART_SHA:
        raise ValueError('Accessory dependency manifest is not the verified conversion')
    report, artifacts, bindings = json.loads(receipt), {}, {}
    for row in report['objects']:
        data = (directory/row['object_file']).read_bytes()
        if len(data) != row['object_bytes'] or sha256(data) != row['object_sha256']:
            raise ValueError('Accessory dependency object differs from its verified conversion')
        file = 'accessory-'+row['object_file']
        artifacts[file] = data
        for consumer in row['consumers']:
            index = consumer['donor_villager_index']
            if index in bindings:
                raise ValueError('Duplicate villager accessory dependency')
            bindings[index] = {**consumer, 'key': row['key'], 'tool': row['tool'],
                'object_file': file, 'object_bytes': len(data), 'object_sha256': sha256(data),
                'native_model_offset': row['native_model_offset'],
                'source_manifest_sha256': VERIFIED_ART_SHA, 'runtime_attached': False}
    return artifacts, bindings


def text_data_relocations(rel):
    """Read actual same-module PPC references, preserving halfword relocations."""
    sections = rel_sections(rel)
    module, table, size = u32(rel, 0), u32(rel, 0x28), u32(rel, 0x2C)
    if not size or size % 8 or table+size > len(rel):
        raise ValueError('Invalid accessory source relocation table')
    imports = list(struct.iter_unpack('>II', rel[table:table+size]))
    starts = {first for _, first in imports}
    if len(starts) != len(imports) or any(not 0 <= first < len(rel) for first in starts):
        raise ValueError('Invalid accessory relocation stream offsets')
    result = []
    for imported_module, first in imports:
        limit = min((at for at in starts if at > first), default=len(rel))
        section, address, ended = None, 0, False
        for at in range(first, limit-7, 8):
            delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, at)
            if kind == 203:
                ended = True
                break
            if kind == 202:
                if target_section >= len(sections):
                    raise ValueError('Invalid accessory relocation source section')
                section, address = target_section, 0
                continue
            if section is None:
                raise ValueError('Accessory relocation has no source section')
            address += delta
            if address > sections[section][1]:
                raise ValueError('Accessory relocation escapes its source section')
            if (kind not in (0, 201, 204) and section == 1
                    and imported_module == module and target_section == 5):
                if target >= sections[5][1]:
                    raise ValueError('Accessory PPC data reference escapes its target')
                result.append((address, kind, target))
        if not ended:
            raise ValueError('Unterminated accessory relocation stream')
    return result


def command_records(raw):
    """Locate resource loads without interpreting triangle payloads as opcodes."""
    if not raw or len(raw) % 8:
        raise ValueError('Incomplete accessory display list')
    at = 0
    while at < len(raw):
        a, b = struct.unpack_from('>II', raw, at)
        yield at, a, b
        count = (a >> 17 & 127)+1
        size = (1+(max(0, count-3)+3)//4)*8 if a >> 24 == 0x0A else 8
        if at+size > len(raw):
            raise ValueError('Accessory packed triangles exceed their display list')
        at += size


def prepare(rel, symbols_bytes):
    verify_sources(rel, symbols_bytes)
    symbols = symbols_bytes.decode()
    sections = rel_sections(rel)
    table = symbol_data(rel, symbols, PROFILE_TABLE)
    if (symbol_span(symbols, PROFILE_TABLE) != (0x42034, 136)
            or sha256(table) != PROFILE_TABLE_SHA):
        raise ValueError('Changed actual tool-to-accessory profile table')
    spans = [(name, int(at, 16), int(size, 16)) for name, at, size in re.findall(
        r'^(crw_\w+) = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', symbols, re.M)]
    text_refs = text_data_relocations(rel)
    draw = symbol_data(rel, symbols, 'npc_draw_data_tbl')
    consumers = {tool: [] for tool in range(52, 68)}
    for index in range(216, 236):
        tool, joint = struct.unpack_from('>2h', draw, index*DRAW_STRIDE+104)
        if tool == -1:
            if joint != -1:
                raise ValueError('Accessory-free donor has an attachment joint')
            continue
        if tool not in consumers or joint not in (13, 25):
            raise ValueError('Unreviewed islander accessory or joint')
        consumers[tool].append({'donor_villager_index': index, 'joint': joint})
    if any(len(rows) != 1 for rows in consumers.values()):
        raise ValueError('Changed sixteen-islander accessory bindings')

    prepared = []
    for tool, key in enumerate(ACCESSORIES, 52):
        profile_name = 'T_'+key.capitalize()+'_Profile'
        profile_at, profile_size = symbol_span(symbols, profile_name)
        profile = symbol_data(rel, symbols, profile_name)
        profile_id = struct.unpack_from('>H', table, tool*2)[0]
        expected_profile = struct.pack('>HBBIHHI', profile_id, 5, 0, 0x30, 0, 16, 0x1D4)+bytes(20)
        if profile_size != 36 or profile != expected_profile:
            raise ValueError('Changed accessory actor identity, size, or scalar behaviour')
        functions = data_pointers(rel, profile_at, profile_size, expected_section=1)
        if (set(functions) != {profile_at+16, profile_at+20, profile_at+24, profile_at+28}
                or functions[profile_at+20] != 0x4B38C
                or rel[sections[1][0]+0x4B38C:sections[1][0]+0x4B394] != bytes.fromhex('386000004E800020')):
            raise ValueError(f'Changed {key} constructor/move/draw bindings or no-op destructor')
        draw_at = functions[profile_at+28]
        draw_symbols = re.findall(r'^(a\w+_actor_draw) = \.text:0x'+f'{draw_at:08X}'+
                                  r';[^\n]* size:0x([0-9A-Fa-f]+) ', symbols, re.M)
        if len(draw_symbols) != 1:
            raise ValueError('Missing unique accessory draw function')
        draw_name, draw_size = draw_symbols[0][0], int(draw_symbols[0][1], 16)
        name = 'crw_cobra_model' if key == 'cobra1' else f'crw_{key}_body_model'
        start, size = symbol_span(symbols, name)
        refs = [(at-draw_at, kind, target) for at, kind, target in text_refs
                if draw_at <= at < draw_at+draw_size]
        if sorted((kind, target) for _, kind, target in refs) != [(4, start), (6, start)]:
            raise ValueError('Accessory draw function does not bind its exact model')
        raw = symbol_data(rel, symbols, name)
        pointers = data_pointers(rel, start, size)
        palettes, textures, vertex_arrays = set(), {}, set()
        for pos, a, _ in command_records(raw):
            if a >> 24 not in (0xF0, 0xFD, 0x01):
                continue
            target = pointers.get(start+pos+4)
            if target is None:
                raise ValueError('Missing accessory resource pointer')
            if a >> 24 == 0xF0:
                palettes.add(target)
            elif a >> 24 == 0xFD:
                width, height, fmt, depth = model_texture_shape(raw[pos:pos+8])
                if fmt != 2 or depth != 0 or width*height//2 > 2048:
                    raise ValueError('Unsupported accessory texture format or dimensions')
                if target in textures and textures[target] != (width, height):
                    raise ValueError('Accessory reinterprets a texture with different dimensions')
                textures[target] = width, height
            else:
                matches = [(n, at, length) for n, at, length in spans
                           if n.endswith('_v') and at <= target < at+length]
                if len(matches) != 1:
                    raise ValueError('Accessory vertices do not bind a unique complete array')
                vertex_arrays.add(matches[0])
        if len(palettes) != 1 or len(vertex_arrays) != 1 or not textures:
            raise ValueError('Unreviewed accessory palette or vertex arrangement')
        palette = next(iter(palettes))
        vertex_name, vertex, vertex_size = next(iter(vertex_arrays))
        resources, offsets, body = [], {}, bytearray()
        for target, expected_size, kind in [(palette, 32, 'palette'),
                *((at, w*h//2, 'texture') for at, (w, h) in textures.items()),
                (vertex, vertex_size, 'vertices')]:
            matches = [(n, size) for n, at, size in spans if at == target]
            if len(matches) != 1 or matches[0][1] != expected_size:
                raise ValueError('Accessory resource symbol or size mismatch')
            resource_name = matches[0][0]
            source = symbol_data(rel, symbols, resource_name)
            if data_pointers(rel, target, expected_size):
                raise ValueError('Unexpected pointer in accessory raw data')
            if kind == 'palette':
                converted = native_palette(source)
            elif kind == 'texture':
                converted = pack4(untile(source, *textures[target], 4))
            else:
                converted = normalise_vertex_flags(source)[0]
            if len(converted) != expected_size:
                raise ValueError('Accessory resource conversion changes its allocation')
            body.extend(bytes((-len(body)) % 32))
            offsets[target] = len(body)
            resources.append({'symbol': resource_name, 'kind': kind, 'donor_offset': target,
                'native_offset': len(body), 'bytes': len(source), 'source_sha256': sha256(source),
                'output_sha256': sha256(converted),
                **({'width': textures[target][0], 'height': textures[target][1]} if kind == 'texture' else {})})
            body.extend(converted)
        rows = parse_model(raw, start, pointers, palette, textures, vertex, vertex_size, accessory=True)
        prepared.append({'key': key, 'tool': tool, 'consumers': consumers[tool],
            'profile_symbol': profile_name, 'profile_id': profile_id, 'profile_sha256': sha256(profile),
            'draw_function': draw_name, 'draw_function_offset': draw_at,
            'draw_function_sha256': sha256(rel[sections[1][0]+draw_at:sections[1][0]+draw_at+draw_size]),
            'draw_model_relocations': refs, 'model_symbol': name, 'model_source_sha256': sha256(raw),
            'resources': resources, 'offsets': offsets, 'body': bytes(body), 'rows': rows})
    return prepared


def build_objects(rel, symbols, out):
    prepared = prepare(rel, symbols)
    out.mkdir(parents=True, exist_ok=False)
    sources, sections = [], []
    for entry in prepared:
        source, part_sections = command_source({entry['key']: {'rows': entry['rows']}}, entry['offsets'])
        sources.append(source)
        sections.extend(part_sections)
    source = '\n'.join(sources)
    source_file = out/'commands.c'
    source_file.write_text(source)
    compiled = compile_commands(out/'gbi', source_file, tuple(sections))
    report = {'format': 'AFV3-ACCESSORY-ART-1', 'donor': DONOR,
        'source_rel_sha256': REL_SHA, 'source_symbols_sha256': SYMBOLS_SHA,
        'profile_table_sha256': PROFILE_TABLE_SHA, 'compiler_image': IMAGE,
        'command_source_sha256': sha256(source.encode()), 'objects': [],
        'runtime_installed': False, 'selectable': False}
    for entry in prepared:
        asset = bytearray(entry['body'])
        asset.extend(bytes((-len(asset)) % 8))
        model_at = len(asset)
        commands = compiled[entry['key']]
        asset.extend(commands)
        asset.extend(bytes((-len(asset)) % 16))
        file = entry['key']+'.n64obj.bin'
        (out/file).write_bytes(asset)
        record = {k: v for k, v in entry.items() if k not in ('body', 'rows', 'offsets')}
        record.update(object_file=file, object_bytes=len(asset), object_sha256=sha256(asset),
            native_model_offset=model_at, native_model_bytes=len(commands),
            native_model_sha256=sha256(commands), segment=f'{SEGMENT:08X}',
            triangles=sum(len(row.get('triangles', ())) for row in entry['rows']),
            runtime_installed=False, selectable=False)
        report['objects'].append(record)
    (out/'art.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, default=ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh accessory output directory')
    report = build_objects(read_donor(args.disc)['rel'], args.symbols.read_bytes(), args.output.resolve())
    print(json.dumps({'output': str(args.output), 'accessories': len(report['objects']),
        'bytes': sum(row['object_bytes'] for row in report['objects']), 'runtime_installed': False}, indent=2))


if __name__ == '__main__':
    main()
