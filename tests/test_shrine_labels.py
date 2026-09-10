"""Source-bound native shrine correction without changing other map features."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
from npc_mail_show import relocate_verified_data
import map_names as m
import map_labels as labels
import shrine_labels as shrine

BASE = ROOT/'build/classic-letters-pilot'
FIX = ROOT/'build/v0-first-job-fix-01'
BUILD = ROOT/'build/v0-hardware-fixes-01'


@unittest.skipUnless((BASE/'build.json').is_file(), 'Complete supplied-input v0 required')
class ShrineLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (BASE/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BASE/'build.json').read_text())
        files = by_vrom(cls.base)
        cls.data, cls.reloc = (files[v].extract(cls.base) for v in (m.NEW_VROM, m.NEW_RELOC))
        cls.changed, cls.profile = shrine.patch(cls.native, cls.data, cls.reloc,
            cls.report['map_names']['overlay'], cls.report['runtime_module'])

    def test_complete_word_one_line_and_retained_reference_evidence(self):
        self.assertEqual(self.changed[shrine.LABEL_AT:shrine.LABEL_AT+16], b'Shrine'+bytes(10))
        self.assertEqual(struct.unpack_from('>f', self.changed, shrine.DESCRIPTOR+12)[0], -25.0)
        self.assertEqual(struct.unpack_from('>I', self.changed, shrine.DESCRIPTOR+24)[0], 6)
        self.assertEqual(self.profile['references'], self.report['map_names']['overlay']['references'])
        self.assertEqual(shrine.transform(self.changed, reverse=True), self.data)
        self.assertEqual(labels.installed_report(self.changed)['native_label_correction'],
                         self.profile['native_label_correction'])
        allowed = {i for at, old, _ in shrine.EDITS for i in range(at, at+len(old))}
        self.assertLessEqual({i for i, (a, b) in enumerate(zip(self.data, self.changed)) if a != b}, allowed)

    def test_original_and_corrected_profiles_remain_valid_at_two_heap_bases(self):
        for data, profile in ((self.data, self.report['map_names']['overlay']), (self.changed, self.profile)):
            spec = labels.validate(self.native, data, self.reloc, profile, self.report['runtime_module'])
            for base in (0x801A0010, 0x802F8010):
                result = relocate_verified_data(spec, data, self.reloc, base)
                self.assertEqual(result[shrine.LABEL_AT:shrine.LABEL_AT+16], data[shrine.LABEL_AT:shrine.LABEL_AT+16])
                self.assertEqual(struct.unpack_from('>I', result, shrine.DESCRIPTOR+20)[0], base+shrine.LABEL_AT)

    def test_rehashed_damage_or_wrong_output_metadata_rejected(self):
        for at in (shrine.LABEL_AT, shrine.DESCRIPTOR+12, shrine.DESCRIPTOR+24, labels.BASE_SIZE):
            data = bytearray(self.changed)
            data[at] ^= 1
            profile = copy.deepcopy(self.profile)
            profile['overlay_sha256'] = sha256(data)
            with self.assertRaises(ValueError):
                labels.validate(self.native, bytes(data), self.reloc, profile, self.report['runtime_module'])
        profile = copy.deepcopy(self.profile)
        profile['native_label_correction']['text'] = 'Wishing Well'
        with self.assertRaises(ValueError):
            labels.validate(self.native, self.changed, self.reloc, profile, self.report['runtime_module'])

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Combined correction required')
    def test_combined_cartridge_preserves_furniture_fix_and_all_other_text(self):
        before, after = ((path/'animal-forest-halfwidth.z64').read_bytes() for path in (FIX, BUILD))
        old, new = by_vrom(before), by_vrom(after)
        report = json.loads((BUILD/'build.json').read_text())
        m.verify_shared_parts(after, self.native, report['runtime_module'], report['map_names'])
        self.assertEqual(set(old), set(new))
        for vrom in old:
            a, b = old[vrom].extract(before), new[vrom].extract(after)
            if vrom == m.NEW_VROM:
                self.assertEqual(b, self.changed)
            elif vrom == 0x19D40:
                self.assertEqual(a[:16], b[:16])
            else:
                self.assertEqual(a, b, f'Resource {vrom:08X}')
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), after)


if __name__ == '__main__':
    unittest.main()
