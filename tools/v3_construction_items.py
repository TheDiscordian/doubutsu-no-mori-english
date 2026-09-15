"""Reviewed construction item metadata; conversion does not enable an import."""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import sha256
from gc_names import rel_sections, symbol_data
from v3_furniture_art import CONSTRUCTION_PILOTS, scalar_profile, verify_sources
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor

# Exact donor base ID: (price, ordinary goods group, birth category, feng colour).
# These IDs/indices fit the existing type-3 furniture mapping. The runtime
# registry and optional composer do not enable them until installation is complete.
PROPERTIES = {
    0x31F4: (850, 1, 1, 3),
    0x31F8: (830, 1, 1, 3),
    0x31FC: (850, 2, 2, 3),
    0x320C: (850, 1, 1, 3),
    0x3214: (1050, 1, 1, 0),
    0x3218: (870, 1, 1, 0),
    0x322C: (900, 2, 2, 0),
}
HRA = {(item, 1024 + (item - 0x3000) // 4): f'{0x40050000 | birth << 8:08X}'
       for item, (_, _, birth, _) in PROPERTIES.items()}
FENG = {(item, 1024 + (item - 0x3000) // 4): (colour, 'orange' if colour == 3 else 'none')
        for item, (_, _, _, colour) in PROPERTIES.items()}
STOCK = {item: (1024 + (item - 0x3000) // 4, 'ftr_list' + 'ABC'[group], group,
               (0xCA, 0x196, 0x262)[group])
         for item, (_, group, _, _) in PROPERTIES.items()}


def metadata(rel, symbols):
    verify_sources(rel, symbols)
    source = symbols.decode()
    prices = symbol_data(rel, source, 'ftr_price_table')
    names = symbol_data(rel, source, 'ftrName2_table')
    if (len(prices), len(names), symbol_data(rel, source, 'mRmTp_size_s_data')) != (
            1267 * 2, 242 * 16, b'\x01' + bytes(23)):
        raise ValueError('Changed donor construction names, prices, or footprint')
    # Disambiguate the HRA and feng shui symbols with the same private name.
    actual = re.findall(r'^mMkRm_ftr_info = \.data:0x([0-9A-F]+);[^\n]* size:0x([0-9A-F]+) ',
                        source, re.M)
    if sorted((int(at, 16), int(size, 16)) for at, size in actual) != [
            (0x4EBF0, 0x9E4), (0x4FAFC, 0x13C8)]:
        raise ValueError('Changed construction scoring table identities')
    base = rel_sections(rel)[5][0]
    list_names = re.findall(r'^(ftr_list\w*) =', source, re.M)
    if len(list_names) != 23 or len(set(list_names)) != 23:
        raise ValueError('Changed donor furniture goods-list inventory')
    lists = {}
    for name in list_names:
        data = symbol_data(rel, source, name)
        if not data or len(data) % 2:
            raise ValueError('Incomplete donor furniture goods list')
        ids = struct.unpack('>' + str(len(data) // 2) + 'H', data)
        lists[name] = data, ids
    result, rows = bytearray(), []
    for pilot in CONSTRUCTION_PILOTS:
        item = pilot.item
        price, group, birth, colour = PROPERTIES[item]
        index, list_name, _, _ = STOCK[item]
        name_at = (item - 0x3000) // 4 * 16
        name = names[name_at:name_at + 16]
        profile = symbol_data(rel, source, pilot.profile)
        donor_hra = rel[base + 0x4FAFC + index * 4:base + 0x4FAFC + index * 4 + 4]
        donor_feng = rel[base + 0x4EBF0 + index * 2:base + 0x4EBF0 + index * 2 + 2]
        membership = [(key, ids.count(item)) for key, (_, ids) in lists.items() if item in ids]
        if (name != pilot.name.encode('ascii').ljust(16, b' ')
                or struct.unpack_from('>H', prices, index * 2)[0] != price
                or profile != bytes(32) + scalar_profile(pilot) + bytes(4)
                or donor_hra != bytes.fromhex(HRA[item, index])
                or donor_feng != bytes((colour, 0))
                or membership != [(list_name, 1)]):
            raise ValueError('Changed construction item identity or gameplay properties')
        data, ids = lists[list_name]
        if ids[-1] != 0 or 0 in ids[:-1]:
            raise ValueError('Changed donor ordinary-stock terminator')
        record = struct.pack('>HHHBB', index, item, price, 0, 1) + name + bytes(8)
        result.extend(record)
        rows.append({'id': f'{DONOR}/item/{item:04X}', 'item_id': f'{item:04X}',
            'runtime_index': index, 'name': pilot.name, 'price': price, 'footprint': '1x1',
            'donor_name_sha256': sha256(name), 'donor_profile_sha256': sha256(profile),
            'donor_price_sha256': sha256(prices[index * 2:index * 2 + 2]),
            'record_sha256': sha256(record), 'stock_group': group,
            'donor_list': list_name, 'donor_list_sha256': sha256(data),
            'donor_hra_hex': donor_hra.hex(), 'native_hra_hex': f'{0x40050000 | birth << 9:08x}',
            'feng_hex': donor_feng.hex(), 'runtime_installed': False, 'selectable': False})
    return bytes(result), rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        parser.error('Choose a fresh ignored build/ directory')
    records, rows = metadata(read_donor(args.disc)['rel'], args.symbols.read_bytes())
    report = {'format': 'AFV3-CONSTRUCTION-ITEMS-1', 'source_rel_sha256': REL_SHA,
              'source_symbols_sha256': SYMBOLS_SHA, 'records_sha256': sha256(records),
              'record_bytes': 32, 'imports': rows, 'runtime_installed': False}
    output.mkdir(parents=True)
    (output / 'items.bin').write_bytes(records)
    (output / 'items.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'items': len(rows),
                      'records_sha256': report['records_sha256'], 'runtime_installed': False}))


if __name__ == '__main__':
    main()
