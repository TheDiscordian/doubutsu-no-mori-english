"""Adapt the complete reviewed My_Room range/index sites without resizing it."""
import struct

from aflib import sha256, u32
from v3_furniture_runtime import RAM, RELOC, SECTIONS, SIZE, VROM

ABI, BLOB_SIZE, CODE, MODEL_SHIFT = 7, 0xC000, 0x8000, 0x4000
SOURCE_SHA = '06a23fdecd70488a102e4c9a6f0734687174748c223e7cdd84b469a68c60f5e1'
RELOCATION_SHA = 'a130c711f128e0ba32d5fdba9e06b7480d848d4badc01fe411731dac6983c762'
SOURCES = ('tools/v3_furniture_room.py', 'overlays/v3/room.c',
           'overlays/v3/room.ld', 'overlays/v3/room_entry.S')
RANGES = (0x80937044, 0x8093707C, 0x80938A3C, 0x8093A5F0, 0x8093ADD8,
          0x8093AE8C, 0x8093B168, 0x8093BEF8, 0x8093E868, 0x8093E894,
          0x8093EF1C, 0x809403F8, 0x809411E4, 0x80941200, 0x8094197C,
          0x80941A98, 0x80942AF8, 0x80942CDC, 0x80942F78, 0x809439E0, 0x8094625C)
TRANSFORMS = (
    (0x809386B0, 2, 2, 1, (0x2442F000, 0x30450003)),
    (0x80938AA0, 8, 4, 1, (0x2504F000, 0x00042083)),
    (0x8093AB2C, 3, 3, 2, (0x3063F000, 0x00031B03)),
    (0x8093AB68, 3, 3, 2, (0x3063F000, 0x00031B03)),
    (0x8093ABA4, 3, 3, 2, (0x3063F000, 0x00031B03)),
    (0x8093ABE4, 3, 3, 2, (0x3063F000, 0x00031B03)),
)


def signed(value):
    return (value & 65535) - (65536 if value & 32768 else 0)


def branch_target(address, word):
    return address + 4 + signed(word) * 4


def inspect(data, relocation):
    if sha256(data) != SOURCE_SHA or sha256(relocation) != RELOCATION_SHA:
        raise ValueError('Room detours require the exact installed furniture owner')
    count = u32(relocation, 16)
    fixes, pointers = set(), set()
    for (word,) in struct.iter_unpack('>I', relocation[20:20 + count * 4]):
        section = word >> 30
        at = sum(SECTIONS[:section - 1]) + (word & 0xFFFFFF)
        fixes.add(at)
        if word >> 24 & 63 == 2:
            pointers.add(u32(data, at))
    found = tuple(RAM + at for at in range(0, SECTIONS[0], 4)
                  if u32(data, at) >> 26 == 10 and u32(data, at) & 65535 == 0x1ECD)
    if found != RANGES:
        raise ValueError('Changed room furniture-range inventory')
    rows = []
    for address in RANGES:
        at = address - RAM
        upper, branch, delay = struct.unpack_from('>3I', data, at)
        source = upper >> 21 & 31
        if upper >> 16 & 31 != 1 or source not in (2, 3, 4, 8):
            raise ValueError('Unexpected room range register')
        if branch >> 26 not in (4, 5, 20, 21) or branch >> 16 & 1023 != 32:
            raise ValueError('Unexpected room upper-bound branch')
        lower, lower_branch = struct.unpack_from('>2I', data, at - 8)
        paired = lower == (10 << 26 | source << 21 | 1 << 16 | 0x1000)
        if paired and lower_branch >> 16 != 0x1420:
            raise ValueError('Changed lower furniture branch')
        start = address - 8 if paired else address
        if not paired and (u32(data, at - 4) >> 26 in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23)):
            raise ValueError('Room detour would begin in a branch delay slot')
        if any(offset in fixes for offset in range(start - RAM, at + 12, 4)):
            raise ValueError('Room detour displaces a relocation')
        rows.append({'kind': 'range', 'start': start, 'end': address + 8,
                     'upper': address, 'source': source, 'upper_word': upper,
                     'branch': branch, 'delay': delay, 'paired': paired,
                     'lower_word': lower if paired else None,
                     'lower_target': branch_target(address - 4, lower_branch) if paired else None,
                     'taken': branch_target(address + 4, branch), 'fall': address + 8,
                     'symbol': f'af_v3_room_range_{address:08x}'})
    for address, source, destination, mode, expected in TRANSFORMS:
        at = address - RAM
        if struct.unpack_from('>2I', data, at) != expected or at in fixes or at + 4 in fixes:
            raise ValueError('Changed furniture index/type calculation')
        rows.append({'kind': 'transform', 'start': address, 'end': address + 8,
                     'source': source, 'destination': destination, 'mode': mode,
                     'after': expected[1] if mode == 1 else 0,
                     'symbol': f'af_v3_room_transform_{address:08x}'})
    occupied = set()
    for row in rows:
        area = set(range(row['start'], row['end'], 4))
        if occupied & area:
            raise ValueError('Overlapping room detours')
        occupied |= area
    interiors = occupied - {row['start'] for row in rows}
    if pointers & interiors:
        raise ValueError('Relocated code pointer enters a room detour interior')
    if any(row.get(key) in interiors for row in rows for key in ('taken', 'lower_target')):
        raise ValueError('Emulated room branch targets a replaced interior')
    # Original external branches may enter the retained delay instruction, but
    # never the replaced middle of a detour. Its own lower branch is emulated.
    for at in range(0, SECTIONS[0], 4):
        word = u32(data, at)
        if RAM + at in occupied:
            continue
        op = word >> 26
        target = None
        if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
            target = branch_target(RAM + at, word)
        elif op in (2, 3):
            target = 0x80000000 | (word & 0x3FFFFFF) << 2
        if target in interiors:
            raise ValueError(f'Incoming branch enters room detour: {RAM + at:08X}')
    return rows


