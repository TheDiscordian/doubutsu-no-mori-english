"""Preserve imported shirt indices during the player change-clothes animation."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from player_item_names import SPEC
from v3_furniture_room import query
from v3_npc_clothing import guard_incoming
from v3_villager_readers import relocation_offsets

ABI = 35
SOURCES = ('tools/v3_clothing_wear.py',)
START, END, FUNCTION, FUNCTION_END = 0x808DC378, 0x808DC39C, 0x808DC344, 0x808DC3E4
OWNER_POINTER = 0x8010DD1C
SYMBOL = 'af_v3_player_wear_index'
WINDOW = bytes.fromhex('28a124001420000700a010252841250010200004000000002447dc001000000130e7ffff')
SOURCE_SHA = '744033c6a585ab8edf1e7c0372360a5101baec0ea7f36d0a97cb3bd115dd914d'
FUNCTION_SHA = '29277b539251b2c99067f4833b350853358d74289439f151562f624819f578ca'


def assembly():
    lines = ['/* Player clothing animation index; preserve all other native outputs. */',
             '.set noreorder', '.set noat', '.set gp=64', '.text', f'.globl {SYMBOL}', f'{SYMBOL}:']
    lines += query(5, 7, 3)
    lines += ['slti $at, $a1, 0x2500', 'move $v0, $a1',
              'addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8011', 'lw $ra, -0x22E4($ra)']
    offset = END-SPEC.ram
    while offset:
        amount = min(offset, 0x7000)
        lines.append(f'addiu $ra, $ra, {amount}')
        offset -= amount
    lines += ['addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']
    return '\n'.join(lines)+'\n'


def install(base, compiled):
    files = by_vrom(base)
    data, reloc = files[SPEC.vrom].extract(base), files[SPEC.relocation].extract(base)
    code = files[CODE_VROM].extract(base)
    descriptor = code[OWNER_POINTER-16-CODE_RAM:OWNER_POINTER+8-CODE_RAM]
    at = START-SPEC.ram
    if (sha256(data) != SOURCE_SHA or len(data) != SPEC.file_bytes
            or sha256(data[FUNCTION-SPEC.ram:FUNCTION_END-SPEC.ram]) != FUNCTION_SHA
            or sha256(reloc) != SPEC.relocation_sha256
            or struct.unpack_from('>5I', reloc) != SPEC.sections
            or descriptor.hex() != '007ac420007d9ba0808b2d50808e04d0000000008011792c'
            or data[at:at+len(WINDOW)] != WINDOW
            or relocation_offsets(reloc) & set(range(at, at+len(WINDOW), 4))):
        raise ValueError('Changed complete player owner, animation, descriptor, or index window')
    guard_incoming(data, SPEC.sections[0], SPEC.ram, [(at, len(WINDOW))])
    target = compiled['symbols'][SYMBOL]
    if target & 3 or not 0x80463C30 <= target < 0x80463C30+compiled['bytes'] <= 0x80464000:
        raise ValueError('Player clothing index helper escapes its reservation')
    result = bytearray(data)
    result[at:at+len(WINDOW)] = struct.pack('>9I', 0x08000000 | (target >> 2 & 0x3FFFFFF), *([0]*8))
    return {SPEC.vrom: bytes(result)}, {'vrom': f'{SPEC.vrom:08X}', 'source_sha256': SOURCE_SHA,
        'output_sha256': sha256(result), 'relocation_sha256': sha256(reloc),
        'function_sha256': FUNCTION_SHA, 'start': f'{START:08X}', 'end': f'{END:08X}',
        'before': WINDOW.hex(), 'after': result[at:at+len(WINDOW)].hex(), 'helper': SYMBOL,
        'owner_pointer': f'{OWNER_POINTER:08X}', 'imported_index': '10BF',
        'native_and_unknown_fallbacks_retained': True, 'ordinary_wearing_tested': False}
