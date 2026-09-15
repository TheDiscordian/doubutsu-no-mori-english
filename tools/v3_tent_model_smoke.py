"""Bounded silent execution of the installed tent callbacks and item readers."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_npc_draw_smoke import boot_proofs
from v3_import_storage import PACKAGE, PACKAGE_RAM, PACKAGE_SIZE, ROWS, ROWS_RAM, ITEMS, ITEMS_RAM, slot
import v3_tent_model as tent


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_bytes())
    if report['runtime_abi'] != 69 or sha256(rom) != report['output_sha256']:
        raise ValueError('Tent probe requires the complete current ABI 69 cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)
    callbacks = report['tent_model']['code']
    at = PACKAGE + tent.RAM - PACKAGE_RAM
    code = blob[at:at + callbacks['bytes']]
    native = blob[ROWS + slot(0x336C) * 80:ROWS + (slot(0x336C) + 1) * 80]
    item = blob[ITEMS + slot(0x336C) * 32:ITEMS + (slot(0x336C) + 1) * 32]
    asset = blob[0x24E000:0x24E000 + 4288]
    if (sha256(code) != callbacks['sha256'] or sha256(asset) != tent.ASSET_SHA
            or sha256(blob[PACKAGE:PACKAGE + PACKAGE_SIZE]) != report['tent_model']['package_sha256']):
        raise ValueError('Changed installed tent resources')

    def check(label, address, expected):
        observed = debug.read_memory(address, len(expected))
        record({'tent_model_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if observed == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected:
            raise ValueError('Native tent mismatch: ' + label + '; observed ' + observed.hex())

    proofs = boot_proofs(rom)
    def call(address, args, proof=None, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480,
                            verified_code=proof)
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Incorrect native tent reader return')
        return result['return_value']

    check('complete installed callbacks', tent.RAM, code)
    check('complete installed callback table', tent.VTABLE, bytes.fromhex(report['tent_model']['vtable_hex']))
    check('complete enabled tent profile', ROWS_RAM + slot(0x336C) * 80, native)
    check('complete English item row', ITEMS_RAM + slot(0x336C) * 32, item)
    state_before = debug.read_memory(0x8046C000, 864)
    allocation = call(0x8009BFC0, [0x3020])
    if allocation % 16 or not MODULE_RAM + 0x8000 <= allocation <= 0x80400000 - 0x3020:
        raise ValueError('No bounded private tent callback allocation')
    origin = (allocation + 31) & ~31
    bank, actor, other, gfx, game, arena, stubs = (origin + n for n in
        (0x20, 0x1120, 0x18A0, 0x2020, 0x2360, 0x2420, 0x2860))
    edge = b'V3TN' * 4
    guards = (allocation, bank + 4288, actor - 16, actor + 0x740,
              other - 16, other + 0x740, gfx - 16, gfx + 0x300,
              game - 16, game + 0x80, arena - 16, arena + 0x400,
              stubs - 16, stubs + 32, origin + 0x2FF0, TEST_STACK + 0x40)
    debug.write_memory(allocation, b'\xA5' * 0x3020)
    for address in guards:
        debug.write_memory(address, edge)
    debug.write_memory(bank, asset)
    # Lower-memory jump stubs use the existing verified-code mechanism. The
    # actual callbacks remain at their installed Expansion Pak addresses.
    names = ('ct', 'mv', 'dw', 'dt')
    jumps = b''.join(struct.pack('>II', 0x08000000 |
        (callbacks['symbols']['af_v3_tent_model_' + name] >> 2 & 0x3FFFFFF), 0) for name in names)
    debug.write_memory(stubs, jumps)
    for address in (0x8002FE00, 0x80034CE0):
        call(address, [stubs, len(jumps)], proofs[address])

    def callback(which, target):
        call(stubs + names.index(which) * 8, [target, 0, game, bank], (stubs, jumps))

    call(0x801969C8, [game + 16, 16, 0x336C], expected=1)
    check('full English name through installed native reader', game + 16, b'tent model      ')
    call(0x800A5630, [0x336C], expected=10)
    call(0x800C0194, [0x336C], expected=2550)
    call(0x800BE69C, [0x336F], expected=0)
    debug.write_memory(actor + 0x12C, b'\x00')
    debug.write_memory(other + 0x12C, b'\x01')
    callback('ct', actor)
    callback('ct', other)
    check('constructor initial off fade', actor + 0x1A4, bytes(4))
    check('constructor independent initial on fade', other + 0x1A4, struct.pack('>f', 1))
    debug.write_memory(actor + 0x12C, b'\x01')
    debug.write_memory(other + 0x12C, b'\x00')
    callback('mv', actor)
    callback('mv', other)
    check('native increasing donor step', actor + 0x1A4, struct.pack('>f', .1))
    check('native independent decreasing donor step', other + 0x1A4, struct.pack('>f', .9))
    debug.write_memory(game, struct.pack('>I', gfx))
    debug.write_memory(gfx + 0x298, struct.pack('>II', arena, arena + 0x400))
    palettes = []
    for target, frame in ((actor, .1), (other, .9)):
        head, tail = struct.unpack('>II', debug.read_memory(gfx + 0x298, 8))
        data = (tail - 96) & ~31
        callback('dw', target)
        check('four complete model parts and per-frame palette segment', head,
            struct.pack('>12I', 0xDA380003, data, 0xDB060020, data + 64,
                0xDE000000, 0x06000C50, 0xDE000000, 0x06000D18,
                0xDE000000, 0x06000E00, 0xDE000000, 0x06000FF0))
        check('bounded native arena endpoints', gfx + 0x298, struct.pack('>II', head + 48, data))
        on = struct.unpack_from('>16H', asset, 32)
        off = struct.unpack_from('>16H', asset, 64)
        fade = struct.unpack('>f', struct.pack('>f', frame))[0]
        colours = [((a & 1) | sum(int((a >> s & 31) + fade * ((b >> s & 31) - (a >> s & 31))) << s
                    for s in (1, 6, 11))) for a, b in zip(off, on)]
        palette = struct.pack('>16H', *colours)
        check('all native interpolated palette colours', data + 64, palette)
        palettes.append((data + 64, palette))
    callback('dt', actor)
    callback('ct', actor)
    check('reused actor starts fully on', actor + 0x1A4, struct.pack('>f', 1))
    callback('dt', other)
    check('destroy resets private fade', other + 0x1A4, bytes(4))
    for at, palette in palettes:
        check('submitted palette survives actor destruction and reuse', at, palette)
    check('complete source asset unchanged', bank, asset)
    for address in guards:
        check('private allocation and stack guard', address, edge)
    check('complete save runtime retained', 0x8046C000, state_before)
    check('complete current resident prefix retained', BLOB_RAM, blob[:0xC000])
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_tent_model_callbacks': True, 'installed_upper_memory_code_executed': True,
        'native_item_readers': True, 'independent_instance_palettes': True,
        'actual_native_draw_commands': True, 'gpu_rendering_tested': False,
        'ordinary_acquisition_or_persistence_tested': False, 'requires_checkpoint_restore': True}
