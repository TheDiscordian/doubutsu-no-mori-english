"""Selected furniture action, hand-transfer, and room-placement menu dispatch."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_furniture_room import BLOB_SIZE, branch_target, query

ABI, CODE = 21, 0xA800
VROM, RELOC, RAM, SIZE = 0x03950000, 0x03960000, 0x8086F310, 44384
ROOT_VROM, ROOT_RAM, ROOT_SIZE = 0x7749C0, 0x8085BAC0, 0x13620
SOURCE_SHA = '0462b689b147edced562fec29d8910b89fa47a0d27034db89c01f296d69d9613'
RELOC_SHA = 'd2db49411e8c8ddd4bca5e1633ffcb142c0b97b199a9a6014e1655099e378901'
ROOT_SHA = '3812a0538eead12ea59bc1826e8df7c6bd02e8575e0a3a36dfec31f717d262d3'
SOURCES = ('tools/v3_furniture_menu.py', 'overlays/v3/menu.ld')
SITES = ((0x80872BB0, 0x3043F000, 0x00031B03, 'place-in-room dispatch'),
         (0x8087480C, 0x3058F000, 0x0018CB03, 'held-item target eligibility'),
         (0x80875688, 0x30EDF000, 0x000D7303, 'ordinary item action menu'))
INDEX_START, INDEX_END = 0x80871B6C, 0x80871B84
INDEX_WORDS = (0x30A50FFF, 0x04A10002, 0x00A00821, 0x24A10003, 0x00012883, 0x30A5FFFF)
INDEX_SYMBOL = 'af_v3_menu_placement_index'


def inspect(native_code, root, data, reloc):
    if (sha256(root), sha256(data), sha256(reloc)) != (ROOT_SHA, SOURCE_SHA, RELOC_SHA):
        raise ValueError('Changed current tag overlay, parent, or relocation source')
    at = 0x8010DCEC - CODE_RAM
    if native_code[at:at + 28] != bytes.fromhex('00000000007749C0007778B08085BAC08086F0E00000000080117920'):
        raise ValueError('Changed native submenu parent allocation descriptor')
    if struct.unpack_from('>8I', root, 0x2CB0) != (VROM, VROM + SIZE, RAM, RAM + SIZE,
                                                  0x808787A0, 0x80878904, 0x80878904, 0):
        raise ValueError('Changed native tag owner descriptor/constructor')
    if struct.unpack_from('>5I', reloc) != (SIZE, 0, 0, 0, 886):
        raise ValueError('Changed flattened tag relocation format')
    records = struct.unpack_from('>886I', reloc, 20)
    fixes = {w & 0xFFFFFF for w in records}
    if (struct.unpack_from('>6I', data, INDEX_START - RAM) != INDEX_WORDS or
            fixes & set(range(INDEX_START - RAM, INDEX_END - RAM, 4))):
        raise ValueError('Changed or relocated furniture-drop index conversion')
    rows, interiors = [], set(range(INDEX_START + 4, INDEX_END, 4))
    for start, first, second, purpose in SITES:
        at = start - RAM
        if struct.unpack_from('>2I', data, at) != (first, second) or fixes & {at, at + 4}:
            raise ValueError('Changed or relocated menu type window')
        source, temporary, destination = first >> 21 & 31, first >> 16 & 31, second >> 11 & 31
        if source == temporary:
            raise ValueError('Menu query would lose its original item')
        rows.append({'start': start, 'end': start + 8, 'source': source,
                     'temporary': temporary, 'destination': destination, 'first': first,
                     'second': second, 'purpose': purpose, 'symbol': f'af_v3_menu_type_{start:08x}'})
        interiors.add(start + 4)
    for at in range(0, 0x9610, 4):
        if INDEX_START <= RAM + at < INDEX_END:
            continue  # The displaced signed-division branch is internal.
        word = u32(data, at)
        op = word >> 26
        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23):
            target = branch_target(RAM + at, word)
        elif op in (2, 3):
            target = 0x80000000 | (word & 0x3FFFFFF) << 2
        else:
            continue
        if target in interiors:
            raise ValueError('Incoming branch enters a menu detour interior')
    if any(u32(data, w & 0xFFFFFF) in interiors for w in records if w >> 24 & 63 == 2):
        raise ValueError('Relocated pointer enters a menu detour interior')
    return rows


def assembly(rows):
    lines = ['/* Generated checked tag type detours. */', '.set noreorder', '.set noat', '.set gp=64', '.text']
    for row in rows:
        name = row['symbol']
        lines += [f'.globl {name}', f'{name}:', f'.word 0x{row["first"]:08x}']
        lines += query(row['source'], row['destination'], 2)
        # The parent loader updates its constructor pointer after tag init.
        # None of these three runtime menu paths runs during that constructor.
        lines += continuation(row['end'])
    lines += [f'.globl {INDEX_SYMBOL}', f'{INDEX_SYMBOL}:']
    lines += query(5, 1, 1)
    # Native drop strips the type nibble before dividing by four. Imported
    # furniture needs its expanded runtime index, not a low-bank alias. The
    # query differs from item-0x1000 only for an enabled import; keep the old
    # low-twelve-bit result for every other sixteen-bit input, including gaps.
    lines += ['addiu $a1, $a1, -4096', f'beq $at, $a1, {INDEX_SYMBOL}_native',
              'andi $a1, $a1, 4095', 'or $a1, $at, $zero',
              f'{INDEX_SYMBOL}_native:', 'or $at, $a1, $zero',
              'sra $a1, $at, 2', 'andi $a1, $a1, 65535']
    lines += continuation(INDEX_END)
    return '\n'.join(lines) + '\n'


def continuation(address):
    offset = address - 0x808787A0
    if not -32768 <= offset < 32768:
        raise ValueError('Menu continuation exceeds the checked constructor-relative offset')
    return ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8011',
            'lw $ra, -0x2314($ra)', 'lw $ra, 0x2cc0($ra)',
            f'addiu $ra, $ra, {offset}', 'addiu $sp, $sp, 16',
            'jr $ra', 'ld $ra, -8($sp)']


def install(base, native_code, blob, rows, helper, symbols, room_symbols):
    files = by_vrom(base)
    original, reloc = files[VROM].extract(base), files[RELOC].extract(base)
    if (len(blob) != BLOB_SIZE or any(blob[CODE:-16]) or len(helper) > BLOB_SIZE - CODE - 16
            or room_symbols['af_v3_room_query'] != 0x804680B8):
        raise ValueError('Menu helper overlaps the resident layout or has a changed query ABI')
    if rows != inspect(native_code, files[ROOT_VROM].extract(base), original, reloc):
        raise ValueError('Menu inventory changed during compilation')
    data = bytearray(original)
    for row in rows:
        target = symbols[row['symbol']]
        if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper):
            raise ValueError('Menu detour target outside compiled code')
        struct.pack_into('>II', data, row['start'] - RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
    target = symbols[INDEX_SYMBOL]
    if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper):
        raise ValueError('Furniture-drop index helper outside compiled code')
    data[INDEX_START - RAM:INDEX_END - RAM] = struct.pack('>6I',
        0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0, 0, 0)
    blob[CODE:CODE + len(helper)] = helper
    return {VROM: bytes(data)}, {'source_sha256': SOURCE_SHA, 'output_sha256': sha256(data),
        'relocation_sha256': RELOC_SHA, 'parent_sha256': ROOT_SHA, 'sites': rows,
        'placement_index': {'start': INDEX_START, 'end': INDEX_END,
                            'symbol': INDEX_SYMBOL, 'original_words': list(INDEX_WORDS)},
        'ordinary_placement_tested': False, 'save_profile_support_ready': False}
