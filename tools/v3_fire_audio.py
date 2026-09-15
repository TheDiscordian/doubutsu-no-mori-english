"""Convert complete camping fire loops against the current native sound resources.

Outputs are local, uninstalled resources. An installer must provide the measured
permanent audio capacity before registering the new level-sound dispatch.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32, verified_rom
from apply_translation import write_new
from v3_import_catalog import ROOT
from v3_villager_audio import (AUDIO_SHA, DOL_SHA, GC_SECTIONS, NATIVE_HEADERS,
    extended_envelope, extended_native_interpreter, header_entry, instrument,
    read_audio_donor, resource, span)
from v3_speed_bag_sound_runtime import permanent_budget

BASE = ROOT / 'build/v3-tent-model-loader-01'
BASE_SHA = '6655157c072b0b2e291224c1f22e5d4c45ed9a6299c5a6e478ecaaaf257c35de'
REPORT_SHA = '82c4ba4a5067d3debd19c5c459205efcba12c005bd371d627326f654b79950e0'
NATIVE_VROMS = {'seq': 0x01920000, 'bank': 0x019F0000, 'wave': 0x01A50000}
PROGRAMS = {
    'bonfire': (0x5C, 0x2F08, 82, '8eb66e7c1b104eada7db882dc40044660e4dc2d1c3b93e66fe42dd2f9746cd84'),
    'campfire': (0x5D, 0x2F5A, 80, '8c8ed22bce448775cbdb3a50c382f45367cc174334b7d27aafc645c1b7d22d7b'),
}
PARTS = {
    12: {
        'instrument': (32, 'f0c78b03861774a9e14207f7371a764ac6b3659547667a26465fb3fbcca7ece3'),
        'envelope': (12, 'ae32d6d76b151c21afa182933895272f01050f66d813eb886718f273d44e97dd'),
        'sample': (16, '260062ae34c7a7903735a901b5a0d576b19d305e075e5bba393e259318f3db2f'),
        'loop': (48, 'e0147e54f4ad53d7787850b887c8dd524369dd9f2b518d031d30e917ffdc71f7'),
        'book': (72, '5143eeb38adcf864c1c1c53fc58fca1df272f2e17adaabce39734212e0d21f68'),
        'wave': (18514, 'e9670f4ab5ecf3c7dcc78f2fbd8ff5541a4d440923768825c3a86cfe1c6031c8'),
    },
    14: {
        'instrument': (32, '144e71a22e73a8b853e57b96224c3a0c3285bec1b206a0ffcc3bd9853c9d16ad'),
        'envelope': (12, 'ae32d6d76b151c21afa182933895272f01050f66d813eb886718f273d44e97dd'),
        'sample': (16, '8be817b0388cbbf4bf2d4d47884ad8eb43365217d947db1c71ecaf3fc0453849'),
        'loop': (16, '4309c50ef7489a46820c61f4c873f9b23cc226a6adeddca0374c881e5a4948ed'),
        'book': (72, '86b61a1998a3517c54464e53d6c8a600a8102b201046efc86e48ff0aac61c320'),
        'wave': (2826, 'fff06893ec27f2da9bc8c9075ee5f2ed9f35087f4f59330f5dd590f883e87b9f'),
    },
}


def verify_parts(parts):
    if set(parts) != set(PARTS):
        raise ValueError('Missing fire sound instrument')
    for index, expected in PARTS.items():
        if set(parts[index]) != set(expected) or any(
                (len(parts[index][k]), sha256(parts[index][k])) != v for k, v in expected.items()):
            raise ValueError('Changed or incomplete fire instrument dependency')


def parse_program(data, base, *, prefix=False):
    """Parse the complete two-layer fire forms, including every loop target.

    No general sequence rewriting: the inspected native interpreter supplies
    large notes, rests, C2/C4/C6/CB, and FB. Unknown or unreachable bytes reject.
    """
    start = 4 if prefix else 0
    if len(data) < start + 16:
        raise ValueError('Truncated fire program')
    if prefix and (data[0] != 0xEB or data[1] > 3 or data[2] > 125 or data[3] != 0xC4):
        raise ValueError('Invalid explicit native bank/large-note prefix')
    if tuple(data[start + i] for i in (0, 3, 6)) != (0x88, 0x89, 0xFF):
        raise ValueError('Incomplete two-layer fire channel')
    layers = [struct.unpack_from('>H', data, start + i)[0] - base for i in (1, 4)]
    if layers[0] != start + 7 or not layers[0] < layers[1] < len(data):
        raise ValueError('Fire layer pointers escape their program')
    pointers = [start + 1, start + 4]
    instruments, envelopes, tracks = [], [], []

    def duration(at):
        value = span(data, at, 1)[0]
        end = at + 1
        if value & 128:
            value = (value & 127) * 256 + span(data, end, 1)[0]
            end += 1
        if not value:
            raise ValueError('Zero-duration fire event')
        return value, end

    for number, begin in enumerate(layers):
        at, events, starts, elapsed = begin, [], set(), 0
        while at < len(data):
            op = data[at]
            starts.add(at)
            event = {'offset': at, 'opcode': f'{op:02X}'}
            at += 1
            if 0x40 <= op <= 0x7F:
                delay, at = duration(at)
                velocity = span(data, at, 1)[0]
                at += 1
                if velocity > 127:
                    raise ValueError('Invalid fire velocity')
                event.update(note=op & 63, duration=delay, velocity=velocity)
                elapsed += delay
            elif op == 0xC0:
                delay, at = duration(at)
                event['rest'] = delay
                elapsed += delay
            elif op in (0xC2, 0xC6):
                value = span(data, at, 1)[0]
                if op == 0xC6:
                    if value > 125:
                        raise ValueError('Fire uses a reserved instrument')
                    instruments.append(at)
                    event['instrument'] = value
                else:
                    event['transpose'] = value
                at += 1
            elif op == 0xC4:
                event['continuous'] = True
            elif op == 0xCB:
                pointer, decay = struct.unpack('>HB', span(data, at, 3))
                target = pointer - base
                if pointer & 1 or span(data, target, 8) != bytes.fromhex('00327FBCFFFF0000'):
                    raise ValueError('Invalid or misaligned complete fire envelope')
                pointers.append(at)
                envelopes.append(target)
                event.update(envelope=target, decay=decay)
                at += 3
            elif op == 0xFB:
                target = struct.unpack('>H', span(data, at, 2))[0] - base
                if target not in starts or not any(
                        e['offset'] >= target and ('duration' in e or 'rest' in e) for e in events):
                    raise ValueError('Fire loop is outside its layer or has no elapsed time')
                pointers.append(at)
                at += 2
                event['loop'] = target
                events.append(event)
                break
            else:
                raise ValueError(f'Unreviewed fire note opcode {op:02X}')
            events.append(event)
        if not events or 'loop' not in events[-1]:
            raise ValueError('Unterminated fire loop')
        tracks.append({'start': begin, 'end': at, 'first_cycle_ticks': elapsed, 'events': events})
        if number == 0 and at != layers[1]:
            raise ValueError('Unaccounted bytes between fire layers')
    if (len(envelopes) != 1 or len(instruments) != 2 or envelopes[0] != at + 1
            or data[at] != 0 or envelopes[0] + 8 != len(data)):
        raise ValueError('Unaccounted fire program/envelope data')
    return {'pointers': pointers, 'instruments': instruments, 'envelope': envelopes[0], 'layers': tracks}


def bind_program(name, source, offset, selector=1, mapping=None):
    mapping = {12: 72, 14: 73} if mapping is None else mapping
    _, origin, size, digest = PROGRAMS[name]
    if (len(source), sha256(source)) != (size, digest):
        raise ValueError('Changed complete source fire program')
    if (offset < 0 or offset & 1 or offset + size + 4 > 0x10000 or not 0 <= selector <= 3
            or set(mapping) != {12, 14} or any(not 0 <= i <= 125 for i in mapping.values())):
        raise ValueError('Fire program binding exceeds native operands or envelope alignment')
    parsed = parse_program(source, origin)
    result = bytearray(bytes((0xEB, selector, mapping[12], 0xC4)) + source)
    for at in parsed['pointers']:
        target = struct.unpack_from('>H', source, at)[0] - origin
        struct.pack_into('>H', result, at + 4, offset + 4 + target)
    for at in parsed['instruments']:
        result[at + 4] = mapping[source[at]]
    parse_program(result, offset, prefix=True)
    return bytes(result)


def extract(dol, audio):
    if sha256(dol.data) != DOL_SHA or sha256(audio) != AUDIO_SHA:
        raise ValueError('Unverified fire sound donor')
    gs = {k: span(audio, *struct.unpack_from('>II', header_entry(dol.read, 0x800CE450, i)))
          for i, k in enumerate(('seq', 'bank', 'wave'))}
    sequence, _ = resource(dol.read, GC_SECTIONS, gs, 'seq', 242)
    bank, header = resource(dol.read, GC_SECTIONS, gs, 'bank', 153)
    wave, _ = resource(dol.read, GC_SECTIONS, gs, 'wave', 5)
    if (sha256(sequence) != '790526e46582305f94eb05851337ccab5b8aa248c451e98f99f2d65965ab2a22'
            or header[10:13] != bytes((5, 255, 126))):
        raise ValueError('Changed donor fire dispatcher or font')
    parts, programs, descriptions = {}, {}, {}
    for name, (sid, at, size, digest) in PROGRAMS.items():
        if struct.unpack_from('>H', sequence, 0x2E02 + sid * 2)[0] != at:
            raise ValueError('Donor fire loop does not use the reviewed level table')
        data = span(sequence, at, size)
        if sha256(data) != digest:
            raise ValueError('Changed donor fire loop')
        parse_program(data, at)
        programs[name] = data
    for index in PARTS:
        inst = span(bank, u32(bank, 8 + index * 4), 32)
        sample = span(bank, u32(inst, 16), 16)
        size, start, loop, book = struct.unpack('>4I', sample)
        parts[index] = {'instrument': inst, 'envelope': extended_envelope(bank, u32(inst, 4)),
            'sample': sample, 'loop': span(bank, loop, 48 if u32(bank, loop + 8) else 16),
            'book': span(bank, book, 8 + 16 * u32(bank, book) * u32(bank, book + 4)),
            'wave': span(wave, start, size)}
        descriptions[index] = instrument(bank, wave, index, 126, extended=True)
    verify_parts(parts)
    return parts, programs, descriptions


def append_font(bank, wave, parts):
    verify_parts(parts)
    if len(bank) != 0x2AB0 or bank[:8] != bytes(8) or bank[0x128:0x130] != bytes(8) or len(wave) & 15:
        raise ValueError('Changed current sound-font spare slots or wave alignment')
    # A complete semantic comparison after appending checks all 72 retained
    # instruments. First also prove no pointed resource overlaps the spare words.
    original = [instrument(bank, wave, i, 72, extended=True) for i in range(72)]
    for i in range(72):
        inst_at = u32(bank, 8 + 4 * i)
        ptrs = [inst_at, u32(bank, inst_at + 4)]
        for field in (8, 16, 24):
            p = u32(bank, inst_at + field)
            if p:
                ptrs.extend((p, u32(bank, p + 8), u32(bank, p + 12)))
        if any(p < 0x130 or p & 3 for p in ptrs):
            raise ValueError('Native sound resource reaches a spare table word')
    result, waves, rows = bytearray(bank), bytearray(wave), []

    def append(data):
        result.extend(bytes(-len(result) % 16))
        at = len(result)
        result.extend(data)
        return at

    for source, target in ((12, 72), (14, 73)):
        p = parts[source]
        waves.extend(bytes(-len(waves) % 16))
        wave_at = len(waves)
        waves.extend(p['wave'])
        inst, sample = bytearray(p['instrument']), bytearray(p['sample'])
        struct.pack_into('>I', inst, 4, append(p['envelope']))
        struct.pack_into('>3I', sample, 4, wave_at, append(p['loop']), append(p['book']))
        struct.pack_into('>I', inst, 16, append(sample))
        pointer = append(inst)
        struct.pack_into('>I', result, 8 + 4 * target, pointer)
        rows.append({'donor_instrument': source, 'native_instrument': target,
            'instrument_offset': pointer, 'wave_offset': wave_at, 'sample_bytes': len(p['wave'])})
    result.extend(bytes(-len(result) % 16))
    waves.extend(bytes(-len(waves) % 16))
    for i, before in enumerate(original):
        if instrument(result, waves, i, 74, extended=True) != before:
            raise ValueError('Fire append modifies an existing native/speed-bag instrument')
    return bytes(result), bytes(waves), rows


def prepare(current, report, donor):
    if sha256(current) != BASE_SHA or report['output_sha256'] != BASE_SHA:
        raise ValueError('Fire audio requires the complete current cartridge')
    files = by_vrom(current)
    code = files[CODE_VROM].extract(current)
    read = lambda at, size: span(code, at - CODE_RAM, size)
    interpreter = extended_native_interpreter(read)
    sources = {k: files[v].extract(current) for k, v in NATIVE_VROMS.items()}
    sequence, se = resource(read, NATIVE_HEADERS, sources, 'seq', 199)
    bank, be = resource(read, NATIVE_HEADERS, sources, 'bank', 140)
    wave, we = resource(read, NATIVE_HEADERS, sources, 'wave', 5)
    if (len(sequence) != 0x4D20 or be[10:13] != bytes((5, 255, 72)) or we[9] != 4
            or sequence[0x164:0x188] != bytes.fromhex(
                'E9EEC4DC7FECC600D800FE65C8FFFA017E60F2F6C2265CE4F4F090919293CC0075FB016E')):
        raise ValueError('Changed native level-sound dispatch or current font')
    for reader, table, sid, mapping in ((read, 0x80115D80, 199, bytes((4, 2, 141, 140, 139))),
            (donor[0].read, 0x800CE490, 242, bytes((4, 2, 155, 154, 153)))):
        at = struct.unpack('>H', reader(table + sid * 2, 2))[0]
        if reader(table + at, 5) != mapping:
            raise ValueError('Changed native/donor level-sound font selection')
    parts, programs, descriptions = extract(*donor)
    new_bank, new_wave, imports = append_font(bank, wave, parts)
    for row in imports:
        if instrument(new_bank, new_wave, row['native_instrument'], 74, extended=True) != descriptions[row['donor_instrument']]:
            raise ValueError('Native fire instrument differs from complete donor')
    new_seq = bytearray(sequence)
    table = len(new_seq)
    no_op = table + 128 * 2
    new_seq.extend(sequence[0x265C:0x26E4] + struct.pack('>H', no_op) * (128 - 68))
    new_seq.extend(bytes((0xFF, 0)))
    converted = {}
    for name, (sid, _, _, _) in PROGRAMS.items():
        at = len(new_seq)
        data = bind_program(name, programs[name], at)
        new_seq.extend(data)
        struct.pack_into('>H', new_seq, table + sid * 2, at)
        converted[name] = {'sound_id': sid, 'offset': at, 'bytes': len(data), 'sha256': sha256(data),
            'parsed': parse_program(data, at, prefix=True)}
    new_seq.extend(bytes(-len(new_seq) % 16))
    # The original C2 instruction remains; only its two-byte table operand moves.
    if sequence[0x178:0x17B] != bytes.fromhex('C2265C'):
        raise ValueError('Changed native level-table operand')
    struct.pack_into('>H', new_seq, 0x179, table)
    old_budget = permanent_budget(code)
    growth = sum(((len(b) + 31) & -32) - ((len(a) + 31) & -32)
                 for a, b in ((sequence, new_seq), (bank, new_bank)))
    required = old_budget['conservative_required'] + growth
    metadata = {'format': 'AFV3-FIRE-AUDIO-1', 'base_sha256': BASE_SHA,
        'donor_dol_sha256': DOL_SHA, 'donor_audio_sha256': AUDIO_SHA,
        'source_parts': PARTS, 'native_interpreter': interpreter,
        'retained_instruments': 72, 'instrument_count': 74, 'font': 140, 'wave': 5,
        'imports': imports, 'programs': converted, 'level_table': table,
        'level_table_count': 128, 'original_level_entries': 68, 'reserved_no_op': no_op,
        'original_headers': {'seq': se.hex(), 'bank': be.hex(), 'wave': we.hex()},
        'permanent_audio': {'before': old_budget, 'additional_bytes': growth,
            'required_bytes': required, 'additional_capacity_required': max(0, required - old_budget['capacity']),
            'allocation_change_installed': False},
        'runtime_installed': False, 'native_synthesis_tested': False, 'web_patcher_changed': False}
    return {'seq': bytes(new_seq), 'bank': new_bank, 'wave': new_wave}, metadata


def build(output, disc):
    output = output.resolve()
    if output.exists() or not output.is_relative_to(ROOT / 'build'):
        raise ValueError('Choose a fresh ignored build/ directory')
    verified_rom((ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    raw = (BASE / 'build.json').read_bytes()
    if sha256(raw) != REPORT_SHA:
        raise ValueError('Changed source cartridge report')
    data, report = prepare((BASE / 'animal-forest-v3-asset-loader.z64').read_bytes(),
                           json.loads(raw), read_audio_donor(disc))
    report['resources'] = {k: {'bytes': len(v), 'sha256': sha256(v)} for k, v in data.items()}
    report['converter_sha256'] = sha256(Path(__file__).read_bytes())
    output.mkdir(parents=True)
    for k, v in data.items():
        write_new(output / f'fire.{k}.bin', v)
    write_new(output / 'audio.json', (json.dumps(report, indent=2) + '\n').encode())
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--disc', type=Path, default=ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
    args = parser.parse_args()
    result = build(args.output, args.disc)
    print(json.dumps({'resources': result['resources'], 'permanent_audio': result['permanent_audio']}, indent=2))
