"""Verify donor melody programs and their complete shared N64 instrument assets."""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32, verified_rom
from apply_translation import write_new
from gamecube import Disc
from v3_import_catalog import ROOT

DOL_SHA = 'e3166b15b810ff20397784fc83b2eb053db5d0c2a9e22ac2ead63a645881d150'
AUDIO_SHA = '3a631dac1a2abb0d5449f85d9b41b7a6346b582d5ac04b73e87aa65ebe66d93f'
PILOTS = {'cheri': (232, 285), 'punchy': (235, 286)}
GC_SECTIONS = {'seq': 0x800CCA40, 'bank': 0x800CD9E0, 'wave': 0x800CE3E0}
NATIVE_HEADERS = {'seq': 0x80115090, 'bank': 0x80114700, 'wave': 0x80115020}
NATIVE_FILES = {'seq': 0x27130, 'bank': 0xE4D10, 'wave': 0x13D9A0}


class Dol:
    def __init__(self, data):
        if len(data) < 256:
            raise ValueError('Truncated DOL header')
        self.data = data
        self.sections = [(u32(data, i * 4), u32(data, 0x48 + i * 4), u32(data, 0x90 + i * 4))
                         for i in range(18) if u32(data, 0x90 + i * 4)]
        for offset, address, size in self.sections:
            if offset < 256 or offset + size > len(data) or not 0x80000000 <= address < address + size <= 0x81800000:
                raise ValueError('Invalid DOL section bounds')
        for i, (off, ram, size) in enumerate(self.sections):
            for other, address, length in self.sections[i + 1:]:
                if max(off, other) < min(off + size, other + length) or max(ram, address) < min(ram + size, address + length):
                    raise ValueError('Overlapping DOL sections')

    def read(self, address, size):
        if size <= 0:
            raise ValueError('Empty DOL read')
        for offset, base, length in self.sections:
            if base <= address and address + size <= base + length:
                return self.data[offset + address - base:offset + address - base + size]
        raise ValueError('DOL resource crosses or escapes its section')


def read_audio_donor(path):
    with Disc(path) as disc:
        if disc.header[:8] != b'GAFE01\0\0':
            raise ValueError('Villager audio requires the GAFE01 revision 0 donor')
        offset = u32(disc.header, 0x420)
        header = disc.read(offset, 256)
        size = max(u32(header, i * 4) + u32(header, 0x90 + i * 4)
                   for i in range(18) if u32(header, 0x90 + i * 4))
        dol = disc.read(offset, size)
        entries = [e for e in disc.files() if e['path'] == 'audiorom.img']
        if len(entries) != 1 or entries[0]['size'] != 8300384:
            raise ValueError('Changed donor audio archive')
        audio = disc.read(entries[0]['offset'], entries[0]['size'])
    if sha256(dol) != DOL_SHA or sha256(audio) != AUDIO_SHA:
        raise ValueError('Changed donor executable or audio assets')
    return Dol(dol), audio


def span(data, offset, size):
    if offset < 0 or size <= 0 or offset + size > len(data):
        raise ValueError('Audio resource exceeds its containing asset')
    return data[offset:offset + size]


def header_entry(read, base, index):
    count = struct.unpack('>H', read(base, 2))[0]
    if not 0 <= index < count:
        raise ValueError('Audio header index outside its table')
    return read(base + 16 + index * 16, 16)


def resource(read, headers, sources, kind, index):
    entry = header_entry(read, headers[kind], index)
    offset, size = struct.unpack_from('>II', entry)
    if entry[8] != 2 or not size:
        raise ValueError('Unsupported audio medium or alias entry')
    return span(sources[kind], offset, size), entry


def extended_envelope(bank, address):
    for index in range(64):
        delay, target = struct.unpack('>hh', span(bank, address+4*index, 4))
        if delay in (0, -1):
            if target != 0 or index < 2:
                raise ValueError('Invalid extended envelope terminator')
            return span(bank, address, 4*(index+1))
        if delay == -4 and index == 0 and target == 0:
            continue
        if delay <= 0 or not 0 <= target <= 32767:
            raise ValueError('Unsupported extended envelope control or amplitude')
    raise ValueError('Unterminated extended envelope')


