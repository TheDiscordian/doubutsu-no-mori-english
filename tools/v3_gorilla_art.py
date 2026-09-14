"""Convert Yodel's complete donor gorilla mesh into a separate native object."""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom, sha256, u32, verified_rom
from gc_names import symbol_data
from map_artwork import compile_commands
from stall_model_source import packed
from title_assets import model_texture_shape
from toolchain import IMAGE
from v3_furniture_art import verify_sources
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import (DRAW_BASE, DRAW_STRIDE, data_pointers, native_species,
                             normalise_vertex_flags, symbol_span)
from v3_villager_mesh import faces

MODEL_LIMIT = 0x2800
SEGMENT = 0x06000000
VERIFIED_ART_SHA = '7e5912b8ee5f5343584790e89b2e2de87b9cbdb9972b7efa1041aa7b69da669c'
BODY_TILES = {0: (0, 16, 8), 0x40: (0x40, 16, 8), 0x80: (0x80, 32, 32),
              0x280: (0x480, 16, 8), 0x2C0: (0x6C0, 16, 16),
              0x340: (0x740, 16, 16), 0x3C0: (0x7C0, 16, 8)}
MUTABLE_TILES = {8: (0x280, 32, 16), 9: (0x380, 32, 16), 10: (0x4C0, 32, 32)}


def load_object(directory, rom, rel, symbols):
    """Reuse the verified complete model while keeping its source identity pinned."""
    verified_rom(rom)
    verify_sources(rel, symbols)
    receipt = (directory/'art.json').read_bytes()
    if sha256(receipt) != VERIFIED_ART_SHA:
        raise ValueError('Gorilla model manifest differs from the verified conversion')
    report = json.loads(receipt)
    data = (directory/report['model_file']).read_bytes()
    if len(data) != report['model_bytes'] or sha256(data) != report['model_sha256']:
        raise ValueError('Gorilla model differs from its verified conversion')
    return data, report


