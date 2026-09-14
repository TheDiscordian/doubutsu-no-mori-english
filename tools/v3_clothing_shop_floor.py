"""Keep imported garment placement, selection, and sales on native clothing paths."""
import struct

from aflib import by_vrom, sha256, u32
from v3_furniture_room import branch_target, query
from v3_shop_floor import CODE, LIMIT, RAM, VROM, RELOC, SECTIONS, inspect as original_inspect
from v3_villager_readers import relocation_offsets

ABI = 39
SOURCES = ('tools/v3_clothing_shop_floor.py',)
SITES = ((0x80953F14, 0x50200004, 0x24011F35, 'clothing reserve point'),
         (0x809548C8, 0x14200013, 0x28612200, 'clothing floor selection'),
         (0x80954A74, 0x10200013, 0x97A40046, 'clothing sale and mannequin removal'))


def inspect(base, code):
    original_inspect(base, code)  # Complete original owner/relocation/descriptor validation.
    files = by_vrom(base)
    data, reloc = (files[v].extract(base) for v in (VROM, RELOC))
    if tuple(RAM+i+4 for i in range(0, SECTIONS[0], 4)
             if u32(data, i) == 0x28612500) != tuple(row[0] for row in SITES):
        raise ValueError('Changed complete clothing shop-floor range inventory')
    rows, fixes = [], relocation_offsets(reloc)
    for at, branch, delay, purpose in SITES:
        if (struct.unpack_from('>3I', data, at-RAM-4) != (0x28612500, branch, delay)
                or at-RAM in fixes or at-RAM+4 in fixes):
            raise ValueError('Changed clothing shop branch, delay, or relocation')
        rows.append({'start': at, 'branch': branch, 'delay': delay,
                     'taken': branch_target(at, branch), 'fall': at+8, 'purpose': purpose,
                     'symbol': f'af_v3_cloth_floor_{at:08x}'})
    return rows


def assembly(rows):
    def resume(address):
        if not RAM <= address < RAM+SECTIONS[0]: raise ValueError('Clothing floor continuation escapes code')
        return ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8010',
                'lw $ra, 0x1140($ra)', f'addiu $ra, $ra, {address-RAM}',
                'addiu $sp, $sp, 16', 'jr $ra', 'ld $ra, -8($sp)']
    lines = ['/* Single-word clothing branches; preserve incoming delay-slot paths. */',
             '.set noreorder', '.set noat', '.set gp=64', '.text']
    for row in rows:
        name, branch = row['symbol'], row['branch'] >> 26
        lines += [f'.globl {name}', f'{name}:', 'slti $at, $v1, 0x2500',
                  f'bnez $at, {name}_decide', 'nop']
        lines += query(3, 1, 3)+['sltu $at, $zero, $at', f'{name}_decide:']
        condition = 'bnez' if branch == 5 else 'beqz'
        # The retained jump delay already performs the sale's stack read once.
        # Preserve its loaded A0 through the query; do not read it a second time.
        delay = row['delay'] if branch == 5 else 0
        lines += [f'{condition} $at, {name}_taken', f'.word 0x{delay:08x}']
        lines += resume(row['fall'])+[f'{name}_taken:']
        if branch == 20: lines += [f'.word 0x{row["delay"]:08x}']
        lines += resume(row['taken'])
    return '\n'.join(lines)+'\n'


def install(data, blob, rows, compiled, floor):
    if (sha256(data) != floor['output_sha256'] or not rows
            or sha256(blob[CODE:CODE+compiled['bytes']]) != compiled['sha256']
            or CODE+compiled['bytes'] > LIMIT
            or compiled['symbols']['af_v3_room_query'] != 0x804680B8):
        raise ValueError('Changed current furniture floor owner or compiled clothing helper')
    output = bytearray(data)
    for row in rows:
        at, target = row['start']-RAM, compiled['symbols'][row['symbol']]
        if (u32(data, at) != row['branch'] or u32(data, at+4) != row['delay']
                or target & 3 or not 0x80460000+CODE <= target < 0x80460000+CODE+compiled['bytes']):
            raise ValueError('Invalid clothing floor branch or installed target')
        struct.pack_into('>I', output, at, 0x08000000 | (target >> 2 & 0x3FFFFFF))
    return bytes(output), {'source_sha256': sha256(data), 'output_sha256': sha256(output),
        'sites': rows, 'single_word_patches': True, 'save_format_changed': False,
        'ordinary_purchase_tested': False}