def instrument(bank, wave, instrument_id, instrument_count, *, extended=False):
    if not 0 <= instrument_id < instrument_count:
        raise ValueError('Missing voice instrument')
    data = span(bank, u32(bank, 8 + instrument_id * 4), 32)
    if data[0] != 0:
        raise ValueError('Instrument unexpectedly pre-relocated')
    envelope = extended_envelope(bank, u32(data, 4)) if extended else span(bank, u32(data, 4), 12)
    if not extended and tuple(struct.unpack_from('>h', envelope, i)[0] for i in (0, 4, 8)) != (-4, 1, -1):
        raise ValueError('Pilot instrument uses an unsupported envelope')
    samples = []
    for at in (8, 16, 24):
        pointer, tuning = struct.unpack_from('>II', data, at)
        if not pointer:
            if tuning:
                raise ValueError('Missing wave has nonzero tuning')
            samples.append(None)
            continue
        header = span(bank, pointer, 16)
        flags, sample, loop, book = struct.unpack('>4I', header)
        if flags >> 24 or not 0 < flags < 0x1000000:
            raise ValueError('Unsupported waveform codec, flags, or medium')
        loop_header = span(bank, loop, 16)
        loops = u32(loop_header, 8)
        loop_data = span(bank, loop, 48 if loops else 16)
        order, predictors = struct.unpack('>II', span(bank, book, 8))
        if not 1 <= order <= 2 or not 1 <= predictors <= 16:
            raise ValueError('Unsupported ADPCM predictor dimensions')
        coefficients = span(bank, book, 8 + 16 * order * predictors)
        samples.append({'tuning': tuning, 'sample_bytes': flags,
            'sample_sha256': sha256(span(wave, sample, flags)),
            'loop_sha256': sha256(loop_data), 'predictor_sha256': sha256(coefficients)})
    return {'ranges_and_decay': data[1:4].hex(), 'envelope_sha256': sha256(envelope),
            'samples': samples}


def program_shape(program, note_at):
    """Compare native opcodes/operand widths, retaining the donor's operand values."""
    result = bytearray(program)
    if note_at == 17:
        if tuple(result[i] for i in (6, 8, 12)) != (0xE3, 0xE2, 0xE1):
            raise ValueError('Unsupported vibrato opcode structure')
        for i in (7, 9, 10, 11, 13, 14, 15):
            result[i] = 0
    result[note_at] = 0x40
    for i in range(note_at + 1, len(result) - 1):
        result[i] = result[i] & 0x80 if i == note_at + 1 else 0
    return bytes(result)