def convert_commands(raw, start, pointers, vertex, vertex_bytes):
    """Translate the reviewed gorilla subset, retaining partial vertex loads."""
    # Decode the entire cache/face stream first so no unloaded vertex or missing
    # resource can reach generated native commands.
    decoded = faces(raw, donor=True, vertex_start=vertex, vertex_bytes=vertex_bytes,
                    pointers=pointers, start=start)
    values, count, state = ['    gsDPPipeSync(),'], 1, {}
    at, materials = 0, []

    def emit(value):
        nonlocal count
        values.append('    '+value+',')
        count += 1

    while at < len(raw):
        a, b = struct.unpack_from('>II', raw, at)
        op, step = a >> 24, 8
        if op == 0xFD:
            width, height, fmt, depth = model_texture_shape(raw[at:at+8])
            pair, zero = struct.unpack_from('>II', raw, at+8)
            segment, source = b >> 24, b & 0xFFFFFF
            expected = BODY_TILES.get(source) if segment == 11 else MUTABLE_TILES.get(segment)
            if (expected is None or segment != 11 and source or expected[1:] != (width, height)
                    or fmt != 2 or depth or zero):
                raise ValueError('Unreviewed gorilla texture identity or dimensions')
            palette = 14 if segment == 10 else 15
            modes = (pair >> 10 & 3, pair >> 8 & 3)
            if (pair != 0xD2F00000 | palette << 12 | modes[0] << 10 | modes[1] << 8
                    or modes not in ((0, 0), (0, 2), (1, 1))
                    or segment == 10 and modes != (1, 1)):
                raise ValueError('Unreviewed gorilla palette, wrapping, or coordinate shifts')
            extent = ((width-1)*4, (height-1)*4)
            step = 16
            if at+24 <= len(raw) and u32(raw, at+16) >> 24 == 0xF2:
                first, last = struct.unpack_from('>II', raw, at+16)
                if first != 0xF2000000 or last not in (0x3C03C, 0x7C03C, 0xFC07C):
                    raise ValueError('Unreviewed gorilla explicit tile extent')
                extent = last >> 12 & 4095, last & 4095
                step += 8
            wrap = {0: 'G_TX_CLAMP', 1: 'G_TX_WRAP', 2: 'G_TX_MIRROR | G_TX_WRAP'}
            emit('gsDPPipeSync()')
            emit(f'gsDPSetTile(G_IM_FMT_CI, G_IM_SIZ_4b, {width//16}, {expected[0]//8}, '
                 f'G_TX_RENDERTILE, {palette}, {wrap[modes[1]]}, {height.bit_length()-1}, 0, '
                 f'{wrap[modes[0]]}, {width.bit_length()-1}, 0)')
            emit(f'gsDPSetTileSize(G_TX_RENDERTILE, 0, 0, {extent[0]}, {extent[1]})')
            materials.append({'source': b, 'tmem': expected[0], 'width': width, 'height': height,
                              'palette': palette, 'wrap': modes, 'extent': extent})
        elif op == 1:
            n, end = a >> 12 & 255, (a & 255)//2
            offset = pointers[start+at+4]-vertex
            emit(f'gsSPVertex(0x{SEGMENT+offset:08X}, {n}, {end-n})')
        elif op == 0x0A:
            n = (a >> 17 & 127)+1
            step = (1+(max(0, n-3)+3)//4)*8
            triangles = packed(raw[at:at+step], 32)
            for i in range(0, len(triangles), 2):
                if i+1 < len(triangles):
                    args = (*triangles[i], 0, *triangles[i+1], 0)
                    emit('gsSP2Triangles('+', '.join(map(str, args))+')')
                else:
                    emit('gsSP1Triangle('+', '.join(map(str, (*triangles[i], 0)))+')')
        elif op == 0xDA:
            if a != 0xDA380003 or b >> 24 != 13 or b & 63 or b & 0xFFFFFF >= 12*64:
                raise ValueError('Gorilla matrix is outside the twelve visible-joint matrices')
            emit(f'gsSPMatrix(0x{b:08X}, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW)')
        elif op in (0xD7, 0xD9, 0xE2, 0xFC, 0xFA):
            expected = {0xD7: (0xD7000002, 0), 0xD9: (0xD9000000, 0x230405),
                        0xE2: (0xE200001C, 0xC8112078), 0xFC: (0xFC127E60, 0xFFFFF3F8),
                        0xFA: (0xFA000080, 0xFFFFFFFF)}[op]
            if (a, b) != expected:
                raise ValueError('Unreviewed gorilla render state')
            # Repeated identical settings within one list have no intervening
            # command that changes that state. Every list still sets its own state.
            if state.get(op) != (a, b):
                if op == 0xD7:
                    emit('gsSPTexture(0xFFFF, 0xFFFF, 0, G_TX_RENDERTILE, G_ON)')
                else:
                    emit(f'{{{{0x{a:08X}, 0x{b:08X}}}}}')
                state[op] = a, b
        elif op == 0xDF:
            emit('gsSPEndDisplayList()')
        else:
            raise ValueError(f'Unconverted gorilla graphics command {op:02X}')
        at += step
    if set(state) != {0xD7, 0xD9, 0xE2, 0xFC, 0xFA}:
        raise ValueError('Gorilla list lacks its complete render state')
    return values, count*8, materials, len(decoded)


def prepare(rom, rel, symbols_bytes):
    verified_rom(rom)
    verify_sources(rel, symbols_bytes)
    symbols = symbols_bytes.decode()
    skeleton_at, skeleton_size = symbol_span(symbols, 'cKF_bs_r_gor_1')
    joint_at, joint_size = symbol_span(symbols, 'cKF_je_r_gor_1_tbl')
    vertex, vertex_bytes = symbol_span(symbols, 'gor_1_v')
    if (skeleton_size, joint_size, vertex_bytes) != (8, 26*12, 429*16):
        raise ValueError('Changed actual donor gorilla model dimensions')
    draw_at = DRAW_BASE+229*DRAW_STRIDE
    draw_pointers = data_pointers(rel, draw_at, DRAW_STRIDE)
    if draw_pointers.get(draw_at+4) != skeleton_at:
        raise ValueError('Yodel does not bind the selected gorilla skeleton')
    skeleton = symbol_data(rel, symbols, 'cKF_bs_r_gor_1')
    if skeleton != bytes.fromhex('1a0c000000000000') or data_pointers(rel, skeleton_at, 8) != {skeleton_at+4: joint_at}:
        raise ValueError('Changed gorilla skeleton or joint-table binding')
    joints = symbol_data(rel, symbols, 'cKF_je_r_gor_1_tbl')
    joint_pointers = data_pointers(rel, joint_at, joint_size)
    if any((p-joint_at) % 12 for p in joint_pointers) or len(joint_pointers) != 12:
        raise ValueError('Changed gorilla visible-joint bindings')
    vertices, changed = normalise_vertex_flags(symbol_data(rel, symbols, 'gor_1_v'))
    spans = {}
    for name, at, size in re.findall(
            r'^(\w+) = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', symbols, re.M):
        spans.setdefault(int(at, 16), []).append((name, int(size, 16)))
    selected = {}
    for pointer in joint_pointers.values():
        names = spans.get(pointer, ())
        if len(names) != 1 or pointer < vertex+vertex_bytes:
            raise ValueError('Gorilla joint has no unique complete model symbol')
        selected[pointer] = names[0]
    last = max(at+size for at, (_, size) in selected.items())
    pointers = data_pointers(rel, vertex, last-vertex)
    source = ['/* Generated from the local verified donor; do not distribute. */', '#include <PR/mbi.h>']
    sections, records = [], []
    for pointer, (name, size) in selected.items():
        raw = symbol_data(rel, symbols, name)
        values, native_size, materials, triangle_count = convert_commands(raw, pointer,
            {p: target for p, target in pointers.items() if pointer <= p < pointer+size}, vertex, vertex_bytes)
        source += [f'const Gfx {name}[] __attribute__((section(".{name}"), aligned(8))) = {{', *values, '};']
        sections.append((name, native_size))
        records.append({'symbol': name, 'donor_offset': pointer, 'source_sha256': sha256(raw),
                        'native_bytes': native_size, 'materials': materials, 'triangles': triangle_count})
    native_row, _, metadata = native_species(rom, 'gor')
    native_model = by_vrom(rom)[int(metadata['native_model_vrom'], 16)].extract(rom)
    native_skeleton = u32(native_row, 4) & 0xFFFFFF
    native_joints = u32(native_model, native_skeleton+4) & 0xFFFFFF
    for offset in range(0, joint_size, 12):
        old = native_model[native_joints+offset:native_joints+offset+12]
        if old[4:] != joints[offset+4:offset+12] or bool(u32(old, 0)) != (joint_at+offset in joint_pointers):
            raise ValueError('Gorilla needs a different animation rig or joint hierarchy')
    return {'vertices': vertices, 'joints': joints, 'skeleton': skeleton,
            'joint_at': joint_at, 'joint_pointers': joint_pointers, 'records': records,
            'source': '\n'.join(source)+'\n', 'sections': tuple(sections),
            'vertex_flags_normalised': changed, 'native_reference': metadata}


def build_object(rom, rel, symbols, output):
    data = prepare(rom, rel, symbols)
    output.mkdir(parents=True, exist_ok=False)
    source = output/'commands.c'
    source.write_text(data['source'])
    compiled = compile_commands(output/'gbi', source, data['sections'])
    model, offsets = bytearray(data['vertices']), {}
    for row in data['records']:
        commands = compiled[row['symbol']]
        offsets[row['donor_offset']] = len(model)
        row.update(native_offset=len(model), native_sha256=sha256(commands))
        model.extend(commands)
    joint_offset = len(model)
    joints = bytearray(data['joints'])
    for pointer, target in data['joint_pointers'].items():
        struct.pack_into('>I', joints, pointer-data['joint_at'], SEGMENT+offsets[target])
    model.extend(joints)
    skeleton_offset = len(model)
    model.extend(data['skeleton'][:4]+struct.pack('>I', SEGMENT+joint_offset))
    model.extend(bytes((-len(model)) % 16))
    if len(model) > MODEL_LIMIT:
        raise ValueError('Complete gorilla model exceeds the native reserved NPC model buffer')
    (output/'yodel.n64model.bin').write_bytes(model)
    report = {'format': 'AFV3-GORILLA-ART-1', 'donor': DONOR, 'villager_index': 229,
        'source_rom_sha256': sha256(rom), 'source_rel_sha256': REL_SHA, 'source_symbols_sha256': SYMBOLS_SHA,
        'compiler_image': IMAGE, 'command_source_sha256': sha256(data['source'].encode()),
        'model_file': 'yodel.n64model.bin', 'model_bytes': len(model), 'model_sha256': sha256(model),
        'model_buffer_bytes': MODEL_LIMIT, 'spare_model_bytes': MODEL_LIMIT-len(model),
        'vertices': 429, 'vertex_bytes': len(data['vertices']), 'vertices_sha256': sha256(data['vertices']),
        'vertex_flags_normalised': data['vertex_flags_normalised'], 'joints': 26, 'visible_joints': 12,
        'joint_offset': joint_offset, 'skeleton': f'{SEGMENT+skeleton_offset:08X}',
        'triangles': sum(r['triangles'] for r in data['records']), 'models': data['records'],
        'native_reference': data['native_reference'], 'target_model_bank': None,
        'runtime_installed': False, 'selectable': False}
    (output/'art.json').write_text(json.dumps(report, indent=2)+'\n')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--n64', type=Path, default=ROOT/'local/rom/Doubutsu no Mori (Japan).z64')
    parser.add_argument('--disc', type=Path, default=ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Choose a fresh gorilla conversion directory')
    report = build_object(args.n64.read_bytes(), read_donor(args.disc)['rel'], args.symbols.read_bytes(),
                          args.output.resolve())
    print(json.dumps({key: report[key] for key in ('model_bytes', 'spare_model_bytes', 'vertices',
                                                  'triangles', 'runtime_installed')}, indent=2))


if __name__ == '__main__':
    main()
