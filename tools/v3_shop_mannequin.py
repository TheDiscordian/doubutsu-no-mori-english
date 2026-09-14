"""Recognise selected additive garments in native shop mannequin counting/search."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_furniture_room import branch_target, query
from v3_npc_clothing import guard_incoming
from v3_villager_readers import relocation_offsets

ABI, CODE, LIMIT = 38, 0x4C00, 0x5000
VROM, RELOC, RAM, SIZE, POINTER = 0x84E080, 0x84F0E0, 0x809592B0, 4192, 0x801012E0
SECTIONS = (4064, 64, 64, 0, 32)
SOURCE_SHA = '4381a0683e999c14da2a9c75898203710842ff2b35fee8b5ce5b02ceb6ba67b0'
RELOC_SHA = '7041005848b758b0ef7e97ebfae4267697a2daa7b5108c403b16a8a95034fb68'
STARTS = (0x80959320, 0x80959348, 0x80959370, 0x80959398, 0x809596C8, 0x8095972C)
SOURCES = ('tools/v3_shop_mannequin.py', 'overlays/v3/shop_mannequin.ld')


def inspect(base):
    files = by_vrom(base)
    data, reloc, code = (files[v].extract(base) for v in (VROM, RELOC, CODE_VROM))
    if (sha256(data) != SOURCE_SHA or len(data) != SIZE or sha256(reloc) != RELOC_SHA
            or struct.unpack_from('>5I', reloc) != SECTIONS
            or struct.unpack_from('>6I', code, POINTER-16-CODE_RAM) !=
               (VROM, RELOC, RAM, RAM+SIZE, 0, 0x8095A290)):
        raise ValueError('Changed complete mannequin owner, relocation, or descriptor')
    if tuple(RAM+i for i in range(0, SECTIONS[0], 4)
             if u32(data, i) >> 26 == 10 and u32(data, i) & 65535 == 0x2400) != STARTS:
        raise ValueError('Changed complete mannequin clothing-range inventory')
    rows, fixes = [], relocation_offsets(reloc)
    for start in STARTS:
        at = start-RAM
        lower, branch, upper, choose, delay = struct.unpack_from('>5I', data, at)
        source = 2 if start < 0x80959400 else 3
        likely = source == 2
        if ((lower, branch, upper, choose, delay) !=
                ((10 << 26) | source << 21 | 1 << 16 | 0x2400, 0x14200003,
                 (10 << 26) | source << 21 | 1 << 16 | 0x2500,
                 0x54200004 if likely else 0x14200003, 0x24840001 if likely else 0)
                or fixes & set(range(at, at+16, 4))
                or u32(data, at-4) >> 26 in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23)):
            raise ValueError('Changed or relocated mannequin branch window')
        rows.append({'start': start, 'end': start+16, 'source': source,
                     'lower': lower, 'upper': upper, 'delay': delay,
                     'taken': branch_target(start+12, choose), 'fall': start+20,
                     'symbol': f'af_v3_mannequin_{start:08x}'})
    guard_incoming(data, SECTIONS[0], RAM, [(s-RAM, 16) for s in STARTS])
    return data, reloc, rows


def continuation(address):
    if not RAM <= address < RAM+SECTIONS[0]: raise ValueError('Mannequin continuation outside code')
    return ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8010',
            'lw $ra, 0x12E0($ra)', f'addiu $ra, $ra, {address-RAM}',
            'addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']


def assembly(rows):
    lines = ['/* Preserve native garment/sold counting and complete item identities. */',
             '.set noreorder', '.set noat', '.set gp=64', '.text']
    for row in rows:
        name = row['symbol']
        lines += [f'.globl {name}', f'{name}:', f'.word 0x{row["lower"]:08x}',
                  f'bnez $at, {name}_fall', f'.word 0x{row["upper"]:08x}',
                  f'bnez $at, {name}_taken', 'nop']
        # Mode 3 gives a nonzero full index only for a valid imported garment
        # here: original 24xx, including index zero, took the native fast path.
        lines += query(row['source'], 1, 3)
        lines += ['sltu $at, $zero, $at', f'beqz $at, {name}_fall', 'nop',
                  f'{name}_taken:', f'.word 0x{row["delay"]:08x}']
        lines += continuation(row['taken'])
        lines += [f'{name}_fall:']+continuation(row['fall'])
    return '\n'.join(lines)+'\n'


def install(base, blob, helper, compiled, room, selection):
    data, reloc, rows = inspect(base)
    if (len(blob) != 0xC000 or any(blob[CODE:LIMIT]) or not helper
            or len(helper) > LIMIT-CODE or sha256(helper) != compiled['sha256']
            or len(helper) != compiled['bytes']
            or compiled['symbols']['af_v3_room_query'] != room['symbols']['af_v3_room_query']
            or room['symbols']['af_v3_room_query'] != 0x804680B8
            or not 238 <= selection['shuffle_capacity'] <= (CODE-0x4800)//4):
        raise ValueError('Mannequin helper overlaps or has changed compiled dependencies')
    output = bytearray(data)
    for row in rows:
        target = compiled['symbols'][row['symbol']]
        if target & 3 or not 0x80460000+CODE <= target < 0x80460000+CODE+len(helper):
            raise ValueError('Mannequin detour outside its installed helper')
        at = row['start']-RAM
        struct.pack_into('>4I', output, at, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0, 0, 0)
    blob[CODE:CODE+len(helper)] = helper
    return {VROM: bytes(output)}, {'vrom': f'{VROM:08X}', 'source_sha256': SOURCE_SHA,
        'output_sha256': sha256(output), 'relocation_sha256': sha256(reloc),
        'sites': rows, 'code': compiled, 'native_allocation_and_dma_retained': True,
        'ordinary_shop_display_tested': False}
