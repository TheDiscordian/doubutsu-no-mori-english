"""Complete donor melodies and additive instrument resources, without playback."""
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_villager_audio import (build_audio, extended_envelope, extended_native_interpreter,
    extended_program, extended_sequence_programs, read_audio_donor, header_entry,
    resource, GC_SECTIONS, NATIVE_HEADERS, NATIVE_FILES)
from v3_villager_assets_runtime import ART, ART_SHA


class ParserTests(unittest.TestCase):
    def test_multiple_notes_rest_instrument_switch_and_vibrato(self):
        # Synthetic data, not a copied game melody.
        program = bytes.fromhex('EB0301780009E300E2010203D704FF40808130C005C602410820FF')
        parsed = extended_program(program)
        self.assertEqual(parsed['bytes'], len(program))
        self.assertEqual(parsed['instruments'], [1, 2])
        self.assertEqual(parsed['events'], [
            {'kind': 'note', 'pitch': 0, 'duration': 129, 'velocity': 48, 'instrument': 1},
            {'kind': 'rest', 'duration': 5}, {'kind': 'instrument', 'instrument': 2},
            {'kind': 'note', 'pitch': 1, 'duration': 8, 'velocity': 32, 'instrument': 2}])
        for length in range(len(program)):
            with self.assertRaises(ValueError): extended_program(program[:length])
        for at, value in ((0, 0), (1, 4), (5, 127), (6, 0xE4), (14, 0),
                          (15, 0xC7), (18, 128), (20, 0), (22, 126), (26, 0)):
            changed = bytearray(program); changed[at] = value
            with self.assertRaises(ValueError): extended_program(changed)

    def test_full_track_table_and_final_padding(self):
        program = bytes.fromhex('EB0300780001FF401020FF')
        data = bytearray(256)
        for index in range(19):
            at = 42+len(program)*index
            struct.pack_into('>H', data, 4+2*index, at)
            data[at:at+len(program)] = program
        self.assertEqual(len(extended_sequence_programs(data)), 19)
        for at, value in ((4, 255), (7, 42), (42, 0), (250, 0), (255, 99)):
            changed = data.copy(); changed[at] = value
            with self.assertRaises(ValueError): extended_sequence_programs(changed)
        with self.assertRaises(ValueError): extended_sequence_programs(bytes(0x610))

    def test_long_envelope_keeps_all_points_and_rejects_unknown_control(self):
        data = b''.join(struct.pack('>hh', a, b) for a, b in
                        [(-4, 0), (1, 32000), (30, 16000), (30, 8000), (-1, 0)])
        self.assertEqual(extended_envelope(data+bytes(16), 0), data)
        for length in range(0, len(data), 4):
            with self.assertRaises(ValueError): extended_envelope(data[:length], 0)
        for value in (-2, -3, -4):
            changed = bytearray(data); struct.pack_into('>h', changed, 8, value)
            with self.assertRaises(ValueError): extended_envelope(changed, 0)


