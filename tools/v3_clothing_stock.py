"""Add the real cherry shirt to native A stock without changing B/C seasons."""
import struct

from aflib import CODE_RAM, by_vrom, sha256
from gc_names import symbol_data
from v3_furniture_art import verify_sources

ABI, VROM, SIZE, TABLE, APPENDED, DESCRIPTOR = 37, 0x011E5000, 560, 0x1F0, 0x230, 0x8010DAB8
CALL, ORIGINAL = 0x800BFE4C, 0x800BFAA8
SOURCE_SHA = '7a939815d2f483dec67ea98d01f9d711ef7143ed9e63cf948478b0702f3f3d85'
DONOR_SHA = '7851eefd2ebb8eeb4ae6b1361a76f0bdf813718b1d68178afa8f48b54c9c51c6'
SOURCES = ('tools/v3_clothing_stock.py', 'overlays/v3/clothing_stock.c', 'overlays/v3/clothing_stock.S')
OWNERS = ((0x800BFCF0, 0x800BFF8C, '74f06da63023a4086fa1ef341a513038d1713bd7cee19db4528cb9f9edb36456'),
          (0x800BEBEC, 0x800BEC80, '855f858da39ba937465494c0ade8eb4707f2863f7157ddbb9fd56d82dfb562b6'),
          (ORIGINAL, 0x800BFC00, '9a27e00c996e9898677d997c91d85b7bd50113ac9907f3ede6fd54a67ba2bcfd'))


def goods(base, rel, symbols, imports):
    verify_sources(rel, symbols)
    old = by_vrom(base)[VROM].extract(base)
    donor = symbol_data(rel, symbols.decode(), 'cloth_listA')
    counts = symbol_data(rel, symbols.decode(), 'cloth_season_cnt')
    if (len(old) != SIZE or sha256(old) != SOURCE_SHA or sha256(donor) != DONOR_SHA
            or donor[54:56] != bytes.fromhex('24BF') or counts != bytes((32, 10, 11, 9, 9))
            or old[0x21C:0x221] != counts
            or struct.unpack_from('>3I', old, TABLE) != (0x6000000, 0x6000090, 0x6000120)
            or len(imports) != 1 or imports[0]['donor_item_id'] != '24BF' or imports[0]['item_id'] != '34BF'):
        raise ValueError('Changed native/donor clothing stock or unsupported selected garment')
    native_a = old[:0x90]
    if native_a[-2:] != bytes(2) or any(not 0x2400 <= i < 0x2500 for (i,) in struct.iter_unpack('>H', native_a[:-2])):
        raise ValueError('Invalid complete original clothing A list')
    expanded = native_a[:64]+bytes.fromhex('34BF')+native_a[64:]
    result = bytearray(old+expanded)
    struct.pack_into('>I', result, TABLE, 0x06000000+APPENDED)
    result += bytes(-len(result)%16)
    if len(result) != 720: raise ValueError('Unexpected clothing stock size')
    return bytes(result), {'source_sha256': SOURCE_SHA, 'output_sha256': sha256(result),
        'donor_list': 'cloth_listA', 'donor_list_sha256': DONOR_SHA, 'donor_any_season_position': 27,
        'native_a_sha256': sha256(native_a), 'expanded_a_sha256': sha256(expanded),
        'item_id': '34BF', 'inserted_index': 32, 'expanded_a_offset': APPENDED,
        'bytes': len(result), 'native_bytes': SIZE, 'pointer_table': TABLE,
        'all_other_lists_and_original_counts_retained': True}


def install(base, code, helper, compiled, rel, symbols, imports):
    if sha256(helper) != compiled['sha256'] or len(helper) != compiled['bytes']:
        raise ValueError('Changed complete asset helper for clothing stock')
    target, entry = (compiled['symbols'][s] for s in ('af_v3_clothing_stock_call', 'af_v3_clothing_stock_index'))
    if (target | entry) & 3 or not 0x80460100 <= entry < target <= 0x80460100+len(helper)-8 <= 0x80460FF8:
        raise ValueError('Clothing stock code escapes the asset reservation')
    bridge = struct.pack('>2I', 0x08000000 | (entry >> 2 & 0x3FFFFFF), 0x02202825)
    if helper[target-0x80460100:target-0x80460100+8] != bridge:
        raise ValueError('Changed native selected-list transport bridge')
    for start, end, digest in OWNERS:
        if sha256(code[start-CODE_RAM:end-CODE_RAM]) != digest:
            raise ValueError('Changed native clothing selection, RNG wrapper, or allocation')
    at = CALL-CODE_RAM
    if code[at:at+8] != bytes.fromhex('0C02FEAA27A40050'):
        raise ValueError('Changed native clothing selection call or delay slot')
    descriptor_at = DESCRIPTOR-CODE_RAM
    if struct.unpack_from('>3I', code, descriptor_at) != (VROM, VROM+SIZE, 0x60001F0):
        raise ValueError('Changed native clothing goods resource descriptor')
    data, report = goods(base, rel, symbols, imports)
    struct.pack_into('>I', code, at, 0x0C000000 | (target >> 2 & 0x3FFFFFF))
    struct.pack_into('>I', code, descriptor_at+4, VROM+len(data))
    report.update({'call': f'{CALL:08X}', 'call_after': bytes(code[at:at+8]).hex(),
        'helper_entry': f'{entry:08X}', 'caller_bridge': f'{target:08X}',
        'descriptor': f'{DESCRIPTOR:08X}', 'selection_and_allocation_sources': OWNERS,
        'allocation': 'native size-derived aligned arena/malloc with original free path',
        'additional_temporary_stock_bytes': len(data)-SIZE,
        'ordinary_stock_and_purchase_tested': False})
    return {VROM: data}, report
