"""Bind shared villager body tiles to both games' actual ordered mesh faces."""
import re
import struct

from aflib import by_vrom, sha256, u32
from gc_names import rel_sections, symbol_data
from stall_model_source import packed
from title_assets import model_texture_shape
from v3_villager_art import LAYOUTS, data_pointers, symbol_span


def faces(raw, *, donor, vertex_start=0, vertex_bytes, pointers=None, start=0):
    """Resolve both partial vertex caches, retaining each vertex's joint matrix."""
    cache, result, used = {}, [], set()
    material, matrix, tile = None, None, None
    at = 0
    while at+8 <= len(raw):
        a, b = struct.unpack_from('>II', raw, at)
        op, step, triangles = a >> 24, 8, ()
        if op == 0x01:
            count, end = a >> 12 & 255, (a & 255)//2
            first = end-count
            if donor:
                pointer = (pointers or {}).get(start+at+4)
                used.add(start+at+4)
                if b or pointer is None:
                    raise ValueError('Missing donor mesh vertex binding')
            else:
                if b >> 24 != 6:
                    raise ValueError('Native mesh vertices leave segment 6')
                pointer = b & 0xFFFFFF
            offset = pointer-vertex_start
            if (not 0 <= first < end <= 32 or a != 0x01000000 | count << 12 | end*2
                    or offset < 0 or offset % 16 or offset+count*16 > vertex_bytes):
                raise ValueError('Mesh vertex load exceeds the array or cache')
            for i in range(count):
                cache[first+i] = (offset//16+i, matrix)
        elif op == 0xDA:
            if a != 0xDA380003 or b >> 24 != 13 or b & 63 or b & 0xFFFFFF >= 26*64:
                raise ValueError('Unsupported species joint matrix')
            matrix = b
        elif donor and op == 0xFD:
            w, h, fmt, depth = model_texture_shape(raw[at:at+8])
            if fmt != 2 or depth or b >> 24 not in (8, 9, 10, 11):
                raise ValueError('Unsupported segmented species texture')
            if at+16 > len(raw):
                raise ValueError('Missing Dolphin tile pair')
            pair, zero = struct.unpack_from('>II', raw, at+8)
            if pair >> 24 != 0xD2 or zero:
                raise ValueError('Unsupported Dolphin tile pair')
            material = (b, w, h, pair)
            step = 16
        elif not donor and op == 0xF5:
            if a >> 19 & 31 != 8 or b >> 24:
                raise ValueError('Native species tile is not CI4 render tile zero')
            tile = ((a & 511)*8, a, b)
        elif op == 0xF2:
            if not donor:
                if tile is None or a != 0xF2000000 or b >> 24:
                    raise ValueError('Unsupported native species tile extent')
                material = (*tile, (b >> 12 & 4095)//4+1, (b & 4095)//4+1)
        elif donor and op == 0x0A:
            count = (a >> 17 & 127)+1
            step = (1+(max(0, count-3)+3)//4)*8
            triangles = packed(raw[at:at+step], 32)
        elif not donor and op in (5, 6):
            words = (a & 0xFFFFFF, b) if op == 6 else (a & 0xFFFFFF,)
            if op == 5 and b or op == 6 and b >> 24:
                raise ValueError('Unsupported native triangle flags')
            triangles = []
            for word in words:
                indices = tuple(word >> shift & 255 for shift in (16, 8, 0))
                if any(v & 1 for v in indices):
                    raise ValueError('Unaligned native triangle index')
                triangles.append(tuple(v//2 for v in indices))
        elif op == 0xDF:
            if (a, b) != (0xDF000000, 0) or donor and at+8 != len(raw):
                raise ValueError('Invalid species display-list termination')
            if donor and used != set(pointers or {}):
                raise ValueError('Unaccounted species display-list relocation')
            if not result:
                raise ValueError('Species joint has no triangles')
            return result
        elif op not in (0xE7, 0xD7, 0xFC, 0xE2, 0xFA, 0xD9):
            raise ValueError(f'Unsupported species graphics command {op:02X}')
        for triangle in triangles:
            if material is None or any(v not in cache for v in triangle):
                raise ValueError('Species triangle lacks material or loaded vertices')
            result.append((tuple(cache[v] for v in triangle), material))
        at += step
    raise ValueError('Unterminated species display list')


def verify_body_mesh(rom, rel, symbols, species, row, metadata):
    """Compare complete ordered faces and their native/GC texture bindings."""
    model = by_vrom(rom)[int(metadata['native_model_vrom'], 16)].extract(rom)
    vertex_at, vertex_bytes = symbol_span(symbols, f'{species}_1_v')
    joint_at, joint_size = symbol_span(symbols, f'cKF_je_r_{species}_1_tbl')
    joint_pointers = data_pointers(rel, joint_at, joint_size)
    spans = {}
    for name, at, size in re.findall(
            r'^(\w+) = \.data:0x([0-9A-Fa-f]+);[^\n]* size:0x([0-9A-Fa-f]+) ', symbols, re.M):
        spans.setdefault(int(at, 16), []).append((name, int(size, 16)))
    skeleton = u32(row, 4) & 0xFFFFFF
    joints = u32(model, skeleton+4) & 0xFFFFFF
    layout, bindings, face_count, joint_count = LAYOUTS[species], set(), 0, 0
    base = rel_sections(rel)[5][0]
    bound_lists = {}
    for pointer in joint_pointers.values():
        matches = spans.get(pointer, ())
        if len(matches) != 1 or pointer < vertex_at+vertex_bytes:
            raise ValueError('Missing unique donor joint display list')
        bound_lists[pointer] = matches[0]
    last = max(pointer+size for pointer, (_, size) in bound_lists.items())
    model_pointers = data_pointers(rel, vertex_at, last-vertex_at)
    for joint in range(joint_size//12):
        native_pointer = u32(model, joints+joint*12)
        donor_pointer = joint_pointers.get(joint_at+joint*12)
        if bool(native_pointer) != bool(donor_pointer):
            raise ValueError('Species visible joints differ')
        if not donor_pointer:
            continue
        name, size = bound_lists[donor_pointer]
        native = faces(model[native_pointer & 0xFFFFFF:], donor=False, vertex_bytes=vertex_bytes)
        donor = faces(rel[base+donor_pointer:base+donor_pointer+size], donor=True,
                      vertex_start=vertex_at, vertex_bytes=vertex_bytes, start=donor_pointer,
                      pointers={p: target for p, target in model_pointers.items()
                                if donor_pointer <= p < donor_pointer+size})
        if len(native) != len(donor):
            raise ValueError(f'{species}/{name}: changed triangle count')
        for (nf, nt), (gf, gt) in zip(native, donor):
            # Cyclic vertex order is equivalent; reversed winding is not.
            if not any(nf == gf[i:]+gf[:i] for i in range(3)):
                raise ValueError(f'{species}/{name}: changed ordered face or joint matrix')
            source, w, h, pair = gt
            target, word, mode, native_w, native_h = nt
            segment = source >> 24
            if segment == 11:
                expected = [p for p in layout['parts'] if p[0] == source & 0xFFFFFF]
                if len(expected) != 1 or expected[0][1:] != (target, w, h):
                    raise ValueError(f'{species}/{name}: changed body tile binding')
                cropped = layout.get('edge_rows', {}).get(source & 0xFFFFFF)
                storage_h = cropped[0] if cropped else h
                if min(h, native_h) != storage_h or (word >> 9 & 511)*8 != w//2:
                    raise ValueError('Species tile stride or height differs from its storage')
                bindings.add((source & 0xFFFFFF, target, w, h, native_w, native_h, word, mode, pair))
            elif source & 0xFFFFFF or (w, h) != ((32, 32) if segment == 10 else (32, 16)):
                raise ValueError('Changed mutable species texture source')
            elif target != layout[{8: 'eye', 9: 'mouth', 10: 'cloth'}[segment]]:
                raise ValueError('Changed mutable species texture destination')
        face_count += len(native)
        joint_count += 1
    if {b[0] for b in bindings} != {p[0] for p in layout['parts']}:
        raise ValueError('A body texture piece is not bound by the actual mesh')
    return {'ordered_triangles': face_count, 'visible_joints': joint_count,
            'vertex_indices_and_joint_matrices_match': True,
            'body_tile_bindings': [dict(zip(('source', 'target', 'width', 'donor_height',
                'native_extent_width', 'native_extent_height', 'tile_word', 'tile_mode',
                'donor_tile_word'), values)) for values in sorted(bindings)],
            'native_model_sha256': sha256(model)}
