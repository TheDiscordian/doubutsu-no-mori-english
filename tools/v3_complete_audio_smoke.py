"""Actual expanded voice-font loading, full melody copies, and sample transfers."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_all_audio_runtime import BLOB, BLOB_RAM, PACKAGE_RAM, PACKAGE_VROM, PACKAGE_BYTES
from v3_audio_runtime import STATE


def trace_notes(debug, rom_path, record):
    """Follow real tune commands, note layers, and streamed samples on this build.

    This is a controlled valid town tune, not an ordinary NPC conversation.
    No audio program, instrument, engine flag, or instruction is rewritten.
    """
    from v3_villager_audio import extended_native_interpreter, extended_sequence_programs
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report.get('complete_villager_audio'):
        raise ValueError('Note tracing requires its exact full-audio cartridge')
    files = by_vrom(rom)
    code = files[CODE_VROM].extract(rom)
    extended_native_interpreter(lambda at, size: code[at-CODE_RAM:at-CODE_RAM+size])
    resources = report['complete_villager_audio']['files']
    bank_row, wave_row = resources['bank'], resources['wave']
    font = rom[bank_row['physical_rom']:bank_row['physical_rom']+bank_row['bytes']]
    if sha256(font) != bank_row['sha256']:
        raise ValueError('Changed compiled voice font')

    def bounded(at, size):
        if at & 3 or not 0x80000400 <= at <= 0x80400000-size:
            raise ValueError(f'Note trace address escapes native audio RAM: {at:08X}')
        return at

    def word(at):
        return u32(debug.read_memory(at, 4), 0)

    def check(label, at, expected):
        actual = debug.read_memory(at, len(expected))
        record({'note_trace_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed'})
        if actual != expected:
            raise ValueError('Note trace mismatch: '+label)

    samples = {}
    for index in range(84, 88):
        instrument = u32(font, 8+index*4)
        sample = u32(font, instrument+16)
        length, source = struct.unpack_from('>2I', font, sample)
        samples[index] = (wave_row['physical_rom']+source, length & 0xFFFFFF)
    group = bounded(word(0x80151B70), 0x160)
    sequence = bounded(word(group+0x18), 0x4D20)
    channel = bounded(word(group+0x38+15*4), 0x100)
    voice = 263
    melody = next(row for row in report['villager_audio']['imports'] if row['voice'] == voice)
    original = debug.read_memory(int(melody['ram'], 16), melody['bytes'])
    if sha256(original) != melody['sha256']:
        raise ValueError('Changed resident imported melody')
    programs = extended_sequence_programs(original)
    record({'note_trace_source': voice, 'runtime_abi': report['runtime_abi'],
            'group': f'{group:08X}', 'channel': f'{channel:08X}',
            'sequence': f'{sequence:08X}', 'program_instruments':
            [programs[i]['instruments'] for i in range(4)],
            'physical_audio_playback': False, 'engine_or_program_writes': False})
    saved = debug.read_memory(0x8046C000, 864)
    notes = MODULE_RAM+0x6500
    # Native and donor controllers recognise 14 as hold and 15 as end. The
    # islander programs change instruments after 24 ticks; ordinary unheld
    # notes finish at that boundary, correctly omitting their extended tails.
    tune = bytes((0, 14, 14, 1, 14, 14, 2, 14, 14, 3, 14, 14, 15, 15, 15, 15))
    edge = b'V3NT'*4
    debug.write_memory(notes, tune)
    for at in (notes-16, notes+16):
        debug.write_memory(at, edge)
    record(debug.call('800FCE80', [voice, notes], return_address=MODULE_RAM+0x6480))
    copied = bytearray(original)
    for index in range(19):
        at = 4+2*index
        struct.pack_into('>H', copied, at, struct.unpack_from('>H', copied, at)[0]+0x4610)
    check('unaltered complete melody with native pointer relocation', sequence+0x4610, copied)
    observed, selected = set(), set()
    for frame in range(97):
        state = debug.read_memory(channel, 0x100)
        layers = []
        for slot in range(4):
            at = u32(state, 0x54+slot*4)
            if not at:
                continue
            layer = debug.read_memory(bounded(at, 0x90), 0x90)
            instrument = layer[2]
            if instrument-2 in samples and layer[0] & 0x80:
                selected.add(instrument-2)
            layers.append({'address': f'{at:08X}', 'flags': layer[0],
                'inst_or_wave': instrument, 'delay': struct.unpack_from('>h', layer, 0x1A)[0],
                'pc': f'{u32(layer, 0x64):08X}', 'instrument': f'{u32(layer, 0x58):08X}',
                'tuned_sample': f'{u32(layer, 0x5C):08X}',
                'native_channel': f'{u32(layer, 0x3C):08X}'})
        count = word(0x8014BB20)
        if not 0 < count <= 256:
            raise ValueError('Unbounded native sample-DMA list')
        cache = debug.read_memory(bounded(word(0x8014BB1C), count*16), count*16)
        transfers = []
        for slot in range(count):
            row = cache[slot*16:(slot+1)*16]
            ram, source = struct.unpack_from('>2I', row)
            size = struct.unpack_from('>H', row, 10)[0]
            if not row[14] or not size:
                continue
            for instrument, (begin, length) in samples.items():
                first, end = max(source, begin), min(source+size, begin+length)
                if first >= end:
                    continue
                data = debug.read_memory(bounded(ram, size)+first-source, end-first)
                matched = data == rom[first:end]
                transfers.append({'instrument': instrument, 'source': f'{first:08X}',
                    'bytes': end-first, 'ttl': row[14], 'matches_rom': matched})
                if matched:
                    observed.add(instrument)
        record({'note_trace_frame': frame, 'channel_flags': state[0], 'bank_id': state[7],
            'channel_pc': f'{u32(state, 0x64):08X}', 'ports': state[0xC8:0xD0].hex(),
            'layers': layers, 'completed_imported_transfers': transfers})
        # A cache transfer can include a neighbouring waveform through DMA
        # read-ahead. Require actual note selection too, not overlap alone.
        if observed == set(samples) and selected == set(samples):
            break
        if frame < 96:
            debug.advance_game_frame()
    check('resident melody remains intact', int(melody['ram'], 16), original)
    check('loaded melody remains intact', sequence+0x4610, copied)
    check('save/profile state remains intact', 0x8046C000, saved)
    for at in (notes-16, notes+16):
        check('town tune fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    result = {'native_note_trace': True, 'selected_imported_instruments': sorted(selected),
        'new_instrument_dma': sorted(observed),
        'all_four_streamed': observed == set(samples) and selected == set(samples),
        'frames': frame, 'requires_checkpoint_restore': True,
        'physical_audio_played': False, 'ordinary_conversation': False,
        'town_tune': list(tune)}
    record(result)
    if not result['all_four_streamed']:
        raise ValueError('Not all four imported instruments reached actual note selection and sample transfer')
    return result


def exercise(debug, rom_path, record, *, speech_tail=False):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent/'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or report.get('runtime_abi') != 53:
        raise ValueError('Complete audio check requires the exact current cartridge')
    files, complete = by_vrom(rom), report['complete_villager_audio']
    blob = files[BLOB].extract(rom)
    prefix = bytearray(blob[:0xC000])
    package = blob[PACKAGE_VROM-BLOB:PACKAGE_VROM-BLOB+PACKAGE_BYTES]
    code = files[CODE_VROM].extract(rom)

    def check(label, at, expected):
        if speech_tail and label in ('complete current prefix', 'complete loaded accessory code and all twenty melodies',
                'actual native relocated audio header', 'expanded voice count and bank bindings',
                'complete native relocated font including all original and new instruments', 'main sequence remains intact'):
            return
        actual = debug.read_memory(at, len(expected))
        record({'complete_audio_check': label, 'address': f'{at:08X}', 'bytes': len(expected),
            'assertion': 'passed' if actual == expected else 'failed',
            'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('Complete native audio mismatch: '+label)

    def word(at): return u32(debug.read_memory(at, 4), 0)

    def bounded(at, size):
        if at % 4 or not 0x80000400 <= at <= 0x80400000-size:
            raise ValueError('Native audio address escapes its ordinary RAM allocation')
        return at

    def call(at, args):
        result = debug.call(f'{at:08X}', args, return_address=MODULE_RAM+0x6480)
        record(result)
        return result['return_value']

    check('complete current prefix', BLOB_RAM, prefix)
    check('complete loaded accessory code and all twenty melodies', PACKAGE_RAM, package)
    saved = debug.read_memory(0x8046C000, 864)
    for row in complete['files'].values():
        expected = bytearray.fromhex(row['header_after'])
        struct.pack_into('>I', expected, 0, row['physical_rom'])
        check('actual native relocated audio header', row['header_address'], expected)
    font_row, wave_row = complete['files']['bank'], complete['files']['wave']
    font = rom[font_row['physical_rom']:font_row['physical_rom']+font_row['bytes']]
    info = bounded(word(0x8014BD48), 145*20)+2*20
    check('expanded voice count and bank bindings', info, bytes.fromhex('580002ff0000'))
    table = bounded(word(info+8), 88*4)
    bank = bounded(table-8, len(font))
    expected_font = bytearray(font)
    samples = set()
    imported_samples = {}
    for index in range(88):
        inst = u32(font, 8+index*4)
        if not inst:
            if index != 83: raise ValueError('Unexpected empty compiled instrument')
            continue
        struct.pack_into('>I', expected_font, 8+index*4, bank+inst)
        expected_font[inst] = 1
        struct.pack_into('>I', expected_font, inst+4, bank+u32(font, inst+4))
        for field in (8, 16, 24):
            sample = u32(font, inst+field)
            if not sample: continue
            struct.pack_into('>I', expected_font, inst+field, bank+sample)
            samples.add(sample)
            if index >= 84:
                imported_samples[index] = (wave_row['physical_rom']+u32(font, sample+4), u32(font, sample))
    for at in samples:
        flags, source, loop, book = struct.unpack_from('>4I', font, at)
        struct.pack_into('>4I', expected_font, at, flags | 0x09000000,
                         wave_row['physical_rom']+source, bank+loop, bank+book)
    check('complete native relocated font including all original and new instruments', bank, expected_font)
    heap_start, heap_current, heap_size, count = struct.unpack('>4I', debug.read_memory(0x8014C260, 16))
    bounded(heap_start, heap_size)
    if heap_size != 0x1A800 or not heap_start <= heap_current <= heap_start+heap_size or not 1 <= count <= 7:
        raise ValueError('Expanded font exceeds the native permanent audio heap')
    record({'complete_audio_heap': True, 'capacity': heap_size, 'used': heap_current-heap_start,
            'loaded_resources': count, 'all_seven_resources_conservative_spare': complete['after_budget']['conservative_spare']})
    sequence = bounded(word(0x8014CBA8), 0x4D20)
    check('main sequence remains intact', sequence, bytes.fromhex('FB0006003A10'))
    notes = MODULE_RAM+0x6500
    debug.write_memory(notes, bytes((0, 2, 4, 5, 7, 9, 11, 12, 11, 9, 7, 5, 4, 2, 0, 14)))
    edge = b'V3VA'*4
    guards = (notes-16, notes+16, TEST_STACK-0x800, TEST_STACK+0x40)
    for at in guards: debug.write_memory(at, edge)
    observations = set()
    imports = {r['voice']: r for r in report['villager_audio']['imports']}
    seq_file = files[0x01920000].extract(rom)
    container = u32(code, 0x80115090-CODE_RAM+16+205*16)
    track = 6 if speech_tail else 15
    relative = 0x3A10 if speech_tail else 0x4610
    for voice, frames in (((263, 60),) if speech_tail else ((263, 12), (277, 12), (285, 2), (29, 2))):
        before = bytearray(debug.read_memory(sequence+0x3A10, 0x1200))
        if voice >= 256:
            row = imports[voice]
            at = int(row['ram'], 16)-PACKAGE_RAM
            fragment = bytearray(package[at:at+row['bytes']])
        else:
            at = container+u32(code, 0x80119640-CODE_RAM+voice*4)
            size = u32(code, 0x80119240-CODE_RAM+voice*4)
            fragment = bytearray(seq_file[at:at+size])
        for index in range(19):
            at = 4+2*index
            struct.pack_into('>H', fragment, at, struct.unpack_from('>H', fragment, at)[0]+relative)
        offset = relative-0x3A10
        before[offset:offset+len(fragment)] = fragment
        call(0x800FD280 if speech_tail else 0x800FCE80, [voice] if speech_tail else [voice, notes])
        check('complete relocated melody pool for '+str(voice), sequence+0x3A10, before)
        struct.pack_into('>H', prefix, STATE+track*2, voice)
        check('only owned full-ID tags change', BLOB_RAM, prefix)
        if voice in (285, 29) and call(0x800FD0D4, [29 if voice == 285 else 285]) != 0xFFFFFFFF:
            raise ValueError('Expanded audio accepts the wrong full-ID alias')
        for frame in range(frames):
            record(debug.advance_game_frame())
            count = word(0x8014BB20)
            if not 0 < count <= 256: raise ValueError('Unbounded native sample-DMA list')
            rows = debug.read_memory(bounded(word(0x8014BB1C), count*16), count*16)
            for slot in range(count):
                row = rows[slot*16:(slot+1)*16]
                ram, device = struct.unpack_from('>II', row)
                size = struct.unpack_from('>H', row, 10)[0]
                if not row[14]: continue
                for instrument, (source, length) in imported_samples.items():
                    first, end = max(source, device), min(source+length, device+size)
                    if first >= end: continue
                    actual = debug.read_memory(bounded(ram, size)+first-device, end-first)
                    if actual == rom[first:end]:
                        observations.add(instrument)
            if speech_tail and observations:
                break
        tag = call(0x800EF3C0, [0, track, 2]) & 255
        if tag != voice & 255: raise ValueError('Native audio did not consume the complete voice ID')
        check('native audio preserves the loaded melody', sequence+0x3A10, before)
        record({'native_complete_voice': voice, 'port_tag': tag, 'frames': frame+1, 'track': track})
    if not observations:
        raise ValueError('No completed streamed sample transfer observed for the new instruments')
    record({'new_voice_instruments_with_completed_sample_dma': sorted(observations)})
    check('shared resident package remains immutable', PACKAGE_RAM, package)
    check('complete prefix and tags retained', BLOB_RAM, prefix)
    check('save/profile state retained', 0x8046C000, saved)
    for at in guards: check('fixture guard', at, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE')*4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_complete_voice_font': not speech_tail, 'native_melodies': [263] if speech_tail else [263, 277, 285, 29],
        'speech_transfer_tail_only': speech_tail,
        'new_instrument_dma': sorted(observations), 'physical_audio_played': False,
        'listening_or_ordinary_conversation': False, 'requires_checkpoint_restore': True}
