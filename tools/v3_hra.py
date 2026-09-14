"""Extend the translated native HRA evaluator without replacing its scoring rules."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from catalogue_names import Image, elf_inventory
from gc_names import rel_sections
from npc_mail_show import relocate_verified_data
from v3_furniture_art import verify_sources
from v3_furniture_room import assembly as room_assembly, branch_target, query

ABI = 19
VROM, RELOC, RAM = 0x81D9D0, 0x821740, 0x809259E0
NEW_VROM, NEW_RELOC = 0x03F40000, 0x03F48000
SIZE, START, COUNT, TABLE = 15728, 16976, 1267, 0x809286CC
SECTIONS = (10704, 5024, 0, 1248, 245)
SOURCE_SHA = 'bb2d983ca0751681838d02dd96d5e7fdf63402d2acdc8410cfd3c0f1d89712a1'
RELOC_SHA = 'a53d04cb5992a96bff77aa8cb9f022aff02764821f659c5578763b61fc6e39a5'
DONOR_SHA = '231d23625c126b048d95be99f397e2f05f564af23423c1f911d706acaec37f0e'
SOURCES = ('tools/v3_hra.py', 'overlays/v3/hra.c', 'overlays/v3/hra.ld')
RANGES = (0x80926178, 0x809261C4, 0x80926210, 0x80926370, 0x809263C4,
          0x809263FC, 0x80926434, 0x8092646C, 0x809266CC, 0x80926888,
          0x809268DC, 0x80926914, 0x8092694C, 0x80926984, 0x809275C4,
          0x80927620, 0x80927664, 0x80927FF4, 0x80928084, 0x809280F8)
IMPORTS = {'af_v3_room_query': 0x804680B8, 'af_v3_furniture_import_profile': 0x80465000}


def sources(base):
    files = by_vrom(base)
    data, reloc = (files[v].extract(base) for v in (VROM, RELOC))
    if (len(data) != SIZE or sha256(data) != SOURCE_SHA or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS):
        raise ValueError('Changed complete translated HRA owner or relocation')
    return data, reloc


def table(base, rel, symbols, furniture):
    data, _ = sources(base)
    verify_sources(rel, symbols)
    # Two private symbols share this name. Select the pinned HRA definition,
    # not the earlier two-byte feng shui table returned by name-only lookup.
    lines = [line for line in symbols.decode().splitlines() if line.startswith('mMkRm_ftr_info =')]
    if len(lines) != 2 or not any('.data:0x0004FAFC;' in line and 'size:0x13C8' in line for line in lines):
        raise ValueError('Changed disambiguated donor HRA symbol')
    start = rel_sections(rel)[5][0] + 0x4FAFC
    donor = rel[start:start + 1266 * 4]
    if sha256(donor) != DONOR_SHA:
        raise ValueError('Changed actual donor HRA table')
    native = data[TABLE - RAM:TABLE - RAM + 947 * 4]
    output = bytearray(native + bytes.fromhex('FC000000') * (COUNT - 947))
    # The original upper bound includes the one-past-table marker 1ECC. Give
    # that marker an inert OTHER/unobtainable row so it cannot index series 63
    # into the 55-entry search buffer. It is not an imported or orderable item.
    output[947 * 4:948 * 4] = bytes.fromhex('D4002000')
    records, seen = [], set()
    for row in furniture:
        item, index = int(row['item_id'], 16), row['runtime_index']
        if (item, index) not in ((0x3224, 1161), (0x32B8, 1198)) or index in seen:
            raise ValueError('Unreviewed or duplicate HRA import')
        seen.add(index)
        donor_metadata = donor[index * 4:index * 4 + 4]
        if donor_metadata != bytes.fromhex('40050200' if item == 0x3224 else '40050000'):
            raise ValueError('Changed imported HRA properties')
        # Native birth categories occupy five bits [13:9], followed by surface
        # [8:7]. GC adds a birth bit, moving birth/surface down by one. Face and
        # lucky remain at [15:14]. Do not copy four-byte records unchanged.
        value = u32(donor_metadata, 0)
        birth, surface = value >> 8 & 63, value >> 6 & 3
        if birth >= 19 or value & 63:
            raise ValueError('Donor HRA category lacks a reviewed native equivalent')
        metadata = struct.pack('>I', value & 0xFFFFC000 | birth << 9 | surface << 7)
        output[index * 4:index * 4 + 4] = metadata
        records.append({'item_id': f'{item:04X}', 'runtime_index': index,
                        'metadata': metadata.hex(), 'donor_metadata': donor_metadata.hex(),
                        'series': 16, 'birth_category': birth, 'surface': surface})
    # Construction uses a native 32-bit completion mask, not an arbitrary list.
    construction = sum(output[i * 4] >> 2 == 16 for i in range(COUNT))
    if data[0x809283B0 - RAM + 16 * 3] != 2 or not 19 <= construction <= 32:
        raise ValueError('Imported construction group exceeds native completion capacity')
    return bytes(output), records


def relocation_slots(reloc):
    return [(sum(SECTIONS[:(w >> 30) - 1]) + (w & 0xFFFFFF), w >> 24 & 63)
            for (w,) in struct.iter_unpack('>I', reloc[20:20 + SECTIONS[4] * 4])]


def inspect(base):
    data, reloc = sources(base)
    fixes = dict(relocation_slots(reloc))
    found = tuple(RAM + at for at in range(0, SECTIONS[0], 4)
                  if u32(data, at) >> 26 == 10 and u32(data, at) & 65535 == 0x1ECD)
    if found != RANGES:
        raise ValueError('Changed complete HRA range inventory')
    rows = []
    for address in RANGES:
        at = address - RAM
        lower, lower_branch, upper, branch, delay = struct.unpack_from('>5I', data, at - 8)
        paired = address not in RANGES[:2]
        if (upper >> 16 & 31 != 1 or branch >> 16 not in (0x1020, 0x5420)
                or paired and (lower & 0xFC1FFFFF != 0x28011000 or lower_branch >> 16 != 0x1420)):
            raise ValueError('Changed native HRA branch contract')
        start = address - 8 if paired else address
        rows.append({'kind': 'range', 'start': start, 'end': address + 8,
            'upper': address, 'source': upper >> 21 & 31, 'upper_word': upper,
            'branch': branch, 'delay': delay, 'paired': paired,
            'lower_word': lower if paired else None,
            'lower_target': branch_target(address - 4, lower_branch) if paired else None,
            'taken': branch_target(address + 4, branch), 'fall': address + 8,
            'symbol': f'af_v3_hra_range_{address:08x}'})
    # Each accepted furniture read has ADDIU item,-1000 in a branch delay slot.
    # Keep that entry point intact and adapt the following SRA/SLL pair instead.
    transforms = [a + 12 for a in RANGES[2:]] + [0x8092801C, 0x809280AC]
    found = [RAM + at for at in range(0, SECTIONS[0], 4)
             if u32(data, at) >> 26 == 9 and u32(data, at) & 65535 == 0xF000]
    if sorted(found) != sorted(a - 4 for a in transforms):
        raise ValueError('Changed complete HRA item-index inventory')
    for address in transforms:
        offset, shift, scale = struct.unpack_from('>3I', data, address - RAM - 4)
        source, temporary = offset >> 21 & 31, offset >> 16 & 31
        destination = shift >> 11 & 31
        if shift != temporary << 16 | destination << 11 | 2 << 6 | 3 or scale != destination << 16 | (scale >> 11 & 31) << 11 | 2 << 6:
            raise ValueError('Changed HRA index/rotation arithmetic')
        rows.append({'kind': 'index', 'start': address, 'end': address + 8,
            'source': source, 'destination': temporary, 'shift': shift, 'scale': scale,
            'symbol': f'af_v3_hra_index_{address:08x}'})
    occupied = {address for row in rows for address in range(row['start'], row['end'], 4)}
    if len(occupied) != sum((row['end'] - row['start']) // 4 for row in rows):
        raise ValueError('Overlapping HRA hooks')
    interiors = occupied - {row['start'] for row in rows}
    if any(a - RAM in fixes for a in occupied):
        raise ValueError('HRA hook displaces a native relocation')
    for at in range(0, SECTIONS[0], 4):
        if RAM + at in occupied:
            continue
        word = u32(data, at)
        target = None
        if word >> 26 in (1, 4, 5, 6, 7, 20, 21, 22, 23):
            target = branch_target(RAM + at, word)
        elif word >> 26 in (2, 3):
            target = 0x80000000 | (word & 0x3FFFFFF) << 2
        if target in interiors:
            raise ValueError('Incoming branch enters a replaced HRA interior')
    if any(u32(data, at) in interiors for at, kind in fixes.items() if kind == 2):
        raise ValueError('Native pointer enters a replaced HRA interior')
    return rows


def resume(address):
    offset = address - RAM
    if not 0 <= offset < SECTIONS[0]:
        raise ValueError('HRA continuation escapes original text')
    return ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8010',
            'lw $ra, 0x7b50($ra)', f'addiu $ra, $ra, {offset}',
            'addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']


def assembly(rows):
    result = room_assembly([r for r in rows if r['kind'] == 'range'], return_builder=resume)
    for row in rows:
        if row['kind'] != 'index':
            continue
        result += '\n'.join([f'.globl {row["symbol"]}', f'{row["symbol"]}:']
            + query(row['source'], row['destination'], 1)
            + [f'.word 0x{row["shift"]:08x}', f'.word 0x{row["scale"]:08x}']
            + resume(row['end'])) + '\n'
    return result


def install(base, code, suffix, compiled, metadata, records, rows):
    old, reloc = sources(base)
    symbols = compiled['symbols']
    if (rows != inspect(base) or len(suffix) != compiled['bytes'] or len(suffix) % 16
            or not 0 < len(suffix) <= 0x8000 - START
            or any(symbols[name] != target for name, target in IMPORTS.items())):
        raise ValueError('Changed HRA compiled image or dependencies')
    data = bytearray(old + bytes(START - SIZE) + suffix)
    table_address = symbols['af_v3_hra_table']
    at = table_address - RAM
    if not START <= at <= len(data) - len(metadata) or data[at:at + len(metadata)] != metadata:
        raise ValueError('Linked HRA table differs from complete conversion')
    slots = relocation_slots(reloc)
    changes = {}

    def word(address, before, after):
        pos = address - RAM
        if u32(old, pos) != before or pos in changes and changes[pos] != after:
            raise ValueError(f'Conflicting HRA patch at {address:08X}')
        changes[pos] = after
        struct.pack_into('>I', data, pos, after)

    high, pointer_changes = {}, []
    for pos, kind in slots:
        original = u32(old, pos)
        if kind == 5:
            high[original >> 16 & 31] = pos, original
        elif kind == 6:
            hi_at, hi = high[original >> 21 & 31]
            target = (hi & 65535) * 65536 + (original & 65535) - (65536 if original & 32768 else 0)
            is_end = target == TABLE + 947 * 4 and original >> 26 == 9
            if TABLE <= target < TABLE + 947 * 4 or is_end:
                new = table_address + (COUNT * 4 if is_end else target - TABLE)
                word(RAM + hi_at, hi, hi & 0xFFFF0000 | (new + 0x8000) >> 16 & 65535)
                word(RAM + pos, original, original & 0xFFFF0000 | new & 65535)
                pointer_changes.append({'high': RAM + hi_at, 'low': RAM + pos, 'before': target, 'after': new})
    if len(pointer_changes) != 48:
        raise ValueError('Changed complete HRA metadata pointer inventory')
    for row in rows:
        for address in range(row['start'], row['end'], 4):
            target = symbols[row['symbol']]
            if not RAM + START <= target < RAM + len(data):
                raise ValueError('HRA detour escapes compiled suffix')
            after = 0x08000000 | (target >> 2 & 0x3FFFFFF) if address == row['start'] else 0
            word(address, u32(old, address - RAM), after)
        slots.append((row['start'] - RAM, 4))
    word(0x80925A5C, 0x27BDFFF8, 0x08000000 | (symbols['af_v3_hra_remaining'] >> 2 & 0x3FFFFFF))
    word(0x80925A60, 0x00803825, 0)
    slots.append((0x80925A5C - RAM, 4))
    for pos, kind, target, name in elf_inventory(compiled['elf_relocations'], ram=RAM):
        if not START <= pos <= len(data) - 4 or pos & 3:
            raise ValueError('HRA suffix relocation escapes owned image')
        if RAM <= target < RAM + len(data):
            slots.append((pos, kind))
        elif IMPORTS.get(name) != target or kind != 4:
            raise ValueError('Unbound HRA suffix target')
    if len({pos for pos, _ in slots}) != len(slots):
        raise ValueError('Duplicate HRA relocation')
    size = (24 + 4 * len(slots) + 15) & ~15
    values = [0x40000000 | kind << 24 | pos for pos, kind in slots]
    new_rel = (struct.pack('>5I', len(data), 0, 0, 0, len(slots))
        + struct.pack('>' + str(len(values)) + 'I', *values)
        + bytes(size - 24 - len(values) * 4) + struct.pack('>I', size))
    if len(data) + size > 0x8800:
        raise ValueError('HRA transient image and relocation exceed reviewed bound')
    allowed = {i for pos in changes for i in range(pos, pos + 4)}
    for loaded in (0x801A0010, 0x802F8010, 0x803D0010):
        before = relocate_verified_data(Image(RAM, START, SECTIONS), old, reloc, loaded)
        after = relocate_verified_data(Image(RAM, len(data), (len(data), 0, 0, 0, len(slots))), bytes(data), new_rel, loaded)
        if any(a != b and i not in allowed for i, (a, b) in enumerate(zip(before, after))):
            raise ValueError('HRA adaptation changes unrelated relocated code/data/BSS')
    scheduler = []
    def scheduler_word(address, before, after):
        if u32(code, address - CODE_RAM) != before:
            raise ValueError('Changed HRA scheduler allocation or load contract')
        struct.pack_into('>I', code, address - CODE_RAM, after)
        scheduler.append({'address': address, 'before': before, 'after': after})
    end = RAM + len(data)
    for address, register, value, original in (
            (0x8009CED0, 10, end, 0x80929C30),
            (0x8009CF0C, 7, end, 0x80929C30),
            (0x8009CF00, 4, NEW_VROM, VROM),
            (0x8009CF04, 5, NEW_VROM + len(data), VROM + SIZE)):
        lows = {0x8009CED0: 0x8009CED8, 0x8009CF0C: 0x8009CF10,
                0x8009CF00: 0x8009CF1C, 0x8009CF04: 0x8009CF18}
        scheduler_word(address, 0x3C000000 | register << 16 | (original + 0x8000) >> 16,
                       0x3C000000 | register << 16 | (value + 0x8000) >> 16)
        scheduler_word(lows[address], 0x24000000 | register << 21 | register << 16 | original & 65535,
                       0x24000000 | register << 21 | register << 16 | value & 65535)
    return {VROM: bytes(data), RELOC: new_rel}, {
        'imports': records, 'source_sha256': SOURCE_SHA, 'source_relocation_sha256': RELOC_SHA,
        'donor_table_sha256': DONOR_SHA, 'metadata_rows': COUNT, 'metadata_address': table_address,
        'metadata_sha256': sha256(metadata), 'source_resident_bytes': START, 'bytes': len(data),
        'relocation_bytes': size, 'on_demand_growth': len(data) - START,
        'output_sha256': sha256(data), 'relocation_sha256': sha256(new_rel),
        'sites': rows, 'pointer_changes': pointer_changes, 'scheduler': scheduler,
        'patches': [{'address': RAM + at, 'before': u32(old, at), 'after': word} for at, word in sorted(changes.items())],
        'save_format_changed': False, 'native_scoring_tested': False,
        'ordinary_scoring_tested': False, 'feng_shui_implemented': False}
