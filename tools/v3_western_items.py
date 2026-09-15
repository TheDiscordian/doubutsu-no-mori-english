"""Verify seven Western furnishings and their real stock/scoring identities.

Converted models and metadata are not installed or playable imports. Preserve
the donor event-reward route for the saddle fence and well.
"""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import sha256
from gc_names import rel_sections, symbol_data
from item_identity_sheet import SHEET_SHA, sheet_rows
from v3_furniture_art import WESTERN_PILOTS, scalar_profile, verify_sources
from v3_import_catalog import DONOR, REL_SHA, ROOT, SYMBOLS_SHA, read_donor
from v3_villager_art import data_pointers, symbol_span

# Price, sole acquisition list, full donor HRA/feng records, catalogue position.
PROPERTIES = {
    0x32B0: (520, 'ftr_listC', 'DC050200', '0000', 259),
    0x32B4: (1020, 'ftr_listA', 'DC050080', '0000', 255),
    0x32BC: (2180, 'ftr_listEvent', 'DC050300', '0000', 257),
    0x32C0: (880, 'ftr_listA', 'DC050000', '0000', 263),
    0x3328: (890, 'ftr_listB', 'DC050100', '0400', 256),
    0x3330: (1230, 'ftr_listB', 'DC050100', '0000', 260),
    0x3334: (2700, 'ftr_listEvent', 'DC050300', '0000', 262),
}