def sequence_programs(data):
    """Parse the two pilot forms, including relative note starts and terminators.

    Preserve complete donor padding; it is not guessed at or stripped. Each
    program must have a real N64 counterpart with the same opcode/operand layout.
    """
    if not 42 <= len(data) <= 0x600 or len(data) % 16:
        raise ValueError('Melody does not fit one native reserved track slot')
    offsets = struct.unpack_from('>19H', data, 4)
    if offsets[0] != 42 or tuple(sorted(set(offsets))) != offsets or offsets[-1] >= len(data):
        raise ValueError('Invalid nineteen-track melody table')
    tracks = []
    for i, start in enumerate(offsets):
        end = offsets[i + 1] if i < 18 else len(data)
        track = span(data, start, end - start)
        if len(track) < 11 or track[0:2] != bytes((0xEB, 3)) or track[3] != 0x78:
            raise ValueError('Unsupported melody bank selection or note start')
        note_at = 6 + struct.unpack_from('>h', track, 4)[0]
        if note_at not in (7, 17) or track[note_at - 1] != 255:
            raise ValueError('Invalid relative note program target')
        if note_at == 17 and track[6:16] != bytes.fromhex('e300e2104020e1407f40'):
            raise ValueError('Unsupported pilot vibrato program')
        at = note_at
        if not 0x40 <= track[at] < 0x80:
            raise ValueError('Pilot note is not a duration/velocity large note')
        pitch = track[at] & 0x3F
        at += 1
        delay = track[at]; at += 1
        if delay & 0x80:
            delay = (delay & 0x7F) * 256 + track[at]; at += 1
        velocity = track[at]; at += 1
        if not delay or velocity > 127 or track[at] != 255:
            raise ValueError('Invalid pilot note duration, velocity, or terminator')
        at += 1
        if i < 18 and at != len(track):
            raise ValueError('Unaccounted bytes between melody programs')
        if i == 18 and any(byte not in (0, 0x30) for byte in track[at:]):
            raise ValueError('Unknown bytes after final melody terminator')
        tracks.append({'offset': start, 'bytes': at, 'note_offset': note_at,
            'pitch': pitch, 'delay': delay, 'velocity': velocity, 'instrument': track[2],
            'vibrato_operands': track[6:note_at - 1].hex(),
            'normalized': program_shape(track[:at], note_at)})
    return tracks


def extended_program(track):
    """Read the islanders' bounded channel/large-note programs, without rewriting.

    Only commands verified in the donor interpreter are accepted. Native
    counterpart matching and complete instrument comparison happen separately.
    """
    if len(track) < 11 or track[:2] != b'\xEB\x03' or track[3] != 0x78:
        raise ValueError('Unsupported extended melody channel prefix')
    note_at = 6 + struct.unpack_from('>h', track, 4)[0]
    if not 7 <= note_at < len(track):
        raise ValueError('Extended melody note target escapes its track')
    shape = bytearray(track[:6])
    shape[2] = 0
    cursor, controls = 6, []
    widths = {0xE3: 1, 0xE2: 3, 0xE1: 3, 0xD7: 1}
    while cursor < note_at-1:
        op = track[cursor]
        width = widths.get(op)
        if width is None or cursor+1+width > note_at-1:
            raise ValueError('Unknown or truncated extended channel command')
        operands = track[cursor+1:cursor+1+width]
        controls.append({'opcode': f'{op:02X}', 'operands': operands.hex()})
        shape.extend(bytes([op])+bytes(width))
        cursor += 1+width
    if track[cursor] != 255 or cursor+1 != note_at:
        raise ValueError('Extended melody channel lacks its exact terminator')
    shape.append(255)
    cursor = note_at
    events, instruments = [], {track[2]}
    selected = track[2]

    def duration(at):
        if at >= len(track):
            raise ValueError('Truncated extended note duration')
        first = track[at]
        width = 2 if first & 128 else 1
        if at+width > len(track):
            raise ValueError('Truncated wide extended note duration')
        value = (first & 127)*256+track[at+1] if width == 2 else first
        if not value:
            raise ValueError('Zero extended note duration')
        return value, width

    while cursor < len(track):
        op = track[cursor]
        if op == 255:
            if not any(e['kind'] == 'note' for e in events):
                raise ValueError('Extended melody has no notes')
            shape.append(255)
            return {'bytes': cursor+1, 'note_offset': note_at,
                'instrument': track[2], 'instruments': sorted(instruments),
                'channel_controls': controls, 'events': events, 'normalized': bytes(shape)}
        if 0x40 <= op < 0x80 or op == 0xC0:
            delay, width = duration(cursor+1)
            end = cursor+1+width+(op != 0xC0)
            if end > len(track):
                raise ValueError('Truncated extended note velocity')
            shape.extend(bytes([0xC0 if op == 0xC0 else 0x40, track[cursor+1] & 128])
                         + bytes(width-1))
            if op == 0xC0:
                events.append({'kind': 'rest', 'duration': delay})
            else:
                velocity = track[end-1]
                if velocity > 127:
                    raise ValueError('Invalid extended note velocity')
                events.append({'kind': 'note', 'pitch': op & 63, 'duration': delay,
                               'velocity': velocity, 'instrument': selected})
                shape.append(0)
            cursor = end
        elif op == 0xC6:
            if cursor+1 >= len(track) or track[cursor+1] >= 0x7E:
                raise ValueError('Unknown extended note instrument')
            selected = track[cursor+1]
            instruments.add(selected)
            events.append({'kind': 'instrument', 'instrument': selected})
            shape.extend(b'\xC6\x00')
            cursor += 2
        else:
            raise ValueError(f'Unsupported extended note opcode {op:02X}')
    raise ValueError('Unterminated extended melody note program')


