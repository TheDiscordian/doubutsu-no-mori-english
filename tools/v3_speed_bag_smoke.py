"""Exercise converted speed-bag animation in private native-engine storage."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from runtime_layout import MODULE_RAM, RESERVATION, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_import_catalog import ROOT


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    build = json.loads((path.parent/'build.json').read_text())
    art_path = ROOT/'build/v3-speed-bag-art-01'
    art = json.loads((art_path/'art.json').read_text())
    asset = (art_path/'speed-bag.n64obj.bin').read_bytes()
    if (sha256(rom) != build['output_sha256'] or len(asset) != 3728 or
            sha256(asset) != '3b10054b80021c00a5a12d98aeb4afcd76b7201ad68f55c1ac77c1b3a7844893' or
            art['object_sha256'] != sha256(asset) or art['runtime_installed']):
        raise ValueError('Native speed-bag probe requires the checked converted artifact')
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    original = by_vrom(native)[CODE_VROM].extract(native)
    files = by_vrom(rom)
    current = files[CODE_VROM].extract(rom)
    first, last = 0x80051A80, 0x80052D20
    engine = original[first-CODE_RAM:last-CODE_RAM]
    if current[first-CODE_RAM:last-CODE_RAM] != engine:
        raise ValueError('Native keyframe engine changed')
    prefix = files[BLOB].extract(rom)[:0xC000]
    edge = b'V3SB'*4

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'speed_bag_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Speed-bag native mismatch: '+label+'; observed '+actual.hex())

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=(first, engine) if first <= address < last else None)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native speed-bag animation return')
        return result['return_value']

    check('complete retained keyframe engine', first, engine)
    check('complete current resident prefix', BLOB_RAM, prefix)
    state_before = debug.read_memory(0x8046C000, 864)
    segments = debug.read_memory(0x801458A0, 64)
    allocation = call(0x8009BFC0, [0x1700])
    if allocation % 16 or not MODULE_RAM+RESERVATION <= allocation <= 0x80400000-0x1700:
        raise ValueError('No bounded private speed-bag allocation')
    bank, state, joint, morph = (allocation+n for n in (0x10, 0x1440, 0x14E0, 0x1520))
    guards = (allocation, allocation+0x1410, state-16, state+0x70,
              joint-16, joint+18, morph-16, morph+18, allocation+0x16F0,
              TEST_STACK-0x800, TEST_STACK+0x40)
    debug.write_memory(allocation, b'\xA5'*0x1700)
    for address in guards: debug.write_memory(address, edge)
    debug.write_memory(bank, asset)
    try:
        debug.write_memory(0x801458B8, struct.pack('>I', bank-0x80000000))
        animation = 0x06000000+art['headers']['animation']['native_offset']
        skeleton = 0x06000000+art['headers']['skeleton']['native_offset']
        call(0x80052228, [state, skeleton, animation, joint, morph])
        call(0x80052298, [state, animation, 0])
        check('actual native header pointer resolution', state+0x18,
              struct.pack('>II', bank+(skeleton & 0xFFFFFF), bank+(animation & 0xFFFFFF)))
        check('three-vector native joint and morph destinations', state+0x24, struct.pack('>II', joint, morph))
        for frame, angles in ((1, (0, 0, 0)), (57, (0, -546, 54)), (69, (0, 0, 0))):
            debug.write_memory(state+12, struct.pack('>ff', 0.0, float(frame)))
            call(0x800528D4, [state], 1 if frame == 69 else 0)
            check(f'native root and both-joint pose at frame {frame}', joint,
                  struct.pack('>9h', 800, 6508, 800, 0, 0, -16384, *angles))
            check(f'zero-speed frame {frame} retained', state+16, struct.pack('>f', float(frame)))
        check('complete converted object retained', bank, asset)
        check('unused model-bank capacity retained', bank+len(asset), b'\xA5'*(0x1400-len(asset)))
        check('morph array unused in ordinary non-morph evaluation', morph, b'\xA5'*18)
        for address in guards: check('private allocation/stack guard', address, edge)
    finally:
        debug.write_memory(0x801458A0, segments)
    check('all native segment bases restored', 0x801458A0, segments)
    check('all save runtime bytes retained', 0x8046C000, state_before)
    check('complete current prefix retained', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_speed_bag_rig_and_keyframe_evaluation': True,
            'frames': [1, 57, 69], 'installed_item_or_interaction': False,
            'gpu_rendering_or_audio_tested': False, 'requires_checkpoint_restore': True}
