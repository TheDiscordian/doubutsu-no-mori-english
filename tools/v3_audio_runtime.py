"""Bind verified melody assets and wider native audio entry points."""
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_villager_audio import build_audio

ABI = 3
TABLE, STATE, DATA = 0x2900, 0x2B00, 0x3000
SOURCES = ('tools/v3_audio_runtime.py', 'tools/v3_villager_audio.py', 'overlays/v3/melody.c')
WIDE_PATCHES = {
    0x800F922C: (0x29C10100, 0x29C1012B),  # Na_VoiceSe accepts the donor's full range.
    0x800FCE9C: (0x308700FF, 0x3087FFFF),  # Na_Inst low sixteen bits.
    0x800FCEB4: (0xA3A7001B, 0xA7A7001A),  # Preserve a complete ID across subtrack selection.
    0x800FCEC0: (0x93A4001B, 0x97A4001A),
    0x800FD298: (0x30E400FF, 0x30E4FFFF),  # Na_MelodyVoice forwards complete IDs.
}


def install(native, code, blob, symbols, donor):
    assets, audio = build_audio(native, *donor)
    original = by_vrom(native)[CODE_VROM].extract(native)
    for start, end in ((0x800F91FC, 0x800F9C24), (0x800FCE80, 0x800FD2C8)):
        if code[start - CODE_RAM:end - CODE_RAM] != original[start - CODE_RAM:end - CODE_RAM]:
            raise ValueError('Native voice or melody code is no longer the reviewed implementation')
    if len(blob) != 0x4000 or any(blob[TABLE:0x3FF0]):
        raise ValueError('V3 audio metadata/state/data reservation is occupied')
    at = DATA
    installed = []
    for row in sorted(audio['villagers'], key=lambda r: r['voice']):
        data = assets[row['file']]
        if at + len(data) > len(blob) - 16:
            raise ValueError('Imported melodies exceed the V3 resident reservation')
        blob[at:at + len(data)] = data
        struct.pack_into('>II', blob, TABLE + (row['voice'] - 256) * 8, 0x80460000 + at, len(data))
        installed.append({'id': row['id'], 'voice': row['voice'], 'bytes': len(data),
            'ram': f'{0x80460000 + at:08X}', 'sha256': sha256(data)})
        at += len(data)
    blob[STATE:STATE + 32] = b'\xFF' * 32
    for address, (expected, replacement) in WIDE_PATCHES.items():
        if u32(code, address - CODE_RAM) != expected:
            raise ValueError('Changed eight-bit voice narrowing instruction')
        struct.pack_into('>I', code, address - CODE_RAM, replacement)
    hooks = ((0x800FCEEC, 'af_v3_melody_start', (0x27BDFFB8, 0xAFA5004C)),
             (0x800FD0D4, 'af_v3_melody_count', (0x27BDFFE0, 0xAFBF0014)))
    for address, helper, expected in hooks:
        target = symbols[helper]
        if (struct.unpack_from('>2I', code, address - CODE_RAM) != expected
                or not 0x80460100 <= target < 0x80461000):
            raise ValueError('Changed native melody entry or invalid V3 helper')
        struct.pack_into('>2I', code, address - CODE_RAM, 0x08000000 | (target >> 2 & 0x3FFFFFF), 0)
    control = by_vrom(native)[0x27130].extract(native)
    seq_at = 0x80115090 - CODE_RAM + 16 + 199 * 16
    offset, size = struct.unpack_from('>II', original, seq_at)
    if size != 0x4C30 or control[offset:offset + 6] != bytes.fromhex('FB0006003A10'):
        raise ValueError('Changed native main-sequence melody reservation')
    return {'imports': installed, 'conversion': audio, 'mutable_voice_state': '80462B00',
            'full_native_playback_test': 'pending', 'main_sequence': 199,
            'native_instruments_and_samples_reused': True}
