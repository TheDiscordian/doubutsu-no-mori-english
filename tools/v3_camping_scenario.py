"""Generate one bounded current-camping startup and actual item-reader check."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from apply_translation import write_new
from v3_asset_loader import BLOB
from v3_camping_runtime import ABI, PACKAGE, PACKAGE_RAM, PACKAGE_SIZE, ITEMS, ITEMS_RAM, ROWS, ROWS_RAM, slot


def scenario(image, report):
    if report['runtime_abi'] != ABI or sha256(image) != report['output_sha256']:
        raise ValueError('Camping check requires the matching current cartridge report')
    blob = by_vrom(image)[BLOB].extract(image)
    actions = [{'wait': 16}]
    def read(address, value):
        actions.append({'read': [f'{address:08X}', len(value)], 'expect': value.hex()})
    def write(address, value):
        actions.append({'write': [f'{address:08X}', value.hex()]})
    def call(address, args, expected=None):
        row = {'address': f'{address:08X}', 'arguments': args, 'return_address': '8019AD60'}
        if expected is not None:
            row['expect_return'] = expected
        actions.append({'call': row})
    read(0x8019ACD0, struct.pack('>I', 1))
    read(0x80460000, blob[:16])
    read(PACKAGE_RAM, blob[PACKAGE:PACKAGE + 16])
    read(PACKAGE_RAM + PACKAGE_SIZE - 16, bytes.fromhex('AFACC0DE') * 4)
    read(0x80472850, bytes.fromhex('AF46C0DE') * 4)
    rows = report['camping']['imports']
    if len(rows) != 7:
        raise ValueError('Incomplete current camping table')
    for row in rows:
        i = slot(int(row['item_id'], 16))
        read(ROWS_RAM + i * 80, blob[ROWS + i * 80:ROWS + (i + 1) * 80])
        read(ITEMS_RAM + i * 32, blob[ITEMS + i * 32:ITEMS + (i + 1) * 32])
        read(0x80470010 + row['runtime_index'] * 4, bytes.fromhex(row['profile_ram']))
    actions += [{'save_state': True}, {'pause_game_thread': True}]
    edge = b'V3CP' * 4
    write(0x8019AE00, edge + bytes(16) + edge)
    for row in rows:
        item = int(row['item_id'], 16)
        # Use the existing native dispatch entries, never an unchecked direct
        # call into Expansion Pak code. Quarter-turn readers share identity.
        call(0x801969C8, [0x8019AE10, 16, item], 1)
        read(0x8019AE00, edge + row['name'].encode().ljust(16, b' ') + edge)
        call(0x800A5630, [item | 3], 10)
        call(0x800C0194, [item | 3], row['price'])
        call(0x800BE69C, [item | 3], int(row['footprint'] == '1x2'))
    read(0x8003CE34, bytes(4))
    read(0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    actions += [{'load_state': True}, {'wait': 1}]
    read(0x8003CE34, bytes(4))
    read(PACKAGE_RAM + PACKAGE_SIZE - 16, bytes.fromhex('AFACC0DE') * 4)
    return actions


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    image = (args.build / 'animal-forest-v3-asset-loader.z64').read_bytes()
    report = json.loads((args.build / 'build.json').read_bytes())
    actions = scenario(image, report)
    write_new(args.output, (json.dumps(actions, indent=2) + '\n').encode())
    print(json.dumps({'actions': len(actions), 'native_calls': sum('call' in row for row in actions)}))
