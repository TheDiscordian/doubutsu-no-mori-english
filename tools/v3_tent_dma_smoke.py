"""Actual installed tent DMA into its Expansion Pak bank, with isolated ownership."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB, BLOB_RAM
from v3_import_storage import ROWS_RAM, slot
from v3_npc_draw_smoke import boot_proofs


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_bytes())
    if sha256(rom) != report['output_sha256'] or not report['tent_model'].get('loader'):
        raise ValueError('Tent DMA probe requires the repaired current cartridge')
    blob = by_vrom(rom)[BLOB].extract(rom)
    helper = report['furniture']['expanded_tables']['expanded_code']
    code = blob[0x5800:0x5800 + helper['bytes']]
    if sha256(code) != helper['sha256']:
        raise ValueError('Changed installed furniture DMA code')

    def check(label, address, expected):
        observed = debug.read_memory(address, len(expected))
        record({'tent_dma_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if observed == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected:
            raise ValueError('Native tent DMA mismatch: ' + label)

    def call(address, args, expected=None, proof=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480, verified_code=proof)
        if expected is not None:
            result['assertion'] = 'passed' if result['return_value'] == expected else 'failed'
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Incorrect native tent DMA result')
        return result['return_value']

    check('complete current resident prefix', BLOB_RAM, blob[:0xC000])
    check('complete repaired resident furniture helper', BLOB_RAM + 0x5800, code)
    owner = debug.read_memory(0x80100DF0, 32)
    if struct.unpack_from('>II', owner, 8) != (0x80936710, 0x8094F610):
        raise ValueError('Unrecognised native furniture owner descriptor')
    pool = report['furniture']['bank_pool']
    bank, size = pool['data'], pool['bank_bytes']
    bank_before = debug.read_memory(bank, size)
    index = int(report['furniture']['expanded_tables']['bank_index_ram'], 16) + 1243
    index_before = debug.read_memory(index, 1)
    row = ROWS_RAM + slot(0x336C) * 80
    profile_before = debug.read_memory(row, 80)
    state_before = debug.read_memory(0x8046C000, 864)
    allocation = call(0x8009BFC0, [0x19040])
    if allocation & 15 or not MODULE_RAM + 0x8000 <= allocation <= 0x80400000 - 0x19040:
        raise ValueError('No bounded isolated native bank-owner table')
    live, bridge = allocation + 16, allocation + 0x18F20
    edge = b'V3TD' * 4
    debug.write_memory(allocation, bytes(0x19040))
    for at in (allocation, allocation + 0x19030, bridge - 16, bridge + 8):
        debug.write_memory(at, edge)
    # Only the descriptor's loaded-owner pointer and bank slot are fixture data.
    # The actual resident gate, bank checks, and native ROM DMA execute unchanged.
    debug.write_memory(0x80100E00, struct.pack('>I', live))
    debug.write_memory(live + 0x18D68, struct.pack('>I', bank))
    public = next(r for r in report['furniture']['expanded_tables']['public_entries']
                  if r['name'] == 'af_v3_furniture_import_dma')
    check('actual public DMA bridge', public['entry'], bytes.fromhex(public['after']))
    stub = struct.pack('>II', 0x08000000 | ((public['entry'] >> 2) & 0x3FFFFFF), 0)
    debug.write_memory(bridge, stub)
    for address, proof in boot_proofs(rom).items():
        if address in (0x8002FE00, 0x80034CE0):
            call(address, [bridge, len(stub)], proof=proof)
    payload = blob[0x24E000:0x24E000 + 4288]
    expected = payload + b'\xA5' * (size - len(payload))
    debug.write_memory(bank, b'\xA5' * size)
    debug.write_memory(index, b'\xFF')
    call(bridge, [1243, 0x336C, bank, 0], expected=1, proof=(bridge, stub))
    check('complete actual model DMA and untouched bank padding', bank, expected)
    check('successful DMA records its native bank index', index, b'\x00')
    debug.write_memory(bank, b'\xA5' * size)
    call(bridge, [1243, 0x336F, bank, 0xFFFFFFFF], expected=1, proof=(bridge, stub))
    check('existing-bank rotated reload keeps all parts and palettes', bank, expected)
    for label, offset, replacement in (('disabled profile', 4, bytes(4)),
            ('unreviewed callback table', 72, struct.pack('>I', 0x80483704))):
        debug.write_memory(row + offset, replacement)
        call(bridge, [1243, 0x336C, bank, 0], expected=0, proof=(bridge, stub))
        check(label + ' leaves loaded bank intact', bank, expected)
        debug.write_memory(row, profile_before)
    for at in (allocation, allocation + 0x19030, bridge - 16, bridge + 8):
        check('private owner and bridge guard', at, edge)
    check('complete save runtime retained', 0x8046C000, state_before)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    debug.write_memory(bank, bank_before)
    debug.write_memory(index, index_before)
    debug.write_memory(0x80100DF0, owner)
    check('complete original owner descriptor restored', 0x80100DF0, owner)
    check('complete resident prefix retained', BLOB_RAM, blob[:0xC000])
    call(0x8009C040, [allocation])
    return {'actual_upper_memory_tent_dma': True, 'native_existing_bank_reload': True,
        'disabled_and_unreviewed_callback_rejection': True, 'ordinary_bank_acquisition_tested': False,
        'gpu_or_hardware_tested': False, 'requires_checkpoint_restore': True}
