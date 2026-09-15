"""Complete the two aloha mannequin scoring rows without changing saved formats."""
import argparse
import copy
import json
from pathlib import Path
import struct

from aflib import apply_ups, by_vrom, fix_checksum, make_ups, sha256, verified_rom
from apply_translation import write_new
from gc_names import rel_sections, symbol_data
from v3_asset_loader import BLOB, ROOT
from v3_furniture_art import verify_sources
from v3_registry import CLOTHING, CLOTHING_DISPLAYS
import v3_hra as hra
import v3_feng_shui as feng

BASE = ROOT / 'build/v3-construction-catalogue-03'
BASE_SHA = '5d6e3abdb2b67f33b99264dd2a4a0069c542c34c60b397fcf9df97121237fbc7'
REPORT_SHA = '0f33275f8f62d65ef0f3de7e4e8da038d2ca630f58ffad4d83fb53954f6b11d6'
SOURCES = ('tools/v3_aloha_scoring.py', 'tools/v3_registry.py', 'tools/v3_hra.py',
           'tools/v3_feng_shui.py', 'tools/v3_furniture_art.py')


def metadata(rel, symbols, installed):
    verify_sources(rel, symbols)
    conversion = symbol_data(rel, symbols.decode(), 'mRmTp_Item1ItemNo2FtrItemNo_AtPlayerRoom')
    start = rel_sections(rel)[5][0]
    h = rel[start + 0x4FAFC:start + 0x4FAFC + 1266 * 4]
    f = rel[start + 0x4EBF0:start + 0x4EBF0 + 1266 * 2]
    if (sha256(conversion) != '5228a779089eca94c3f751a814e169f74ff085a57626673c86d7d789fadd6c66'
            or conversion[80:84] != bytes.fromhex('380317ac')
            or sha256(h) != hra.DONOR_SHA or sha256(f) != feng.DONOR_SHA):
        raise ValueError('Changed donor mannequin conversion or full scoring tables')
    rows = []
    for donor, profile in ((0x241A, 0x80466548), (0x241B, 0x80466598)):
        index, item = CLOTHING_DISPLAYS[donor]
        pocket = CLOTHING[donor][0]
        actual = [r for r in installed if r['donor_item_id'] == f'{donor:04X}']
        source_index = (0x17AC - 0x1000) // 4 + donor - 0x2400
        if (len(actual) != 1 or actual[0]['item_id'] != f'{item:04X}'
                or actual[0]['pocket_item_id'] != f'{pocket:04X}'
                or actual[0]['runtime_index'] != index or actual[0]['profile_ram'] != f'{profile:08X}'
                or h[source_index * 4:source_index * 4 + 4] != bytes.fromhex('D4050800')
                or f[source_index * 2:source_index * 2 + 2] != bytes(2)):
            raise ValueError('Changed actual aloha display identity or donor scoring row')
        rows.append({'donor_item_id': f'{donor:04X}', 'item_id': f'{item:04X}',
            'pocket_item_id': f'{pocket:04X}', 'runtime_index': index,
            'donor_runtime_index': source_index, 'profile_ram': f'{profile:08X}',
            'donor_metadata': 'd4050800', 'metadata': 'd4051000',
            'series': 53, 'birth_category': 8, 'surface': 0, 'feng_metadata': '0000'})
    return rows


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    base = (BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
    raw = (BASE / 'build.json').read_bytes()
    if sha256(base) != BASE_SHA or sha256(raw) != REPORT_SHA:
        raise ValueError('Changed complete construction integration source')
    report = json.loads(raw)
    if report['runtime_abi'] != 62: raise ValueError('Changed runtime contract')
    files = by_vrom(base)
    blob = files[BLOB].extract(base)
    rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
    symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
    rows = metadata(rel, symbols, report['aloha_display']['rows'])
    image = bytearray(base)
    changes = []
    updated = {}
    for key, tool, width in (('hra', hra, 4), ('feng_shui', feng, 2)):
        record = copy.deepcopy(report[key])
        entry = files[tool.NEW_VROM]
        data = bytearray(entry.extract(base))
        at = record['metadata_address'] - tool.RAM
        if (entry.pend or sha256(data) != record['output_sha256']
                or sha256(files[tool.NEW_RELOC].extract(base)) != record['relocation_sha256']
                or record['metadata_rows'] != 2051
                or not files[BLOB].pstart <= entry.pstart <= files[BLOB].pstart + len(blob) - len(data)):
            raise ValueError('Changed complete scoring resource or shared physical backing')
        for row in rows:
            index = row['runtime_index']
            offset = at + index * width
            before = bytes(data[offset:offset + width])
            expected = bytes.fromhex('FC000000') if width == 4 else bytes(2)
            after = bytes.fromhex(row['metadata'] if width == 4 else row['feng_metadata'])
            if before != expected: raise ValueError('Aloha scoring target is already assigned')
            data[offset:offset + width] = after
            if before != after:
                changes.append({'offset': entry.pstart + offset, 'before': before.hex(),
                                'after': after.hex(), 'item_id': row['item_id']})
            added = {k: v for k, v in row.items() if k != 'feng_metadata'}
            if width == 2:
                added = {k: row[k] for k in ('donor_item_id', 'item_id', 'pocket_item_id', 'runtime_index', 'donor_runtime_index', 'profile_ram')}
                added.update(metadata='0000', colour='none')
            record['imports'].append(added)
        image[entry.pstart:entry.pstart + len(data)] = data
        record.update(output_sha256=sha256(data), metadata_sha256=sha256(data[at:at + 2051 * width]))
        updated[key] = record
    if len(changes) != 2: raise ValueError('Unexpected aloha scoring change count')
    fix_checksum(image)
    image = bytes(image)
    native = verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    patch = make_ups(native, image)
    if apply_ups(native, patch) != image: raise ValueError('Aloha scoring reconstruction failed')
    result = {**report, **updated, 'build': 'v3-aloha-scoring', 'input_build_sha256': BASE_SHA,
        'output_sha256': sha256(image), 'patch_sha256': sha256(patch),
        'blob_sha256': sha256(files[BLOB].extract(image)),
        'aloha_scoring': {'imports': rows, 'writes': changes, 'runtime_abi_changed': False,
            'saved_format_changed': False, 'saved_profile_changed': False, 'additional_ram_allocation': 0,
            'native_test': 'pending', 'not_a_playtest_handoff': True,
            'compatibility': 'Same saved format and profile as the complete ABI 62 construction cartridge; keep backups.'},
        'native_test': 'pending complete imported-garment scoring check',
        'sources': {**report['sources'], **{p: sha256((ROOT / p).read_bytes()) for p in SOURCES}}}
    output.mkdir(parents=True)
    write_new(output / 'animal-forest-v3-asset-loader.z64', image)
    write_new(output / 'asset-loader.ups', patch)
    write_new(output / 'build.json', (json.dumps(result, indent=2) + '\n').encode())
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({key: result[key] for key in ('output_sha256', 'patch_sha256')}))
