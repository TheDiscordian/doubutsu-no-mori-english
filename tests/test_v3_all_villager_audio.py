"""Complete donor melodies and additive instrument resources, without playback."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
from v3_villager_audio import (build_audio, extended_envelope, extended_native_interpreter,
    extended_program, extended_sequence_programs, read_audio_donor)
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


if __name__ == '__main__':
    unittest.main()