def extended_sequence_programs(data):
    if not 42 <= len(data) <= 0x600 or len(data) % 16:
        raise ValueError('Extended melody does not fit one native track slot')
    offsets = struct.unpack_from('>19H', data, 4)
    if offsets[0] != 42 or tuple(sorted(set(offsets))) != offsets or offsets[-1] >= len(data):
        raise ValueError('Invalid extended nineteen-track melody table')
    result = []
    for i, start in enumerate(offsets):
        end = offsets[i+1] if i < 18 else len(data)
        track = span(data, start, end-start)
        program = extended_program(track)
        tail = track[program['bytes']:]
        if (i < 18 and tail) or (i == 18 and (len(tail) >= 32 or any(b not in (0, 0x30) for b in tail))):
            raise ValueError('Unaccounted bytes after extended note terminator')
        result.append({'offset': start, **program})
    return result


INTERPRETER_RANGES = (
    (0x800F3484, 0x800F34C4, '60918c26976b914edf18e74fea977654b15c88151824adb3ca428bc2984f44a0'),
    (0x800F3760, 0x800F3B58, '61a264e3315f4f1373c4516e99c9103744c0adccb1050d28f7887590d005496e'),
    (0x800F42D0, 0x800F46D4, '1fe0d4b926d5d9a0c3a63b7b99e7614a1153f4c94c28c82379ee71dbc58c93f5'),
    (0x800F4870, 0x800F5660, '93d134c9f69c4b6d66329b5c860a0b445e69a5bb99c6f54b81ffdcaecd2ff026'),
    (0x800F2998, 0x800F2B74, 'b23551bbee69f1a599d570c508f77caad30e409f33f0c7227b73db51361ff93c'),
)


def extended_native_interpreter(read):
    """Pin the inspected native interpreter, not an unrelated single-note template."""
    for start, end, digest in INTERPRETER_RANGES:
        if sha256(read(start, end-start)) != digest:
            raise ValueError('Changed native extended melody interpreter')
    commands = ((0xD7, 1, 0x800F4C58), (0xE1, 3, 0x800F4C98),
                (0xE2, 3, 0x800F4C70), (0xE3, 1, 0x800F4CC0), (0xEB, 2, 0x800F4A74))
    for op, width, handler in commands:
        if (read(0x80113210+op, 1) != bytes([width])
                or u32(read(0x80118520+(op-0xA0)*4, 4), 0) != handler):
            raise ValueError('Changed native extended channel dispatch')
    if u32(read(0x801184B8+5*4, 4), 0) != 0x800F3910:
        raise ValueError('Changed native note-instrument dispatch')
    return {'ranges': [{'start': f'{a:08X}', 'end': f'{b:08X}', 'sha256': d}
                       for a, b, d in INTERPRETER_RANGES],
        'channel_handlers': {f'{op:02X}': f'{handler:08X}' for op, _, handler in commands},
        'note_instrument_handler': '800F3910', 'rest_handler': '800F42D0',
        'large_note_handler': '800F43D4'}


