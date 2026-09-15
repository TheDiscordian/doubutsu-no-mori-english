"""Add reviewed furniture to native goods lists, retaining native rarity logic."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from gc_names import symbol_data
from v3_furniture_art import verify_sources
from v3_construction_items import STOCK as CONSTRUCTION_STOCK

ABI, CODE, LIMIT, BRIDGE = 16, 0x9C00, 0x9D00, 0xBAA0
CLOTHING_ABI = 36
VROM, TABLE, DESCRIPTOR = 0x011E6000, 0x38C, 0x8010DAA0
SOURCE_SHA = 'ec1b8d3ed3ae8228ba9a16a5851f804659e53148517186aa5416a82de5b4d6a2'
ENTRY, END = 0x800C05E0, 0x800C0684
ENTRY_SHA = 'd1870d741a325ea9a0f6247f84daca6fb9aa96b9c0960f09df1733e1ccb97703'
SOURCES = ('tools/v3_shops.py', 'tools/v3_construction_items.py',
           'overlays/v3/shops.c', 'overlays/v3/shops.ld')


def goods(base, rel, symbols, imports, *, garden=False, western=False, western_large=False,
          school_desks=False):
    verify_sources(rel, symbols)
    files = by_vrom(base)
    old = files[VROM].extract(base)
    if len(old) != 960 or sha256(old) != SOURCE_SHA:
        raise ValueError('Changed complete native furniture goods lists')
    pointers = struct.unpack_from('>12I', old, TABLE)
    if pointers != (0x06000000, 0x060000CC, 0x06000198, 0x06000264,
                    0x060002E8, 0x060002F8, 0x06000338, 0x06000350,
                    0x06000354, 0x0600036C, 0x06000384, 0):
        raise ValueError('Changed complete native list descriptor set')
    selected, insertions = [], []
    garden_rules = {}
    if garden:
        from v3_garden_items import metadata
        from v3_hra import sources, RAM, TABLE as HRA_TABLE
        native_hra, _ = sources(base)
        lottery = struct.unpack('>30H', old[0x2F8:0x334])
        if old[0x334:0x338] != bytes(4) or any(not 0x1000 <= item < 0x1ECC or
               (struct.unpack_from('>I', native_hra, HRA_TABLE - RAM + (item - 0x1000))[0] >> 9 & 31) != 7
               for item in lottery):
            raise ValueError('Native list 5 is not the complete lottery birth-category list')
        for row in metadata(rel, symbols)[1]:
            if row['ordinary_stock']:
                group = row['stock_group']
                garden_rules[int(row['item_id'], 16)] = (row['runtime_index'], row['donor_list'], group,
                                                        (0xCA, 0x196, 0x262)[group])
            elif row['donor_list'] == 'ftr_listLottery':
                garden_rules[int(row['item_id'], 16)] = (row['runtime_index'], row['donor_list'], 5, 0x334)
    if western:
        from v3_western_items import metadata
        from v3_hra import sources, RAM, TABLE as HRA_TABLE
        native_hra, _ = sources(base)
        event = struct.unpack('>64H', old[0x264:0x2E4])
        if old[0x2E4:0x2E8] != bytes(4) or any(not 0x1000 <= item < 0x1ECC or
               (struct.unpack_from('>I', native_hra, HRA_TABLE - RAM + (item - 0x1000))[0] >> 9 & 31) != 3
               for item in event):
            raise ValueError('Native list 3 is not the complete event birth-category list')
        for row in metadata(rel, symbols)[1]:
            group = row['stock_group'] if row['ordinary_stock'] else 3
            garden_rules[int(row['item_id'], 16)] = (row['runtime_index'], row['donor_list'], group,
                                                    (0xCA, 0x196, 0x262, 0x2E4)[group])
    if western_large:
        from v3_western_items import metadata
        if not garden or not western:
            raise ValueError('Large Western stock requires verified ordinary, event, and lottery lists')
        for row in metadata(rel, symbols, large=True)[1]:
            group = row['stock_group'] if row['ordinary_stock'] else 5
            if group == 5 and row['donor_list'] != 'ftr_listLottery':
                raise ValueError('Unreviewed large Western reward route')
            garden_rules[int(row['item_id'], 16)] = (row['runtime_index'], row['donor_list'], group,
                                                    {1: 0x196, 2: 0x262, 5: 0x334}[group])
    if school_desks:
        from v3_school_desks import metadata
        from v3_asset_loader import ROOT
        for row in metadata(rel, symbols, ROOT / 'build/item-identity-megasheet.xlsx')[1]:
            group = row['stock_group']
            garden_rules[int(row['item_id'], 16)] = (row['runtime_index'], row['donor_list'], group,
                                                    (0xCA, 0x196, 0x262)[group])
    for row in imports:
        item = int(row['item_id'], 16)
        rules = {0x3224: (1161, 'ftr_listC', 2, 0x262),
                 0x32B8: (1198, 'ftr_listA', 0, 0xCA),
                 0x3350: (1236, 'ftr_listA', 0, 0xCA), **CONSTRUCTION_STOCK, **garden_rules}
        if item not in rules or row['runtime_index'] != rules[item][0]:
            raise ValueError('Unreviewed ordinary-stock item')
        _, name, group, at = rules[item]
        donor = symbol_data(rel, symbols.decode(), name)
        ids = struct.unpack('>' + str(len(donor) // 2) + 'H', donor)
        if ids[-1] != 0 or 0 in ids[:-1] or ids.count(item) != 1 or old[at:at + 2] != bytes(2):
            raise ValueError('Changed donor goods membership or native list terminator')
        insertions.append((at, item))
        selected.append({'item_id': f'{item:04X}', 'group': group,
                         'donor_list': name, 'donor_list_sha256': sha256(donor)})
    if len({item for _, item in insertions}) != len(insertions):
        raise ValueError('Duplicate selected shop identity')
    shift = lambda at: at + sum(2 for start, _ in insertions if start <= at)
    output, cursor = bytearray(), 0
    for at, item in sorted(insertions):
        output += old[cursor:at] + struct.pack('>H', item)
        cursor = at
    output += old[cursor:]
    new_table = shift(TABLE)
    # A single addition moves the pointer table by two bytes. Align it separately
    # while retaining all earlier lists, terminators, and native event contents.
    table_padding = -new_table % 4
    output[new_table:new_table] = bytes(table_padding)
    new_table += table_padding
    for i, pointer in enumerate(pointers):
        struct.pack_into('>I', output, new_table + i * 4,
                         0x06000000 | shift(pointer & 0xFFFFFF) if pointer else 0)
    output += bytes(-len(output) % 16)
    return bytes(output), new_table, sorted(selected, key=lambda r: r['item_id'])


def install(base, code, blob, helper, compiled, collection, furniture, rel, symbols, imports, *, clothing_items=None):
    if (len(blob) != 0xC000 or not helper or len(helper) > LIMIT - CODE
            or any(blob[CODE:LIMIT]) or any(blob[BRIDGE:BRIDGE + 16])
            or 0x99C0 + collection['bytes'] > CODE
            or compiled['symbols']['af_v3_shop_category'] != 0x80460000 + CODE
            or compiled['symbols']['af_v3_original_shop_category'] != 0x80460000 + BRIDGE
            or compiled['symbols']['af_v3_furniture_import_profile'] != 0x80465000
            or furniture['symbols']['af_v3_furniture_import_profile'] != 0x80465000):
        raise ValueError('Shop helper overlaps live code or has changed dependencies')
    if clothing_items is not None and (compiled['symbols'].get('af_v3_item_type') != 0x8046744C
            or clothing_items['symbols']['af_v3_item_type'] != 0x8046744C):
        raise ValueError('Clothing shop category has a changed shared item dependency')
    at = ENTRY - CODE_RAM
    if sha256(code[at:END - CODE_RAM]) != ENTRY_SHA or struct.unpack_from('>II', code, at) != (0xAFA40000, 0x3084FFFF):
        raise ValueError('Changed complete native shop category function')
    descriptor_at = DESCRIPTOR - CODE_RAM
    descriptor = (VROM, VROM + 960, 0x06000000 | TABLE)
    if struct.unpack_from('>3I', code, descriptor_at) != descriptor:
        raise ValueError('Changed native furniture stock resource descriptor')
    data, table, records = goods(base, rel, symbols, imports)
    jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
    struct.pack_into('>4I', blob, BRIDGE, 0xAFA40000, 0x3084FFFF, jump(ENTRY + 8), 0)
    struct.pack_into('>II', code, at, jump(0x80460000 + CODE), 0)
    struct.pack_into('>3I', code, descriptor_at, VROM, VROM + len(data), 0x06000000 | table)
    blob[CODE:CODE + len(helper)] = helper
    native = by_vrom(base)[CODE_VROM].extract(base)
    owners = ((0x800BF5F4, 0x800BF770), (0x800BF8E8, 0x800BF9B0),
              (0x800BFCF0, 0x800BFF8C), (0x800C0490, ENTRY),
              (0x800C0684, 0x800C088C), (0x800C1BF0, 0x800C1C38))
    retained = []
    for start, end in owners:
        current = code[start - CODE_RAM:end - CODE_RAM]
        if current != native[start - CODE_RAM:end - CODE_RAM]:
            raise ValueError('Shop list import changes native selection or rarity code')
        retained.append({'start': start, 'end': end, 'sha256': sha256(current)})
    return {VROM: data}, {'imports': records, 'source_sha256': SOURCE_SHA,
        'output_sha256': sha256(data), 'bytes': len(data), 'table_offset': table,
        'descriptor': DESCRIPTOR, 'category_entry': ENTRY, 'category_source_sha256': ENTRY_SHA,
        'retained_owners': retained, 'native_rarity_and_rng_preserved': True,
        'clothing_category_enabled': clothing_items is not None,
        'save_format_changed': False, 'ordinary_shop_gameplay_tested': False}
