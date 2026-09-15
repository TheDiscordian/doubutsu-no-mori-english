"""One isolated native check of installed fire DMA, full rigs, draws, and readers."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_import_storage import PACKAGE, PACKAGE_RAM, ROWS_RAM, slot
from v3_npc_draw_smoke import boot_proofs
from v3_fire import ENTRIES, RAM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_bytes())
    if sha256(rom) != report['output_sha256'] or report['runtime_abi'] != 70 or not report.get('fire'):
        raise ValueError('Fire probe requires the current full ABI 70 cartridge')
    blob = by_vrom(rom)[BLOB].extract(rom)
    callbacks = report['fire']['code']

    def check(label, at, expected):
        observed = debug.read_memory(at, len(expected))
        record({'fire_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
            'assertion': 'passed' if observed == expected else 'failed',
            'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected:
            raise ValueError('Native fire mismatch: ' + label + '; observed ' + observed.hex())

    def call(at, args, expected=None, proof=None):
        result = debug.call(f'{at:08X}', args, return_address=MODULE_RAM + 0x6480, verified_code=proof)
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Incorrect native fire reader/callback result')
        return result['return_value']

    check('complete current prefix', BLOB_RAM, blob[:0xC000])
    at = PACKAGE + RAM - PACKAGE_RAM
    check('installed upper-memory fire callbacks', RAM, blob[at:at + callbacks['bytes']])
    pool = report['furniture']['bank_pool']
    banks = [pool['data'], pool['data'] + pool['bank_bytes']]
    owner = debug.read_memory(0x80100DF0, 32)
    if struct.unpack_from('>II', owner, 8) != (0x80936710, 0x8094F610):
        raise ValueError('Changed furniture bank owner identity')
    bank_before = [debug.read_memory(b, pool['bank_bytes']) for b in banks]
    indices = int(report['furniture']['expanded_tables']['bank_index_ram'], 16) + 1239
    index_before = debug.read_memory(indices, 2)
    segments = debug.read_memory(0x801458A0, 64)
    matrix_owner = debug.read_memory(0x801462B0, 8)
    saved = debug.read_memory(0x8046C000, 864)
    allocation = call(0x8009BFC0, [0x20040])
    if allocation & 15 or not MODULE_RAM + 0x8000 <= allocation <= 0x80400000 - 0x20040:
        raise ValueError('No bounded isolated fire allocation')
    live, actor0, actor1, gfx, game, matrices, opa, xlu, bridge, scratch = (
        allocation + n for n in (0x10, 0x19200, 0x19A00, 0x1A200, 0x1A600,
                                 0x1C800, 0x1D000, 0x1E100, 0x1F200, 0x1F400))
    guard = b'V3FR' * 4
    guards = (allocation, actor0 - 16, actor0 + 0x740, actor1 - 16, actor1 + 0x740,
        gfx - 16, gfx + 0x300, game - 16, game + 0x1EC0, matrices - 16, matrices + 0x400,
        opa - 16, opa + 0x1000, xlu - 16, xlu + 0x1000, bridge - 16, bridge + 64,
        scratch - 16, scratch + 128, allocation + 0x20030, TEST_STACK + 0x40)
    debug.write_memory(allocation, b'\xA5' * 0x20040)
    for a in guards: debug.write_memory(a, guard)
    debug.write_memory(0x80100E00, struct.pack('>I', live))
    debug.write_memory(live + 0x18D68, struct.pack('>2I', *banks))
    public = next(r for r in report['furniture']['expanded_tables']['public_entries']
                  if r['name'] == 'af_v3_furniture_import_dma')
    targets = [callbacks['symbols'][name] for name in ENTRIES] + [public['entry']]
    jumps = b''.join(struct.pack('>II', 0x08000000 | (target >> 2 & 0x3FFFFFF), 0) for target in targets)
    debug.write_memory(bridge, jumps)
    for address, proof in boot_proofs(rom).items():
        if address in (0x8002FE00, 0x80034CE0): call(address, [bridge, len(jumps)], proof=proof)
    debug.write_memory(gfx, bytes(0x300))
    debug.write_memory(game, bytes(0x1EC0))
    debug.write_memory(game, struct.pack('>I', gfx))
    identity = struct.pack('>16f', *(1 if i in (0, 5, 10, 15) else 0 for i in range(16)))
    debug.write_memory(game + 0x1E5C, identity)
    debug.write_memory(0x801462B0, struct.pack('>II', matrices, matrices))
    checks = []
    for n, actor in enumerate((actor0, actor1)):
        row = report['fire']['imports'][n]
        item, bank = int(row['item_id'], 16), banks[n]
        index = row['runtime_index']
        size = row['object_bytes']
        asset_at = int(row['object_vrom'], 16) - BLOB
        asset = blob[asset_at:asset_at + size]
        debug.write_memory(bank, b'\xA5' * pool['bank_bytes'])
        debug.write_memory(indices + n, b'\xFF')
        call(bridge + 48, [index, item | 3, bank, n], expected=1, proof=(bridge, jumps))
        check(row['name'] + ' complete actual DMA and bank padding', bank, asset + b'\xA5' * (pool['bank_bytes'] - size))
        check(row['name'] + ' actual bank registration', indices + n, bytes((n,)))
        debug.write_memory(0x801458B8, struct.pack('>I', bank - 0x80000000))
        debug.write_memory(actor, bytes(0x210) + b'\xA5' * 0x500 + bytes(0x30))
        debug.write_memory(actor + 0x714, struct.pack('>fff', 1, 1, 1))
        call(bridge + n * 24, [actor, bank], proof=(bridge, jumps))
        rig, anim = ((0x1F38, 0x1F00), (0x1780, 0x1748))[n]
        check(row['name'] + ' complete resolved rig headers', actor + 0x14C, struct.pack('>II', bank + rig, bank + anim))
        check(row['name'] + ' joint and morph buffers', actor + 0x158, struct.pack('>II', actor + 0x1A4, actor + 0x1DA))
        check(row['name'] + ' constructor speed and repeat mode', actor + 0x140, struct.pack('>ffI', .5, 1.5, 1))
        call(bridge + n * 24 + 8, [actor, live, game, bank], proof=(bridge, jumps))
        check(row['name'] + ' native move keeps half-speed', actor + 0x140, struct.pack('>ff', .5, 2))
        call(0x801969C8, [scratch, 16, item], expected=1)
        check(row['name'] + ' complete English name', scratch, row['name'].encode().ljust(16, b' '))
        call(0x800C0194, [item], expected=row['price'])
        call(0x800BE69C, [item | 3], expected=2 if n else 0)
        for rotation in (0, 3):
            call(0x800BE72C, [item | rotation, 7, 9, scratch], expected=2 if n else 0)
            cells = [(1, 7, 9), (1, 8, 9), (1, 8, 10), (1, 7, 10)] if n else [(1, 7, 9)] + [(0, 7, 9)] * 3
            check(row['name'] + ' complete native placement footprint', scratch, b''.join(struct.pack('>3i', *c) for c in cells))
        # Catalogue uses generic frame 3; room uses play frame 10. The matrix
        # bank always follows generic parity. Submit both without reusing arena.
        debug.write_memory(game + 0xA0, struct.pack('>I', 3))
        debug.write_memory(game + 0x1EA0, struct.pack('>I', 10))
        debug.write_memory(gfx + 0x298, struct.pack('>II', opa, opa + 0xFF8))
        debug.write_memory(gfx + 0x2A8, struct.pack('>II', xlu, xlu + 0xFF8))
        matrix = actor + 0x210 + 0x280
        for room, frame in ((0, 3), (live, 10)):
            debug.write_memory(matrices, identity)
            head, tail = struct.unpack('>II', debug.read_memory(gfx + 0x298, 8))
            xhead = struct.unpack('>I', debug.read_memory(gfx + 0x2A8, 4))[0]
            data = (tail - 176) & ~15
            call(bridge + n * 24 + 16, [actor, room, game, bank], proof=(bridge, jumps))
            check(row['name'] + ' complete rig opaque commands', head, struct.pack('>10I',
                0xDA380003, data, 0xDB060034, matrix, 0xDA380003, matrix,
                0xDE000000, 0x06001070 if n else 0x06001360, 0xDA380003, matrix + 64))
            check(row['name'] + ' billboard flame and scroll segment', xhead, struct.pack('>10I',
                0xDA380003, data, 0xDB060024, data + 128, 0xDB060034, matrix,
                0xDA380003, data + 64, 0xDE000000, 0x06001660 if n else 0x06001E20))
            check(row['name'] + ' exact arena consumption', gfx + 0x298, struct.pack('>II', head + 40, data))
            check(row['name'] + ' balanced native matrix stack', 0x801462B4, struct.pack('>I', matrices))
            y = (-frame * (6 if n else 12) // 4) & 4095
            x = -frame & 4095 if n else 0
            scroll = struct.pack('>10I', 0xE8000000, 0, 0xF2000000 | y, 124 << 12 | (y + 252) & 4095,
                0xE8000000, 0, 0xF2000000 | x << 12, 0x1000000 | ((x + (252 if n else 124)) & 4095) << 12 | 124,
                0xDF000000, 0)
            check(row['name'] + ' actual context-specific two-tile scroll', data + 128, scroll)
            if checks: check('earlier submitted scroll remains immutable', *checks[-1])
            checks.append((data + 128, scroll))
        check(row['name'] + ' unused actor matrix bank retained', actor + 0x210, b'\xA5' * 0x280)
        check(row['name'] + ' unused joint matrices retained', matrix + 128, b'\xA5' * (0x280 - 128))
        checks.clear()  # The next actor's private test starts a fresh frame arena.
    for address in guards: check('private allocation and stack guard', address, guard)
    for n, bank in enumerate(banks): debug.write_memory(bank, bank_before[n])
    debug.write_memory(indices, index_before)
    debug.write_memory(0x801458A0, segments)
    debug.write_memory(0x801462B0, matrix_owner)
    debug.write_memory(0x80100DF0, owner)
    check('restored native owner descriptor', 0x80100DF0, owner)
    check('complete saved runtime retained', 0x8046C000, saved)
    check('complete prefix retained', BLOB_RAM, blob[:0xC000])
    for address in (0x80483FF0, 0x804A0000): check('resident code/table guard', address, bytes.fromhex('AFACC0DE') * 4)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'actual_fire_dma': True, 'installed_full_rig_callbacks': True,
        'native_billboard_and_scroll_commands': True, 'four_cell_native_readers': True,
        'gpu_rendering_tested': False, 'ordinary_acquisition_or_persistence_tested': False,
        'requires_checkpoint_restore': True}
