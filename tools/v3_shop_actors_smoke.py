"""Actual relocated shop interaction windows and complete ticket decisions."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from shop_units import PRICE_BIASES
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs
from v3_shop_actors import SHOPS


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    shops = report.get('shop_actors')
    if sha256(rom) != report['output_sha256'] or not shops:
        raise ValueError('Shop actor probe requires its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:0xC000]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'shop_actor_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native shop actor check failed: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Shop actor call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    def put(at, value):
        debug.write_memory(at, struct.pack('>I', value))

    check('complete current resident prefix', BLOB_RAM, blob)
    size = 0x8000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Shop actor fixture allocation failed')
    owner = allocation + 16
    before = debug.command('g')
    initial = [int(before[i:i + 16], 16) for i in range(0, len(before), 16)]
    if len(initial) != 71 or initial[37] & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('Shop windows require the paused game frame')
    pointers = {row['pointer']: debug.read_memory(row['pointer'], 4) for row in shops['sites']}
    edge = b'V3SA' * 4
    guards = (allocation, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    windows = 0
    try:
        for name, spec in SHOPS.items():
            data, reloc = (files[v].extract(rom) for v in (spec.vrom, spec.relocation))
            if (sha256(data), sha256(reloc)) != (shops['owners'][name]['output_sha256'], spec.relocation_sha256):
                raise ValueError('Changed current native shop actor')
            expected = relocate_verified_data(spec, data, reloc, owner,
                                               address_constants=(PRICE_BIASES[spec.vrom],))
            call(0x800262D0, [spec.vrom, spec.vrom + len(data), spec.ram,
                              spec.ram + spec.resident_bytes, owner, owner + spec.resident_bytes, len(reloc)])
            check('complete native-relocated ' + name, owner, expected)
            rows = [row for row in shops['sites'] if row['owner'] == name]
            put(rows[0]['pointer'], owner)
            for i, row in enumerate(rows):
                # Each distinct live-register/continuation site needs one import
                # and native fallback. Disabled selection is checked in the full
                # ticket function below, not every permutation of every window.
                for item in (0x2400, 0x3225 if i % 2 == 0 else 0x32BB):
                    regs = initial.copy()
                    for i in range(1, 32):
                        if i not in (26, 27):
                            regs[i] = (0x13579000 + i) << 32 | (0x2468A000 + i)
                    regs[row['source']] = item
                    regs[29], regs[37] = extend(TEST_STACK), extend(owner + row['start'] - spec.ram)
                    wanted = regs.copy()
                    if row['temporary'] is not None:
                        wanted[row['temporary']] = item & 0xF000
                    wanted[row['destination']] = 1 if item >> 12 == 3 else item >> 12
                    if row['after']:
                        wanted[1] = 1
                    target = owner + row['end'] - spec.ram
                    stop = f'0,{target:x},4'
                    if debug.command('Z' + stop) != 'OK':
                        raise ValueError('Shop interaction breakpoint refused')
                    try:
                        if debug.command('G' + ''.join(f'{n:016x}' for n in regs)) != 'OK':
                            raise ValueError('Shop interaction register write refused')
                        stopped = debug.command('c')
                        raw = debug.command('g')
                        actual = [int(raw[i:i + 16], 16) for i in range(0, len(raw), 16)]
                        differences = {str(i): [f'{wanted[i]:016X}', f'{actual[i]:016X}']
                            for i in (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70)) if wanted[i] != actual[i]}
                        passed = stopped[:3] in ('T05', 'S05') and actual[37] & 0xFFFFFFFF == target and not differences
                        record({'shop_window': f'{row["start"]:08X}', 'owner': name, 'item': f'{item:04X}',
                                'register_differences': differences, 'assertion': 'passed' if passed else 'failed'})
                        if not passed:
                            raise ValueError('Shop interaction window failed')
                        windows += 1
                    finally:
                        debug.command('z' + stop)
                        debug.command('G' + before)
            ticket = owner + rows[1]['start'] - 8 - spec.ram
            for item, result in ((0x1004, 1), (0x3225, 1), (0x32BB, 1), (0x2000, 0), (0x3000, 0)):
                call(ticket, [item], result, (owner, expected))
            put(BLOB_RAM + 0x7254, 0)
            call(ticket, [0x32BB], 0, (owner, expected))
            put(BLOB_RAM + 0x7254, 1)
            check('complete shop actor retained after queries', owner, expected)
        check('complete resident prefix retained', BLOB_RAM, blob)
        for at in guards:
            check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        put(BLOB_RAM + 0x7254, 1)
        for at, data in pointers.items():
            debug.write_memory(at, data)
    call(0x8009C040, [allocation])
    return {'native_shop_owners': 5, 'shop_register_windows': windows,
            'complete_native_ticket_decisions': 30, 'ordinary_shop_controls_tested': False,
            'payment_confirmation_tested': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
