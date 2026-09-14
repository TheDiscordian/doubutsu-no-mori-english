"""Extract the actual speed-bag sound and bind its complete native audio structures.

This produces local resources, not a registered sound. The main sound sequence,
font/wave tables, and their runtime allocation still need an installer.
"""
import argparse
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32, verified_rom
from apply_translation import write_new
from v3_import_catalog import ROOT
from v3_villager_audio import (AUDIO_SHA, DOL_SHA, GC_SECTIONS, NATIVE_FILES,
                              NATIVE_HEADERS, header_entry, read_audio_donor, resource, span)

PARTS = {
    'program': (27, 'e640c40b7f7731e00b4bcbfe111e884ce50d6cc3cd485c3129922a2b789849a6'),
    'instrument': (32, '4467e0497f2a3df0773005701a7e6045a0c640008b12981a022e6fd8530cbf6d'),
    'envelope': (12, 'ae32d6d76b151c21afa182933895272f01050f66d813eb886718f273d44e97dd'),
    'sample': (16, 'c132027f066b8dc45cfdcea88f6533c70118615e910735af68928b7a24df1561'),
    'loop': (48, '9d50335f7aa4807899cf4c0ad95d049e87f2bf67affcf118b1f62f1d13425151'),
    'book': (72, '2f8c7d39ef2cc7776a5fda2a8b606e00b23aa7ea39d454dff7711c59ce864256'),
    'wave': (11062, '228e4965358c5a8f1744b620a1b75df81b09cbecf8c6fb1777cfca91b5c86b23')}


def verify_parts(parts):
    if set(parts) != set(PARTS) or any((len(parts[k]), sha256(parts[k])) != identity
                                     for k, identity in PARTS.items()):
        raise ValueError('Changed or incomplete actual speed-bag sound')


def extract(native, dol, audio):
    verified_rom(native)
    if sha256(dol.data) != DOL_SHA or sha256(audio) != AUDIO_SHA:
        raise ValueError('Unverified speed-bag audio donor')
    files = by_vrom(native)
    code = files[CODE_VROM].extract(native)
    def nr(at, size): return span(code, at-CODE_RAM, size)
    ns = {k: files[v].extract(native) for k, v in NATIVE_FILES.items()}
    gs = {k: span(audio, *struct.unpack_from('>II', header_entry(dol.read, 0x800CE450, i)))
          for i, k in enumerate(('seq', 'bank', 'wave'))}
    gsfx, _ = resource(dol.read, GC_SECTIONS, gs, 'seq', 242)
    nsfx, _ = resource(nr, NATIVE_HEADERS, ns, 'seq', 199)
    if (sha256(gsfx) != '790526e46582305f94eb05851337ccab5b8aa248c451e98f99f2d65965ab2a22'
            or sha256(nsfx) != '58c01203fb544ef1eeffb0311094fd941868cd850fd9bb726f8f929a9f4388ca'
            or struct.unpack_from('>6H', gsfx, 0x188) != (0x194, 0x294, 0x3B7E, 0x3C20, 0x394, 0x46A)
            or struct.unpack_from('>6H', nsfx, 0x188) != (0x194, 0x27C, 0x2ED8, 0x2F6A, 0x33E, 0x3DA)
            or struct.unpack_from('>H', gsfx, 0x294+0x76*2)[0] != 0x62B):
        raise ValueError('Changed sound dispatcher or donor speed-bag entry')
    for read, table, sequence, expected_bank in ((dol.read, 0x800CE490, 242, 154),
                                                (nr, 0x80115D80, 199, 140)):
        offset = struct.unpack('>H', read(table+sequence*2, 2))[0]
        mapping = read(table+offset, 5)
        if mapping[0] != 4 or mapping[3] != expected_bank:
            raise ValueError('Changed sound selector-one bank mapping')
    bank, entry = resource(dol.read, GC_SECTIONS, gs, 'bank', 154)
    wave, _ = resource(dol.read, GC_SECTIONS, gs, 'wave', 5)
    if entry[10:13] != bytes((5, 255, 118)):
        raise ValueError('Changed donor sound-font instrument/wave identity')
    inst = span(bank, u32(bank, 8+0x67*4), 32)
    sample = span(bank, u32(inst, 16), 16)
    flags, start, loop, book = struct.unpack('>4I', sample)
    parts = {'program': span(gsfx, 0x62B, 27), 'instrument': inst,
             'envelope': span(bank, u32(inst, 4), 12), 'sample': sample,
             'loop': span(bank, loop, 48), 'book': span(bank, book, 72),
             'wave': span(wave, start, flags)}
    verify_parts(parts)
    native_wave, _ = resource(nr, NATIVE_HEADERS, ns, 'wave', 5)
    # The same numeric ID is outside the native group's 97 entries. Its bytes
    # resolve into another table and must never be treated as a matching sound.
    if native_wave.find(parts['wave']) >= 0:
        raise ValueError('Native wave identity review needs updating')
    return parts, {'donor_sound_id': '0176', 'donor_sequence': 242, 'native_sequence': 199,
                   'donor_bank': 154, 'donor_instrument': 103, 'donor_wave': 5,
                   'native_group_one_entries': 97, 'donor_group_one_entries': 128,
                   'native_same_numeric_id_valid': False,
                   'source_sequence_sha256': sha256(gsfx), 'native_sequence_sha256': sha256(nsfx),
                   'sample_absent_from_native_wave_five': True}


