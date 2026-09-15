"""Verify camping identities and gameplay properties from the actual English donor.

The scoring-only mapping preserves the 412-point value. Acquisition remains the
summer-camper route; mapping an HRA weight does not move items into event stock.
"""
import argparse
import json
from pathlib import Path
import re
import struct

from aflib import by_vrom, sha256
from gc_names import rel_sections, symbol_data
from item_identity_sheet import SHEET_SHA, sheet_rows
from v3_furniture_art import CAMPING_PILOTS, scalar_profile, verify_sources
from v3_import_catalog import DONOR, ROOT, REL_SHA, SYMBOLS_SHA, read_donor
from v3_villager_art import data_pointers, symbol_span

BASE = ROOT / 'build/v3-import-storage-02'
BASE_SHA = 'f12da1a8575403ab74ded685e916bf082b5c1d53e6b73c0ae74c0fe87d282ade'
REPORT_SHA = 'a3534ac6e88f07bca7c476ed44914278cfbb063ccadfab8891e3bf2183681dfb'
PROPERTIES = {
    0x3364: (3460, 'D4052500', '0100', 466, 0),
    0x3370: (1980, 'D4052500', '0000', 462, 0),
    0x339C: (1180, 'D4052580', '0200', 467, 0),
    0x33A4: (1300, 'D4052500', '0000', 465, 0),
    0x33A8: (3380, 'D4052500', '0000', 468, 24),
    0x33AC: (1960, 'D4052500', '0400', 470, 0),
    0x33B0: (1470, 'D4052500', '0000', 469, 0),
}
TENT = (0x335C, 0x3360, 0x3364, 0x336C, 0x3370, 0x339C, 0x33A4, 0x33A8, 0x33AC, 0x33B0, 0)
ORDERABLE_LISTS = ('ftr_listA', 'ftr_listB', 'ftr_listC', 'ftr_listTrain',
                  'ftr_listEvent', 'ftr_listLottery', 'ftr_listEventPresentChumon')


def identity_evidence(path):
    if sha256(path.read_bytes()) != SHEET_SHA:
        raise ValueError('Changed camping identity worksheet')
    cells = list(sheet_rows(path, 'Items'))
    if any(cells[0][1].get(k) != v for k, v in {
            'C': 'ID (AF)', 'E': 'ID (AC)', 'H': 'Name (AF)', 'J': 'Name (English)'}.items()):
        raise ValueError('Changed camping identity columns')
    result = []
    for pilot in CAMPING_PILOTS:
        matches = [(n, c) for n, c in cells[1:] if c.get('E') == f'{pilot.item:04X}']
        if (len(matches) != 1 or matches[0][1].get('J') != pilot.name
                or any(matches[0][1].get(k) != '-' for k in ('C', 'H', 'CG', 'CJ'))):
            raise ValueError('Camping identity has changed or is ambiguous')
        result.append({'item_id': f'{pilot.item:04X}', 'sheet_row': matches[0][0],
                       'native_id_name_and_artwork_absent': True})
    return result


