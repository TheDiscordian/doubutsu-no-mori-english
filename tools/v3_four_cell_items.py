"""Compile the checked 2x2 item-reader extension without changing a cartridge."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from apply_translation import write_new
from gc_names import symbol_data
from v3_asset_loader import ROOT, compile_part
from v3_furniture_art import verify_sources

CELLS = ((1, 0, 0), (1, 1, 0), (1, 1, 1), (1, 0, 1))
DEFINES = tuple('af_v3_item_' + name + '=af_v3_item_' + name + '_extended'
                for name in ('name', 'type', 'size', 'place', 'price')) + (
    'AF_V3_CONSTRUCTION_ITEMS=1', 'AF_V3_WESTERN_LARGE=1',
    'AF_V3_SPARSE_FURNITURE=1', 'AF_V3_CLOTHING_PROFILE=1',
    'AF_V3_ROSTER_CLOTHING=1', 'AF_V3_MULTI_CELL_ITEMS=1', 'AF_V3_FOUR_CELL_ITEMS=1')


def source_evidence(original, rel, symbols):
    verified_rom(original)
    verify_sources(rel, symbols)
    code = by_vrom(original)[CODE_VROM].extract(original)
    raw = b''.join(struct.pack('>Bxhh', *row) for row in CELLS)
    donor = symbol_data(rel, symbols.decode(), 'mRmTp_size_l_data')
    native = code[0x8010D2FC - CODE_RAM:0x8010D314 - CODE_RAM]
    selector = code[0x800BE6D8 - CODE_RAM:0x800BE72C - CODE_RAM]
    if (donor != raw or native != raw or sha256(selector) !=
            'c798ef6bac0570b744c81890ef4c74cf401b513dc9c124e94f149e35d504161a'):
        raise ValueError('Changed native/donor four-cell footprint or native size selector')
    return {'native_selector_ram': '800BE6D8', 'native_selector_bytes': len(selector),
        'native_selector_sha256': sha256(selector), 'native_table_ram': '8010D2FC',
        'donor_table': 'mRmTp_size_l_data', 'table_bytes': len(raw),
        'table_sha256': sha256(raw), 'cells': [list(row) for row in CELLS],
        'size_query_result': 2, 'placement_result': 2,
        'rotation_changes_footprint': False, 'invalid_result': 3}


def build(output):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    evidence = source_evidence(
        (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
        (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    output.mkdir(parents=True)
    code, compiled = compile_part('items_large', output / 'items', defines=DEFINES,
                                  primary_source='overlays/v3/items.c')
    if len(code) > 0x1000 or compiled['symbols']['af_v3_item_name_extended'] != 0x80483000:
        raise ValueError('Four-cell reader leaves the existing resident code reservation')
    report = {'format': 'AFV3-FOUR-CELL-ITEMS-1', 'source_evidence': evidence,
        'code': compiled, 'runtime_installed': False, 'saved_format_changed': False,
        'web_patcher_enabled': False,
        'integration_requirements': ['replace the checked resident item-reader code',
            'rebind all five public item bridges to the new compiled entry points',
            'refresh resident package and prefix checksums',
            'install complete bonfire callbacks before enabling its selected item']}
    write_new(output / 'items.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    result = build(parser.parse_args().output)
    print(json.dumps({'bytes': result['code']['bytes'], 'sha256': result['code']['sha256'],
                      'runtime_installed': False}))
