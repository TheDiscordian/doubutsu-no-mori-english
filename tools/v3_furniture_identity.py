"""Preserve full imported IDs at the three inlined room inverse conversions."""
import struct

from aflib import sha256, u32
from v3_furniture_room import branch_target, query, return_to
from v3_furniture_runtime import RAM, RELOC, SECTIONS, SIZE, VROM

ABI, CODE, LIMIT = 22, 0x9D00, 0xA200
SOURCE_SHA = 'cfd1b88e8a763013e666a58487304bdcc618819a9f794490948ee804862c7da1'
RELOCATION_SHA = 'a130c711f128e0ba32d5fdba9e06b7480d848d4badc01fe411731dac6983c762'
EXPORTS = {'af_v3_furniture_import_profile': 0x80465000,
           'af_v3_furniture_item': 0x804652E4}
SOURCES = ('tools/v3_furniture_identity.py', 'overlays/v3/identity.c',
           'overlays/v3/identity.ld', 'overlays/v3/room_entry.S')
SITES = (
    (0x80943CA0, 'collision', 5, 5, (0x24A51000, 0x30A5FFFF)),
    (0x80945FC8, 'tile_lookup', 5, 5, (0x00052880, 0x24A51000)),
    (0x8093BBF0, 'model_dma', 16, 18, (0x3204FFFF, 0x3245FFFF)),
)


def inspect(data, relocation):
    if sha256(data) != SOURCE_SHA or sha256(relocation) != RELOCATION_SHA:
        raise ValueError('Room identity requires the exact range-adapted owner')
    count = u32(relocation, 16)
    fixes, pointers = set(), set()
    for (word,) in struct.iter_unpack('>I', relocation[20:20 + count * 4]):
        section = word >> 30
        at = sum(SECTIONS[:section - 1]) + (word & 0xFFFFFF)
        fixes.add(at)
        if word >> 24 & 63 == 2:
            pointers.add(u32(data, at))
    rows = []
    for address, kind, source, destination, expected in SITES:
        at = address - RAM
        if struct.unpack_from('>2I', data, at) != expected or {at, at + 4} & fixes:
            raise ValueError('Changed room inverse-index instructions or relocation')
        if u32(data, at - 4) >> 26 in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23):
            raise ValueError('Room identity detour begins in a delay slot')
        rows.append({'kind': kind, 'start': address, 'end': address + 8,
                     'source': source, 'destination': destination,
                     'expected': list(expected), 'symbol': f'af_v3_identity_{kind}'})
    interiors = {row['start'] + 4 for row in rows}
    if pointers & interiors:
        raise ValueError('Relocated pointer enters a room identity detour')
    for at in range(0, SECTIONS[0], 4):
        word, target = u32(data, at), None
        op = word >> 26
        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
            target = branch_target(RAM + at, word)
        elif op in (2, 3):
            target = 0x80000000 | (word & 0x3FFFFFF) << 2
        if target in interiors:
            raise ValueError(f'Incoming branch enters room identity: {RAM + at:08X}')
    return rows


def assembly(rows):
    result = ['/* Generated checked room identity detours; no donor assets. */',
              '.set noreorder', '.set noat', '.set gp=64', '.text']
    for row in rows:
        result += [f'.globl {row["symbol"]}', f'{row["symbol"]}:']
        if row['kind'] == 'collision':
            # The displaced ADDIU receives index*4 from an earlier SLL.
            result.append('sra $a1, $a1, 2')
        result += [line.replace('af_v3_room_query', 'af_v3_identity_query')
                   for line in query(row['source'], row['destination'], 0)]
        if row['kind'] == 'collision':
            result.append('andi $a1, $a1, 0xffff')
        elif row['kind'] == 'model_dma':
            result += ['andi $a0, $s0, 0xffff', 'andi $a1, $s2, 0xffff']
        # Tile lookup keeps its following branch and masking delay instruction.
        result += return_to(row['end'])
    return '\n'.join(result) + '\n'


def install(changes, blob, rows, code, symbols, furniture_symbols):
    if any(furniture_symbols.get(name) != address for name, address in EXPORTS.items()):
        raise ValueError('Room identity dependencies moved')
    if len(blob) != 0xC000 or len(code) > LIMIT - CODE or any(blob[CODE:LIMIT]):
        raise ValueError('Room identity reservation is unavailable')
    if rows != inspect(changes[VROM], changes[RELOC]):
        raise ValueError('Room identity inventory changed during compilation')
    result = bytearray(changes[VROM])
    for row in rows:
        target = symbols[row['symbol']]
        if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(code):
            raise ValueError('Room identity detour escapes its compiled code')
        struct.pack_into('>2I', result, row['start'] - RAM,
                         0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
    if len(result) != SIZE:
        raise ValueError('Room identity changed native owner size')
    changes[VROM] = bytes(result)
    blob[CODE:CODE + len(code)] = code
    return {'source_sha256': SOURCE_SHA, 'output_sha256': sha256(result),
            'relocation_sha256': RELOCATION_SHA, 'sites': rows,
            'ordinary_pickup_tested': False}
