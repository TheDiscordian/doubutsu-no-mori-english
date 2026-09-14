"""Native melody loading and full-ID checks, without physical audio playback."""
import json
from pathlib import Path
import struct

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from runtime_layout import MODULE_RAM, TEST_STACK
from v3_asset_loader import BLOB, BLOB_RAM
from v3_audio_runtime import STATE


def exercise(debug, rom_path, record):
    path = Path(rom_path)
    rom = path.read_bytes()
    report = json.loads((path.parent / 'build.json').read_text())
    if sha256(rom) != report['output_sha256'] or not report['villager_audio']:
        raise ValueError('V3 audio fixture needs its exact current cartridge')
    files = by_vrom(rom)
    blob = files[BLOB].extract(rom)
    expected_blob = bytearray(blob)
    code = files[CODE_VROM].extract(rom)

    def check(label, address, expected):
        actual = debug.read_memory(address, len(expected))
        record({'v3_audio_check': label, 'address': f'{address:08X}', 'bytes': len(expected),
                'assertion': 'passed' if actual == expected else 'failed',
                'expected_sha256': sha256(expected), 'observed_sha256': sha256(actual)})
        if actual != expected:
            raise ValueError('V3 audio check failed: ' + label)

    def call(address, args, expected=None):
        result = debug.call(f'{address:08X}', args, return_address=MODULE_RAM + 0x6480)
        record(result)
        if expected is not None and result['return_value'] != expected:
            raise ValueError('Unexpected native melody result')
        return result['return_value']

    check('complete startup blob', BLOB_RAM, blob)
    check('startup installed', 0x8019ACD0, struct.pack('>I', 1))
    sequence = u32(debug.read_memory(0x8014CBA8, 4), 0)
    if sequence % 16 or not 0x8019C8E0 <= sequence <= 0x80400000 - 0x4C30:
        raise ValueError('Native main sequence is not loaded in checked RAM')
    check('main sequence header', sequence, bytes.fromhex('FB0006003A10'))
    notes = MODULE_RAM + 0x6500
    debug.write_memory(notes, bytes((0, 2, 4, 5, 7, 9, 11, 12, 11, 9, 7, 5, 4, 2, 0, 14)))
    edge = b'V3AU' * 4
    for address in (notes - 16, notes + 16, TEST_STACK - 0x800, TEST_STACK + 0x40):
        debug.write_memory(address, edge)

    original_audio = files[0x27130].extract(rom)
    container = u32(code, 0x80115090 - CODE_RAM + 16 + 205 * 16)
    # Real public entry points: ordinary tune, speech tune, then an original ID
    # whose port tag aliases Cheri. No audio helper is replaced with a fixture.
    for voice, track, entry in ((285, 15, 0x800FCE80), (286, 6, 0x800FD280), (29, 15, 0x800FCE80)):
        before = bytearray(debug.read_memory(sequence + 0x3A10, 0x1200))
        if voice >= 256:
            row = next(row for row in report['villager_audio']['imports'] if row['voice'] == voice)
            at = int(row['ram'], 16) - BLOB_RAM
            fragment = bytearray(blob[at:at + row['bytes']])
        else:
            offset = u32(code, 0x80119640 - CODE_RAM + voice * 4)
            size = u32(code, 0x80119240 - CODE_RAM + voice * 4)
            fragment = bytearray(original_audio[container + offset:container + offset + size])
        relative = 0x3A10 + (0 if track == 6 else 0xC00)
        for i in range(19):
            at = 4 + 2 * i
            pointer = struct.unpack_from('>H', fragment, at)[0]
            struct.pack_into('>H', fragment, at, pointer + relative)
        before[relative - 0x3A10:relative - 0x3A10 + len(fragment)] = fragment
        call(entry, [voice, notes] if entry == 0x800FCE80 else [voice])
        check(f'complete melody pool after voice {voice}', sequence + 0x3A10, bytes(before))
        struct.pack_into('>H', expected_blob, STATE + track * 2, voice)
        check('only owned full-ID state changes', BLOB_RAM, bytes(expected_blob))
        if track == 15:
            call(0x800FD0D4, [29 if voice == 285 else 285], 0xFFFFFFFF)
        record(debug.advance_game_frame())
        record(debug.advance_game_frame())
        check('audio leaves loaded programs intact', sequence + 0x3A10, bytes(before))
        # Observe native port processing without pretending this is listening
        # verification or a complete in-world villager conversation.
        tag = call(0x800EF3C0, [0, track, 2]) & 255
        count = call(0x800EF3C0, [0, track, 4]) & 255
        record({'v3_audio_voice': voice, 'track': track, 'port_tag': tag, 'note_count': count})
        if tag != voice & 255:
            raise ValueError('Native audio thread did not consume the full-ID melody start')
    for address in (notes - 16, notes + 16, TEST_STACK - 0x800, TEST_STACK + 0x40):
        check('fixture guard', address, edge)
    check('translation guard', 0x8019C8D0, bytes.fromhex('AF32C0DE') * 4)
    check('no faulted thread', 0x8003CE34, bytes(4))
    return {'native_imported_melodies': 2, 'native_original_melodies': 1,
            'low_byte_alias_rejected_both_ways': True, 'physical_audio_played': False,
            'complete_villager_conversation': False, 'requires_checkpoint_restore': True}
