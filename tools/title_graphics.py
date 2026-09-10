#!/usr/bin/env python3
"""Build a bounded N64 title asset package from the supplied English models."""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import struct

from aflib import sha256
from title_assets import ROOT, DATA_BASE, extract, scoped_symbols
from title_model import bindings

SEGMENT = 11
HEADER_BYTES = 96
TMEM_BYTES = 4096
STRIP_ROWS = 12


def word_pair(a, b=0):
    return struct.pack('>2I', a, b)


def load_tile(texture, width, height, low, high, rgba):
    """F3DEX2 full-width texture tile, with original image-space T coordinates."""
    if (width not in (32, 48, 64) or not 0 <= low < high <= height <= 128
            or width*(high-low)*(4 if rgba else Fraction(1, 2)) > TMEM_BYTES):
        raise ValueError('Title tile exceeds texture or TMEM bounds')
    fmt, load_size, render_size = (0, 3, 3) if rgba else (4, 1, 0)
    image_width = width if rgba else width//2
    line = (width*2 if rgba else width//2)//8
    tile = 0xF5000000 | fmt << 21 | load_size << 19 | line << 9
    render = 0xF5000000 | fmt << 21 | render_size << 19 | line << 9
    # Clamp both axes, no wrap/mask/shift. RGBA32 uses two 2-KiB TMEM banks.
    return b''.join((
        word_pair(0xFD000000 | fmt << 21 | load_size << 19 | (image_width-1), texture),
        word_pair(tile, 0x07080200), word_pair(0xE6000000),
        word_pair(0xF4000000 | low*4,
                  0x07000000 | (width-1)*(4 if rgba else 2) << 12 | (high-1)*4),
        word_pair(0xE7000000), word_pair(render, 0x00080200),
        word_pair(0xF2000000 | low*4, (width-1)*4 << 12 | (high-1)*4),
    ))


def slices(model):
    """Preserve source corners/winding; add shared strip edges and filtering rows."""
    vertices = model['vertices']
    s0, t0, s1, t1 = model['texture_bounds']
    if t0 % 32 or t1 % 32 or model['triangles'] != [[0, 1, 2], [0, 2, 3]]:
        raise ValueError('Unsupported title strip bounds or topology')
    corners = {(v[4], v[5]): v for v in vertices}
    if len(corners) != 4 or len({tuple(v[6:]) for v in vertices}) != 1:
        raise ValueError('Unsupported title quad colours or corners')
    if any(corners[s0, t0][i]+corners[s1, t1][i] !=
           corners[s0, t1][i]+corners[s1, t0][i] for i in range(3)):
        raise ValueError('Title strip requires planar affine source geometry')
    rgba = model['palette'] is not None
    step = STRIP_ROWS if rgba else model['height']
    result = []
    for start in range(t0//32, t1//32, step):
        end = min(start+step, t1//32)
        low, high = max(0, start-1), min(model['height'], end+1)
        if not rgba:
            low, high = 0, model['height']
        quad = []
        for original in vertices:
            s, t = original[4], start*32 if original[5] == t0 else end*32
            a, b = corners[s, t0], corners[s, t1]
            coords = [Fraction(a[i])+Fraction((b[i]-a[i])*(t-t0), t1-t0) for i in range(3)]
            # Nearest integer, ties toward +infinity; shared boundaries round identically.
            xyz = [(v+Fraction(1, 2)).__floor__() for v in coords]
            if any(not -32768 <= v <= 32767 for v in (*xyz, s, t)):
                raise ValueError('Title strip vertex exceeds native signed fields')
            quad.append(xyz+[0, s, t]+original[6:])
        result.append({'draw_rows': [start, end], 'load_rows': [low, high],
                       'tmem_bytes': model['width']*(high-low)*(4 if rgba else 1)//(1 if rgba else 2),
                       'vertices': quad})
    return result


def package(rel, symbols):
    files, textures = extract(rel, symbols)
    source, entries = bindings(rel, symbols), scoped_symbols(symbols)
    blob, allocated, models = bytearray(HEADER_BYTES), {}, []
    def append(data, alignment=16):
        blob.extend(bytes((-len(blob)) % alignment))
        offset = len(blob)
        blob.extend(data)
        if len(blob) > 0x60000:
            raise ValueError('English title asset package exceeds its size limit')
        return offset
    def pointer(offset):
        if not HEADER_BYTES <= offset < len(blob):
            raise ValueError('English title pointer escapes allocated data')
        return SEGMENT << 24 | offset
    def raw(offset):
        return rel[DATA_BASE+offset:DATA_BASE+offset+entries[offset]['bytes']]
    for row in textures['textures']:
        if row['output_format'] == 'N64_IA8':
            continue  # Press Start and notices use their independent native renderer.
        allocated[int(row['offset'], 16)] = append(files[row['file']])
    for model in source['models']:
        bands, commands = slices(model), bytearray()
        commands.extend(word_pair(0xD7000002, 0xFFFFFFFF))
        for band in bands:
            vertex = append(b''.join(struct.pack('>hhhHhh4B', *v) for v in band['vertices']))
            band['vertex_offset'] = vertex
            low, high = band['load_rows']
            commands.extend(word_pair(0xE7000000))
            commands.extend(load_tile(pointer(allocated[int(model['texture'], 16)]),
                                      model['width'], model['height'], low, high,
                                      model['palette'] is not None))
            commands.extend(word_pair(0x01004008, pointer(vertex)))
            commands.extend(word_pair(0x06000204, 0x00000406))
        commands.extend(word_pair(0xDF000000))
        offset = append(commands)
        allocated[int(model['offset'], 16)] = offset
        models.append({**model, 'package_offset': offset, 'command_bytes': len(commands),
                       'texture_offset': allocated[int(model['texture'], 16)], 'strips': bands})
    skeletons = []
    for skeleton in source['skeletons']:
        joint_data = bytearray()
        for joint in skeleton['joints']:
            shape = pointer(allocated[int(joint['model'], 16)]) if joint['model'] else 0
            joint_data.extend(struct.pack('>IBBhhh', shape, joint['children'], 0, *joint['translation']))
        joints = append(joint_data)
        skel = append(struct.pack('>BBHI', len(skeleton['joints']), skeleton['shown_joints'], 0, pointer(joints)))
        arrays = [append(raw(int(at, 16))) for at in skeleton['animation_arrays']]
        animation = bytearray(raw(int(skeleton['animation_offset'], 16)))
        struct.pack_into('>4I', animation, 0, *(pointer(at) for at in arrays))
        anim = append(animation)
        skeletons.append({**skeleton, 'skeleton_package_offset': skel, 'animation_package_offset': anim,
                          'joint_package_offset': joints, 'array_package_offsets': arrays})
    blob.extend(bytes((-len(blob)) % 16))
    header = [0x41465447, 1, len(blob), SEGMENT, len(models), len(skeletons)]
    for s in skeletons:
        header += [pointer(s['skeleton_package_offset']), pointer(s['animation_package_offset']), s['joint_work_entries']]
    # Source rendering order A/B/C/D, followed by the independent trademark model.
    header += [pointer(allocated[at]) for at in (0x5EE458, 0x5EE430, 0x5EE408, 0x5EE3E0, 0x5F3CA0)]
    struct.pack_into('>'+str(len(header))+'I', blob, 0, *header)
    report = {'version': 1, 'bytes': len(blob), 'sha256': sha256(blob),
              'source_sha256': source['source_sha256'], 'segment': SEGMENT,
              'models': models, 'skeletons': skeletons,
              'strips': sum(len(m['strips']) for m in models),
              'max_tmem_bytes': max(b['tmem_bytes'] for m in models for b in m['strips']),
              'texture_bytes': sum(t['bytes'] for t in textures['textures'] if t['output_format'] != 'N64_IA8'),
              'installed': False, 'status': 'Native asset package; actor integration and execution pending'}
    return bytes(blob), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'build/title-graphics')
    args = parser.parse_args()
    blob, report = package((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                           (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    args.output.mkdir(parents=True, exist_ok=True)
    target = args.output/'title.bin'
    if target.exists() or target.is_symlink():
        if target.is_symlink() or target.read_bytes() != blob:
            raise ValueError('Existing English title package differs')
    else:
        with target.open('xb') as output:
            output.write(blob)
    (args.output/'title.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({k: report[k] for k in ('bytes', 'sha256', 'strips', 'max_tmem_bytes', 'installed')}, indent=2))


if __name__ == '__main__':
    main()
