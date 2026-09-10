"""Read-only native material candidates and exact named English GC texel matches."""
import argparse
from bisect import bisect_right
from collections import Counter
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom, sha256, u32, verified_rom
from title_assets import DATA_BASE, REL_SHA256, SYMBOLS_SHA256, model_texture_shape, pack4, untile

ROOT = Path(__file__).resolve().parents[1]
FORMATS = {(2, 0): ('ci4', 4), (2, 1): ('ci8', 8), (3, 1): ('ia8', 8),
           (4, 0): ('i4', 4), (4, 1): ('i8', 8)}
LIMITATIONS = [
    'Discovery candidates only: not complete display-list reachability or whole-game inventory',
    'Native segment 6 resolves only within the containing DMA owner; other segments need separate binding',
    'Dynamic materials, cross-object pointers, suballocations, and unsupported formats remain unresolved',
    'CI matches compare texel indices, not palettes or visible colours',
    'A match does not prove English wording or active native use; unmatched does not imply Japanese',
    'No English application credit, cartridge changes, runtime testing, or hardware acceptance',
]


def objects(symbols):
    rows = []
    pattern = r'^(\w+) = \.data:0x([0-9A-Fa-f]+); // type:object size:0x([0-9A-Fa-f]+) '
    for name, address, size in re.findall(pattern, symbols.decode(), re.M):
        address, size = int(address, 16), int(size, 16)
        if size > 0:
            rows.append((address, size, name))
    rows.sort()
    if any(a+size > b for (a, size, _), (b, _, _) in zip(rows, rows[1:])):
        raise ValueError('Ambiguous overlapping GC object symbols')
    return rows


def owner_at(rows, addresses, address, size):
    index = bisect_right(addresses, address)-1
    if index < 0:
        return None
    start, length, name = rows[index]
    return rows[index] if start <= address and address+size <= start+length else None


def data_pointers(rel):
    pointers = {}
    table, size = u32(rel, 0x28), u32(rel, 0x2C)
    for module, first in struct.iter_unpack('>II', rel[table:table+size]):
        section, address = None, 0
        for at in range(first, len(rel)-7, 8):
            delta, kind, target_section, target = struct.unpack_from('>HBBI', rel, at)
            if kind == 203:
                break
            if kind == 202:
                section, address = target_section, 0
                continue
            address += delta
            if section != 5 or kind in (0, 201, 204):
                continue
            if (module, kind, target_section) == (u32(rel, 0), 1, 5):
                if address in pointers or u32(rel, DATA_BASE+address):
                    raise ValueError('Ambiguous GC data relocation')
                pointers[address] = target
        else:
            raise ValueError('Unterminated GC relocation stream')
    return pointers


def converted(data, width, height, fmt, bits):
    values = untile(data, width, height, bits)
    if bits == 4:
        return pack4(values)
    if fmt == 'ia8':
        return bytes((v << 4 & 240) | v >> 4 for v in values)
    return values


def gc_inventory(rel, symbols):
    if sha256(rel) != REL_SHA256 or sha256(symbols) != SYMBOLS_SHA256:
        raise ValueError('Changed supplied GC artwork source')
    rows = objects(symbols)
    addresses = [r[0] for r in rows]
    found, skipped = {}, Counter()
    for address, texture in data_pointers(rel).items():
        command = address-4
        if command % 8 or u32(rel, DATA_BASE+command) >> 24 != 0xFD:
            continue
        model = owner_at(rows, addresses, command, 8)
        if model is None or not re.search(r'_model(?:T|\d|_|$)', model[2]):
            skipped['outside_named_model'] += 1
            continue
        try:
            w, h, fmt_code, size_code = model_texture_shape(rel[DATA_BASE+command:DATA_BASE+command+8])
        except ValueError:
            skipped['not_dolphin_texture'] += 1
            continue
        if (fmt_code, size_code) not in FORMATS:
            skipped['unsupported_format'] += 1
            continue
        fmt, bits = FORMATS[fmt_code, size_code]
        length = w*h*bits//8
        texture_owner = owner_at(rows, addresses, texture, length)
        if texture_owner is None or DATA_BASE+texture+length > len(rel):
            skipped['texture_not_bound_to_named_storage'] += 1
            continue
        try:
            data = converted(rel[DATA_BASE+texture:DATA_BASE+texture+length], w, h, fmt, bits)
        except ValueError:
            skipped['incomplete_tile_blocks'] += 1
            continue
        key = (texture, w, h, fmt)
        if key not in found:
            found[key] = {'texture': f'{texture:08X}', 'symbol': texture_owner[2],
                          'symbol_offset': texture-texture_owner[0], 'width': w, 'height': h,
                          'format': fmt, 'bytes': length, 'texel_sha256': sha256(data), 'readers': []}
        found[key]['readers'].append({'command': f'{command:08X}', 'model': model[2]})
    return list(found.values()), dict(skipped)


