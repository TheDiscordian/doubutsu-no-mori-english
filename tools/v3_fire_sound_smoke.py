"""Current native fire-sound allocation, real header/font loading, and streamed audio."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from runtime_layout import MODULE_RAM
from v3_asset_loader import BLOB, BLOB_RAM


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_bytes())
    if sha256(rom) != report['output_sha256'] or not report.get('fire_sound'):
        raise ValueError('Fire audio requires the current installed sound cartridge')
    sound, files = report['fire_sound'], by_vrom(rom)
    prefix = files[BLOB].extract(rom)[:0xC000]
    code = files[CODE_VROM].extract(rom)

    def check(label, at, expected):
        observed = debug.read_memory(at, len(expected))
        record({'fire_sound_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
            'assertion': 'passed' if observed == expected else 'failed',
            'expected_sha256': sha256(expected), 'observed_sha256': sha256(observed)})
        if observed != expected:
            raise ValueError('Native fire audio mismatch: ' + label)

    def word(at):
        return u32(debug.read_memory(at, 4), 0)

    def bounded(at, size):
        if at & 3 or not 0x80000400 <= at <= 0x80400000 - size:
            raise ValueError('Fire audio pointer escapes ordinary RAM')
        return at

    def call(at, args):
        result = debug.call(f'{at:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result)
        return result['return_value']

    check('complete current prefix', BLOB_RAM, prefix)
    saved = debug.read_memory(0x8046C000, 864)
    for row in sound['wave_headers']:
        expected = bytearray.fromhex(row['after'])
        struct.pack_into('>I', expected, 0, row['physical'])
        check('actual native wave header ' + str(row['index']), row['address'], expected)
    for kind in ('seq', 'bank'):
        row = sound['resources'][kind]
        expected = bytearray.fromhex(row['header_after'])
        struct.pack_into('>I', expected, 0, row['physical'])
        check('actual native fire ' + kind + ' header', row['header_address'], expected)
    total, fixed, permanent = sound['heap_settings']
    heap_base = bounded(word(0x8014CB84), total)
    check('actual enlarged audio heap size', 0x8014CB88, struct.pack('>I', total))
    for label, at, expected_size, expected_base in (
            ('fixed', 0x8014BEC0, fixed, heap_base),
            ('session', 0x8014BEA0, total - fixed, heap_base + fixed),
            ('permanent', 0x8014C260, permanent, None)):
        start, current, size, count = struct.unpack('>4I', debug.read_memory(at, 16))
        bounded(start, size)
        if (size != expected_size or not start <= current <= start + size
                or (expected_base is not None and start != expected_base)
                or not heap_base <= start < start + size <= heap_base + total):
            raise ValueError('Incorrect actual native ' + label + ' audio allocation')
        record({'native_fire_audio_pool': label, 'base': start, 'capacity': size,
            'used': current - start, 'allocations': count, 'assertion': 'passed'})
    row = sound['resources']['seq']
    sequence = bounded(word(0x8014CBA8), row['bytes'])
    seq = rom[row['physical']:row['physical'] + row['bytes']]
    check('native main-sequence identity', sequence, seq[:6])
    check('actual relocated level dispatch', sequence + 0x179, seq[0x179:0x17B])
    check('complete installed fire table, programs, and envelopes', sequence + 0x4D20, seq[0x4D20:])

    font_row, wave_row = sound['resources']['bank'], sound['resources']['wave']
    font = rom[font_row['physical']:font_row['physical'] + font_row['bytes']]
    info = bounded(word(0x8014BD48), 145 * 20) + 140 * 20
    check('actual 74-instrument native font and wave binding', info, bytes.fromhex('4A0005FF0000'))
    bank = bounded(word(info + 8) - 8, len(font))
    expected, samples, added_samples = bytearray(font), set(), {}
    for index in range(74):
        inst = u32(font, 8 + index * 4)
        if not 0x130 <= inst <= len(font) - 32:
            raise ValueError('Unexpected complete current instrument pointer')
        struct.pack_into('>I', expected, 8 + index * 4, bank + inst)
        expected[inst] = 1
        struct.pack_into('>I', expected, inst + 4, bank + u32(font, inst + 4))
        for field in (8, 16, 24):
            sample = u32(font, inst + field)
            if sample:
                struct.pack_into('>I', expected, inst + field, bank + sample)
                samples.add(sample)
                if index >= 72:
                    added_samples[index] = (wave_row['physical'] + u32(font, sample + 4), u32(font, sample))
    for at in samples:
        flags, source, loop, book = struct.unpack_from('>4I', font, at)
        struct.pack_into('>4I', expected, at, flags | 0x09000000,
            wave_row['physical'] + source, bank + loop, bank + book)
    check('complete native font and every original/imported sample relocation', bank, expected)
    # Use the ordinary system-level entry to exercise the registered level
    # dispatcher. This is not positional furniture interaction. Require both
    # native slots to be free, avoiding the original full-slot replacement bug.
    slots = debug.read_memory(0x80114124, 6)
    if slots[0] or slots[3]:
        raise ValueError('Native system-level slots are occupied; no replacement fixture is allowed')
    for sid in (0x5C, 0x5D):
        call(0x800FA580, [sid])
    observed = set()
    for frame in range(40):
        record(debug.advance_game_frame())
        count = word(0x8014BB20)
        if not 0 < count <= 256:
            raise ValueError('Unbounded native audio sample-DMA list')
        rows = debug.read_memory(bounded(word(0x8014BB1C), count * 16), count * 16)
        for slot in range(count):
            row = rows[slot * 16:(slot + 1) * 16]
            ram, device = struct.unpack_from('>2I', row)
            size = struct.unpack_from('>H', row, 10)[0]
            if not row[14]:
                continue
            for index, (wave_start, length) in added_samples.items():
                first, last = max(device, wave_start), min(device + size, wave_start + length)
                if first >= last:
                    continue
                actual = debug.read_memory(bounded(ram, size) + first - device, last - first)
                if actual == rom[first:last] and index not in observed:
                    observed.add(index)
                    record({'native_fire_sample_dma': index, 'frame': frame + 1,
                        'sample_start': first - wave_start, 'sample_end': last - wave_start,
                        'sha256': sha256(actual), 'assertion': 'passed'})
        if observed == {72, 73}:
            break
    for sid in (0x5C, 0x5D):
        call(0x800FA720, [sid])
    check('both native system-level slots released', 0x80114124, bytes(6))
    check('fire programs retain complete envelopes and loop targets', sequence + 0x4D20, seq[0x4D20:])
    check('complete save state retained', 0x8046C000, saved)
    check('complete resident prefix retained', BLOB_RAM, prefix)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    if observed != {72, 73}:
        raise ValueError('No completed native transfer for every actual fire sample')
    return {'native_fire_audio_allocation_and_font': True, 'both_new_samples_transferred': True,
        'native_level_dispatch_start_stop': True, 'positional_furniture_interaction': False,
        'physical_audio_played': False, 'pcm_or_listening_verified': False,
        'requires_checkpoint_restore': True}