def score_mapping(rel, symbols, cartridge, report, *, source_sha256=BASE_SHA):
    """Bind the source weight and the actual installed native bitfield consumer."""
    verify_sources(rel, symbols)
    if sha256(cartridge) != source_sha256 or report['output_sha256'] != source_sha256:
        raise ValueError('Camping scoring needs the checked expanded-storage cartridge')
    source = symbol_data(rel, symbols.decode(), 'mMkRm_birth_point_table')
    files = by_vrom(cartridge)
    data = files[0x03F40000].extract(cartridge)
    h = report['hra']; extension = h['birth_extension']
    at = extension['points_address'] - 0x809259E0
    if (sha256(data) != h['output_sha256'] or len(source) != 38 * 4
            or extension['count'] != 23 or extension['stack_bytes'] != 264
            or sha256(data[at:at + 92]) != extension['points_sha256']
            or struct.unpack_from('>I', source, 37 * 4)[0] != 412
            or struct.unpack_from('>I', data, at + 3 * 4)[0] != 412
            or any(struct.unpack_from('>I', data, p['address'] - 0x809259E0)[0] != p['after']
                   for p in extension['patches'])):
        raise ValueError('Changed camping/native HRA point equivalence or evaluator')
    # All three native bitfield extractions are in EvaluateBasePoint. They
    # extract bits 13:9 and index the point counters, not an acquisition list.
    found = [(0x809259E0 + i, struct.unpack_from('>I', data, i)[0]) for i in range(0, 10704, 4)
             if data[i:i + 4] in (bytes.fromhex('000b5c80'), bytes.fromhex('000b5ec2'))]
    expected = [(address + d, word) for address in (0x809275E0, 0x8092763C, 0x80927680)
                for d, word in ((0, 0x000B5C80), (4, 0x000B5EC2))]
    if found != expected:
        raise ValueError('Changed native HRA birth-field consumer inventory')
    return {'donor_category': 37, 'native_scoring_category': 3, 'points': 412,
            'domain': 'HRA base-point metadata only', 'acquisition_category_changed': False,
            'native_counter_count': 23, 'extra_stack_or_counter_memory': 0,
            'native_hra_sha256': sha256(data), 'native_points_sha256': extension['points_sha256'],
            'donor_points_sha256': sha256(source), 'native_consumers': [a for a, _ in found[::2]]}


