"""Connect imported shop stock to reserve points, floor selection, and removal."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from v3_furniture_room import branch_target, query

ABI, CODE, LIMIT = 18, 0x7C00, 0x7FF0
VROM, RELOC, RAM, POINTER = 0x848BF0, 0x849AC0, 0x80953E20, 0x80101140
SIZE, SECTIONS = 3792, (3680, 112, 0, 0, 29)
SOURCE_SHA = '41daf5b28f0ed36645262b83eccdfa5427827c24b418484e5efa5818ec32f4cc'
RELOC_SHA = 'deca35901a3e894bcd2bd18c5bcafaa00d629e4cc2df00252d3e3be2b42ddf63'
SOURCES = ('tools/v3_shop_floor.py', 'overlays/v3/shop_floor.ld')
SITES = ((0x80953E54, 4, 0x50200004, 0x24011F36, 'reserve-point selection'),
         (0x80954888, 3, 0x14200023, 0x28612000, 'floor-item selection'),
         (0x80954AD0, 3, 0x1020001D, 0x3C028013, 'sold furniture removal'))


def inspect(base, code):
    files = by_vrom(base)
    data, reloc = (files[v].extract(base) for v in (VROM, RELOC))
    if (sha256(data), sha256(reloc)) != (SOURCE_SHA, RELOC_SHA):
        raise ValueError('Changed complete shop floor owner or relocation')
    if struct.unpack_from('>5I', reloc) != SECTIONS:
        raise ValueError('Changed shop floor sections')
    if struct.unpack_from('>8I', code, POINTER - 16 - CODE_RAM) != (
            VROM, VROM + SIZE, RAM, RAM + SIZE, 0, 0x80954C80, 0, 0):
        raise ValueError('Changed shop floor allocation descriptor')
    found = [RAM + at + 4 for at in range(0, SECTIONS[0], 4)
             if u32(data, at) >> 26 == 10 and u32(data, at) & 65535 == 0x1ECD]
    if found != [row[0] for row in SITES]:
        raise ValueError('Changed complete shop floor range inventory')
    records = struct.unpack_from('>29I', reloc, 20)
    fixes = {(0, 0, SECTIONS[0], sum(SECTIONS[:2]))[w >> 30] + (w & 0xFFFFFF) for w in records}
    rows = []
    for address, source, branch, delay, purpose in SITES:
        at = address - RAM
        upper = 10 << 26 | source << 21 | 1 << 16 | 0x1ECD
        if struct.unpack_from('>3I', data, at - 4) != (upper, branch, delay) or {at, at + 4} & fixes:
            raise ValueError('Changed shop floor branch/delay contract')
        rows.append({'start': address, 'source': source, 'branch': branch, 'delay': delay,
                     'fall': address + 8, 'taken': branch_target(address, branch),
                     'likely': branch >> 26 == 20, 'purpose': purpose,
                     'symbol': f'af_v3_shop_floor_{address:08x}'})
    return rows


def assembly(rows):
    def resume(address):
        offset = address - RAM
        if not 0 <= offset < SECTIONS[0]:
            raise ValueError('Shop floor continuation escapes its owner')
        return ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8010',
                'lw $ra, 0x1140($ra)', f'addiu $ra, $ra, {offset}',
                'addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']
    lines = ['/* Checked single-word shop floor branch detours. */',
             '.set noreorder', '.set noat', '.set gp=64', '.text']
    for row in rows:
        name = row['symbol']
        lines += [f'.globl {name}', f'{name}:'] + query(row['source'], 1, 0)
        # Keep the original delay word in the actor: a preceding branch enters
        # that instruction directly in the floor selector. These three words
        # have only checked register effects; recompute the upper predicate, then
        # reproduce the original branch's delay effect and annul semantics.
        branch = 'bnez' if row['branch'] >> 26 == 5 else 'beqz'
        lines += [f'{branch} $at, {name}_taken',
                  'nop' if row['likely'] else f'.word 0x{row["delay"]:08x}']
        lines += resume(row['fall']) + [f'{name}_taken:']
        if row['likely']:
            lines += [f'.word 0x{row["delay"]:08x}']
        lines += resume(row['taken'])
    return '\n'.join(lines) + '\n'


def install(base, code, blob, rows, helper, symbols, actors, room):
    if (len(blob) != 0xC000 or not helper or len(helper) > LIMIT - CODE
            or any(blob[CODE:LIMIT]) or 0x7600 + actors['bytes'] > CODE
            or symbols['af_v3_room_query'] != 0x804680B8
            or room['symbols']['af_v3_room_query'] != 0x804680B8):
        raise ValueError('Shop floor helper overlaps memory or changes its query dependency')
    if rows != inspect(base, code):
        raise ValueError('Shop floor inventory changed during construction')
    data = bytearray(by_vrom(base)[VROM].extract(base))
    for row in rows:
        target = symbols[row['symbol']]
        if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper):
            raise ValueError('Shop floor branch target escapes compiled code')
        struct.pack_into('>I', data, row['start'] - RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF))
    blob[CODE:CODE + len(helper)] = helper
    return {VROM: bytes(data)}, {'sites': rows, 'source_sha256': SOURCE_SHA,
        'output_sha256': sha256(data), 'relocation_sha256': RELOC_SHA,
        'extra_allocation_bytes': 0, 'save_format_changed': False,
        'ordinary_shop_gameplay_tested': False}
