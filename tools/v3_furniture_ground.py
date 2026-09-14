"""Selected imported furniture drop flags and ground-render descriptor dispatch."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from v3_furniture_room import BLOB_SIZE, branch_target, query

ABI, CODE = 11, 0xAE00
VROM, RELOC, RAM = 0x805E30, 0x80F760, 0x8090D530
SIZE, RESIDENT = 39216, 40384
SOURCE_SHA = 'e6e4fa4482a3e3c0877028b19fbab2dc68082a3e97f273bd5e7819f074677af7'
RELOC_SHA = '2a64fe752b8cecc4f4d6df214aafe34e1d5d36500dc3a65e53e8f6040141bb76'
SECTIONS = (31440, 7536, 240, 1168, 1103)
SOURCES = ('tools/v3_furniture_ground.py', 'overlays/v3/ground.ld')
SITES = ((0x8090F888, (0x308CF000, 0x000C6B03), 12, 13, 'drop furniture flags'),
         (0x8090FA1C, (0x00095303, 0x15410004), None, 10, 'alternate drop furniture flags'),
         (0x80911CF0, (0x3082F000, 0x00021303), 2, 2, 'ground descriptor selection'))


def inspect(code, data, reloc):
    if (sha256(data), sha256(reloc)) != (SOURCE_SHA, RELOC_SHA):
        raise ValueError('Changed ground-item owner or relocation source')
    at = 0x80100CB0 - CODE_RAM
    if code[at:at + 32] != bytes.fromhex('00805e300080f7608090d530809172f000000000809150000000000000000000'):
        raise ValueError('Changed ground-item allocation descriptor')
    if struct.unpack_from('>5I', reloc) != SECTIONS:
        raise ValueError('Changed ground-item section layout')
    records = struct.unpack_from('>1103I', reloc, 20)
    starts = (0, 0, SECTIONS[0], SECTIONS[0] + SECTIONS[1])
    positions = [(w, starts[w >> 30] + (w & 0xFFFFFF)) for w in records]
    fixes = {at for _, at in positions}
    interiors = {start + 4 for start, *_ in SITES}
    for start, words, _, _, _ in SITES:
        at = start - RAM
        if struct.unpack_from('>2I', data, at) != words or fixes & {at, at + 4}:
            raise ValueError('Changed or relocated ground type window')
    if u32(data, 0x8090FA24 - RAM) != 0x00001025:
        raise ValueError('Changed alternate drop branch delay')
    for at in range(0, SECTIONS[0], 4):
        word, target = u32(data, at), None
        op = word >> 26
        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
            target = branch_target(RAM + at, word)
        elif op in (2, 3):
            target = 0x80000000 | (word & 0x3FFFFFF) << 2
        if target in interiors:
            raise ValueError('Incoming branch enters a ground detour interior')
    if any(u32(data, at) in interiors for w, at in positions if w >> 24 & 63 == 2):
        raise ValueError('Relocated pointer enters a ground detour interior')


def return_to(address):
    offset = address - RAM
    if not 0 <= offset < 0x8000:
        raise ValueError('Ground continuation exceeds checked offset')
    return ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8010',
            'lw $ra, 0x0cc0($ra)', f'addiu $ra, $ra, {offset}',
            'addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']


def assembly():
    lines = ['/* Checked ground-item type windows. */', '.set noreorder', '.set noat', '.set gp=64', '.text']
    for start, words, temporary, destination, _ in SITES:
        name = f'af_v3_ground_type_{start:08x}'
        lines += [f'.globl {name}', f'{name}:']
        if temporary is not None:
            lines += [f'.word 0x{words[0]:08x}']
        lines += query(4, destination, 2)
        if temporary is None:
            # Replace the original SRA/BNE pair, preserving its zero-V0 delay
            # on both outcomes. The mask in the earlier branch delay is intact.
            lines += [f'bne $10, $at, {name}_taken', 'move $v0, $zero']
            lines += return_to(0x8090FA28)
            lines += [f'{name}_taken:'] + return_to(0x8090FA34)
        else:
            lines += return_to(start + 8)
    return '\n'.join(lines) + '\n'


def install(base, code, blob, helper, symbols, room_symbols):
    files = by_vrom(base)
    original, reloc = (files[v].extract(base) for v in (VROM, RELOC))
    inspect(code, original, reloc)
    if (len(blob) != BLOB_SIZE or any(blob[CODE:-16]) or len(helper) > BLOB_SIZE - CODE - 16
            or room_symbols['af_v3_room_query'] != 0x804680B8):
        raise ValueError('Ground helper overlaps resident data or has a changed query ABI')
    data = bytearray(original)
    for start, _, _, _, _ in SITES:
        target = symbols[f'af_v3_ground_type_{start:08x}']
        if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper):
            raise ValueError('Ground detour target outside compiled code')
        struct.pack_into('>II', data, start - RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
    blob[CODE:CODE + len(helper)] = helper
    return {VROM: bytes(data)}, {'source_sha256': SOURCE_SHA, 'output_sha256': sha256(data),
        'relocation_sha256': RELOC_SHA, 'sites': [start for start, *_ in SITES],
        'ordinary_drop_pickup_tested': False, 'save_reload_tested': False}
