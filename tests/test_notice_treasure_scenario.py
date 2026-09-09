"""Source-bound treasure fixtures and bounded debugger waypoint handling."""

import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from notice_treasure_scenario import scenario, rng, SEEDS
from notice_treasure_smoke import traced_call
from notice_record import unpack
from runtime_layout import TEST_RETURN


@unittest.skipUnless((ROOT/'build/notice-treasure-pilot/build.json').is_file(), 'Local treasure ROM required')
class TreasureScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        build = ROOT/'build/notice-treasure-pilot'
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (build/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((build/'build.json').read_text())
        cls.plan = scenario(cls.native, cls.built, cls.report)

    def test_all_source_ids_capitals_and_burial_kinds_are_present(self):
        request = self.plan[3]['test_notice_treasure']
        cases = request['cases']
        self.assertEqual([(c['template'], c['capital'], c['item']) for c in cases],
                         [(n, cap, item) for n in range(0x1F0, 0x202) for cap in (0, 1) for item in (0x2512, 0x11FC)])
        self.assertEqual({c['hole'] for c in cases if c['item'] == 0x2512}, set(range(25)))
        for case in cases:
            value = unpack(bytes.fromhex(case['wire']), expected_catalog=4)
            self.assertEqual(value.templates, (case['template'],))
            self.assertEqual(value.initial_capital, bool(case['capital']))
            if case['template'] == 0x1F4:
                self.assertEqual(tuple(i for i, _ in value.fields), (1, 3, 5))
            self.assertGreater(len(bytes.fromhex(case['body'])), 96)

    def test_original_rng_models_template_selection_without_runtime_patches(self):
        for variant, seed in enumerate(SEEDS):
            final, values = rng(seed)
            self.assertLess(values[0], 0.4)
            self.assertLess(values[1], 1/3)
            self.assertEqual(int(values[5]*3), variant)
            self.assertEqual(rng(seed, 0), (seed, []))
            self.assertEqual(final, self.plan[3]['test_notice_treasure']['cases'][variant*4]['rng_final'])

    def test_continuation_does_not_replay_completed_cases_or_skip_checkpoint(self):
        plan = scenario(self.native, self.built, self.report, skip_complete=72)
        self.assertEqual(plan[3]['test_notice_treasure']['skip_complete'], 72)
        self.assertEqual(plan[1], {'save_state': True})
        self.assertEqual(plan[4], {'load_state': True})
        self.assertFalse(any('capture' in a or 'test_flash' in a for a in plan))
        for value in (-1, 73, True, 0.5):
            with self.assertRaises(ValueError): scenario(b'', b'', {}, skip_complete=value)

    def test_reader_plan_uses_identical_published_records_without_replaying_creation(self):
        plan = scenario(self.native, self.built, self.report, reader_only=True, skip_complete=17)
        request = plan[3]['test_notice_reader']
        self.assertEqual(request['cases'], self.plan[3]['test_notice_treasure']['cases'])
        self.assertTrue(request['treasure_only'])
        self.assertTrue(request['report']['treasure'])
        self.assertEqual(request['skip_initial'], 17)
        self.assertEqual(len(bytes.fromhex(request['data'])), 15984)
        self.assertEqual(plan[:3], self.plan[:3])
        self.assertEqual(plan[4:], self.plan[4:])
        self.assertFalse(any('test_notice_treasure' in a for a in plan))
        with self.assertRaises(ValueError): scenario(b'', b'', {}, reader_only=1)


class FakeDebugger:
    """Transport-only fake; it makes no assertions about native game execution."""
    def __init__(self, addresses):
        self.addresses = iter(addresses)
        self.pc = 0
        self.active = set()
    def command(self, packet):
        if packet.startswith('Z'): self.active.add(packet[1:]); return 'OK'
        if packet.startswith('z'): self.active.remove(packet[1:]); return 'OK'
        if packet == 'c': self.pc = next(self.addresses); return 'T05'
        if packet == 'g':
            registers = [0]*71; registers[37] = self.pc
            return ''.join(f'{r:016x}' for r in registers)
        raise ValueError('Unexpected fake command')
    def call(self, address, args):
        self.command('c')
        if self.pc != TEST_RETURN: raise ValueError('Unexpected final stop')
        return {'test_only_function_call': address}


class TreasureTraceTests(unittest.TestCase):
    def test_shared_entries_and_malloc_returns_are_rearmed_between_phases(self):
        entry, malloc, placed = 0x800A5E58, 0x80197D78, 0x800A6178
        addresses = [entry, malloc, placed, entry, malloc]
        debug = FakeDebugger(addresses+[TEST_RETURN])
        hits = []
        traced_call(debug, 0x800A5F08, {a: lambda regs: hits.append(regs[37]) for a in addresses},
                    lambda row: None, rearm={placed: (entry,), entry: (malloc,)})
        self.assertEqual(hits, addresses)
        self.assertFalse(debug.active)

    def test_handles_waypoints_then_returns_to_existing_call_contract(self):
        debug = FakeDebugger([0x800A6170, 0x80197D78, TEST_RETURN])
        rows, hits = [], []
        original = debug.command
        traced_call(debug, 0x800A5F08, {a: lambda regs: hits.append(regs[37]) for a in (0x800A6170, 0x80197D78)}, rows.append)
        self.assertEqual(hits, [0x800A6170, 0x80197D78])
        self.assertFalse(debug.active)
        self.assertEqual(debug.command, original)
        self.assertEqual(rows[-1]['test_only_function_call'], '800A5F08')

    def test_exception_and_stop_limit_restore_transport_and_breakpoints(self):
        for failure in ('callback', 'limit'):
            debug = FakeDebugger([0x800A6170]*4)
            original = debug.command
            def callback(regs):
                if failure == 'callback': raise ValueError('Test callback failed')
            with self.assertRaises(ValueError):
                traced_call(debug, 0x800A5F08, {0x800A6170: callback}, lambda row: None, limit=2)
            self.assertFalse(debug.active)
            self.assertEqual(debug.command, original)


if __name__ == '__main__': unittest.main()
