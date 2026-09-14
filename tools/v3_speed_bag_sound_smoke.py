"""Actual native sound loading, trigger dispatch, and streamed sample DMA."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_speed_bag_sound_runtime import SOUND_ID
from v3_villager_audio import NATIVE_HEADERS


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_text())
    sound = report.get('speed_bag_sound')
    if sha256(rom) != report['output_sha256'] or not sound or sound['sound_id'] != '0169':
        raise ValueError('Speed-bag sound probe needs the current complete cartridge')
    files = by_vrom(rom)
    code = files[CODE_VROM].extract(rom)
    blob = files[BLOB].extract(rom)[:0xC000]

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'speed_bag_sound_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Native speed-bag sound mismatch: '+label+'; observed '+actual.hex())

    def word(at): return u32(debug.read_memory(at, 4), 0)
    def bounded(at, size):
        if at % 4 or not 0x80000400 <= at <= 0x80400000-size:
            raise ValueError('Native audio pointer escapes N64 RAM')
        return at

    def call(at, args):
        result = debug.call(f'{at:08X}', args, return_address=MODULE_RAM+0x6480)
        record(result)
        return result['return_value']

    check('complete current resident prefix', BLOB_RAM, blob)
    saved = debug.read_memory(0x8046C000, 864)
    for kind, index in (('seq', 199), ('bank', 140), ('wave', 5)):
        row = sound['files'][kind]
        at = NATIVE_HEADERS[kind]+16+index*16
        expected = bytearray(code[at-CODE_RAM:at-CODE_RAM+16])
        struct.pack_into('>I', expected, 0, row['physical_rom']+row['header_offset'])
        check('native relocated '+kind+' header', at, bytes(expected))
    sequence = bounded(word(0x8014CBA8), 0x4D20)
    seq_row = sound['files']['seq']
    seq_file = files[seq_row['vrom']].extract(rom)
    new_sequence = seq_file[seq_row['header_offset']:seq_row['header_offset']+0x4D20]
    check('native main-sequence signature', sequence, new_sequence[:6])
    check('native expanded dispatch pointer', sequence+0x18A, new_sequence[0x18A:0x18C])
    check('complete appended dispatch, hit program, and envelope', sequence+0x4C30, new_sequence[0x4C30:])
    info_base = bounded(word(0x8014BD48), 145*20)
    info = info_base+140*20
    check('native instrument count and wave bindings', info, bytes.fromhex('480005ff0000'))
    instruments = bounded(word(info+8), 72*4)
    bank = instruments-8
    instrument = bounded(word(instruments+71*4), 32)
    if instrument != bank+0x29F0:
        raise ValueError('Native appended instrument pointer does not match its complete font')
    bank_row = sound['files']['bank']
    bank_data = files[bank_row['vrom']].extract(rom)[bank_row['header_offset']:]
    expected = bytearray(bank_data[0x29F0:0x2A10])
    expected[0] = 1
    for at in (4, 16): struct.pack_into('>I', expected, at, bank+u32(expected, at))
    check('complete native relocated appended instrument', instrument, bytes(expected))
    sample = bounded(word(instrument+16), 16)
    wave_row = sound['files']['wave']
    wave_start = wave_row['physical_rom']+wave_row['original_file_bytes']
    expected_sample = struct.pack('>4I', 0x09002B36, wave_start, bank+0x2A2C, bank+0x2A5C)
    check('native ADPCM medium, address, loop, and predictor binding', sample, expected_sample)
    check('complete donor loop and predictor data in native bank', bank+0x2A2C, bank_data[0x2A2C:0x2AA4])
    heap_start, heap_current, heap_size, heap_count = struct.unpack('>4I', debug.read_memory(0x8014C260, 16))
    bounded(heap_start, heap_size)
    if heap_size != 0x1A800 or not heap_start <= heap_current <= heap_start+heap_size or not 1 <= heap_count <= 7:
        raise ValueError('Native permanent audio allocation is not the checked bounded heap')
    record({'native_permanent_audio_capacity': heap_size, 'used': heap_current-heap_start,
            'remaining': heap_start+heap_size-heap_current, 'loaded_resource_count': heap_count,
            'complete_inventory_conservative_spare': sound['after_budget']['conservative_spare']})
    edge = b'V3SA'*4
    for at in (TEST_STACK-0x800, TEST_STACK+0x40): debug.write_memory(at, edge)
    before_slots = debug.read_memory(0x80113C34, 6*32)
    call(0x800F8D5C, [SOUND_ID])
    slots = debug.read_memory(0x80113C34, 6*32)
    matches = [i for i in range(6) if struct.unpack_from('>H', slots, i*32)[0] == SOUND_ID]
    if len(matches) != 1:
        raise ValueError('Native trigger did not allocate exactly one speed-bag sound')
    track = matches[0]
    check('native trigger keeps donor priority', 0x80113C34+track*32+28, bytes((70,)))
    record({'native_speed_bag_track': track, 'trigger_slot_before_sha256': sha256(before_slots)})
    observed = []
    for frame in range(8):
        try:
            record(debug.advance_game_frame())
        except (ValueError, TimeoutError) as error:
            record({'sound_frame_failure': str(error), 'frame': frame+1,
                    'registers': debug.command('g'), 'thread': debug.thread_snapshot(),
                    'faulted_thread': f'{word(0x8003CE34):08X}',
                    'sample_dma_state': debug.read_memory(0x8014BB1C, 16).hex()})
            raise
        list_at = bounded(word(0x8014BB1C), 16)
        count = word(0x8014BB20)
        if not 0 < count <= 256:
            raise ValueError('Unbounded native audio sample-DMA list')
        rows = debug.read_memory(bounded(list_at, count*16), count*16)
        for i in range(count):
            row = rows[i*16:(i+1)*16]
            ram, device = struct.unpack_from('>2I', row)
            size = struct.unpack_from('>H', row, 10)[0]
            first, last = max(device, wave_start), min(device+size, wave_start+11062)
            if first >= last or not row[14]: continue
            actual = debug.read_memory(bounded(ram, size)+(first-device), last-first)
            # A live descriptor can precede its asynchronous PI completion.
            # Count only exact completed transfers; never replace the DMA path.
            if actual == rom[first:last]:
                observed.append((first-wave_start, last-wave_start))
                record({'native_speed_bag_sample_dma': True, 'frame': frame+1, 'slot': i,
                        'sample_start': first-wave_start, 'sample_end': last-wave_start,
                        'matched_sha256': sha256(actual)})
        if frame == 3:
            # Verify retrigger through the same public entry while the sound runs.
            call(0x800F8D5C, [SOUND_ID])
    if not observed:
        raise ValueError('No completed native sample DMA observed for the actual imported sound')
    check('sound playback retains all appended code and envelopes', sequence+0x4C30, new_sequence[0x4C30:])
    check('native wave descriptor remains valid', sample, expected_sample)
    check('complete resident prefix retained', BLOB_RAM, blob)
    check('complete save runtime retained', 0x8046C000, saved)
    for at in (TEST_STACK-0x800, TEST_STACK+0x40): check('test stack guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_sound_loader_and_trigger': True, 'actual_sample_dma': True,
            'sample_dma_observations': len(observed), 'sound_id': f'{SOUND_ID:04X}',
            'physical_audio_played': False, 'pcm_or_listening_verified': False,
            'ordinary_furniture_interaction': False, 'requires_checkpoint_restore': True}