def extend_voice_bank(native_bank, native_wave, donor_bank, donor_wave, missing):
    """Retain all native instruments and append the four actual islander voices.

    This supplies complete local resources. Installing the larger font/wave
    entries and measuring their audio allocation is a separate runtime step.
    """
    if (sorted(missing) != [84, 85, 86, 87] or native_bank[:8] != bytes(8)
            or native_bank[0x154:0x160] != bytes(12)):
        raise ValueError('Unreviewed native voice-bank layout or extension set')
    shift, first = 16, 0x160
    bank = bytearray(native_bank[:first]+bytes(shift)+native_bank[first:])
    waves = bytearray(native_wave)
    pointers, cache = {}, {}

    def relocate(at):
        value = u32(native_bank, at)
        if value:
            if not first <= value < len(native_bank) or value % 4:
                raise ValueError('Native instrument pointer outside original resource data')
            pointers[at] = value
        return value

    # Instrument, envelope, sample, loop, and ADPCM-book pointers are all
    # bank-relative. Wave offsets and tuning words are not bank pointers.
    for index in range(83):
        inst = relocate(8+4*index)
        if not inst:
            raise ValueError('Unexpected empty original voice instrument')
        envelope = relocate(inst+4)
        cache.setdefault(('envelope', extended_envelope(native_bank, envelope)), envelope+shift)
        for field in (8, 16, 24):
            sample = relocate(inst+field)
            if sample:
                loop = relocate(sample+8)
                book = relocate(sample+12)
                loop_data = span(native_bank, loop, 48 if u32(native_bank, loop+8) else 16)
                order, count = struct.unpack('>2I', span(native_bank, book, 8))
                cache.setdefault(('loop', loop_data), loop+shift)
                cache.setdefault(('book', span(native_bank, book, 8+16*order*count)), book+shift)
    for at, target in pointers.items():
        struct.pack_into('>I', bank, at+(shift if at >= first else 0), target+shift)
    installed, reused = [], []

    def append(data, kind):
        key = kind, data
        if key not in cache:
            at = (len(bank)+15) & ~15
            bank.extend(bytes(at-len(bank))+data)
            cache[key] = at
        elif cache[key] < len(native_bank)+shift:
            reused.append({'kind': kind, 'offset': cache[key], 'bytes': len(data), 'sha256': sha256(data)})
        return cache[key]

    for index in sorted(missing):
        original = span(donor_bank, u32(donor_bank, 8+index*4), 32)
        inst = bytearray(original)
        env = extended_envelope(donor_bank, u32(inst, 4))
        struct.pack_into('>I', inst, 4, append(env, 'envelope'))
        for field in (8, 16, 24):
            pointer = u32(original, field)
            if not pointer:
                continue
            sample = bytearray(span(donor_bank, pointer, 16))
            length, source, loop, book = struct.unpack('>4I', sample)
            # Full instrument validation rejects unsupported codec/medium flags.
            loop_data = span(donor_bank, loop, 48 if u32(donor_bank, loop+8) else 16)
            order, count = struct.unpack('>2I', span(donor_bank, book, 8))
            book_data = span(donor_bank, book, 8+16*order*count)
            wave = span(donor_wave, source, length)
            at = (len(waves)+15) & ~15
            waves.extend(bytes(at-len(waves))+wave)
            struct.pack_into('>3I', sample, 4, at, append(loop_data, 'loop'), append(book_data, 'book'))
            struct.pack_into('>I', inst, field, append(bytes(sample), 'sample'))
        pointer = append(bytes(inst), 'instrument')
        struct.pack_into('>I', bank, 8+index*4, pointer)
        installed.append({'instrument': index, 'offset': pointer,
                          'source_instrument_sha256': sha256(original)})
    bank.extend(bytes((-len(bank)) % 16))
    waves.extend(bytes((-len(waves)) % 16))
    if u32(bank, 8+83*4):
        raise ValueError('Unused voice-bank identity 83 became occupied')
    for index in range(83):
        if (instrument(native_bank, native_wave, index, 83, extended=True)
                != instrument(bank, waves, index, 88, extended=True)):
            raise ValueError('Extended bank changed an original instrument')
    for index in sorted(missing):
        if instrument(bank, waves, index, 88, extended=True) != missing[index]:
            raise ValueError('Extended bank changed a donor instrument')
    return bytes(bank), bytes(waves), {'bank_id': 2, 'wave_id': 2,
        'native_instrument_count': 83, 'instrument_count': 88, 'empty_slots': [83],
        'imports': installed, 'original_data_shift': shift,
        'reused_original_structures': reused,
        'font_bytes': len(bank), 'font_growth_bytes': len(bank)-len(native_bank),
        'wave_bytes': len(waves), 'wave_growth_bytes': len(waves)-len(native_wave),
        'font_sha256': sha256(bank), 'wave_sha256': sha256(waves),
        'runtime_installed': False, 'audio_allocation_verified': False}


