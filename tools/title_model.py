#!/usr/bin/env python3
"""Bind English title geometry, skeletons, and animation using actual REL fixups."""
import argparse
import json
from pathlib import Path
import struct

from aflib import sha256, u32
from gc_names import rel_sections
from title_assets import (ROOT, REL_SHA256, DATA_BASE, START, END, CI4, I4,
                          MODEL_OFFSETS, scoped_symbols, model_texture_shape)

GROUPS = (
    ('animal', 0x5EA2BC, 0x5EA1C0, 0x5E69F0),
    ('cros', 0x5F1038, 0x5F0F90, 0x5EEB1C),
    ('sing', 0x5F3A58, 0x5F39B0, 0x5F1744),
)


def title_pointers(rel):
    if sha256(rel) != REL_SHA256:
        raise ValueError('Changed supplied title REL')
    sections = rel_sections(rel)
    if sections[5][0] != DATA_BASE:
        raise ValueError('Changed title data section')
    module_id, table, size = u32(rel, 0), u32(rel, 0x28), u32(rel, 0x2C)
    if size % 8 or not 0 < size <= 256 or not 0 <= table <= len(rel)-size:
        raise ValueError('Invalid title REL import table')
    imports = list(struct.iter_unpack('>2I', rel[table:table+size]))
    starts = sorted(offset for _, offset in imports)
    if len(set(starts)) != len(starts) or any(offset % 4 or not 0 <= offset < len(rel) for offset in starts):
        raise ValueError('Invalid title REL relocation stream')
    pointers = {}
    for imported_module, first in imports:
        limit = min((offset for offset in starts if offset > first), default=len(rel))
        section, address, ended = None, 0, False
        for position in range(first, limit-7, 8):
            delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, position)
            if kind == 203:
                ended = True
                break
            if kind == 202:
                if target_section >= len(sections):
                    raise ValueError('Invalid title REL source section')
                section, address = target_section, 0
                continue
            if section is None:
                raise ValueError('Title REL fixup has no source section')
            address += delta
            if address > sections[section][1]:
                raise ValueError('Title REL fixup exceeds source section')
            if kind in (0, 201, 204) or section != 5 or not START <= address < END:
                continue
            if (kind != 1 or imported_module != module_id or target_section != 5
                    or address % 4 or address+4 > END or not START <= target < END
                    or address in pointers or u32(rel, DATA_BASE+address) != 0):
                raise ValueError('Unsupported, duplicate, or external title pointer fixup')
            pointers[address] = target
        if not ended:
            raise ValueError('Unterminated title REL relocation stream')
    return pointers


