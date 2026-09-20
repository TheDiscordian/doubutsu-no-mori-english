"""Generate one changed-storage native check from the current checked cartridge."""
import argparse
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from apply_translation import write_new
from textbanks import Bank
from v3_asset_loader import BLOB
from v3_import_storage import PACKAGE, PACKAGE_RAM, PACKAGE_SIZE, CHOICE_NEW, ABI, ROWS_RAM


def scenario(image, report):
    if report.get('resource_capacity'):
        from v3_resource_capacity import native_scenario
        return native_scenario(image,report)
    if report['runtime_abi'] != ABI or sha256(image) != report['output_sha256']:
        raise ValueError('Storage check requires the matching current cartridge report')
    files = by_vrom(image)
    blob = files[BLOB].extract(image)
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
    # Check all imported resolved pointers, plus the low/high absent boundaries.
    for row in report['furniture']['imports']:
        read(0x80470010 + row['runtime_index'] * 4, bytes.fromhex(row['profile_ram']))
    read(0x80470010 + 1024 * 4, bytes(4))
    read(0x80470010 + 2047 * 4, bytes(16))
    read(ROWS_RAM + 1023 * 80, bytes(80))
    actions += [{'save_state': True}, {'pause_game_thread': True}]
    # Changed direct readers exercise a one-cell item, two-cell item, callback
    # item, retained shirt reader, and both ends of the empty canonical range.
    for item, kind, price in ((0x3224, 10, 840), (0x32D8, 10, 3680),
                              (0x3350, 10, 2990), (0x34BF, 12, 380),
                              (0x3000, 0, 0), (0x3FFC, 0, 0)):
        # Prices are bound to actual installed metadata, not guessed fixtures.
        if kind == 10:
            at = PACKAGE + 0x25000 + (item - 0x3000) // 4 * 32
            price = struct.unpack_from('>H', blob, at + 4)[0]
        call(0x800A5630, [item], kind)
        call(0x800C0194, [item], price)
    bank = Bank('select', CHOICE_NEW, 0xD06000, files[CHOICE_NEW].extract(image), files[0xD06000].extract(image))
    entries = bank.entries()
    if len(entries) != 462 or any(len(row) > 20 for row in entries):
        raise ValueError('Unexpected English choice bank or reader capacity')
    chosen = [0, 460, 461] + [next(i for i, row in enumerate(entries) if i % 2 == parity and len(row) > 16) for parity in (0, 1)]
    write(0x8019B000, bytes(0x1B0))
    for i in chosen:
        write(0x8019AE00, b'G' * 40)
        call(0x80065528, [i, 0x8019AF00, 0x8019AF04])
        read(0x8019AF00, struct.pack('>2I', CHOICE_NEW + sum(map(len, entries[:i])), len(entries[i])))
        call(0x80065D90, [0x8019B000, 0x8019AE08, i, 0])
        read(0x8019AE00, b'G' * 8 + entries[i].ljust(20, b' ') + b'G' * 12)
    call(0x80065528, [462, 0x8019AF00, 0x8019AF04])
    read(0x8019AF00, bytes(8))
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