def build_audio(native, dol, audio, *, villagers=None, extended=False):
    verified_rom(native)
    if sha256(dol.data) != DOL_SHA or sha256(audio) != AUDIO_SHA:
        raise ValueError('Unverified donor audio source')
    files = by_vrom(native)
    code = files[CODE_VROM].extract(native)
    def nr(address, size):
        return span(code, address - CODE_RAM, size)
    interpreter = extended_native_interpreter(nr) if extended else None
    native_sources = {k: files[v].extract(native) for k, v in NATIVE_FILES.items()}
    gc_sources = {}
    for i, kind in enumerate(('seq', 'bank', 'wave')):
        e = header_entry(dol.read, 0x800CE450, i)
        start, length = struct.unpack_from('>II', e)
        gc_sources[kind] = span(audio, start, length)
    melody, _ = resource(dol.read, GC_SECTIONS, gc_sources, 'seq', 248)
    native_melody, _ = resource(nr, NATIVE_HEADERS, native_sources, 'seq', 205)
    # The main control sequence, not the source container holding the fragments,
    # supplies their bank map. Selector 3 resolves to actual bank 2 in both games.
    mappings = []
    for read, base, index in ((dol.read, 0x800CE490, 242), (nr, 0x80115D80, 199)):
        at = struct.unpack('>H', read(base + index * 2, 2))[0]
        count = read(base + at, 1)[0]
        mapping = read(base + at + 1, count)
        if count != 4 or mapping[count - 3 - 1] != 2:
            raise ValueError('Main melody control sequence no longer binds bank 2')
        mappings.append(list(mapping))
    nbank, nb = resource(nr, NATIVE_HEADERS, native_sources, 'bank', 2)
    gbank, gb = resource(dol.read, GC_SECTIONS, gc_sources, 'bank', 2)
    if nb[10:12] != b'\x02\xff' or gb[10:12] != nb[10:12]:
        raise ValueError('Pilot instruments have different wave-bank bindings')
    nwave, _ = resource(nr, NATIVE_HEADERS, native_sources, 'wave', 2)
    gwave, _ = resource(dol.read, GC_SECTIONS, gc_sources, 'wave', 2)
    native_lengths = struct.unpack('>256I', nr(0x80119240, 1024))
    native_offsets = struct.unpack('>256I', nr(0x80119640, 1024))
    reference_programs = {}
    for voice, (offset, size) in enumerate(zip(native_offsets, native_lengths)) if not extended else ():
        seq = span(native_melody, offset, size)
        offsets = struct.unpack_from('>19H', seq, 4)
        for at in offsets:
            if at < 42 or at + 7 >= len(seq) or seq[at:at + 2] != b'\xEB\x03' or seq[at + 3] != 0x78:
                continue
            note = 6 + struct.unpack_from('>h', seq, at + 4)[0]
            if note not in (7, 17) or at + note + 4 > len(seq):
                continue
            end = at + note + (5 if seq[at + note + 1] & 0x80 else 4)
            program = bytearray(seq[at:end])
            if program[-1] != 255 or not 0x40 <= program[note] < 0x80:
                continue
            if note == 17 and tuple(program[i] for i in (6, 8, 12)) != (0xE3, 0xE2, 0xE1):
                continue
            reference_programs.setdefault(program_shape(program, note), {'voice': voice, 'offset': at})
    artifacts, reports, instruments, missing = {}, [], {}, {}
    roster = [(name.capitalize(), donor, voice) for name, (donor, voice) in PILOTS.items()] if villagers is None else villagers
    for name, donor_id, voice in roster:
        size = u32(dol.read(0x800A9B98 + voice * 4, 4), 0)
        offset = u32(dol.read(0x800AA044 + voice * 4, 4), 0)
        sequence = span(melody, offset, size)
        programs = extended_sequence_programs(sequence) if extended else sequence_programs(sequence)
        proofs = []
        for program in programs:
            normalized = program.pop('normalized')
            if not extended and normalized not in reference_programs:
                raise ValueError('Donor melody program has no verified native command counterpart')
            proof = {'native_interpreter_verified': True} if extended else {'native_program': reference_programs[normalized]}
            proofs.append({**program, **proof})
            for inst in program.get('instruments', [program['instrument']]):
                if inst not in instruments:
                    donor = instrument(gbank, gwave, inst, gb[12], extended=extended)
                    if extended and inst >= nb[12]:
                        missing[inst] = donor
                    else:
                        original = instrument(nbank, nwave, inst, nb[12], extended=extended)
                        if donor != original:
                            raise ValueError(f'Melody instrument {inst} envelope, tuning, or samples differ')
                    instruments[inst] = donor
        file = (f'{donor_id:04x}' if extended else name.lower()) + '.n64melody.bin'
        artifacts[file] = sequence
        reports.append({'id': f'GAFE01-r0/villager/{donor_id:04X}', 'name': name,
            'voice': voice, 'file': file, 'bytes': size, 'donor_offset': offset,
            'sha256': sha256(sequence), 'tracks': proofs, 'runtime_installed': False})
    extension = None
    if missing:
        font, wave, extension = extend_voice_bank(nbank, nwave, gbank, gwave, missing)
        artifacts['villager.soundfont.bin'], artifacts['villager.wave.bin'] = font, wave
    return artifacts, {'format': 'AFV3-VILLAGER-AUDIO-2' if extended else 'AFV3-VILLAGER-AUDIO-1', 'donor_dol_sha256': DOL_SHA,
        'donor_audio_sha256': AUDIO_SHA, 'source_sha256': sha256(native),
        'main_sequence_bank_maps': {'donor': mappings[0], 'native': mappings[1]},
        'shared_instrument_bank': 2, 'shared_wave_bank': 2,
        'instruments': instruments, 'villagers': reports, 'playback_verified': False,
        **({'native_interpreter': interpreter, 'instrument_extension': extension} if extended else {})}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--all-villagers', action='store_true', help='Convert the full verified twenty-villager roster')
    args = p.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'build') or out.exists():
        raise ValueError('Use a fresh directory in ignored build/')
    dol, audio = read_audio_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    roster = None
    if args.all_villagers:
        from v3_villager_assets_runtime import ART, ART_SHA
        manifest = (ART/'art.json').read_bytes()
        if sha256(manifest) != ART_SHA:
            raise ValueError('Changed complete donor roster')
        roster = [(r['name'], int(r['id'].split('/')[-1], 16), r['donor_voice_id'])
                  for r in json.loads(manifest)['villagers']]
        if len(roster) != 20 or {r[1] for r in roster} != set(range(216, 236)):
            raise ValueError('Incomplete additional donor voice set')
    assets, report = build_audio((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), dol, audio,
                                villagers=roster, extended=args.all_villagers)
    out.mkdir(parents=True)
    for name, data in assets.items():
        write_new(out / name, data)
    write_new(out / 'audio.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'output': str(out), 'villagers': len(report['villagers']),
                      'instruments': list(report['instruments']), 'instrument_extension': report.get('instrument_extension')}))


if __name__ == '__main__':
    main()