def identity_evidence(path):
    if sha256(path.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed Western identity worksheet')
    cells = list(sheet_rows(path, 'Items'))
    if any(cells[0][1].get(k) != v for k, v in {
            'C': 'ID (AF)', 'E': 'ID (AC)', 'H': 'Name (AF)', 'J': 'Name (English)'}.items()):
        raise ValueError('Changed Western identity columns')
    result = []
    for pilot in WESTERN_PILOTS:
        matches = [(n, c) for n, c in cells[1:] if c.get('E') == f'{pilot.item:04X}']
        if (len(matches) != 1 or matches[0][1].get('J') != pilot.name
                or any(matches[0][1].get(k) != '-' for k in ('C', 'H', 'CG', 'CJ'))):
            raise ValueError('Western identity has changed or is ambiguous')
        result.append({'item_id': f'{pilot.item:04X}', 'sheet_row': matches[0][0],
                       'native_id_name_and_artwork_absent': True})
    return result


def metadata(rel, symbols):
    verify_sources(rel, symbols)
    text = symbols.decode()
    base = rel_sections(rel)[5][0]
    prices = symbol_data(rel, text, 'ftr_price_table')
    names = symbol_data(rel, text, 'ftrName2_table')
    catalogue = symbol_data(rel, text, 'mCL_furniture_list')
    series = symbol_data(rel, text, 'mMkRm_series_info')
    series_names = symbol_data(rel, text, 'mMkRm_series_name')
    h = rel[base + 0x4FAFC:base + 0x4FAFC + 1266 * 4]
    f = rel[base + 0x4EBF0:base + 0x4EBF0 + 1266 * 2]
    if (len(prices) != 1267 * 2 or len(names) != 242 * 16
            or sha256(h) != '231d23625c126b048d95be99f397e2f05f564af23423c1f911d706acaec37f0e'
            or sha256(f) != '5700370581b13dd85eb1102656f858c9c4dbb4752c646c3ad563893937a2517a'
            or sha256(catalogue) != '91bad7d2198f5da32b464547c3a3c15df9cc77e1969ad7eebc7c0fa45f66956f'
            or series[55 * 3:56 * 3] != bytes.fromhex('020012')
            or series_names[55 * 16:56 * 16] != b'western         '
            or symbol_data(rel, text, 'mRmTp_size_s_data') != b'\x01' + bytes(23)):
        raise ValueError('Changed complete Western item/scoring/catalogue sources')
    list_names = re.findall(r'^(ftr_list\w*) =', text, re.M)
    if len(list_names) != 23 or len(set(list_names)) != 23:
        raise ValueError('Changed complete acquisition-list inventory')
    lists = {}
    for name in list_names:
        raw = symbol_data(rel, text, name)
        if not raw or len(raw) % 2:
            raise ValueError('Incomplete acquisition list')
        lists[name] = raw, struct.unpack('>' + str(len(raw) // 2) + 'H', raw)
    tables = [(at, data_pointers(rel, at, 1266 * 4)) for at in (0x39FB4, 0x7B5B0)]
    records, rows = bytearray(), []
    for pilot in WESTERN_PILOTS:
        item, index = pilot.item, 1024 + (pilot.item - 0x3000) // 4
        price, list_name, hra_hex, feng_hex, position = PROPERTIES[item]
        name = names[(index - 1024) * 16:(index - 1023) * 16]
        profile_at, size = symbol_span(text, pilot.profile)
        profile = symbol_data(rel, text, pilot.profile)
        models = {}
        for _, suffix, slot, expected_size in pilot.models:
            address, model_size = symbol_span(text, pilot.stem + suffix)
            if model_size != expected_size or profile_at + slot in models:
                raise ValueError('Changed or duplicated Western model binding')
            models[profile_at + slot] = address
        membership = [(n, ids.count(item)) for n, (_, ids) in lists.items() if item in ids]
        found = [(n, mode) for n, (i, mode) in enumerate(struct.iter_unpack('>HH', catalogue)) if i == index]
        if (name != pilot.name.encode().ljust(16, b' ')
                or struct.unpack_from('>H', prices, index * 2)[0] != price
                or size != 52 or profile != bytes(32) + scalar_profile(pilot) + bytes(4)
                or any(pointers.get(at + index * 4) != profile_at for at, pointers in tables)
                or data_pointers(rel, profile_at, size) != models
                or h[index * 4:index * 4 + 4] != bytes.fromhex(hra_hex)
                or f[index * 2:index * 2 + 2] != bytes.fromhex(feng_hex)
                or membership != [(list_name, 1)] or found != [(position, 0)]):
            raise ValueError('Changed Western model, item identity, or gameplay properties')
        raw, ids = lists[list_name]
        if ids[-1] != 0 or 0 in ids[:-1]:
            raise ValueError('Changed Western acquisition-list terminator')
        value = int(hra_hex, 16)
        birth, surface = value >> 8 & 63, value >> 6 & 3
        if birth not in (0, 1, 2, 3) or value & 63:
            raise ValueError('Unreviewed Western scoring category')
        native_hra = value & 0xFFFFC000 | birth << 9 | surface << 7
        ordinary = list_name in ('ftr_listA', 'ftr_listB', 'ftr_listC')
        record = struct.pack('>HHHBB', index, item, price, 0, 1) + name + bytes(8)
        records.extend(record)
        rows.append({'id': f'{DONOR}/item/{item:04X}', 'item_id': f'{item:04X}',
            'runtime_index': index, 'name': pilot.name, 'price': price, 'footprint': '1x1',
            'donor_name_sha256': sha256(name), 'donor_profile_sha256': sha256(profile),
            'record_sha256': sha256(record), 'donor_list': list_name,
            'donor_list_sha256': sha256(raw), 'ordinary_stock': ordinary,
            'stock_group': 'ABC'.index(list_name[-1]) if ordinary else None,
            'donor_catalogue_position': position, 'preview_mode': 0,
            'donor_hra_hex': hra_hex.lower(), 'native_hra_hex': f'{native_hra:08x}',
            'series': 55, 'birth_category': birth, 'surface': surface,
            'face': bool(value & 0x8000), 'lucky': bool(value & 0x4000),
            'feng_hex': feng_hex.lower(), 'feng_colour': int(feng_hex[:2], 16),
            'feng_facing_penalty': bool(int(feng_hex[2:], 16)),
            'runtime_requirements': ['install fixed profile, item readers, and selected save dependency',
                'install catalogue and actual ordinary/event stock route',
                'install Western series 55 and its English score-letter name',
                'verify actual model-bank and catalogue-preview capacity'],
            'runtime_installed': False, 'selectable': False})
    return bytes(records), rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--symbols', type=Path, default=ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        parser.error('Choose a fresh ignored build/ directory')
    evidence = identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx')
    records, rows = metadata(read_donor(args.disc)['rel'], args.symbols.read_bytes())
    report = {'format': 'AFV3-WESTERN-ITEMS-1', 'source_rel_sha256': REL_SHA,
        'source_symbols_sha256': SYMBOLS_SHA, 'identity_sheet_sha256': SHEET_SHA,
        'identity_evidence': evidence, 'records_sha256': sha256(records), 'record_bytes': 32,
        'imports': rows, 'runtime_installed': False}
    output.mkdir(parents=True)
    (output / 'items.bin').write_bytes(records)
    (output / 'items.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'output': str(output), 'items': len(rows),
                      'records_sha256': report['records_sha256'], 'runtime_installed': False}))


if __name__ == '__main__':
    main()
