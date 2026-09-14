"""Install bounded native furniture profiles/banks without enabling acquisition."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_furniture_art import PILOTS, build_objects, native_profile
from v3_registry import FURNITURE_REGISTRY_VERSION, furniture_slot

ABI, BLOB_SIZE, CODE = 5, 0x8000, 0x5000
PROFILES, INDICES, IMPORTS, CAPACITY = 0x5800, 0x6C00, 0x7200, 1267
NATIVE_COUNT, BANK_BYTES, BANK_COUNT = 947, 0x1400, 100
VROM, RELOC, RAM, SIZE, RESIDENT = 0x82D7F0, 0x844400, 0x80936710, 0x16C10, 0x18F00
SECTIONS = (0x10E50, 0x5BE0, 0x1E0, 0x22F0, 0x607)
SOURCE_SHA = '4c67db43a7cebe9a35119621a13bac2fe8cb977cd7ab894b6b5e6b08e1d296a0'
CURRENT_SHA = '1a8066ed57b3f666c4b2cbefbb97af707d5242b0d216ccc13d80523ae94595a1'
RELOC_SHA = '418c53a6dc9d7a2e76eb87054394348fa03db0a4a6385251308dd808b438a71f'
SOURCE_FILES = ('tools/v3_furniture_runtime.py', 'tools/v3_furniture_art.py', 'tools/v3_registry.py',
                'overlays/v3/furniture.c', 'overlays/v3/furniture_entry.S', 'overlays/v3/furniture.ld')
HOOKS = (
    (0x8093678C, 'af_v3_furniture_load', (0x27BDFFC0, 0xAFBF001C)),
    (0x80937490, 'af_v3_furniture_has_bank', (0xAFA40000, 0x3084FFFF)),
    (0x809374C4, 'af_v3_furniture_bank', (0xAFA40000, 0x3084FFFF)),
    (0x809374F4, 'af_v3_furniture_bank_address', (0x2401FFFF, 0x14810003)),
    (0x8093885C, 'af_v3_furniture_dma', (0x27BDFFD0, 0xAFBF0014)),
    (0x80942688, 'af_v3_furniture_item', (0xAFA40000, 0xAFA50004)),
)


def relocation_rows(data, relocation):
    if (len(data) != SIZE or len(relocation) != 6208 or
            struct.unpack_from('>5I', relocation) != SECTIONS or u32(relocation, len(relocation) - 4) != 6208):
        raise ValueError('Changed native furniture overlay dimensions')
    rows = []
    for record in struct.unpack_from('>' + str(SECTIONS[4]) + 'I', relocation, 20):
        section, kind, offset = record >> 30, record >> 24 & 63, record & 0xFFFFFF
        if section not in (1, 2, 3) or kind not in (2, 4, 5, 6) or offset % 4 or offset + 4 > SECTIONS[section - 1]:
            raise ValueError('Invalid native furniture relocation')
        at = sum(SECTIONS[:section - 1]) + offset
        rows.append((record, at, kind))
    if len({at for _, at, _ in rows}) != len(rows) or any(relocation[20 + len(rows) * 4:-4]):
        raise ValueError('Duplicate furniture relocation or nonzero trailing data')
    return rows


def mapped_address(value):
    if 0x8094E1F0 <= value <= 0x8094F0BC:
        # Keep the original prefix-clear and gyroid-sharing lengths. Imported
        # static profiles are never heap allocations and must not be freed.
        return 0x80460000 + PROFILES + value - 0x8094E1F0, 'profile'
    if 0x8094F0C0 <= value <= 0x8094F473:
        offset = CAPACITY if value == 0x8094F473 else value - 0x8094F0C0
        return 0x80460000 + INDICES + offset, 'bank'
    return value, None


def patch_owner(data, relocation, symbols):
    if sha256(data) != CURRENT_SHA or sha256(relocation) != RELOC_SHA:
        raise ValueError('Furniture loader is not the reviewed V2 overlay')
    rows = relocation_rows(data, relocation)
    result, high, groups, direct = bytearray(data), {}, {}, []
    for record, at, kind in rows:
        word = u32(data, at)
        if kind == 5:
            if word >> 26 != 15:
                raise ValueError('Invalid furniture high relocation')
            high[word >> 16 & 31] = at
            groups[at] = []
        elif kind == 6:
            register = word >> 21 & 31
            if register not in high:
                raise ValueError('Unpaired furniture low relocation')
            hi = high[register]
            value = ((u32(data, hi) & 65535) << 16) + (word & 65535) - (65536 if word & 32768 else 0)
            target, family = mapped_address(value)
            groups[hi].append((at, value, target, family))
        elif kind == 2:
            target, family = mapped_address(word)
            if family:
                direct.append((at, word, target, family))
    removed, bindings, counts = set(), [], {'profile': 0, 'bank': 0}

    def write(at, value):
        struct.pack_into('>I', result, at, value)

    for hi, lows in groups.items():
        if not any(row[3] for row in lows):
            continue
        if any(row[3] is None for row in lows) or len({(row[2] + 0x8000) >> 16 for row in lows}) != 1:
            raise ValueError('Furniture high relocation mixes moved and retained targets')
        write(hi, u32(data, hi) & 0xFFFF0000 | ((lows[0][2] + 0x8000) >> 16 & 65535))
        removed.add(hi)
        for at, original, target, family in lows:
            write(at, u32(data, at) & 0xFFFF0000 | target & 65535)
            removed.add(at)
            counts[family] += 1
            bindings.append({'high': RAM + hi, 'low': RAM + at, 'original': original, 'target': target})
    if direct or counts != {'profile': 57, 'bank': 15}:
        raise ValueError('Changed furniture table-reference inventory')
    hook_offsets = set()
    for address, name, expected in HOOKS:
        at, target = address - RAM, symbols[name]
        if (struct.unpack_from('>2I', data, at) != expected or
                not 0x80465000 <= target < 0x80465800 or target % 4):
            raise ValueError('Changed furniture entry or helper address')
        hook_offsets.update((at, at + 4))
        write(at, 0x08000000 | (target >> 2 & 0x3FFFFFF))
        write(at + 4, 0)
    if hook_offsets & {at for _, at, _ in rows}:
        raise ValueError('Furniture entry hook overwrites a relocation')
    for address, expected in ((0x80936F00, 0x284103B3), (0x80937594, 0x241203B3),
                              (0x8093BBD0, 0x241403B3)):
        at = address - RAM
        if u32(data, at) != expected:
            raise ValueError('Changed furniture profile/bank traversal bound')
        write(at, expected & 0xFFFF0000 | CAPACITY)
    retained = [record for record, at, _ in rows if at not in removed]
    fixed = bytearray(relocation)
    struct.pack_into('>I', fixed, 16, len(retained))
    fixed[20:-4] = bytes(len(fixed) - 24)
    struct.pack_into('>' + str(len(retained)) + 'I', fixed, 20, *retained)
    return bytes(result), bytes(fixed), {'bindings': bindings, 'reference_counts': counts,
        'original_relocations': len(rows), 'retained_relocations': len(retained),
        'removed_relocation_offsets': sorted(removed), 'source_sha256': CURRENT_SHA,
        'original_native_sha256': SOURCE_SHA,
        'source_relocation_sha256': RELOC_SHA, 'output_sha256': sha256(result),
        'output_relocation_sha256': sha256(fixed), 'original_heap_profile_cleanup_retained': True}


def install(native, base, blob, rel, donor_symbols, helper_symbols, out, *, object_vrom_offset=0):
    if object_vrom_offset not in (0, 0x4000):
        raise ValueError('Unsupported furniture model-tail layout')
    if len(blob) != BLOB_SIZE or any(blob[PROFILES:0x7FF0]):
        raise ValueError('Furniture tables overlap an existing V3 resource')
    files = by_vrom(base)
    original = by_vrom(native)
    actor = files[CODE_VROM].extract(base)
    at = 0x80100DF0 - CODE_RAM
    if struct.unpack_from('>6I', actor, at) != (VROM, VROM + SIZE, RAM, RAM + RESIDENT, 0, 0x8094756C):
        raise ValueError('Changed My_Room actor owner descriptor')
    if sha256(original[VROM].extract(native)) != SOURCE_SHA:
        raise ValueError('Changed original native furniture owner')
    changed, fixed, owner = patch_owner(files[VROM].extract(base), files[RELOC].extract(base), helper_symbols)
    art = build_objects(rel, donor_symbols, out)
    additions, imports = {}, []
    blob[INDICES:INDICES + CAPACITY] = b'\xFF' * CAPACITY
    for slot, (pilot, row) in enumerate(zip(PILOTS, art['objects'])):
        index, item, vrom = furniture_slot(pilot.item)
        vrom += object_vrom_offset
        asset = (out / row['object_file']).read_bytes()
        if (len(asset) > BANK_BYTES or len(asset) != row['object_bytes'] or sha256(asset) != row['object_sha256'] or
                any(e.vstart < vrom + len(asset) and vrom < e.vend for e in files.values())):
            raise ValueError('Imported furniture overlaps ROM data or exceeds a native bank')
        profile = native_profile(pilot, len(asset), row['model_offsets'], vrom)
        offset = IMPORTS + slot * 80
        blob[offset:offset + 80] = struct.pack('>HHI', index, item, 1) + profile + bytes(4)
        struct.pack_into('>I', blob, PROFILES + index * 4, 0x80460000 + offset + 8)
        additions[vrom] = asset
        imports.append({'id': row['id'], 'name': row['name'], 'runtime_index': index,
                        'item_id': f'{item:04X}', 'object_vrom': f'{vrom:08X}', 'object_bytes': len(asset),
                        'object_sha256': sha256(asset), 'profile_ram': f'{0x80460000 + offset + 8:08X}',
                        'profile_sha256': sha256(profile), 'playable': False})
    return {VROM: changed, RELOC: fixed}, additions, {'registry_version': FURNITURE_REGISTRY_VERSION,
        'imports': imports, 'owner': owner, 'artwork': art,
        'profile_table_ram': '80465800', 'bank_index_ram': '80466C00', 'capacity': CAPACITY,
        'native_bank_bytes': BANK_BYTES, 'native_bank_count': BANK_COUNT,
        'mutable_ranges': [[PROFILES, PROFILES + NATIVE_COUNT * 4], [INDICES, INDICES + CAPACITY]],
        'ordinary_item_lifecycle_ready': False, 'native_test': 'pending'}
