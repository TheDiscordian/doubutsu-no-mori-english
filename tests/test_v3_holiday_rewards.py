"""Shared donor selectors and transaction kernel; no historical ROM replay."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_furniture_pipeline import Source
import v3_holiday_rewards as holiday

OUTPUT=ROOT/'build/v3-holiday-rewards-prepared-02'


class SourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.report=holiday.discover(cls.source)

    def test_complete_source_selector_shapes_and_all_candidates(self):
        rows=self.report['rows'];self.assertEqual(len(rows),28)
        self.assertEqual(rows[0]['source_items'],[f'{i:04X}' for i in range(0x2B00,0x2B0F)])
        self.assertEqual(rows[4]['source_items'],[f'{i:04X}' for i in range(0x30A8,0x30E4,4)])
        self.assertEqual(rows[13]['source_items'],[f'{i:04X}' for i in range(0x3378,0x339C,4)])
        self.assertEqual(rows[25]['source_items'],['3094','30A4'])
        fixed=struct.unpack('>28H',self.source.raw('soncho_item_table$582'))
        for r in rows:
            if r['selector']=='fixed':self.assertEqual(r['source_items'],[f'{fixed[r["event"]]:04X}'])
        self.assertEqual(sum(len(r['source_items']) for r in rows),65)
        data=holiday.encode(self.report);self.assertEqual(len(data),370)
        self.assertEqual(data,(OUTPUT/'holiday-rewards.bin').read_bytes())
        prepared=json.loads((OUTPUT/'rewards.json').read_bytes())
        self.assertEqual(prepared['sha256'],sha256(data))
        self.assertFalse(any(prepared[k] for k in ('runtime_installed','calendar_installed','npc_installed','acquisition_installed')))
        self.assertFalse(prepared['kernel']['linked']);self.assertIsNone(prepared['kernel']['resident_address'])
        obj=(OUTPUT/'holiday_rewards.o').read_bytes()
        self.assertEqual(obj[:6],b'\x7fELF\x01\x02')
        self.assertEqual(struct.unpack_from('>HH',obj,16),(1,8))
        self.assertEqual(sha256(obj),prepared['kernel']['sha256'])

    def test_changed_code_dependencies_tables_and_random_ranges_reject(self):
        for at,n,_ in holiday.FUNCTIONS:
            bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel)
            bad.rel[bad.sections[1][0]+at+n-1]^=1
            with self.assertRaisesRegex(ValueError,'complete holiday source function'):holiday.discover(bad)
        for address in (0x106F8,0x10714,0x1074C):
            bad=copy.copy(self.source);bad.data=bytearray(self.source.data);bad.data[address]^=1
            with self.assertRaises(ValueError):holiday.discover(bad)
        bad=copy.copy(self.source);bad.code_relocations=dict(self.source.code_relocations)
        bad.code_relocations[0x7C31C+0x42]=(6,1,4,0x2074)
        with self.assertRaisesRegex(ValueError,'complete holiday source dependencies'):holiday.discover(bad)
        bad=copy.copy(self.source);bad.relocations=dict(self.source.relocations)
        bad.relocations[0x1074C]=(1,True,5,0x7C358)
        with self.assertRaisesRegex(ValueError,'selector jump table'):holiday.discover(bad)
        bad.relocations[0x1074C]=(1,True,1,0x7C3EC)
        with self.assertRaisesRegex(ValueError,'selector jump table'):holiday.discover(bad)
        for at in (0x2068,0x2070,0x2074):
            bad=copy.copy(self.source);bad.rel=bytearray(self.source.rel);bad.rel[bad.sections[4][0]+at]^=1
            with self.assertRaisesRegex(ValueError,'random range'):holiday.discover(bad)

    def test_shared_selector_and_handover_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-holiday-') as temporary:
            binary=Path(temporary)/'test'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_holiday_rewards_test.c'),
                '-o',str(binary)],check=True,capture_output=True,text=True)
            result=subprocess.run([str(binary),str(OUTPUT/'holiday-rewards.bin')],check=True,
                capture_output=True,text=True,timeout=20)
            self.assertIn('four-player receipts, full pockets',result.stdout)
