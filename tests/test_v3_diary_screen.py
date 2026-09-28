"""One complete screen category and its keyboard boundary; no gameplay claim."""
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
from v3_diary_screen import prepare,source_tables,provenance,draw_header
from v3_ui_art import Packet,validate_state


class DiaryScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_screen_category_and_actual_native_packet(self):
        prepared=prepare(self.source)
        output=ROOT/'build/v3-diary-category-work-01/screen-04'
        report=json.loads((output/'screen.json').read_bytes())
        raw=(output/report['file']).read_bytes()
        self.assertEqual(sha256(raw),report['sha256'])
        self.assertEqual(len(raw),report['bytes'])
        self.assertFalse(report['native_installed']);self.assertFalse(report['rendered'])
        self.assertEqual(prepared[5],(output/'commands.c').read_text())
        self.assertEqual(prepared[2],report['resources'])
        self.assertEqual(source_tables(self.source),report['source_tables'])
        self.assertEqual(provenance(prepared[2]),report['provenance_ids'])
        header=draw_header(self.source,report['offsets'])
        self.assertEqual(header,(output/'diary-art.inc').read_bytes())
        self.assertEqual(sha256(header),report['draw_header_sha256'])
        self.assertEqual(len(prepared[4]),141)
        self.assertEqual(len(prepared[2]),148)
        for prefix,number in (('calendar_month_',12),('diary_month_',12),('calendar_palette_',12),
                              ('calendar_year_',10)):
            self.assertTrue(all(prefix+str(i) in report['offsets'] for i in range(number)))
        self.assertTrue(all(f'calendar_day_{i}' in report['offsets'] for i in range(1,32)))
        for row in report['resources']:
            at=row['native_offset'];size=row['bytes']
            self.assertEqual(sha256(raw[at:at+size]),row['output_sha256'])
        for row in report['models']:
            at=row['native_offset'];size=row['bytes'];model=raw[at:at+size]
            self.assertEqual(sha256(model),row['output_sha256'])
            self.assertEqual(model[-8:],struct.pack('>II',0xDF000000,0))
            ops=[a>>24 for a,b in struct.iter_unpack('>II',model)]
            self.assertNotIn(0x0A,ops);self.assertNotIn(0xD2,ops)
            for a,b in struct.iter_unpack('>II',model):
                if a>>24 in (1,0xFD):
                    self.assertEqual(b>>24,6)
                    self.assertLess(b&0xFFFFFF,len(prepared[1]))
        # IA8 months use the full 4 KiB. Dual-texture button alpha occupies
        # another tile without overwriting its colour texture.
        month=prepared[4]['calendar_month_0']['rows'][0]
        self.assertEqual(month['shape'],(32,128));self.assertTrue(month['ia8'])
        button=prepared[4]['cal_hyouji_b2_model']['rows']
        loads=[r for r in button if r['opcode']==0xFD]
        self.assertEqual([(r['ui_tile'],r['ui_tmem']) for r in loads],[(0,0),(1,256)])

    def test_missing_inherited_state_unknown_commands_and_tmem_reject(self):
        p=Packet(self.source)
        with self.assertRaisesRegex(ValueError,'missing material'):
            p.model('month',['cal_win_monthT_model'])
        with self.assertRaisesRegex(ValueError,'inherited UI'):
            p.model('month',['cal_win_monthT_model'],texture=(64,128,3,1))
        with self.assertRaisesRegex(ValueError,'inherited UI'):
            p.model('background',['cal_win_tuki_model'],texture=(32,32,2,0))
        with self.assertRaisesRegex(ValueError,'missing material'):
            p.model('year',['cal_win_nen1_model'],texture=(16,16,4,0))
        with self.assertRaisesRegex(ValueError,'Unsupported UI state'):
            validate_state(0xEF000000,0)
        source=copy.copy(self.source);source.data=bytearray(source.data)
        at,n=source.symbol('cal_win_monthT_model')
        struct.pack_into('>I',source.data,at,0xAB000000)
        with self.assertRaisesRegex(ValueError,'Unsupported UI state'):
            Packet(source).model('month',['cal_win_monthT_model'],texture=(32,128,3,1))
        with self.assertRaisesRegex(ValueError,'state-only'):
            Packet(self.source).model('state',['needlework_before_model'])

    def test_connected_keyboard_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-diary-keyboard-') as tmp:
            binary=Path(tmp)/'check'
            compile=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                'tests/v3_diary_editor_test.c','overlays/v3/diary_editor.c',
                'overlays/v3/diary_menu.c','overlays/v3/diary_calendar.c','overlays/v3/diary.c',
                '-o',str(binary)],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(compile.returncode,0,compile.stdout+compile.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())


if __name__=='__main__':unittest.main()
