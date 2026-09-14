"""Connect selected furniture to shared room grids and shop eligibility."""
import struct

from aflib import CODE_RAM, sha256, u32
from gc_names import symbol_data
from v3_furniture_art import verify_sources
from v3_furniture_room import BLOB_SIZE, assembly, branch_target

ABI, CODE, BRIDGE = 8, 0xA400, 0xA200
SOURCES = ('tools/v3_furniture_fields.py', 'overlays/v3/fields.c', 'overlays/v3/fields.ld')
ENTRIES = (
    (0x800BE844, 0x20C, '05fd68e8243e86368665c2c40086335339ff12ec0b3cf34650e6df8e1053fec9'),
    (0x800BEA50, 0x19C, 'a87684421a52b7264b2037a308c161c25b906be436b15906042dba9d0c7a77b2'),
    (0x800BEE50, 0x64, '4f0c692a58027da5236f703eaf795229d3cfc59d12ca759e00f19947c3ded367'),
)
WINDOWS = (
    (0x800BE910, (0x28811000, 0x14200032, 0x28811ECD, 0x10200030, 0x02602825)),
    (0x800BEACC, (0x2A011000, 0x14200032, 0x2A011ECD, 0x10200030, 0x3204FFFF)),
)


def inspect(code):
    for address, size, digest in ENTRIES:
        if sha256(code[address - CODE_RAM:address - CODE_RAM + size]) != digest:
            raise ValueError('Changed native furniture field/shop function')
    rows = []
    for start, words in WINDOWS:
        if struct.unpack_from('>5I', code, start - CODE_RAM) != words:
            raise ValueError('Changed room-grid comparison sequence')
        lower, lower_branch, upper, branch, delay = words
        rows.append({'kind': 'range', 'start': start, 'end': start + 16,
                     'upper': start + 8, 'source': upper >> 21 & 31,
                     'upper_word': upper, 'branch': branch, 'delay': delay,
                     'paired': True, 'lower_word': lower,
                     'lower_target': branch_target(start + 4, lower_branch),
                     'taken': branch_target(start + 12, branch), 'fall': start + 16,
                     'symbol': f'af_v3_field_range_{start:08x}'})
    return rows


def hook_assembly(rows):
    def direct_return(address):
        if not 0x800BE844 <= address < 0x800BEBEC:
            raise ValueError('Field detour return outside reviewed functions')
        return [f'j 0x{address:08x}', 'nop']
    return assembly(rows, return_builder=direct_return)


def donor_rules(rel, symbols):
    verify_sources(rel, symbols)
    source = symbols.decode()
    birth = symbol_data(rel, source, 'mRmTp_birth_type')
    sound = symbol_data(rel, source, 'mRmTp_ftr_se_type')
    if (len(birth), len(sound), birth[1161], birth[1198], sound[1161], sound[1198]) != (1266, 1266, 2, 0, 0, 0):
        raise ValueError('Changed pilot birth groups or action-sound requirements')
    return {'birth_table_sha256': sha256(birth), 'action_sound_table_sha256': sha256(sound),
            'imports': [{'item_id': '3224', 'shop_group': 2, 'action_sound': 0},
                        {'item_id': '32B8', 'shop_group': 0, 'action_sound': 0}],
            'native_no_action_sound_fallback_retained': True}


def install(code, blob, rows, helper, symbols, room_symbols, rel, donor_symbols):
    if len(blob) != BLOB_SIZE or any(blob[BRIDGE:-16]) or len(helper) > BLOB_SIZE - CODE - 16:
        raise ValueError('Field helpers overlap existing resident data')
    if room_symbols['af_v3_room_query'] != 0x804680B8 or rows != inspect(code):
        raise ValueError('Field query ABI or source inventory changed')
    rules = donor_rules(rel, donor_symbols)
    blob[CODE:CODE + len(helper)] = helper
    jump = lambda value: 0x08000000 | (value >> 2 & 0x3FFFFFF)
    for row in rows:
        target = symbols[row['symbol']]
        if not 0x80460000 + CODE <= target < 0x80460000 + CODE + len(helper):
            raise ValueError('Field range target outside its helper')
        struct.pack_into('>4I', code, row['start'] - CODE_RAM, jump(target), 0, 0, 0)
    at = 0x800BEE50 - CODE_RAM
    first = struct.unpack_from('>2I', code, at)
    if first != (0xAFA40000, 0x3084FFFF) or symbols['af_v3_field_shop'] != 0x80460000 + CODE:
        raise ValueError('Changed shop prologue or helper entry')
    struct.pack_into('>4I', blob, BRIDGE, *first, jump(0x800BEE58), 0)
    struct.pack_into('>2I', code, at, jump(symbols['af_v3_field_shop']), 0)
    return {'sites': rows, 'donor_rules': rules, 'native_entries':
            [{'entry': f'{a:08X}', 'bytes': n, 'sha256': digest} for a, n, digest in ENTRIES],
            'shop_original_bridge_ram': '8046A200', 'ordinary_placement_tested': False,
            'catalogue_acquisition_and_save_ready': False}
