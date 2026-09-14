"""Selected full names, leaf types, prices, and placement footprints for V3."""
import struct

from aflib import CODE_RAM, sha256
from gc_names import symbol_data
from v3_furniture_art import PILOTS, verify_sources
from v3_registry import furniture_slot

ABI, DATA, STRIDE, CODE, BRIDGE = 6, 0x72A0, 32, 0x7300, 0x4600
SOURCES = ('tools/v3_furniture_items.py', 'overlays/v3/items.c', 'overlays/v3/items.ld')
ENTRIES = (
    (0x801969C8, 0x16C, 'af_v3_item_name', (0x27BDFF98, 0xAFBF0064),
     '95ad8ab6e63d769bfcd3a3c53902d783ea2387b5e3a50621b7e927aaa9f06df3'),
    (0x800A5630, 0x9C, 'af_v3_item_type', (0xAFA40000, 0x3084FFFF),
     '11f8590e0ec3fdb4fac9970c443934087e90bc0a971bd7ddbb9bf079126e62de'),
    (0x800BE69C, 0x3C, 'af_v3_item_size', (0xAFA40000, 0x3084FFFF),
     '5a4a23b5939fb2108d01a9f57f1bd875ad1d135f5a737cffabafdd7233daeb8f'),
    (0x800BE72C, 0x118, 'af_v3_item_place', (0x27BDFFC0, 0xAFB00018),
     'c6373a9680578d80795a348b21b3a3fd691ad97b547ca60fe02ba881eee83cf0'),
    (0x800C0194, 0x2FC, 'af_v3_item_price', (0x27BDFF98, 0xAFA40068),
     'a66997e7331946885a87b7008e489484e9cd9ea3884aa970c2ac22d29731946f'),
)


def metadata(rel, symbols):
    verify_sources(rel, symbols)
    source = symbols.decode()
    names = symbol_data(rel, source, 'ftrName2_table')
    prices = symbol_data(rel, source, 'ftr_price_table')
    unit = symbol_data(rel, source, 'mRmTp_size_s_data')
    if (len(names), len(prices), unit) != (242 * 16, 1267 * 2, b'\x01' + bytes(23)):
        raise ValueError('Changed donor furniture name/price/footprint tables')
    result, rows = bytearray(), []
    for pilot, expected_price in zip(PILOTS, (830, 840)):
        index, item, _ = furniture_slot(pilot.item)
        name_at = (pilot.item - 0x3000) // 4 * 16
        name = names[name_at:name_at + 16]
        price = struct.unpack_from('>H', prices, index * 2)[0]
        profile = symbol_data(rel, source, pilot.profile)
        if (name != pilot.name.encode('ascii').ljust(16, b' ') or price != expected_price or
                len(profile) != 52 or profile[40] != 4):
            raise ValueError('Furniture identity, price, or 1x1 donor shape changed')
        row = struct.pack('>HHHBB', index, item, price, 0, 1) + name + bytes(8)
        result.extend(row)
        rows.append({'item_id': f'{item:04X}', 'runtime_index': index, 'name': pilot.name,
                     'price': price, 'footprint': '1x1', 'donor_name_sha256': sha256(name),
                     'donor_price_sha256': sha256(prices[index * 2:index * 2 + 2]),
                     'donor_profile_sha256': sha256(profile), 'record_sha256': sha256(row)})
    return bytes(result), rows


def install(code, module, blob, helper_symbols, rel, symbols):
    from v3_asset_loader import BLOB_RAM, MODULE_RAM
    if (len(blob) != 0x8000 or any(blob[DATA:CODE]) or
            any(blob[BRIDGE:BRIDGE + len(ENTRIES) * 16])):
        raise ValueError('Furniture item metadata or bridge storage overlaps existing data')
    records, rows = metadata(rel, symbols)
    # Match the actual native four-cell offsets, not only its public enum.
    if bytes(code[0x8010D274 - CODE_RAM:0x8010D28C - CODE_RAM]) != b'\x01' + bytes(23):
        raise ValueError('Native single-unit furniture placement changed')
    blob[DATA:DATA + len(records)] = records
    patches = []
    for i, (address, size, helper, expected, digest) in enumerate(ENTRIES):
        owner, base = (module, MODULE_RAM) if address >= MODULE_RAM else (code, CODE_RAM)
        at, target = address - base, helper_symbols[helper]
        if (sha256(owner[at:at + size]) != digest or
                struct.unpack_from('>II', owner, at) != expected or
                not BLOB_RAM + CODE <= target < BLOB_RAM + 0x7FF0 or target & 3):
            raise ValueError(f'Changed native furniture item entry {address:08X}')
        bridge = BRIDGE + i * 16
        # All displaced pairs are stack/prologue instructions, not branches.
        jump = lambda value: 0x08000000 | (value >> 2 & 0x3FFFFFF)
        struct.pack_into('>4I', blob, bridge, *expected, jump(address + 8), 0)
        struct.pack_into('>II', owner, at, jump(target), 0)
        patches.append({'entry': f'{address:08X}', 'native_bytes': size,
                        'native_sha256': digest, 'helper': helper,
                        'bridge_ram': f'{BLOB_RAM + bridge:08X}'})
    return {'imports': rows, 'patches': patches, 'full_name_bytes': 16,
            'metadata_ram': f'{BLOB_RAM + DATA:08X}', 'native_paths_retained': True,
            'ordinary_placement_ready': False, 'save_profile_support_ready': False}
