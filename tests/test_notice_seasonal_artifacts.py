"""Actual compiled seasonal creator, complete resources, and retained profiles."""

import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from notice_seasonal import compiled_resource
from npc_mail_capture import RAM, relocate, source_hashes, validate
from npc_mail_loader import configuration
from runtime_module import resident_c_sources, runtime_source_hashes

DIRECTORY = ROOT/'build/noticeboard-seasonal/creator'


@unittest.skipUnless((DIRECTORY/'overlay.json').is_file(), 'Local compiled seasonal creator required')
class SeasonalArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = (DIRECTORY/'overlay.bin').read_bytes()
        cls.reloc = (DIRECTORY/'relocation.bin').read_bytes()
        cls.report = json.loads((DIRECTORY/'overlay.json').read_text())
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.resource = compiled_resource((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                        (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes())

    def test_independent_complete_builds_and_loader_entry(self):
        self.assertEqual((len(self.data), sha256(self.data)),
                         (58144, '2598d8ed5cc35e06a40e24aab1db93fbca2f8cdab00b752bd91ba7af5cd93637'))
        self.assertEqual((len(self.reloc), sha256(self.reloc)),
                         (848, '95f09d4b0c6ea100caa03cf798ee217836670c4e102ab5538dc2cb7be74b34a1'))
        for name in ('overlay.bin', 'relocation.bin', 'overlay.json', 'seasonal_data.h'):
            self.assertEqual((DIRECTORY/name).read_bytes(), (DIRECTORY.parent/'creator-repeat'/name).read_bytes())
        validate(self.data, self.reloc, self.report, self.module)
        config = configuration(self.data, self.reloc, self.report, self.module)
        self.assertEqual(config[1:5], [58992, 58144, 848, 21920])
        self.assertEqual(config[4], self.report['symbols']['af_notice_seasonal_create'])
        text, data, rodata, bss, _ = struct.unpack_from('>5I', self.reloc)
        self.assertEqual((text+rodata, data, bss), (58144, 0, 0))

    def test_all_compiled_text_tables_and_shops_remain_readonly_at_three_bases(self):
        text = struct.unpack_from('>I', self.reloc)[0]
        payloads = {'entries': self.resource['table'], 'data': self.resource['data'],
                    'shops': b''.join(self.resource['shops'])}
        self.assertEqual([len(payloads[name]) for name in ('entries', 'data', 'shops')], [492, 6143, 64])
        self.assertEqual(len(self.resource['templates']), 41)
        for base in (0x801A0000, 0x80260000, 0x803E0000):
            result = relocate(self.data, self.reloc, base, self.report['imports'].values())
            self.assertEqual(result[text:], self.data[text:])
            for name, payload in payloads.items():
                at = self.report['symbols']['af_notice_seasonal_'+name]
                self.assertGreaterEqual(at, text)
                self.assertEqual(at & 15, 0)
                self.assertEqual(result[at:at+len(payload)], payload)
            # Every original internal call moves to the same relative target.
            for at in range(0, text, 4):
                before = struct.unpack_from('>I', self.data, at)[0]
                if before >> 26 not in (2, 3): continue
                target = 0x80000000 | ((before & 0x3FFFFFF) << 2)
                after = struct.unpack_from('>I', result, at)[0]
                wanted = base+target-RAM if RAM <= target < RAM+text else target
                self.assertEqual(0x80000000 | ((after & 0x3FFFFFF) << 2), wanted)

    def test_recomputed_self_hash_does_not_approve_changed_text_or_shop(self):
        for name in ('entries', 'data', 'shops'):
            data = bytearray(self.data)
            at = self.report['symbols']['af_notice_seasonal_'+name]
            data[at] ^= 1
            report = copy.deepcopy(self.report)
            report['overlay_sha256'] = sha256(data)
            with self.assertRaises(ValueError): validate(data, self.reloc, report, self.module)
        for name in ('entries', 'data', 'shops', 'header'):
            report = copy.deepcopy(self.report)
            report['seasonal_'+name+'_sha256'] = '0'*64
            with self.assertRaises(ValueError): validate(self.data, self.reloc, report, self.module)

    def test_unknown_variant_missing_owner_and_misdirected_exports_rejected(self):
        for value in (False, 1, 'true'):
            report = copy.deepcopy(self.report); report['notice_seasonal'] = value
            with self.assertRaises(ValueError): validate(self.data, self.reloc, report, self.module)
        report = copy.deepcopy(self.report); del report['notice_owner']
        with self.assertRaises(ValueError): validate(self.data, self.reloc, report, self.module)
        with self.assertRaises(ValueError): source_hashes(notice_seasonal=True)
        report = copy.deepcopy(self.report)
        report['symbols']['af_notice_seasonal_data'] = report['symbols']['af_notice_seasonal_create']
        with self.assertRaises(ValueError): validate(self.data, self.reloc, report, self.module)

    def test_current_resident_inventory_includes_but_does_not_link_seasonal_units(self):
        for name in ('module.bin', 'bootstrap.bin'):
            self.assertEqual((ROOT/'build/notice-seasonal-runtime'/name).read_bytes(),
                             (ROOT/'build/notice-treasure-runtime'/name).read_bytes())
        self.assertEqual(self.module['runtime_sources'], runtime_source_hashes(ROOT/'runtime'))
        linked = [p.relative_to(ROOT/'runtime').as_posix() for p in resident_c_sources(ROOT/'runtime')]
        for name in ('seasonal', 'treasure'):
            self.assertNotIn('notice/'+name+'.c', linked)
            self.assertIn('notice/'+name+'.c', self.module['runtime_sources'])
        self.assertIn('af_notice_seasonal_create\t96\tstatic', self.report['stack_usage']['notice_seasonal_creator'])

    def test_previous_owner_and_quest_profiles_remain_verifiable(self):
        for directory in (ROOT/'build/noticeboard-treasure/owner-creator', ROOT/'build/quest-reply-creator'):
            report = json.loads((directory/'overlay.json').read_text())
            validate((directory/'overlay.bin').read_bytes(), (directory/'relocation.bin').read_bytes(),
                     report, self.module)
            self.assertNotIn('notice_seasonal', report)


if __name__ == '__main__': unittest.main()
