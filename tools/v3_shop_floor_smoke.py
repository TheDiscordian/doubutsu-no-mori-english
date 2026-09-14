"""Actual shop-floor branch semantics, reserve selection, and floor item reading."""
import json
from pathlib import Path
import struct
from types import SimpleNamespace

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from npc_mail_show import relocate_verified_data
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_furniture_room_smoke import extend
from v3_npc_draw_smoke import boot_proofs
from v3_shop_floor import POINTER, RAM, RELOC, SECTIONS, SIZE, VROM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom, report = path.read_bytes(), json.loads((path.parent / 'build.json').read_text())
    floor = report.get('shop_floor')
    if sha256(rom) != report['output_sha256'] or not floor:
        raise ValueError('Shop floor probe requires its exact current cartridge')
    files, boot = by_vrom(rom), boot_proofs(rom)
    blob = files[BLOB].extract(rom)[:0xC000]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'shop_floor_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native shop floor check failed: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof or boot.get(address))
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError(f'Shop floor call {address:08X} returned {result["return_value"]}, expected {expected}')
        return result['return_value']

    def put(at, value):
        debug.write_memory(at, struct.pack('>I', value))

    check('complete current resident prefix', BLOB_RAM, blob)
    size = 0x3000
    allocation = call(0x8009BFC0, [size])
    if allocation & 15 or not MODULE_RAM + RESERVATION <= allocation <= 0x80400000 - size:
        raise ValueError('Shop floor fixture allocation failed')
    owner, field, block, grid = (allocation + n for n in (16, 0x1400, 0x1800, 0x2000))
    debug.write_memory(allocation, bytes(size))
    data, reloc = (files[v].extract(rom) for v in (VROM, RELOC))
    if (sha256(data), sha256(reloc)) != (floor['output_sha256'], floor['relocation_sha256']):
        raise ValueError('Changed current shop floor owner')
    expected = relocate_verified_data(SimpleNamespace(ram=RAM, resident_bytes=SIZE, sections=SECTIONS), data, reloc, owner)
    call(0x800262D0, [VROM, VROM + SIZE, RAM, RAM + SIZE, owner, owner + SIZE, len(reloc)])
    check('complete native-relocated shop floor owner', owner, expected)
    proof = (owner, expected)
    globals_before = {at: debug.read_memory(at, 4) for at in (POINTER, 0x80137944, 0x8013A248)}
    put(POINTER, owner)
    edge = b'V3SF' * 4
    guards = (allocation, field - 16, field + 0x200, block - 16, block + 0x700,
              grid - 16, grid + 512, allocation + size - 16, TEST_STACK - 0x800, TEST_STACK + 0x40)
    for at in guards:
        debug.write_memory(at, edge)
    before = debug.command('g')
    initial = [int(before[i:i + 16], 16) for i in range(0, len(before), 16)]
    if len(initial) != 71 or initial[37] & 0xFFFFFFFF != 0x800D334C:
        raise ValueError('Shop floor branches require the paused game frame')
    windows = 0
    try:
        for row in floor['sites']:
            for item, disabled in ((0x1004, False), (0x1EF0, False), (0x3225, False),
                                    (0x32BB, False), (0x32BB, True)):
                put(BLOB_RAM + 0x7254, int(not disabled))
                regs = initial.copy()
                for i in range(1, 32):
                    if i not in (26, 27):
                        regs[i] = (0x13579000 + i) << 32 | (0x2468A000 + i)
                regs[row['source']] = item
                regs[1] = int(item < 0x1ECD)
                regs[29], regs[37] = extend(TEST_STACK), extend(owner + row['start'] - RAM)
                wanted = regs.copy()
                valid = item < 0x1ECD or item >> 12 == 3 and not disabled
                wanted[1] = int(valid)
                taken = valid if row['branch'] >> 26 == 5 else not valid
                if not row['likely'] or taken:
                    if row['delay'] == 0x24011F36:
                        wanted[1] = 0x1F36
                    elif row['delay'] == 0x28612000:
                        wanted[1] = int(item < 0x2000)
                    elif row['delay'] == 0x3C028013:
                        wanted[2] = extend(0x80130000)
                    else:
                        raise ValueError('Unreviewed shop delay effect')
                target = owner + row['taken' if taken else 'fall'] - RAM
                stop = f'0,{target:x},4'
                if debug.command('Z' + stop) != 'OK':
                    raise ValueError('Shop floor breakpoint refused')
                try:
                    if debug.command('G' + ''.join(f'{n:016x}' for n in regs)) != 'OK':
                        raise ValueError('Shop floor register write refused')
                    stopped = debug.command('c'); raw = debug.command('g')
                    actual = [int(raw[i:i + 16], 16) for i in range(0, len(raw), 16)]
                    differences = {str(i): [f'{wanted[i]:016X}', f'{actual[i]:016X}']
                        for i in (*range(26), 28, 29, 30, 31, 33, 34, *range(38, 70)) if wanted[i] != actual[i]}
                    passed = stopped[:3] in ('T05', 'S05') and actual[37] & 0xFFFFFFFF == target and not differences
                    record({'shop_floor_window': f'{row["start"]:08X}', 'item': f'{item:04X}',
                            'disabled': disabled, 'register_differences': differences,
                            'assertion': 'passed' if passed else 'failed'})
                    if not passed:
                        raise ValueError('Shop floor branch/delay result differs')
                    windows += 1
                finally:
                    debug.command('z' + stop); debug.command('G' + before)
                    put(BLOB_RAM + 0x7254, 1)
        put(0x80137944, 0)
        for item, result in ((0x1004, 0x1F2A), (0x3225, 0x1F2A), (0x32BB, 0x1F2A),
                              (0x3000, 0), (0x2000, 0x1F28), (0x1F36, 0x1F2A)):
            call(owner, [item], result, proof)
        put(BLOB_RAM + 0x7254, 0)
        call(owner, [0x32BB], 0, proof)
        put(BLOB_RAM + 0x7254, 1)
        put(0x80137944, 1)
        call(owner, [0x32BB], 0x1F2F, proof)
        put(0x80137944, 0)
        # A real one-block field description, not a substituted lookup callback.
        # Native field existence, bounds, block indexing, and grid loading execute.
        put(0x8013A248, field); put(field + 0x148, block)
        debug.write_memory(field + 0x166, bytes((1, 1)))
        put(block + 0x584, grid)
        code = files[CODE_VROM].extract(rom)
        check('native block getter retained', 0x8008A33C, code[0x8008A33C - CODE_RAM:0x8008A3BC - CODE_RAM])
        call(0x8008A33C, [0, 0], grid)
        for item, result in ((0x1004, 0x1004), (0x3225, 0x3225), (0x32BB, 0x32BB),
                              (0x3000, 0xFFFF), (0, 0xFFFF), (0x1F36, 0xFFFF), (0x2400, 0x2400)):
            debug.write_memory(grid + 84 * 2, struct.pack('>H', item))
            call(owner + 0x809547E4 - RAM, [4, 5], result, proof)
        put(BLOB_RAM + 0x7254, 0)
        debug.write_memory(grid + 84 * 2, bytes.fromhex('32BB'))
        call(owner + 0x809547E4 - RAM, [4, 5], 0xFFFF, proof)
        put(BLOB_RAM + 0x7254, 1)
        check('complete resident prefix retained', BLOB_RAM, blob)
        check('complete shop floor owner retained', owner, expected)
        for at in guards:
            check('fixture guard', at, edge)
        check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        put(BLOB_RAM + 0x7254, 1)
        for at, value in globals_before.items():
            debug.write_memory(at, value)
    call(0x8009C040, [allocation])
    return {'shop_floor_register_windows': windows, 'native_reserve_selections': 8,
            'complete_native_floor_selections': 8, 'native_block_lookup_executed': True,
            'sold_model_removal_executed': False, 'ordinary_shop_controls_tested': False,
            'saved_data_written': False, 'requires_checkpoint_restore': True}