def metadata(rel, symbols):
    verify_sources(rel, symbols)
    text = symbols.decode()
    base = rel_sections(rel)[5][0]
    prices = symbol_data(rel, text, 'ftr_price_table')
    names = symbol_data(rel, text, 'ftrName2_table')
    catalogue = symbol_data(rel, text, 'mCL_furniture_list')
    draw = symbol_data(rel, text, 'furniture_draw_data$436')
    h = rel[base + 0x4FAFC:base + 0x4FAFC + 1266 * 4]
    f = rel[base + 0x4EBF0:base + 0x4EBF0 + 1266 * 2]
    if (len(prices) != 1267 * 2 or len(names) != 242 * 16
            or sha256(h) != '231d23625c126b048d95be99f397e2f05f564af23423c1f911d706acaec37f0e'
            or sha256(f) != '5700370581b13dd85eb1102656f858c9c4dbb4752c646c3ad563893937a2517a'
            or sha256(catalogue) != '91bad7d2198f5da32b464547c3a3c15df9cc77e1969ad7eebc7c0fa45f66956f'):
        raise ValueError('Changed complete camping item/scoring/catalogue sources')
    list_names = re.findall(r'^(ftr_list\w*) =', text, re.M)
    if len(list_names) != 23 or len(set(list_names)) != 23:
        raise ValueError('Changed complete donor acquisition-list inventory')
    lists = {}
    for name in list_names:
        raw = symbol_data(rel, text, name)
        if not raw or len(raw) % 2:
            raise ValueError('Incomplete donor acquisition list')
        lists[name] = struct.unpack('>' + str(len(raw) // 2) + 'H', raw)
        if lists[name][-1] != 0 or 0 in lists[name][:-1]:
            raise ValueError('Changed acquisition-list terminator')
    if lists['ftr_listTent'] != TENT:
        raise ValueError('Changed complete ten-item camping reward list')
    tables = [(a, data_pointers(rel, a, 1266 * 4)) for a in (0x39FB4, 0x7B5B0)]
    records, rows = bytearray(), []
    for pilot in CAMPING_PILOTS:
        item, index = pilot.item, 1024 + (pilot.item - 0x3000) // 4
        price, hra_hex, feng_hex, position, preview = PROPERTIES[item]
        name = names[(index - 1024) * 16:(index - 1023) * 16]
        p_at, size = symbol_span(text, pilot.profile)
        profile = rel[base + p_at:base + p_at + size]
        models = {}
        for label, suffix, slot, expected_size in pilot.models:
            address, model_size = symbol_span(text, dict(pilot.model_symbols).get(label, pilot.stem + suffix))
            if model_size != expected_size or p_at + slot in models:
                raise ValueError('Changed camping model binding')
            models[p_at + slot] = address
        memberships = [(n, ids.count(item)) for n, ids in lists.items() if item in ids]
        found = [(n, mode) for n, (i, mode) in enumerate(struct.iter_unpack('>HH', catalogue)) if i == index]
        preview_hex = '3f59999ac0400000' if preview == 24 else '3f666666c0400000'
        if (name != pilot.name.encode().ljust(16, b' ')
                or struct.unpack_from('>H', prices, index * 2)[0] != price
                or size != 52 or profile != bytes(32) + scalar_profile(pilot) + bytes(4)
                or any(pointers.get(a + index * 4) != p_at for a, pointers in tables)
                or data_pointers(rel, p_at, size) != models
                or h[index * 4:index * 4 + 4] != bytes.fromhex(hra_hex)
                or f[index * 2:index * 2 + 2] != bytes.fromhex(feng_hex)
                or memberships != [('ftr_listTent', 1)] or found != [(position, preview)]
                or draw[preview * 8:preview * 8 + 8].hex() != preview_hex
                or any(item in lists[n] for n in ORDERABLE_LISTS)):
            raise ValueError('Changed camping item, profile, price, reward route, or catalogue framing')
        footprint = 1 if (pilot.shape, pilot.collision) == (3, 1) else 0
        if not footprint and (pilot.shape, pilot.collision) != (4, 0):
            raise ValueError('Unreviewed camping footprint')
        value = int(hra_hex, 16)
        birth, surface = value >> 8 & 63, value >> 6 & 3
        if birth != 37 or value & 63:
            raise ValueError('Unreviewed camping scoring category')
        native_hra = value & 0xFFFFC000 | 3 << 9 | surface << 7
        record = struct.pack('>HHHBB', index, item, price, footprint, 1) + name + bytes(8)
        records.extend(record)
        rows.append({'id': f'{DONOR}/item/{item:04X}', 'item_id': f'{item:04X}',
            'runtime_index': index, 'name': pilot.name, 'price': price,
            'footprint': '1x2' if footprint else '1x1', 'record_sha256': sha256(record),
            'donor_profile_sha256': sha256(profile), 'donor_name_sha256': sha256(name),
            'donor_list': 'ftr_listTent', 'donor_list_sha256': sha256(symbol_data(rel, text, 'ftr_listTent')),
            'ordinary_stock': False, 'catalogue_orderable': False,
            'donor_hra_hex': hra_hex.lower(), 'native_hra_hex': f'{native_hra:08x}',
            'series': value >> 26, 'donor_birth_category': birth, 'native_scoring_category': 3,
            'hra_points': 412, 'surface': surface, 'feng_hex': feng_hex.lower(),
            'feng_colour': int(feng_hex, 16) >> 8 & 7, 'feng_facing_penalty': int(feng_hex, 16) & 255,
            'catalogue_position': position, 'preview_mode': preview,
            'donor_preview_scalar_hex': preview_hex, 'runtime_installed': False,
            'selectable': False, 'acquisition_installed': False})
    return bytes(records), rows


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        parser.error('Choose a fresh ignored build/ output')
    donor = read_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    cartridge, raw = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes(), (BASE / 'build.json').read_bytes()
    if sha256(raw) != REPORT_SHA:
        raise ValueError('Changed current native scoring report')
    mapping = score_mapping(donor['rel'], symbols, cartridge, json.loads(raw))
    records, rows = metadata(donor['rel'], symbols)
    report = {'format': 'AFV3-CAMPING-ITEMS-1', 'donor': DONOR, 'rel_sha256': REL_SHA,
        'symbols_sha256': SYMBOLS_SHA, 'records_sha256': sha256(records), 'scoring_mapping': mapping,
        'identity_evidence': identity_evidence(ROOT / 'build/item-identity-megasheet.xlsx'),
        'imports': rows, 'runtime_installed': False, 'web_patcher_enabled': False,
        'pending': ['cartridge integration', 'summer-camper acquisition adapter', 'ordinary gameplay and persistence']}
    output.mkdir(parents=True)
    from apply_translation import write_new
    write_new(output / 'items.bin', records)
    write_new(output / 'items.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'items': len(rows), 'metadata_bytes': len(records), 'sha256': sha256(records)}))