def native_material(obj, command):
    """Recognise one local load/tile sequence, without asserting reachability."""
    a, pointer = struct.unpack_from('>II', obj, command)
    if a >> 24 != 0xFD:
        return None, 'not_texture_load'
    # Palette TLUT loads are not texture candidates in this inventory.
    if (a >> 21 & 7) not in (2, 3, 4):
        return None, 'unsupported_load_format'
    if pointer >> 24 != 6:
        return None, 'external_segment'
    texture = pointer & 0xFFFFFF
    render = None
    for at in range(command+8, min(command+88, len(obj)-7), 8):
        x, y = struct.unpack_from('>II', obj, at)
        op = x >> 24
        if op not in (0xE6, 0xE7, 0xE8, 0xF3, 0xF5, 0xF2):
            break
        if op == 0xF5 and y >> 24 & 7 == 0:
            render = (x >> 21 & 7, x >> 19 & 3)
        if op == 0xF2:
            if x != 0xF2000000 or y >> 24 or render not in FORMATS:
                return None, 'unsupported_tile'
            right, bottom = y >> 12 & 4095, y & 4095
            if right % 4 or bottom % 4 or render[0] != a >> 21 & 7:
                return None, 'unsupported_tile_coordinates'
            width, height = right//4+1, bottom//4+1
            fmt, bits = FORMATS[render]
            if width*height*bits % 8:
                return None, 'partial_byte_texture'
            size = width*height*bits//8
            if texture+size > len(obj) or texture <= command < texture+size:
                return None, 'texture_outside_local_storage'
            return {'offset': texture, 'width': width, 'height': height, 'format': fmt,
                    'bytes': size, 'texel_sha256': sha256(obj[texture:texture+size])}, None
    return None, 'no_supported_short_material_sequence'


def native_inventory(native):
    verified_rom(native)
    found, skipped = {}, Counter()
    for owner, entry in by_vrom(native).items():
        if entry.pstart == 0xFFFFFFFF:
            continue
        obj = entry.extract(native)
        for command in range(0, len(obj)-7, 8):
            if obj[command] != 0xFD:
                continue
            row, reason = native_material(obj, command)
            if row is None:
                skipped[reason] += 1
                continue
            key = (owner+row['offset'], row['width'], row['height'], row['format'])
            if key not in found:
                found[key] = {'texture': f'{key[0]:08X}', 'owner': f'{owner:08X}',
                              'owner_sha256': sha256(obj), **row, 'commands': []}
            found[key]['commands'].append(f'{owner+command:08X}')
    return list(found.values()), dict(skipped)


def match(native_rows, gc_rows):
    sources = {}
    def key(row):
        return row['format'], row['width'], row['height'], row['texel_sha256']
    for row in gc_rows:
        sources.setdefault(key(row), []).append(row)
    return [{**row, 'gc_matches': [{'texture': gc['texture'], 'symbol': gc['symbol'],
                                   'symbol_offset': gc['symbol_offset']} for gc in sources.get(key(row), [])]}
            for row in native_rows]


def inventory(native, rel, symbols):
    gc_rows, gc_skips = gc_inventory(rel, symbols)
    native_rows, native_skips = native_inventory(native)
    matches = match(native_rows, gc_rows)
    return {'version': 1, 'source_rom_sha256': sha256(native), 'source_rel_sha256': REL_SHA256,
            'source_symbols_sha256': SYMBOLS_SHA256, 'limitations': LIMITATIONS,
            'counts': {'native_candidates': len(matches), 'gc_sources': len(gc_rows),
                       'exact_texel_matches': sum(bool(r['gc_matches']) for r in matches),
                       'unmatched_candidates': sum(not r['gc_matches'] for r in matches)},
            'skipped': {'native': native_skips, 'gamecube': gc_skips},
            'native_candidates': matches, 'gc_sources': gc_rows, 'cartridge_modified': False,
            'translation_credit_awarded': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, default=ROOT/'build/artwork-matches-01.json')
    a = p.parse_args()
    if a.output.exists() or a.output.is_symlink():
        p.error('Use a fresh output file; previous reports are preserved')
    if not a.output.resolve().is_relative_to(ROOT/'build'):
        p.error('Generated inventory must remain in the ignored build directory')
    report = inventory((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    a.output.parent.mkdir(parents=True, exist_ok=True)
    with a.output.open('x') as out:
        json.dump(report, out, indent=2)
        out.write('\n')
    print(json.dumps({'output': str(a.output), **report['counts'], 'translation_credit_awarded': False}))


if __name__ == '__main__':
    main()
