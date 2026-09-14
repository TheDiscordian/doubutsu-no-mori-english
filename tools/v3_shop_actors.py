"""Retain native shop interactions for selected additive furniture identities."""
import struct

from aflib import CODE_RAM, by_vrom, sha256, u32
from shop_units import SHOPS
from v3_furniture_room import branch_target, query

ABI, CODE, LIMIT = 17, 0x7600, 0x7FF0
SOURCES = ('tools/v3_shop_actors.py', 'overlays/v3/shop_actors.ld')
OWNERS = {
    'cranny': ('b1b4c773efb9bbabc17f49352221e1591c524556984fd6424d16fe76a13a0435', 0x80101290,
               (0x809CACBC, 0x809CB6AC, 0x809CBA28, 0x809CBD24)),
    'conv': ('2fd40dcb455c596b9d0d96d7ec6c7d0c6fac314d1decb97abe33248d6b0d427a', 0x801014B0,
             (0x809A6210, 0x809A6C00, 0x809A6F7C, 0x809A7278)),
    'depart': ('63cb120c080538bbf30df68f8e79d1a6cb0cf9a30471597924ee992712547554', 0x801014F0,
               (0x809AAB30, 0x809AB520, 0x809AB89C, 0x809ABB98)),
    'mame': ('ceea395317763b3bbe02612523b60dc1df4a8316d247b6ce714ff73217cdd1d6', 0x80100F90,
             (0x809B7060, 0x809B7AB0, 0x809B7E1C, 0x809B8018)),
    'super': ('e06bb35d7d80a6493fba5384f58c71c0d284e92f19519abd9155ebe54e87ea96', 0x801014D0,
              (0x809CFBEC, 0x809D05DC, 0x809D0958, 0x809D0C54)),
}
PURPOSES = ('purchase camera tracking', 'purchase lottery-ticket eligibility',
            'purchase conversation camera', 'floor-item purchase conversation')


def inspect(base, code):
    files, rows = by_vrom(base), []
    for owner, (digest, descriptor, sites) in OWNERS.items():
        spec = SHOPS[owner]
        data, reloc = (files[v].extract(base) for v in (spec.vrom, spec.relocation))
        if (sha256(data), sha256(reloc)) != (digest, spec.relocation_sha256):
            raise ValueError('Changed complete translated shop actor or relocation')
        if struct.unpack_from('>5I', reloc) != spec.sections:
            raise ValueError('Changed native shop sections')
        if struct.unpack_from('>5I', code, descriptor - CODE_RAM) != (
                spec.vrom, spec.vrom + len(data), spec.ram, spec.ram + spec.resident_bytes, 0):
            raise ValueError('Changed native shop allocation descriptor')
        records = struct.unpack_from('>' + str(spec.sections[4]) + 'I', reloc, 20)
        starts = (0, 0, spec.sections[0], sum(spec.sections[:2]))
        fixes = {starts[w >> 30] + (w & 0xFFFFFF) for w in records}
        interiors = {address + 4 for address in sites}
        for i, address in enumerate(sites):
            # The ordinary shop floor dispatch separates its mask and shift.
            # Replace the later shift/constant pair, retaining intervening stores
            # and the original full item in a0. The twins use the adjacent form.
            expected = ((0x3044F000, 0x00042303), (0x3085F000, 0x00052B03),
                        (0x304FF000, 0x000FC303),
                        (0x3044F000, 0x00042303) if owner == 'mame' else (0x00021303, 0x24010001))[i]
            at = address - spec.ram
            if struct.unpack_from('>2I', data, at) != expected or fixes & {at, at + 4}:
                raise ValueError('Changed or relocated shop interaction window')
            previous = u32(data, at - 4)
            if previous >> 26 in (1, 2, 3, 4, 5, 6, 7, 20, 21, 22, 23):
                raise ValueError('Shop interaction window starts in a delay slot')
            adjacent = expected[0] >> 26 == 12
            source = expected[0] >> 21 & 31 if adjacent else 4
            destination = expected[1] >> 11 & 31 if adjacent else 2
            if not adjacent and u32(data, at - 16) != 0x3082F000:
                raise ValueError('Separated shop type query lost its full item source')
            rows.append({'owner': owner, 'start': address, 'end': address + 8,
                         'source': source, 'destination': destination,
                         'first': expected[0] if adjacent else 0,
                         'after': 0 if adjacent else expected[1],
                         'temporary': expected[0] >> 16 & 31 if adjacent else None,
                         'pointer': descriptor + 16, 'offset': address + 8 - spec.ram,
                         'purpose': PURPOSES[i], 'symbol': f'af_v3_shop_type_{address:08x}'})
        for at in range(0, spec.sections[0], 4):
            word, target = u32(data, at), None
            op = word >> 26
            if op in (1, 4, 5, 6, 7, 20, 21, 22, 23) or (op == 17 and word >> 21 & 31 == 8):
                target = branch_target(spec.ram + at, word)
            elif op in (2, 3):
                target = 0x80000000 | (word & 0x3FFFFFF) << 2
            if target in interiors:
                raise ValueError('Incoming branch enters a shop interaction interior')
        if any(u32(data, starts[w >> 30] + (w & 0xFFFFFF)) in interiors
               for w in records if w >> 24 & 63 == 2):
            raise ValueError('Relocated pointer enters a shop interaction interior')
    return rows


