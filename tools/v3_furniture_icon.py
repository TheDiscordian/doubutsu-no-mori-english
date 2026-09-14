"""Selected imported furniture uses the native submenu leaf descriptor."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from v3_furniture_menu import ROOT_SHA
from v3_furniture_room import BLOB_SIZE, branch_target, query

ABI, CODE = 10, 0xAB00
VROM, RELOC, RAM, SIZE, RESIDENT = 0x7749C0, 0x7778B0, 0x8085BAC0, 0x2EF0, 0x13620
RELOC_SHA = '6bf5b91ed57e9ede41bbff8bbe6dea18844e99fcfe668b88a0e115cc5669a5fa'
SECTIONS = (8720, 3232, 64, 67376, 134)
START, END, LEAF, DRAW = 0x8085C880, 0x8085C888, 0x8085DCF8, 0x8085C980
SYMBOL = 'af_v3_furniture_icon_type'
SOURCES = ('tools/v3_furniture_icon.py', 'overlays/v3/icon.ld')


def inspect(native_code, data, reloc):
    if (sha256(data), sha256(reloc)) != (ROOT_SHA, RELOC_SHA):
        raise ValueError('Changed current submenu parent or relocation source')
    at = 0x8010DCEC - CODE_RAM
    if native_code[at:at + 28] != bytes.fromhex('00000000007749C0007778B08085BAC08086F0E00000000080117920'):
        raise ValueError('Changed native submenu parent allocation descriptor')
    if struct.unpack_from('>5I', reloc) != SECTIONS:
        raise ValueError('Changed submenu parent section layout')
    records = struct.unpack_from('>134I', reloc, 20)
    starts = (0, 0, SECTIONS[0], SECTIONS[0] + SECTIONS[1])
    positions = [(w, starts[w >> 30] + (w & 0xFFFFFF)) for w in records]
    if ({at for _, at in positions} & {START - RAM, START - RAM + 4}
            or struct.unpack_from('>2I', data, START - RAM) != (0x00194B03, 0x24010001)):
        raise ValueError('Changed or relocated icon type window')
    for at in range(0, SECTIONS[0], 4):
        word, target = u32(data, at), None
        op = word >> 26
        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
            target = branch_target(RAM + at, word)
        elif op in (2, 3):
            target = 0x80000000 | (word & 0x3FFFFFF) << 2
        if target == START + 4:
            raise ValueError('Incoming branch enters the icon detour interior')
    if any(u32(data, at) == START + 4 for w, at in positions if w >> 24 & 63 == 2):
        raise ValueError('Relocated pointer enters the icon detour interior')


def assembly():
    lines = ['/* Selected furniture classification; native icon drawing remains intact. */',
             '.set noreorder', '.set noat', '.set gp=64', '.text', f'.globl {SYMBOL}', f'{SYMBOL}:']
    lines += query(16, 9, 2)
    lines += ['addiu $at, $zero, 1', 'addiu $sp, $sp, -16', 'sd $ra, 8($sp)',
              'lui $ra, 0x8011', 'lw $ra, -0x2314($ra)', f'addiu $ra, $ra, {END - RAM}',
              'addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']
    return '\n'.join(lines) + '\n'


def install(base, native_code, blob, helper, symbols, room_symbols):
    files = by_vrom(base)
    original, reloc = (files[v].extract(base) for v in (VROM, RELOC))
    inspect(native_code, original, reloc)
    if (len(blob) != BLOB_SIZE or any(blob[CODE:-16]) or len(helper) > BLOB_SIZE - CODE - 16
            or room_symbols['af_v3_room_query'] != 0x804680B8
            or symbols[SYMBOL] != 0x80460000 + CODE):
        raise ValueError('Icon helper overlaps resident data or has a changed query ABI')
    data = bytearray(original)
    struct.pack_into('>II', data, START - RAM, 0x08000000 | (symbols[SYMBOL] >> 2 & 0x3FFFFFF), 0)
    blob[CODE:CODE + len(helper)] = helper
    return {VROM: bytes(data)}, {'source_sha256': ROOT_SHA, 'output_sha256': sha256(data),
        'relocation_sha256': RELOC_SHA, 'start': START, 'end': END, 'leaf_descriptor': LEAF,
        'draw_continuation': DRAW, 'ordinary_inventory_tested': False}
