"""Canonical garment metadata/ownership without changing its saved format."""
import struct

from aflib import sha256

ABI, CODE, LIMIT, BRIDGES = 42, 0x6C00, 0x6F00, 0x6F00
SOURCES = ('tools/v3_display_items.py', 'overlays/v3/display_items.c', 'overlays/v3/display_items.ld')
TARGETS = {'name': 0x8046D8DC, 'type': 0x8046D9E8, 'place': 0x8046DA6C, 'price': 0x8046DB2C}
COLLECTION_SHA = '255e68e576f3c587070d189cf6d0778b090cc665025558b8acef01e5f1af9b1a'


def scoring_identity(rel, symbols, row):
    from gc_names import symbol_data
    from v3_furniture_art import verify_sources
    from v3_clothing_display import profile_dependency
    verify_sources(rel, symbols)
    conversion = symbol_data(rel, symbols.decode(), 'mRmTp_Item1ItemNo2FtrItemNo_AtPlayerRoom')
    if (row != profile_dependency() or sha256(conversion) !=
            '5228a779089eca94c3f751a814e169f74ff085a57626673c86d7d789fadd6c66'
            or conversion[80:84] != bytes.fromhex('380317ac')):
        raise ValueError('Changed donor clothing-to-mannequin conversion')
    return (0x17AC-0x1000)//4+(0x24BF-0x2400)  # Verified donor model index 682.


def install(blob, helper, compiled, item_report, extended, collection):
    jump = lambda target: 0x08000000 | (target >> 2 & 0x3FFFFFF)
    if (len(blob) != 0xC000 or not helper or len(helper) > LIMIT-CODE
            or len(helper) != compiled['bytes'] or sha256(helper) != compiled['sha256']
            or blob[CODE:CODE+1267] != b'\xFF'*1267
            or compiled['symbols']['af_v3_display_pocket_item'] != 0x80460000+CODE
            or compiled['symbols']['af_v3_furniture_import_profile'] != 0x80465000
            or collection['code']['sha256'] != COLLECTION_SHA
            or sha256(blob[0x99C0:0x99C0+collection['code']['bytes']]) != COLLECTION_SHA):
        raise ValueError('Display readers overlap or change native collection dependencies')
    # The retired bank-index seed contains FF, not zero. Startup and every
    # live reader use the separate expanded table; reclaim only this block.
    blob[CODE:BRIDGES+32] = bytes(BRIDGES+32-CODE)
    item_hooks, collection_hooks = [], []
    for name, target in TARGETS.items():
        original = next(row for row in item_report['hooks'] if row['helper'] == 'af_v3_item_'+name)
        entry = int(original['entry'], 16)
        if (int(original['target'], 16) != target
                or compiled['symbols']['af_v3_base_item_'+name] != target
                or extended['symbols']['af_v3_item_'+name+'_extended'] != target):
            raise ValueError('Changed complete garment metadata dependency')
        at = entry-0x80460000
        before = struct.pack('>2I', jump(target), 0)
        replacement = compiled['symbols']['af_v3_display_item_'+name]
        if (blob[at:at+8] != before or original['after'] != before.hex()
                or not 0x80460000+CODE <= replacement < 0x80460000+CODE+len(helper)):
            raise ValueError('Unbound installed item entry')
        after = struct.pack('>2I', jump(replacement), 0)
        blob[at:at+8] = after
        item_hooks.append({'entry': entry, 'target': replacement, 'base_target': target,
                           'helper': name, 'before': before.hex(), 'after': after.hex()})
    for i, (name, entry) in enumerate((('record', 0x804699C0), ('owned', 0x80469AD4))):
        at, bridge = entry-0x80460000, 0x80460000+BRIDGES+i*16
        before = bytes(blob[at:at+8])
        first, second = struct.unpack('>2I', before)
        replacement = compiled['symbols']['af_v3_display_catalogue_'+name]
        if (collection['code']['symbols']['af_v3_catalogue_'+name] != entry
                or compiled['symbols']['af_v3_prior_catalogue_'+name] != bridge
                or first >> 16 != 0x27BD or second >> 26 != 43
                or not 0x80460000+CODE <= replacement < 0x80460000+CODE+len(helper)):
            raise ValueError('Collection bridge does not preserve its complete native entry')
        stub = before + struct.pack('>2I', jump(entry+8), 0)
        after = struct.pack('>2I', jump(replacement), 0)
        blob[BRIDGES+i*16:BRIDGES+(i+1)*16] = stub
        blob[at:at+8] = after
        collection_hooks.append({'entry': entry, 'target': replacement, 'bridge': bridge,
            'before': before.hex(), 'after': after.hex(), 'bridge_bytes': stub.hex()})
    blob[CODE:CODE+len(helper)] = helper
    return {'code': compiled, 'item_hooks': item_hooks, 'collection_hooks': collection_hooks,
        'item_id': '3AFC', 'pocket_item_id': '34BF', 'name': 'cherry shirt', 'price': 380,
        'display_category': 10, 'native_footprint_equivalent': '17AC',
        'ownership': 'canonical garment clothing bit, not display furniture bit',
        'saved_formats_and_profile_changed': False, 'ordinary_placement_enabled': False}