def assembly(rows):
    lines = ['/* Checked native shop interactions. */', '.set noreorder', '.set noat', '.set gp=64', '.text']
    for row in rows:
        lines += [f'.globl {row["symbol"]}', f'{row["symbol"]}:']
        if row['first']:
            lines += [f'.word 0x{row["first"]:08x}']
        lines += query(row['source'], row['destination'], 2)
        if row['after']:
            lines += [f'.word 0x{row["after"]:08x}']
        if row['pointer'] >> 16 != 0x8010 or not 0 < row['offset'] < 0x8000:
            raise ValueError('Shop continuation exceeds its checked pointer/offset')
        lines += ['addiu $sp, $sp, -16', 'sd $ra, 8($sp)', 'lui $ra, 0x8010',
                  f'lw $ra, {row["pointer"] & 65535}($ra)',
                  f'addiu $ra, $ra, {row["offset"]}', 'addiu $sp, $sp, 16',
                  'jr $ra', 'ld $ra, -8($sp)']
    return '\n'.join(lines) + '\n'


def install(base, code, blob, rows, helper, symbols, item_code, room_code):
    if (len(blob) != 0xC000 or not helper or len(helper) > LIMIT - CODE
            or any(blob[CODE:LIMIT]) or 0x7300 + item_code['bytes'] > CODE
            or symbols['af_v3_room_query'] != 0x804680B8
            or room_code['symbols']['af_v3_room_query'] != 0x804680B8):
        raise ValueError('Shop interaction helper overlaps memory or changes the shared query ABI')
    if rows != inspect(base, code):
        raise ValueError('Shop interaction inventory changed during construction')
    files, changes, owners = by_vrom(base), {}, {}
    for owner, spec in SHOPS.items():
        data = bytearray(files[spec.vrom].extract(base))
        for row in (row for row in rows if row['owner'] == owner):
            target = symbols[row['symbol']]
            if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper):
                raise ValueError('Shop interaction target escapes compiled code')
            struct.pack_into('>II', data, row['start'] - spec.ram,
                             0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
        changes[spec.vrom] = bytes(data)
        owners[owner] = {'vrom': spec.vrom, 'ram': spec.ram,
            'source_sha256': OWNERS[owner][0], 'output_sha256': sha256(data),
            'relocation_sha256': spec.relocation_sha256, 'allocation_bytes': spec.resident_bytes}
    blob[CODE:CODE + len(helper)] = helper
    return changes, {'sites': rows, 'owners': owners, 'extra_allocation_bytes': 0,
                     'save_format_changed': False, 'ordinary_shop_gameplay_tested': False}