def bind_font(parts):
    """One native-compatible instrument font with all bank-relative pointers.

    A future installer may append these resources to an existing font instead.
    Sample address zero is relative to the supplied standalone wave resource.
    """
    verify_parts(parts)
    offsets = {'instrument': 0x10, 'envelope': 0x30, 'sample': 0x3C, 'loop': 0x4C, 'book': 0x7C}
    font = bytearray(0xD0)
    struct.pack_into('>I', font, 8, offsets['instrument'])
    for name, at in offsets.items(): font[at:at+len(parts[name])] = parts[name]
    pointers = {0x14: offsets['envelope'], 0x20: offsets['sample'],
                0x44: offsets['loop'], 0x48: offsets['book']}
    for at, target in pointers.items(): struct.pack_into('>I', font, at, target)
    struct.pack_into('>I', font, 0x40, 0)
    return bytes(font), {'instrument_count': 1, 'drum_count': 0, 'sound_effect_count': 0,
                        'offsets': offsets, 'bank_relative_pointers': {str(k): v for k, v in pointers.items()},
                        'wave_relative_sample_address': 0, 'sample_bytes': len(parts['wave'])}


def bind_program(parts, offset, bank_selector, instrument):
    """Bind channel -> note layer -> custom envelope, preserving timing/tuning."""
    verify_parts(parts)
    if (not 0 <= offset <= 0x10000-27 or not 0 <= bank_selector <= 255
            or not 0 <= instrument <= 125):
        raise ValueError('Speed-bag program binding exceeds native operands')
    program = bytearray(parts['program'])
    program[1], program[2] = bank_selector, instrument
    struct.pack_into('>H', program, 4, offset+7)
    struct.pack_into('>H', program, 8, offset+15)
    return bytes(program)


def build(native, dol, audio, out):
    parts, source = extract(native, dol, audio)
    font, layout = bind_font(parts)
    # Zero-based fragment with placeholder bank selector. This is deliberately
    # not registered or executable until the installer supplies a real binding.
    program = bind_program(parts, 0, 0, 0)
    out.mkdir(parents=True, exist_ok=False)
    for name, data in (('speed-bag.soundfont.bin', font), ('speed-bag.wave.bin', parts['wave']),
                       ('speed-bag.sequence-fragment.bin', program)):
        write_new(out/name, data)
    report = {'format': 'AFV3-SPEED-BAG-AUDIO-1', 'source': source,
              'source_dol_sha256': DOL_SHA, 'source_audio_sha256': AUDIO_SHA,
              'source_parts': {k: {'bytes': len(v), 'sha256': sha256(v)} for k, v in parts.items()},
              'font': {'bytes': len(font), 'sha256': sha256(font), **layout},
              'program': {'bytes': len(program), 'sha256': sha256(program),
                          'binding_required': True, 'layer_offset': 7, 'envelope_offset': 15,
                          'note': 32, 'delay': 110, 'velocity': 120, 'decay': 240},
              'runtime_installed': False, 'native_synthesis_tested': False,
              'public_or_local_patcher_changed': False}
    write_new(out/'audio.json', (json.dumps(report, indent=2)+'\n').encode())
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--disc', type=Path, default=ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    dol, audio = read_audio_donor(args.disc)
    print(json.dumps(build((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), dol, audio, args.output), indent=2))


if __name__ == '__main__':
    main()