def return_to(address):
    offset = address - RAM
    if not 0 <= offset < SECTIONS[0]:
        raise ValueError('Room return escapes its native code')
    lines = ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)',
             'lui $ra, 0x8010', 'lw $ra, 0x0e00($ra)']
    while offset:
        amount = min(offset, 0x7000)
        lines.append(f'addiu $ra, $ra, {amount}')
        offset -= amount
    return lines + ['addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']


def query(source, destination, mode):
    return ['addiu $sp, $sp, -32', 'sd $ra, 24($sp)', f'sw ${source}, 0($sp)',
            f'addiu $ra, $zero, {mode}', 'sw $ra, 4($sp)', 'jal af_v3_room_query', 'nop',
            f'lw ${destination}, 8($sp)', 'ld $ra, 24($sp)', 'addiu $sp, $sp, 32']


def assembly(rows):
    result = ['/* Generated checked detours; no donor assets. */', '.set noreorder',
              '.set noat', '.set gp=64', '.text']
    for row in rows:
        name = row['symbol']
        result += [f'.globl {name}', f'{name}:']
        if row['kind'] == 'transform':
            result += query(row['source'], row['destination'], row['mode'])
            if row['after']:
                result.append(f'.word 0x{row["after"]:08x}')
            result += return_to(row['end'])
            continue
        if row['paired']:
            result += [f'.word 0x{row["lower_word"]:08x}', f'bnez $at, {name}_lower',
                       f'.word 0x{row["upper_word"]:08x}']
        else:
            result += [f'.word 0x{row["upper_word"]:08x}']
        # Original furniture takes this fast path without a C query.
        result += [f'bnez $at, {name}_branch', 'nop']
        result += query(row['source'], 1, 0)
        condition = 'beqz' if row['branch'] >> 26 in (4, 20) else 'bnez'
        result += [f'{name}_branch:', f'{condition} $at, {name}_taken', 'nop']
        result += return_to(row['fall'] + (4 if row['branch'] >> 26 in (20, 21) else 0))
        result += [f'{name}_taken:', f'.word 0x{row["delay"]:08x}']
        result += return_to(row['taken'])
        if row['paired']:
            result += [f'{name}_lower:'] + return_to(row['lower_target'])
    return '\n'.join(result) + '\n'


def install(changes, blob, rows, code, symbols):
    original = changes[VROM]
    if len(blob) != 0x8000 or len(code) > BLOB_SIZE - CODE - 16:
        raise ValueError('Room adapter exceeds its resident allocation')
    if rows != inspect(original, changes[RELOC]):
        raise ValueError('Room detour inventory changed during compilation')
    result = bytearray(original)
    for row in rows:
        target = symbols[row['symbol']]
        if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(code):
            raise ValueError('Room detour symbol outside compiled code')
        at = row['start'] - RAM
        result[at:row['end'] - RAM] = bytes(row['end'] - row['start'])
        struct.pack_into('>I', result, at, 0x08000000 | (target >> 2 & 0x3FFFFFF))
    if len(result) != SIZE:
        raise ValueError('Room adapter changed native owner size')
    blob.extend(bytes(BLOB_SIZE - len(blob)))
    blob[CODE:CODE + len(code)] = code
    blob[-16:] = bytes.fromhex('AF33C0DE') * 4
    changes[VROM] = bytes(result)
    return {'source_sha256': SOURCE_SHA, 'output_sha256': sha256(result),
            'relocation_sha256': sha256(changes[RELOC]), 'sites': rows,
            'range_sites': len(RANGES), 'index_sites': 2, 'field_type_sites': 4,
            'ordinary_placement_tested': False, 'save_profile_support_ready': False}
