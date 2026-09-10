"""Test-only model preview bounds, source binding, and checkpoint requirements."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import event_artwork_preview as preview
import event_artwork_preview_smoke as smoke
from aflib import sha256
from runtime_layout import GUARD_ADDRESS, GUARD_WORD


class MatrixTests(unittest.TestCase):
    def test_signed_fixed_matrix_and_bounded_selections(self):
        values = [-1, 0, 0, 0, 0, 0.5, 0, 0, 0, 0, 1, 0, -50, 50, 500, 1]
        data = preview.matrix(values)
        integers = struct.unpack('>16h', data[:32])
        fractions = struct.unpack('>16H', data[32:])
        self.assertEqual([a+b/65536 for a, b in zip(integers, fractions)], values)
        for mode in range(3):
            self.assertEqual(len(preview.transforms(mode)), 128)
        with self.assertRaises(ValueError):
            preview.transforms(3)
        with self.assertRaises(ValueError):
            preview.matrix([1]*15)
        with self.assertRaises(ValueError):
            preview.matrix([65536]*16)


@unittest.skipUnless((ROOT/'build/title-stall-combined-01/preview.json').is_file(), 'Local combined candidate required')
class FixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (ROOT/'build/title-stall-combined-01/animal-forest-title-preview.z64').read_bytes()
        with tempfile.TemporaryDirectory(prefix='af-event-preview-', dir=ROOT/'build') as directory:
            cls.code = preview.compile_fixture(Path(directory)/'compiled')

    def fake(self):
        memory = bytearray(0x800000)
        class Debug:
            def read_memory(self, at, size):
                return bytes(memory[at-0x80000000:at-0x80000000+size])
            def write_memory(self, at, data):
                if not 0x80000000 <= at <= 0x80800000-len(data):
                    raise AssertionError('Unbounded fixture write')
                memory[at-0x80000000:at-0x80000000+len(data)] = data
        debug = Debug()
        debug.write_memory(0x80000318, smoke.words(0x800000))
        debug.write_memory(GUARD_ADDRESS, smoke.words(*([GUARD_WORD]*4)))
        for at in (0x80400000, 0x804475F0):
            debug.write_memory(at, smoke.words(*([0xAF54C0DE]*4)))
        debug.write_memory(0x802CF188, smoke.words(0x80400100))
        return debug, memory

    def test_independent_compile_and_guarded_complete_fixture(self):
        self.assertEqual(sha256(self.code), preview.CODE_SHA)
        debug, memory = self.fake()
        state = {}
        before = bytes(memory)
        with patch.object(smoke, 'locate', return_value=(None, 0x802CF020, 0x80400010, 0)):
            result = smoke.exercise(debug, {'setup': True, 'code': self.code.hex()}, self.rom, state)
            self.assertTrue(result['checkpoint_restore_required'])
            for mode in range(3):
                smoke.exercise(debug, {'select': mode}, self.rom, state)
                debug.write_memory(preview.META+4, smoke.words(4))
                result = smoke.exercise(debug, {'verify': mode}, self.rom, state)
                self.assertTrue(result['guards_intact'])
                self.assertFalse(result['ordinary_scene'])
            debug.write_memory(preview.DEPTH+320*240*2, b'FAIL')
            with self.assertRaises(ValueError):
                smoke.exercise(debug, {'verify': 2}, self.rom, state)
            memory[:] = before
            self.assertTrue(smoke.exercise(debug, {'restored': True}, self.rom, state)['native_title_callback_restored'])

    def test_unapproved_code_and_occupied_test_memory_rejected_before_install(self):
        debug, memory = self.fake()
        with patch.object(smoke, 'locate', return_value=(None, 0x802CF020, 0x80400010, 0)):
            with self.assertRaises(ValueError):
                smoke.exercise(debug, {'setup': True, 'code': bytes(616).hex()}, self.rom, {})
            debug.write_memory(preview.ASSETS+64, b'used')
            before = bytes(memory)
            with self.assertRaises(ValueError):
                smoke.exercise(debug, {'setup': True, 'code': self.code.hex()}, self.rom, {})
            self.assertEqual(memory, before)


if __name__ == '__main__':
    unittest.main()
