"""Private native callbacks/rig check; no installed item or physical audio."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_import_catalog import ROOT
from v3_npc_draw_smoke import boot_proofs
from v3_speed_bag import ENGINE, SOURCE_FILES, validate_calls


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    build = json.loads((path.parent/'build.json').read_text())
    folder = ROOT/'build/v3-speed-bag-callbacks-01'
    report = json.loads((folder/'callbacks.json').read_text())
    callbacks = (folder/'code.bin').read_bytes()
    asset = (ROOT/'build/v3-speed-bag-art-01/speed-bag.n64obj.bin').read_bytes()
    sound_hook = MODULE_RAM+0x6500
    if (sha256(rom) != build['output_sha256'] or report['sha256'] != sha256(callbacks)
            or report['sound_entry'] != sound_hook or report['runtime_installed']
            or report['source_sha256'] != {p: sha256((ROOT/p).read_bytes()) for p in SOURCE_FILES}
            or sha256(asset) != '3b10054b80021c00a5a12d98aeb4afcd76b7201ad68f55c1ac77c1b3a7844893'):
        raise ValueError('Changed native speed-bag fixture artifact')
    validate_calls(callbacks, (folder/'relocations.txt').read_text(),
                   {**ENGINE, 'af_v3_speed_bag_sound': sound_hook})
    native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    original = by_vrom(native)[CODE_VROM].extract(native)
    files = by_vrom(rom)
    current = files[CODE_VROM].extract(rom)
    windows = ((0x80051A80, 0x80053780), (0x8009ADA8, 0x8009AE00),
               (0x800E13C4, 0x800E14D4))
    proofs = {}
    for first, last in windows:
        expected = original[first-CODE_RAM:last-CODE_RAM]
        if current[first-CODE_RAM:last-CODE_RAM] != expected:
            raise ValueError('Native speed-bag engine window changed')
        proofs[first] = expected
    for at in (0x8002FE00, 0x80034CE0):
        base, data = boot_proofs(rom)[at]
        if (base, data) != boot_proofs(native)[at]:
            raise ValueError('Changed complete native cache function')
        proofs[base] = data

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'speed_bag_callback_check': label, 'address': f'{address:08X}',
                'bytes': len(expected), 'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Native speed-bag mismatch: '+label+'; observed '+actual.hex())

    def call(address, args, proof=None):
        if proof is None:
            proof = next(((at, data) for at, data in proofs.items()
                          if at <= address < at+len(data)), None)
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM+0x6480,
                            verified_code=proof)
        record(result)
        return result['return_value']

    for at, expected in proofs.items(): check('retained native callback dependency', at, expected)
    prefix = files[BLOB].extract(rom)[:0xC000]
    check('complete current resident prefix', BLOB_RAM, prefix)
    state_before = debug.read_memory(0x8046C000, 864)
    segments = debug.read_memory(0x801458A0, 64)
    allocation = call(0x8009BFC0, [0x3000])
    if allocation % 16 or not MODULE_RAM+0x8000 <= allocation <= 0x80400000-0x3000:
        raise ValueError('No bounded private callback allocation')
    bank, actor, gfx, game, display, pool, code = (
        allocation+n for n in (0x10, 0x1440, 0x1BA0, 0x1EC0, 0x2000, 0x2200, 0x2600))
    key = actor+0x134
    sound_record = MODULE_RAM+0x6580
    edge = b'V3SC'*4
    guards = (allocation, allocation+0x1410, actor-16, actor+0x740,
              gfx-16, gfx+0x308, game-16, game+0xE0,
              display-16, display+0x100, pool-16, pool+0x100,
              code-16, code+len(callbacks), allocation+0x2FF0,
              TEST_STACK-0x800, TEST_STACK+0x40)
    debug.write_memory(allocation, b'\xA5'*0x3000)
    for at in guards: debug.write_memory(at, edge)
    debug.write_memory(bank, asset)
    debug.write_memory(code, callbacks)
    # Private sound observer records count, full position pointer, and pre-reset frame.
    observer = struct.pack('>10I', 0x3C080000 | (sound_record >> 16),
                           0x35080000 | (sound_record & 65535), 0x8D090000,
                           0x25290001, 0xAD090000, 0xAD040004,
                           0x8C8A013C, 0xAD0A0008, 0x03E00008, 0)
    debug.write_memory(sound_hook, observer)
    debug.write_memory(sound_record, bytes(12))
    for at, length in ((code, len(callbacks)), (sound_hook, len(observer))):
        call(0x8002FE00, [at, length])
        call(0x80034CE0, [at, length])
    entries = {name: code+offset for name, offset in report['entry_offsets'].items()}

    def callback(which):
        call(entries['af_v3_speed_bag_'+which], [actor, 0, game, bank], (code, callbacks))

    def playback(frame, speed, changed, state=0):
        debug.write_memory(key+12, struct.pack('>ff', speed, frame))
        debug.write_memory(actor+0x12D, bytes((changed,)))
        debug.write_memory(actor+0x3C, struct.pack('>h', state))
        debug.write_memory(sound_record, bytes(12))
        callback('mv')

    try:
        debug.write_memory(0x801458B8, struct.pack('>I', bank-0x80000000))
        callback('ct')
        check('constructor resolves both actual rig headers', key+0x18, struct.pack('>II', bank+0xE84, bank+0xE58))
        check('constructor native joint and morph buffers', key+0x24, struct.pack('>II', actor+0x1A4, actor+0x1DA))
        check('constructor clears speed and switch change', key+12, bytes(4))
        check('constructor clears changed only', actor+0x12C, bytes.fromhex('a500a5a5a5a5a5a5'))
        for frame, angles in ((1, (0, 0, 0)), (57, (0, -546, 54)), (69, (0, 0, 0))):
            playback(frame, 0, 0)
            check(f'native full joint pose at frame {frame}', actor+0x1A4,
                  struct.pack('>9h', 800, 6508, 800, 0, 0, -16384, *angles))
            check('idle does not start sound', sound_record, bytes(12))
        playback(1, 0, 1)
        check('first hit uses full actor position before frame reset', sound_record, struct.pack('>IIf', 1, actor+8, 1))
        check('first hit evaluates then starts half-speed', key+12, struct.pack('>ff', .5, 1))
        playback(20, .5, 0)
        check('running update evaluates twice', key+12, struct.pack('>ff', .5, 21))
        playback(20, .5, 1)
        check('running retrigger sound follows both evaluations', sound_record, struct.pack('>IIf', 1, actor+8, 21))
        check('running retrigger resets and evaluates at existing speed', key+12, struct.pack('>ff', .5, 1.5))
        playback(68.5, .5, 0)
        check('end-of-animation stop remains at last frame', key+12, struct.pack('>ff', .5, 69))
        for state in (5, 6, 13, 15):
            playback(1, 0, 1, state)
            check(f'native transition {state} suppresses sound', sound_record, bytes(12))
            check('silent hit still animates', key+12, struct.pack('>ff', .5, 1))
        for state in (12, 14):
            playback(1, 0, 1, state)
            check(f'native movement {state} is not a donor transition', sound_record, struct.pack('>IIf', 1, actor+8, 1))
        check('owner retains responsibility for clearing changed', actor+0x12D, b'\x01')
        playback(57, 0, 0)
        for parity in (0, 1):
            debug.write_memory(game, bytes(0xE0))
            debug.write_memory(game, struct.pack('>I', gfx))
            debug.write_memory(game+0xA0, struct.pack('>I', parity))
            debug.write_memory(gfx, bytes(0x308))
            debug.write_memory(gfx+0x298, struct.pack('>II', display, pool+0x100))
            debug.write_memory(gfx+0x2A8, struct.pack('>I', display+0x80))
            debug.write_memory(actor+0x210, b'\xA5'*0x500)
            callback('dw')
            matrix = actor+0x210+parity*0x280
            check(f'draw parity {parity} emits base transform and both complete joints', display,
                  struct.pack('>12I', 0xDA380003, pool+0xC0, 0xDB060034, matrix, 0xDA380003, matrix,
                              0xDE000000, 0x06000A48, 0xDA380003, matrix+64, 0xDE000000, 0x06000D48))
            check('draw advances only expected opaque commands', gfx+0x298, struct.pack('>II', display+48, pool+0xC0))
            check('native skeleton sets translucent segment only', display+0x80, struct.pack('>II', 0xDB060034, matrix))
            check('draw advances expected translucent segment', gfx+0x2A8, struct.pack('>I', display+0x88))
            check('draw leaves unused matrix slots intact', matrix+128, b'\xA5'*(0x280-128))
            check('draw leaves other frame matrix bank intact', actor+0x210+(1-parity)*0x280, b'\xA5'*0x280)
        check('complete converted object retained', bank, asset)
        check('unused joint vectors retained', actor+0x1A4+18, b'\xA5'*36)
        check('non-morph callback retains complete morph array', actor+0x1DA, b'\xA5'*54)
        for at in guards: check('private allocation and stack guard', at, edge)
    finally:
        debug.write_memory(0x801458A0, segments)
    check('native segment bases restored', 0x801458A0, segments)
    check('complete save runtime retained', 0x8046C000, state_before)
    check('complete current prefix retained', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    call(0x8009C040, [allocation])
    return {'native_speed_bag_callbacks': True, 'actual_keyframe_engine': True,
            'actual_native_draw_commands': True, 'sound_dispatch_observed': True,
            'sound_synthesis_or_gpu_rendering_tested': False,
            'ordinary_item_installed': False, 'requires_checkpoint_restore': True}
