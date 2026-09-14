"""Native full-asset banks through the real allocator/DMA, using a disposable heap."""
import json
from pathlib import Path
import struct

from aflib import by_vrom, sha256
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_villager_assets_runtime import ABI, BLOB, BLOB_RAM, FLAGS, GROWTH, RESIDENT


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or report.get('runtime_abi') != ABI:
        raise ValueError('Asset check needs the current ABI-51 cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)
    edge = b'V3AS'*4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'villager_assets_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Native asset check failed: '+label)

    def call(address, arguments=(), expected=None):
        result = debug.call(f'{address:08X}', list(arguments), return_address=MODULE_RAM+0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native asset call result')
        return result['return_value']

    check('complete startup resident prefix', BLOB_RAM, blob[:RESIDENT])
    check('startup installed', 0x8019ACD0, bytes.fromhex('00000001'))
    check('relocated growth permissions', BLOB_RAM+GROWTH, files[0xE0D000].extract(rom))
    check('all move-in flags disabled', BLOB_RAM+FLAGS, bytes(20))
    size = 0x6000
    allocation = call(0x8009BFC0, (size,))
    if allocation & 15 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-size:
        raise ValueError('Native asset fixture could not allocate its bounded heap')
    arena, destination = allocation+16, allocation+0x1900
    guards = (allocation, arena+0x1824, destination-16, destination+0x2800,
              allocation+size-16, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards:
        debug.write_memory(at, edge)
    try:
        # Native model, installed pilot, shortest mouthless texture, both new
        # models, largest accessory, last valid bank, and rejection boundaries.
        for bank in (133, 426, 418, 430, 431, 443, 447, 448, 0xFFFF):
            memory = bytearray(0x1824)
            struct.pack_into('>2I', memory, 0x1800, destination, destination+0x2800)
            debug.write_memory(arena, memory)
            debug.write_memory(destination, b'\xA5'*0x2800)
            valid = bank < 448
            call(0x800C5B74, (arena, bank), int(valid))
            if valid:
                start, end = struct.unpack_from('>II', blob, 0x1000+bank*8)
                entry = next(e for e in files.values() if e.vstart <= start < end <= e.vend)
                data = entry.extract(rom)[start-entry.vstart:end-entry.vstart]
                struct.pack_into('>H', memory, 0, bank)
                struct.pack_into('>4I', memory, 4, destination, destination, start, len(data))
                struct.pack_into('>H', memory, 0x50, 1)
                struct.pack_into('>I', memory, 0x17F4, 1)
                struct.pack_into('>I', memory, 0x1800, (destination+len(data)+15) & ~15)
                check(f'bank {bank} complete data and unused buffer tail', destination,
                      data+b'\xA5'*(0x2800-len(data)))
            else:
                check(f'rejected bank {bank} leaves destination untouched', destination, b'\xA5'*0x2800)
            check(f'bank {bank} native status and arena ownership', arena, memory)
        memory = bytearray(0x1824)
        struct.pack_into('>2I', memory, 0x1800, destination, destination+0x2800)
        debug.write_memory(arena, memory)
        call(0x800C5AA0, (arena, arena, 0x123401BF), 1)
        start, end = struct.unpack_from('>II', blob, 0x1000+447*8)
        struct.pack_into('>h', memory, 0, -447)
        struct.pack_into('>4I', memory, 4, 0, destination, start, end-start)
        memory[0x53] = 1
        struct.pack_into('>I', memory, 0x1800, (destination+end-start+15) & ~15)
        check('signed low-halfword bank argument', arena, memory)
        for at in guards:
            check('fixture guard', at, edge)
        check('complete resident prefix after loading', BLOB_RAM, blob[:RESIDENT])
        for at, marker in ((0x8019C8D0, 'AF32C0DE'), (0x8046BFF0, 'AF33C0DE'),
                           (0x8046C350, 'AF53C0DE'), (0x80470000, 'AF46C0DE'),
                           (0x80472850, 'AF46C0DE')):
            check('resident/save/furniture guard', at, bytes.fromhex(marker)*4)
        check('no faulted thread', 0x8003CE34, bytes(4))
    finally:
        call(0x8009C040, (allocation,))
    return {'native_object_loads': 7, 'rejected_indices': 2,
            'accessories_attached': False, 'saved_data_written': False,
            'requires_checkpoint_restore': True}
