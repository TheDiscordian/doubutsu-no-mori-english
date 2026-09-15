"""Source-verified camper event module; deliberately not a cartridge claim."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v3_campsite_event as event
from aflib import sha256

OUTPUT = ROOT / 'build/v3-campsite-event-module-01'


class CampsiteEventTests(unittest.TestCase):
    def test_checked_donor_and_native_contracts(self):
        rel = (ROOT / 'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols = (ROOT / 'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        self.assertEqual(event.donor_schedule(rel, symbols).hex(), '06be004906b8000e00000018')
        self.assertEqual((OUTPUT / 'schedule.bin').read_bytes(), event.donor_schedule(rel, symbols))
        native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(len(event.native_contracts(native)), 5)
        with self.assertRaises(ValueError):
            event.donor_schedule(rel[:-1], symbols)
        with self.assertRaises(ValueError):
            event.native_contracts(native[:-1])

    def test_sanitized_calendar_selection_lifecycle(self):
        with tempfile.TemporaryDirectory(prefix='af-camper-event-') as directory:
            binary = Path(directory) / 'event-test'
            result = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests/v3_campsite_event_test.c'),
                str(ROOT / 'overlays/v3/campsite_event.c'), '-o', str(binary)],
                text=True, capture_output=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stderr)
            run = subprocess.run([str(binary), str(OUTPUT / 'schedule.bin')],
                                 text=True, capture_output=True, timeout=20)
            self.assertEqual(run.returncode, 0, run.stdout + run.stderr)
            self.assertIn('pass:', run.stdout)

    def test_compilation_bounds_and_honest_installation_state(self):
        report = json.loads((OUTPUT / 'event.json').read_text())
        data = (OUTPUT / 'code/code.bin').read_bytes()
        self.assertEqual(sha256(data), report['code']['sha256'])
        self.assertEqual(report['code']['symbols']['af_v3_campsite_schedule'], 0x804A2100)
        self.assertLessEqual(0x804A2100 + len(data), 0x804A4000)
        self.assertEqual(report['native_event_types'], 70)
        for key in ('installed', 'rom_changed', 'web_patcher_changed', 'saved_format_changed'):
            self.assertFalse(report[key])
        self.assertIn('extended native event directory and manager binding', report['pending'])
        for name, expected in report['source_sha256'].items():
            self.assertEqual(sha256((ROOT / name).read_bytes()), expected)


if __name__ == '__main__':
    unittest.main()
