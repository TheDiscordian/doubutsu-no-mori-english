"""Selected clothing classifications and three additional native tag decisions."""
import struct

from aflib import sha256, u32
from v3_furniture_menu import RAM, SIZE, continuation
from v3_furniture_room import branch_target, query

ABI, CODE, LIMIT = 34, 0x3C30, 0x4000
SOURCES = ('tools/v3_clothing_menu.py', 'overlays/v3/clothing_menu.ld')
SITES = ((0x808735CC, 0x306EF000, 0x000EC303, 'held clothing animation'),
         (0x8087477C, 0x308EF000, 0x000E7B03, 'clothing hand eligibility'),
         (0x80874CE4, 0x3098F000, 0x0018CB03, 'clothing cursor destination'))


def inspect(data, reloc, owner):
    if (len(data) != SIZE or sha256(data) != owner['output_sha256']
            or sha256(reloc) != owner['relocation_sha256']
            or struct.unpack_from('>5I', reloc) != (SIZE, 0, 0, 0, 886)):
        raise ValueError('Changed current complete tag or relocation source')
    records = struct.unpack_from('>886I', reloc, 20)
    fixes = {w & 0xFFFFFF for w in records}
    rows, interiors = [], set()
    for start, first, second, purpose in SITES:
        at = start-RAM
        if (struct.unpack_from('>2I', data, at) != (first, second)
                or fixes & {at, at+4}
                or u32(data, at-4) >> 26 in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23)):
            raise ValueError('Changed, relocated, or delay-slot clothing type window')
        source, temporary, destination = first >> 21 & 31, first >> 16 & 31, second >> 11 & 31
        if source == temporary: raise ValueError('Clothing query loses its full item ID')
        rows.append({'start': start, 'end': start+8, 'source': source, 'temporary': temporary,
                     'destination': destination, 'first': first, 'second': second,
                     'purpose': purpose, 'symbol': f'af_v3_clothing_menu_{start:08x}'})
        interiors.add(start+4)
    for at in range(0, 0x9610, 4):
        word, target = u32(data, at), None
        op = word >> 26
        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
            target = branch_target(RAM+at, word)
        elif op in (2, 3):
            target = 0x80000000 | (word & 0x3FFFFFF) << 2
        if target in interiors: raise ValueError('Incoming branch enters clothing window interior')
    if any(u32(data, w & 0xFFFFFF) in interiors for w in records if w >> 24 & 63 == 2):
        raise ValueError('Relocated pointer enters clothing window interior')
    return rows


def assembly(rows):
    lines = ['/* Checked native clothing tag decisions. */', '.set noreorder', '.set noat',
             '.set gp=64', '.text']
    for row in rows:
        lines += [f'.globl {row["symbol"]}', f'{row["symbol"]}:', f'.word 0x{row["first"]:08x}']
        lines += query(row['source'], row['destination'], 2)+continuation(row['end'])
    return '\n'.join(lines)+'\n'


def install(blob, helper, compiled, data, reloc, owner, room, items, rewards):
    rows = inspect(data, reloc, owner)
    symbols = compiled['symbols']
    if (len(blob) != 0xC000 or not helper or len(helper) > LIMIT-CODE or any(blob[CODE:LIMIT])
            or 0x3A00+rewards['bytes'] > CODE or sha256(helper) != compiled['sha256']
            or sha256(blob[0x8000:0x8000+room['bytes']]) != room['sha256']
            or room['symbols']['af_v3_room_value'] != 0x80468000
            or symbols['af_v3_room_value_clothing'] != 0x80460000+CODE
            or symbols['af_v3_room_query'] != room['symbols']['af_v3_room_query']
            or symbols['af_v3_item_type'] != items['symbols']['af_v3_item_type']):
        raise ValueError('Clothing type code overlaps or has changed compiled dependencies')
    result = bytearray(data)
    jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
    for row in rows:
        target = symbols[row['symbol']]
        if target & 3 or not 0x80460000+CODE <= target < 0x80460000+CODE+len(helper):
            raise ValueError('Clothing menu target outside installed helper')
        struct.pack_into('>2I', result, row['start']-RAM, jump(target), 0)
    before = bytes(blob[0x8000:0x8008])
    struct.pack_into('>2I', blob, 0x8000, jump(symbols['af_v3_room_value_clothing']), 0)
    blob[CODE:CODE+len(helper)] = helper
    return bytes(result), {'source_sha256': sha256(data), 'output_sha256': sha256(result),
        'relocation_sha256': sha256(reloc), 'sites': rows, 'code': compiled,
        'query_entry': '80468000', 'query_before': before.hex(),
        'query_after': blob[0x8000:0x8008].hex(), 'full_item_ids_retained': True,
        'furniture_range_and_index_modes_unchanged': True,
        'ordinary_clothing_actions_tested': False}