@unittest.skipUnless((ROOT/'build/v3-all-villager-audio-02/audio.json').exists(), 'Local complete audio bundle required')
class ActualDonorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        manifest = (ART/'art.json').read_bytes()
        if sha256(manifest) != ART_SHA:
            raise ValueError('Changed complete source roster')
        cls.roster = [(r['name'], int(r['id'].split('/')[-1], 16), r['donor_voice_id'])
                      for r in json.loads(manifest)['villagers']]
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.donor = read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.assets, cls.report = build_audio(cls.native, *cls.donor, villagers=cls.roster, extended=True)
        cls.out = ROOT/'build/v3-all-villager-audio-02'

    def test_complete_twenty_voice_outputs_and_original_pilot_retention(self):
        self.assertEqual(len(self.report['villagers']), 20)
        self.assertEqual({r['voice'] for r in self.report['villagers']}, set(range(260, 278)) | {285, 286})
        self.assertEqual(len(self.report['instruments']), 29)
        for name, data in self.assets.items():
            self.assertEqual(data, (self.out/name).read_bytes())
        self.assertEqual(self.report, json.loads((self.out/'audio.json').read_text(),
            object_pairs_hook=lambda pairs: {int(k) if k.isdecimal() else k: v for k, v in pairs}))
        pilots, _ = build_audio(self.native, *self.donor)
        self.assertEqual(pilots['cheri.n64melody.bin'], self.assets['00e8.n64melody.bin'])
        self.assertEqual(pilots['punchy.n64melody.bin'], self.assets['00eb.n64melody.bin'])
        self.assertTrue(all(len(r['tracks']) == 19 and not r['runtime_installed'] for r in self.report['villagers']))

    def test_native_and_donor_instruments_retain_complete_sound_data(self):
        # build_audio compares every one of the 83 original and four imported
        # instruments, including all envelopes, tunings, samples, loops, and books.
        extension = self.report['instrument_extension']
        self.assertEqual([r['instrument'] for r in extension['imports']], [84, 85, 86, 87])
        self.assertEqual(extension['instrument_count'], 88)
        self.assertEqual(extension['font_growth_bytes'], 592)
        self.assertEqual(len(extension['reused_original_structures']), 4)
        self.assertEqual(extension['wave_growth_bytes'], 7584)
        self.assertEqual(u32(self.assets['villager.soundfont.bin'], 8+83*4), 0)
        self.assertEqual(sha256(self.assets['villager.soundfont.bin']), extension['font_sha256'])
        self.assertEqual(sha256(self.assets['villager.wave.bin']), extension['wave_sha256'])
        self.assertFalse(extension['runtime_installed'])
        self.assertFalse(extension['audio_allocation_verified'])

    def test_native_interpreter_and_donor_sources_fail_closed(self):
        code = bytearray(by_vrom(self.native)[CODE_VROM].extract(self.native))
        def read(address, size): return code[address-CODE_RAM:address-CODE_RAM+size]
        self.assertEqual(extended_native_interpreter(read), self.report['native_interpreter'])
        code[0x800F3910-CODE_RAM] ^= 1
        with self.assertRaises(ValueError): extended_native_interpreter(read)
        damaged = bytearray(self.donor[1]); damaged[-1] ^= 1
        with self.assertRaises(ValueError): build_audio(self.native, self.donor[0], damaged,
                                                        villagers=self.roster, extended=True)

    def test_original_tune_controller_preserves_hold_and_instrument_tail_timing(self):
        # Compare the complete original tune-controller programs, including
        # held-note and stop-layer branches, rather than extending their timing
        # to force the new sample test to pass.
        files = by_vrom(self.native)
        code = files[CODE_VROM].extract(self.native)
        read = lambda at, size: code[at-CODE_RAM:at-CODE_RAM+size]
        native, _ = resource(read, NATIVE_HEADERS,
            {'seq': files[NATIVE_FILES['seq']].extract(self.native)}, 'seq', 199)
        dol, audio = self.donor
        start, size = struct.unpack_from('>II', header_entry(dol.read, 0x800CE450, 0))
        donor, _ = resource(dol.read, GC_SECTIONS,
            {'seq': audio[start:start+size]}, 'seq', 242)

        def commands(sequence, begin, end, pool):
            result, cursor = [], begin
            while cursor < end:
                opcode = sequence[cursor]
                cursor += 1
                self.assertGreaterEqual(opcode, 0x50)
                spec = read(0x80113210+opcode, 1)[0] if opcode >= 0xA0 else 0
                args = []
                for index in range(spec & 3):
                    width = 2 if spec & (0x80 >> index) else 1
                    value = int.from_bytes(sequence[cursor:cursor+width], 'big')
                    cursor += width
                    if (opcode in (0xC2, 0xF5, 0xFA, 0xFB, 0xFC)
                            or opcode == 0xC7 and index == 1):
                        if value >= pool:
                            value = ('melody', value-pool)
                        else:
                            self.assertTrue(begin <= value <= end)
                            value = ('controller', value-begin)
                    args.append(value)
                if opcode == 0xE8:
                    # The env command reads five further bytes in its handler,
                    # after the three operands described by SCOM_TABLE.
                    args.extend(sequence[cursor:cursor+5])
                    cursor += 5
                result.append((opcode, tuple(args)))
            self.assertEqual(cursor, end)
            return result

        native_commands = commands(native, 0x38F6, 0x3A06, 0x3A10)
        donor_commands = commands(donor, 0x4614, 0x4724, 0x4740)
        self.assertEqual(native_commands, donor_commands)
        self.assertIn((0xC8, (14,)), native_commands)
        self.assertIn((0xC8, (15,)), native_commands)
        self.assertIn((0x90, ()), native_commands)
        current_path = os.environ.get('V3_COMPLETE_AUDIO_BUILD')
        if current_path:
            current_path = Path(current_path)
            current_rom = (current_path/'animal-forest-v3-asset-loader.z64').read_bytes()
            current = json.loads((current_path/'build.json').read_text())
            self.assertEqual(sha256(current_rom), current['output_sha256'])
            row = current['fire_sound']['resources']['seq']
            sequence = current_rom[row['physical']:row['physical']+row['bytes']]
            self.assertEqual(sha256(sequence), row['sha256'])
            self.assertEqual(commands(sequence, 0x38F6, 0x3A06, 0x3A10), donor_commands)


if __name__ == '__main__':
    unittest.main()
