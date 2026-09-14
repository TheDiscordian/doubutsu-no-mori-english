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


def instrument(bank, wave, instrument_id, instrument_count):
    if not 0 <= instrument_id < instrument_count:
        raise ValueError('Missing voice instrument')
    data = span(bank, u32(bank, 8 + instrument_id * 4), 32)
    if data[0] != 0:
        raise ValueError('Instrument unexpectedly pre-relocated')
    envelope = span(bank, u32(data, 4), 12)
    if tuple(struct.unpack_from('>h', envelope, i)[0] for i in (0, 4, 8)) != (-4, 1, -1):
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


def build_audio(native, dol, audio):
    verified_rom(native)
    if sha256(dol.data) != DOL_SHA or sha256(audio) != AUDIO_SHA:
        raise ValueError('Unverified donor audio source')
    files = by_vrom(native)
    code = files[CODE_VROM].extract(native)
    def nr(address, size):
        return span(code, address - CODE_RAM, size)
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
    for voice, (offset, size) in enumerate(zip(native_offsets, native_lengths)):
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
    artifacts, reports, instruments = {}, [], {}
    for name, (donor_id, voice) in PILOTS.items():
        size = u32(dol.read(0x800A9B98 + voice * 4, 4), 0)
        offset = u32(dol.read(0x800AA044 + voice * 4, 4), 0)
        sequence = span(melody, offset, size)
        programs = sequence_programs(sequence)
        proofs = []
        for program in programs:
            normalized = program.pop('normalized')
            if normalized not in reference_programs:
                raise ValueError('Donor melody program has no verified native command counterpart')
            proofs.append({**program, 'native_program': reference_programs[normalized]})
            inst = program['instrument']
            if inst not in instruments:
                donor = instrument(gbank, gwave, inst, gb[12])
                original = instrument(nbank, nwave, inst, nb[12])
                if donor != original:
                    raise ValueError('Pilot melody instrument, envelope, tuning, or samples differ')
                instruments[inst] = donor
        file = name + '.n64melody.bin'
        artifacts[file] = sequence
        reports.append({'id': f'GAFE01-r0/villager/{donor_id:04X}', 'name': name.capitalize(),
            'voice': voice, 'file': file, 'bytes': size, 'donor_offset': offset,
            'sha256': sha256(sequence), 'tracks': proofs, 'runtime_installed': False})
    return artifacts, {'format': 'AFV3-VILLAGER-AUDIO-1', 'donor_dol_sha256': DOL_SHA,
        'donor_audio_sha256': AUDIO_SHA, 'source_sha256': sha256(native),
        'main_sequence_bank_maps': {'donor': mappings[0], 'native': mappings[1]},
        'shared_instrument_bank': 2, 'shared_wave_bank': 2,
        'instruments': instruments, 'villagers': reports, 'playback_verified': False}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    out = args.output.resolve()
    if not out.is_relative_to(ROOT / 'build') or out.exists():
        raise ValueError('Use a fresh directory in ignored build/')
    dol, audio = read_audio_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    assets, report = build_audio((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), dol, audio)
    out.mkdir(parents=True)
    for name, data in assets.items():
        write_new(out / name, data)
    write_new(out / 'audio.json', (json.dumps(report, indent=2) + '\n').encode())
    print(json.dumps({'output': str(out), 'villagers': len(assets), 'shared_instruments': list(report['instruments'])}))


if __name__ == '__main__':
    main()
