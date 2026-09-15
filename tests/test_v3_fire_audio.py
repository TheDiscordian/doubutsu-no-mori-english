"""Complete fire audio conversion, with native/speed-bag retention and capacity."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import v3_fire_audio as fire
from aflib import by_vrom, CODE_RAM, CODE_VROM, sha256, u32
from v3_villager_audio import NATIVE_HEADERS, instrument, read_audio_donor, resource, span

OUTPUT = ROOT / 'build/v3-fire-audio-02'


class FireAudio(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.donor = read_audio_donor(ROOT / 'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.parts, cls.programs, cls.descriptions = fire.extract(*cls.donor)
        cls.rom = (fire.BASE / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base_report = json.loads((fire.BASE / 'build.json').read_text())
        cls.generated, cls.result = fire.prepare(cls.rom, cls.base_report, cls.donor)
        cls.report = json.loads((OUTPUT / 'audio.json').read_text())
        files = by_vrom(cls.rom)
        code = files[CODE_VROM].extract(cls.rom)
        read = lambda at, size: span(code, at - CODE_RAM, size)
        sources = {k: files[v].extract(cls.rom) for k, v in fire.NATIVE_VROMS.items()}
        cls.previous = {k: resource(read, NATIVE_HEADERS, sources, k, index)[0]
                        for k, index in (('seq', 199), ('bank', 140), ('wave', 5))}

    def test_complete_current_conversion_and_all_source_dependencies(self):
        for k, data in self.generated.items():
            self.assertEqual(data, (OUTPUT / f'fire.{k}.bin').read_bytes())
            self.assertEqual({'bytes': len(data), 'sha256': sha256(data)}, self.report['resources'][k])
        self.assertEqual(self.report['converter_sha256'], sha256((ROOT / 'tools/v3_fire_audio.py').read_bytes()))
        self.assertEqual((len(self.parts[12]['wave']), len(self.parts[14]['wave'])), (18514, 2826))
        self.assertEqual(struct.unpack_from('>4I', self.parts[12]['loop']), (64, 32896, 0xFFFFFFFF, 32913))
        self.assertEqual(struct.unpack_from('>4I', self.parts[14]['loop']), (0, 5024, 0, 0))
        for source, target in ((12, 72), (14, 73)):
            self.assertEqual(instrument(self.generated['bank'], self.generated['wave'], target, 74, extended=True),
                             self.descriptions[source])

    def test_full_two_layer_notes_rests_and_loop_timing(self):
        expected = {
            'bonfire': (36, 110, [26,24,24,21,24,26,22,25,25,22],
                        [302,7,333,199,27,221,52,185,66,174], [53,76,76,70,75,60,65,45,68,60]),
            'campfire': (41, 60, [40,38,38,36,39,35,38,38,39,36],
                         [302,8,333,112,185,199,17,221,66,174], [35,55,50,55,30,40,50,45,25,40]),
        }
        for name, (note, volume, pitches, durations, velocities) in expected.items():
            parsed = fire.parse_program(self.programs[name], fire.PROGRAMS[name][1])
            first, crackle = [row['events'] for row in parsed['layers']]
            notes = [e for e in first if 'note' in e]
            self.assertEqual([(e['note'], e['duration'], e['velocity']) for e in notes], [(note, 32000, volume)])
            self.assertTrue(any(e.get('continuous') for e in first))
            self.assertEqual(first[-1]['loop'], notes[0]['offset'])
            notes = [e for e in crackle if 'note' in e]
            self.assertEqual([e['note'] for e in notes], pitches)
            self.assertEqual([e['duration'] for e in notes], durations)
            self.assertEqual([e['velocity'] for e in notes], velocities)
            self.assertEqual([e['rest'] for e in crackle if 'rest' in e], [100,300])
            self.assertEqual(crackle[-1]['loop'], notes[0]['offset'])
            self.assertEqual([e['transpose'] for e in crackle if 'transpose' in e], [5] if name == 'bonfire' else [])

    def test_rebinding_changes_only_explicit_instruments_and_addresses(self):
        for name, source in self.programs.items():
            parsed = fire.parse_program(source, fire.PROGRAMS[name][1])
            for offset in (0, 0x4E22, (0x10000 - len(source) - 4) & ~1):
                data = fire.bind_program(name, source, offset)
                self.assertEqual(data[:4], bytes((0xEB, 1, 72, 0xC4)))
                native = fire.parse_program(data, offset, prefix=True)
                self.assertEqual([x['first_cycle_ticks'] for x in native['layers']],
                                 [x['first_cycle_ticks'] for x in parsed['layers']])
                restored = bytearray(data[4:])
                for at in parsed['pointers']:
                    self.assertEqual(struct.unpack_from('>H', data, at + 4)[0],
                                     struct.unpack_from('>H', source, at)[0] - fire.PROGRAMS[name][1] + offset + 4)
                    restored[at:at + 2] = source[at:at + 2]
                for at in parsed['instruments']:
                    self.assertEqual(data[at + 4], {12:72, 14:73}[source[at]])
                    restored[at] = source[at]
                self.assertEqual(restored, source)
                self.assertEqual((offset + native['envelope']) % 2, 0)

    def test_existing_native_and_speed_bag_resources_remain_complete(self):
        bank, wave = self.generated['bank'], self.generated['wave']
        old_bank, old_wave = self.previous['bank'], self.previous['wave']
        restored = bytearray(bank[:len(old_bank)])
        restored[0x128:0x130] = bytes(8)
        self.assertEqual(restored, old_bank)
        self.assertEqual(wave[:len(old_wave)], old_wave)
        for index in range(72):
            self.assertEqual(instrument(bank, wave, index, 74, extended=True),
                             instrument(old_bank, old_wave, index, 72, extended=True))
        self.assertEqual(len(bank) - len(old_bank), 352)
        self.assertEqual(len(wave) - len(old_wave), 21360)
        for row in self.result['imports']:
            self.assertEqual(row['wave_offset'] % 16, 0)
            self.assertEqual(row['instrument_offset'] % 16, 0)

    def test_original_level_dispatch_and_reserved_ids(self):
        sequence, old = self.generated['seq'], self.previous['seq']
        restored = bytearray(sequence[:len(old)])
        restored[0x179:0x17B] = old[0x179:0x17B]
        self.assertEqual(restored, old)
        table, no_op = self.result['level_table'], self.result['reserved_no_op']
        self.assertEqual(struct.unpack_from('>H', sequence, 0x179)[0], table)
        self.assertEqual(sequence[table:table + 136], old[0x265C:0x26E4])
        self.assertEqual(sequence[no_op], 255)
        assigned = {v['sound_id']: v['offset'] for v in self.result['programs'].values()}
        for sid in range(68, 128):
            self.assertEqual(struct.unpack_from('>H', sequence, table + sid * 2)[0], assigned.get(sid, no_op))
        for name, row in self.result['programs'].items():
            data = sequence[row['offset']:row['offset'] + row['bytes']]
            self.assertEqual(data, fire.bind_program(name, self.programs[name], row['offset']))
        self.assertEqual(len(sequence) - len(old), 432)

    def test_memory_shortfall_is_explicit_not_an_installed_sound_claim(self):
        budget = self.report['permanent_audio']
        self.assertEqual(budget['before']['conservative_spare'], 32)
        self.assertEqual(budget['additional_bytes'], 800)
        self.assertEqual(budget['required_bytes'], 109312)
        self.assertEqual(budget['additional_capacity_required'], 768)
        self.assertFalse(budget['allocation_change_installed'])
        for flag in ('runtime_installed', 'native_synthesis_tested', 'web_patcher_changed'):
            self.assertFalse(self.report[flag])

    def test_changed_parts_programs_and_invalid_bindings_reject(self):
        for source, resources in self.parts.items():
            for name, data in resources.items():
                bad = copy.deepcopy(self.parts)
                bad[source][name] = bytes((data[0] ^ 1,)) + data[1:]
                with self.assertRaises(ValueError):
                    fire.verify_parts(bad)
        for name, source in self.programs.items():
            for at in (-2, 1, 0x10000):
                with self.assertRaises(ValueError):
                    fire.bind_program(name, source, at)
            with self.assertRaises(ValueError):
                fire.bind_program(name, source, 0, mapping={12: 126,14:73})
            with self.assertRaises(ValueError):
                fire.bind_program(name, source[:-1], 0)
            for bad in (b'', source[:-1], source + b'\0', source[:7] + b'\xC7' + source[8:]):
                with self.assertRaises(ValueError):
                    fire.parse_program(bad, fire.PROGRAMS[name][1])
            with self.assertRaises(ValueError):
                fire.parse_program(b'', 0, prefix=True)


if __name__ == '__main__':
    unittest.main()
