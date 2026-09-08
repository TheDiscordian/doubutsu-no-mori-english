#!/usr/bin/env python3
"""Inventory native date consumers and verify their installed call targets."""

import argparse
from collections import Counter
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256, verified_rom
from audit_string_callers import audit
from runtime_module import verify_test_module

FORMATTERS = (
    ('year', 0x800C4084, 'af_format_year'),
    ('month', 0x800C40F8, 'af_format_month'),
    ('weekday', 0x800C4168, 'af_format_weekday'),
    ('day', 0x800C41B8, 'af_format_day'),
    ('hour', 0x800C4228, 'af_format_hour'),
    ('minute', 0x800C42E8, 'af_format_minute'),
    ('second', 0x800C4350, 'af_format_second'),
    ('number_unit', 0x800C43B8, None),
)


def call_target(word):
    if word >> 26 not in (2, 3):
        raise ValueError('Expected a direct native date call')
    return 0x80000000 | ((word & 0x3FFFFFF) << 2)


def inventory(native, installed, build):
    native = verified_rom(native)
    module = build['runtime_module']
    verify_test_module(installed, module)
    files = by_vrom(installed)
    moved = {int(k, 16): int(v, 16) for k, v in build.get('vrom_relocations', {}).items()}
    rows, definitions = [], None
    for field, original, symbol in FORMATTERS:
        evidence = audit(native, original)
        if definitions is not None and definitions != evidence['definition_sha256']:
            raise ValueError('Date executable definitions changed during inventory')
        definitions = evidence['definition_sha256']
        destination = int(module['symbols'][symbol], 16) if symbol else None
        for caller in evidence['callers']:
            vrom, offset = int(caller['vrom'], 16), int(caller['offset'], 16)
            current_vrom = moved.get(vrom, vrom)
            data = files[current_vrom].extract(installed)
            if offset > len(data)-4:
                raise ValueError('Installed date caller is outside its DMA file')
            actual = call_target(struct.unpack_from('>I', data, offset)[0])
            if actual == original:
                state = 'native_formatter_remaining'
            elif actual == destination:
                state = 'resident_formatter_installed'
            else:
                raise ValueError(f'Unrecognised installed date target at {caller["call_ram"]}')
            rows.append({'field': field, 'segment': caller['segment'],
                'call_ram': caller['call_ram'], 'native_vrom': caller['vrom'],
                'installed_vrom': f'{current_vrom:08X}', 'offset': caller['offset'],
                'native_file_sha256': caller['file_sha256'], 'installed_file_sha256': sha256(data),
                'original_target': f'{original:08X}', 'installed_target': f'{actual:08X}',
                'state': state})
    return {'native_sha256': sha256(native), 'installed_sha256': sha256(installed),
            'definition_sha256': definitions, 'callers': rows,
            'states': dict(Counter(row['state'] for row in rows)),
            'scope': 'Direct J/JAL entry calls in pinned executable sections; no indirect or inlined-use proof',
            'completion_claim': False,
            'warning': 'Installed targets alone do not establish caller capacity, formatting, delivery, or gameplay'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-rom', type=Path, required=True)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--build-report', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inventory(args.native_rom.read_bytes(), args.rom.read_bytes(),
                       json.loads(args.build_report.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'callers': len(result['callers']), 'states': result['states'],
                      'output': str(args.output), 'completion_claim': False}))


if __name__ == '__main__':
    main()