def bindings(rel, symbols):
    pointers, entries = title_pointers(rel), scoped_symbols(symbols)
    def raw(offset):
        entry = entries[offset]
        return rel[DATA_BASE+offset:DATA_BASE+offset+entry['bytes']]
    def pointer(offset):
        if offset not in pointers:
            raise ValueError(f'Missing actual title pointer fixup: {offset:08X}')
        return pointers[offset]
    plans = [(row[0], row[1], row[2], row[3]) for row in CI4]+[(o, w, h, None) for o, w, h in I4]
    if len(plans) != len(MODEL_OFFSETS):
        raise ValueError('Incomplete title model bindings')
    models = []
    for (texture, width, height, palette), offset in zip(plans, MODEL_OFFSETS):
        data = raw(offset)
        if model_texture_shape(data) != (width, height, 2 if palette is not None else 4, 0):
            raise ValueError('Title shape differs from actual model command')
        commands = [(offset+i*8, a, b) for i, (a, b) in enumerate(struct.iter_unpack('>2I', data))]
        image = [at for at, a, _ in commands if a >> 24 == 0xFD]
        vertex = [(at, a) for at, a, _ in commands if a >> 24 == 1]
        palettes = [at for at, a, _ in commands if a >> 24 == 0xF0]
        triangles = [(a, b) for _, a, b in commands if a >> 24 == 0x0A]
        if triangles != [(0x0A020000, 0x62008200)] or commands[-1][1:] != (0xDF000000, 0):
            raise ValueError('Changed title quad triangle topology')
        if len(image) != 1 or pointer(image[0]+4) != texture or len(vertex) != 1:
            raise ValueError('Wrong title texture or vertex binding')
        if palette is not None and (len(palettes) != 1 or pointer(palettes[0]+4) != palette):
            raise ValueError('Wrong scoped title palette binding')
        if palette is None and palettes:
            raise ValueError('Unexpected title intensity palette')
        at, command = vertex[0]
        if command != 0x01004008:
            raise ValueError('Title model is not the expected four-vertex quad')
        vertices = pointer(at+4)
        owners = [start for start, row in entries.items() if start <= vertices and vertices+64 <= start+row['bytes']]
        if len(owners) != 1 or not entries[owners[0]]['symbol'].endswith('_v'):
            raise ValueError('Title quad does not belong to its scoped vertex array')
        quad = [list(struct.unpack_from('>hhhHhh4B', rel, DATA_BASE+vertices+i*16)) for i in range(4)]
        ss, tt = sorted({v[4] for v in quad}), sorted({v[5] for v in quad})
        if (len(ss) != 2 or len(tt) != 2 or not 0 <= ss[0] < ss[1] <= width*32
                or not 0 <= tt[0] < tt[1] <= height*32
                or {(v[4], v[5]) for v in quad} != {(s, t) for s in ss for t in tt}):
            raise ValueError(f'Unsupported title quad texture bounds: {offset:08X}, {width}x{height}, {[(v[4], v[5]) for v in quad]}')
        models.append({'offset': f'{offset:08X}', 'symbol': entries[offset]['symbol'],
            'texture': f'{texture:08X}', 'palette': None if palette is None else f'{palette:08X}',
            'width': width, 'height': height, 'vertices_offset': f'{vertices:08X}',
            'vertices': quad, 'triangles': [[0, 1, 2], [0, 2, 3]],
            'texture_bounds': [ss[0], tt[0], ss[1], tt[1]], 'source_sha256': sha256(data)})
    model_ids = {int(row['offset'], 16) for row in models}
    skeletons = []
    for name, skeleton_at, joints_at, animation_at in GROUPS:
        skeleton = raw(skeleton_at)
        count, shown = skeleton[:2]
        if len(skeleton) != 8 or pointer(skeleton_at+4) != joints_at or len(raw(joints_at)) != count*12:
            raise ValueError('Changed title skeleton ownership or joint count')
        joints, pending = [], 1
        for i in range(count):
            at = joints_at+i*12
            shape = pointers.get(at, 0)
            _, children, flags, x, y, z = struct.unpack_from('>IBBhhh', rel, DATA_BASE+at)
            if pending <= 0 or flags != 0 or (shape and shape not in model_ids):
                raise ValueError('Invalid title skeleton tree or model reference')
            pending += children-1
            joints.append({'model': f'{shape:08X}' if shape else None, 'children': children, 'translation': [x, y, z]})
        if pending != 0 or sum(row['model'] is not None for row in joints) != shown:
            raise ValueError('Incomplete title skeleton tree')
        animation = raw(animation_at)
        flag_at, data_at, counts_at, constants_at = [pointer(animation_at+i*4) for i in range(4)]
        flags = raw(flag_at)
        lengths = struct.unpack('>'+str(len(raw(counts_at))//2)+'h', raw(counts_at))
        dynamic = (flags[0] & 0x38).bit_count()+sum((flag & 7).bit_count() for flag in flags)
        if (len(animation) != 20 or len(flags) != count or len(lengths) != dynamic
                or any(length <= 0 for length in lengths)
                or sum(lengths)*6 != len(raw(data_at))
                or (count*3+3-dynamic)*2 != len(raw(constants_at))):
            raise ValueError('Incomplete title keyframe or constant arrays')
        skeletons.append({'name': name, 'skeleton_offset': f'{skeleton_at:08X}',
            'animation_offset': f'{animation_at:08X}', 'joints': joints, 'shown_joints': shown,
            'joint_work_entries': count+1, 'animation_duration': struct.unpack_from('>h', animation, 18)[0],
            'animation_arrays': [f'{at:08X}' for at in (flag_at, data_at, counts_at, constants_at)],
            'dynamic_tracks': dynamic, 'keyframes': sum(lengths)})
    return {'version': 1, 'source_sha256': REL_SHA256, 'pointer_fixups': {f'{k:08X}': f'{v:08X}' for k, v in sorted(pointers.items())},
            'models': models, 'skeletons': skeletons, 'installed': False,
            'status': 'Verified source model bindings; N64 display lists and actor integration pending'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/title-english-assets/model.json')
    args = parser.parse_args()
    report = bindings((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                      (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output': str(args.output), 'pointer_fixups': len(report['pointer_fixups']),
        'models': len(report['models']), 'skeletons': [{k: s[k] for k in ('name', 'shown_joints', 'dynamic_tracks', 'keyframes')} for s in report['skeletons']]}, indent=2))


if __name__ == '__main__':
    main()
