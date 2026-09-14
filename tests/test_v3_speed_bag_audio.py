"""Complete donor hit sound, native bank pointers, and sequence bindings."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, u32
from v3_speed_bag_audio import PARTS, bind_font, bind_program, extract, verify_parts
from v3_villager_audio import read_audio_donor

OUTPUT = ROOT/'build/v3-speed-bag-audio-01'


class AudioRejectionTests(unittest.TestCase):
    def test_incomplete_or_unknown_sound_is_rejected(self):
        for parts in ({}, {'wave': b'noise'}, {k: bytes(size) for k, (size, _) in PARTS.items()}):
            with self.assertRaises(ValueError): verify_parts(parts)


@unittest.skipUnless((OUTPUT/'audio.json').exists(), 'Local complete sound conversion required')
class ActualSoundTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        dol, audio = read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.parts, cls.source = extract((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(), dol, audio)
        cls.report = json.loads((OUTPUT/'audio.json').read_text())

    def test_complete_sample_predictor_and_both_envelopes(self):
        self.assertEqual(self.report['source'], self.source)
        for name, data in self.parts.items():
            self.assertEqual((len(data), sha256(data)), PARTS[name])
        self.assertEqual((OUTPUT/'speed-bag.wave.bin').read_bytes(), self.parts['wave'])
        self.assertEqual(self.parts['instrument'][:4], bytes((0, 0, 127, 250)))
        self.assertEqual(struct.unpack_from('>I', self.parts['instrument'], 20)[0], 0x3F306666)
        self.assertEqual(struct.unpack_from('>4I', self.parts['loop']), (96, 19648, 0xFFFFFFFF, 19665))
        self.assertEqual(struct.unpack_from('>2I', self.parts['book']), (2, 2))
        self.assertEqual(list(struct.iter_unpack('>hh', self.parts['envelope'])), [(1, 0), (1, 32700), (-1, 0)])
        self.assertEqual(list(struct.iter_unpack('>hh', self.parts['program'][15:])), [(1, 32700), (275, 12690), (-1, 0)])

    def test_all_native_font_fields_and_relative_pointers(self):
        font, layout = bind_font(self.parts)
        self.assertEqual((OUTPUT/'speed-bag.soundfont.bin').read_bytes(), font)
        self.assertEqual(len(font), 208)
        self.assertEqual(struct.unpack_from('>4I', font), (0, 0, 16, 0))
        instrument = bytearray(font[16:48])
        self.assertEqual((u32(instrument, 4), u32(instrument, 16)), (48, 60))
        struct.pack_into('>I', instrument, 4, u32(self.parts['instrument'], 4))
        struct.pack_into('>I', instrument, 16, u32(self.parts['instrument'], 16))
        self.assertEqual(bytes(instrument), self.parts['instrument'])
        self.assertEqual(font[48:60], self.parts['envelope'])
        self.assertEqual(struct.unpack_from('>4I', font, 60), (11062, 0, 76, 124))
        self.assertEqual(font[76:124], self.parts['loop'])
        self.assertEqual(font[124:196], self.parts['book'])
        self.assertEqual(font[196:], bytes(12))
        self.assertEqual(sha256(font), self.report['font']['sha256'])

    def test_program_addresses_change_without_changing_sound_or_timing(self):
        for offset, bank, instrument in ((0, 0, 0), (0x4D00, 1, 71), (0xFFE5, 4, 0)):
            program = bind_program(self.parts, offset, bank, instrument)
            self.assertEqual(program[:4], bytes((0xEB, bank, instrument, 0x88)))
            self.assertEqual(struct.unpack_from('>H', program, 4)[0], offset+7)
            self.assertEqual(program[6:8], bytes((0xFF, 0xCB)))
            self.assertEqual(struct.unpack_from('>H', program, 8)[0], offset+15)
            self.assertEqual(program[10:], self.parts['program'][10:])
        self.assertEqual(bind_program(self.parts, 0, 0, 0), (OUTPUT/'speed-bag.sequence-fragment.bin').read_bytes())
        for values in ((-1, 1, 71), (0xFFE6, 1, 71), (0, -1, 0), (0, 256, 0), (0, 1, 126)):
            with self.assertRaises(ValueError): bind_program(self.parts, *values)

    def test_changed_components_fail_and_runtime_remains_uninstalled(self):
        for name, data in self.parts.items():
            changed = {**self.parts, name: bytes((data[0] ^ 1,))+data[1:]}
            with self.assertRaises(ValueError): bind_font(changed)
        self.assertFalse(self.source['native_same_numeric_id_valid'])
        self.assertFalse(self.report['runtime_installed'])
        self.assertFalse(self.report['native_synthesis_tested'])
        self.assertFalse(self.report['public_or_local_patcher_changed'])


if __name__ == '__main__':
    unittest.main()
