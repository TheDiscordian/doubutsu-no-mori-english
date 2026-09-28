"""Complete diary category data and editing/save core; no native UI claim."""
import copy
import json
import re
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256, yaz0_decode
from v3_furniture_pipeline import Source
import v3_diaries as diaries
from tests.test_v3_save_compressed import canonical


class DiaryTests(unittest.TestCase):
    def test_calendar_against_actual_donor_code(self):
        reference=ROOT/'local/ac-decomp/src/game'
        for name in ('m_calendar.c','m_calendar_ovl.c'):
            self.assertEqual(sha256((reference/name).read_bytes()),diaries.REFERENCES['src/game/'+name])
        source=(reference/'m_calendar.c').read_text()
        source+=(reference/'m_calendar_ovl.c').read_text().split('static void mDC_set_string',1)[0]
        source=re.sub(r'^#include[^\n]*\n','',source,flags=re.M)
        with tempfile.TemporaryDirectory(prefix='v3-diary-calendar-') as temp:
            out=Path(temp)
            (out/'reference-calendar.inc').write_text(source)
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(out),'-I'+str(ROOT/'overlays/v3'),'tests/v3_diary_calendar_test.c',
                'overlays/v3/diary.c','overlays/v3/diary_calendar.c','-o',str(out/'check')],
                cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(out/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_sanitized_connected_menu_and_native_surface_adapter(self):
        with tempfile.TemporaryDirectory(prefix='v3-diary-menu-') as temp:
            binary=Path(temp)/'check'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                'tests/v3_diary_menu_test.c','overlays/v3/diary.c','overlays/v3/diary_calendar.c',
                'overlays/v3/diary_menu.c','overlays/v3/diary_room.c','overlays/v3/room_carry.c',
                '-o',str(binary)],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_prepared_mips_core_and_current_build_bindings(self):
        output = ROOT/'build/v3-diary-category-work-01/prepared-04'
        report = json.loads((output/'diaries.json').read_text())
        raw = (output/report['code_file']).read_bytes()
        self.assertEqual(sha256(raw),report['compiled']['sha256'])
        self.assertEqual(len(raw),report['compiled']['bytes'])
        self.assertLess(len(raw),0x6000-16)
        self.assertEqual(report['compiled']['symbols']['af_v3_save_reset'],0x80670000)
        self.assertEqual(report['planned_memory'],diaries.LAYOUT)
        # The shared emitter adds a separate UI category without changing this
        # compiled core. Verify current generated carried commands below, and
        # verify only this category's provenance entries through ui_text.
        derived={'tools/v3_furniture_art.py','translations/provenance.json'}
        for path, digest in report['sources'].items():
            if path in derived:continue
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertFalse(report['native_installed'])
        self.assertTrue(all(not r['selectable'] for r in report['rows']))
        from v3_furniture_install import inputs
        image, prior = inputs(ROOT/report['base_lock'])
        self.assertEqual(diaries.native_contract(image),report['native_interaction'])
        art=report['carried_artwork']
        self.assertEqual(sha256((output/art['file']).read_bytes()),art['sha256'])
        self.assertEqual(art['shared_styles'],16)
        self.assertEqual(set(art['offsets']),{'material','geometry'})
        self.assertEqual(report['ui_text'],diaries.ui_text(Source(
            (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())))
        from v3_furniture_pipeline import prepare_material_pair
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        parts=[(name,*source.symbol(name)) for name in ('obj_item_diaryT_mat_model','obj_item_diaryT_gfx_model')]
        prepared=prepare_material_pair(source,parts)
        self.assertEqual(prepared[5],(output/'carried/commands.c').read_text())
        self.assertEqual(prior['runtime_abi'],report['base_runtime_abi'])
        self.assertEqual(prior['save_codec']['format_version'],9)
        for name in ('af_v3_save_check_extended','af_v3_save_pack_extended'):
            self.assertEqual(report['compiled']['link_symbols'][name],prior['save_codec']['active_codec_code']['symbols'][name])

    def test_sanitized_native_save_adapter_and_editor_capacity(self):
        with tempfile.TemporaryDirectory(prefix='v3-diary-save-') as temp:
            out = Path(temp)
            flags = ['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections',
                '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1','-DAF_V3_SURFACE_PROFILE=1',
                '-DAF_V3_CREATURE_PROFILE=1','-DAF_V3_INSECT_SEASONS=1','-DAF_V3_DIARY_STORAGE=1']
            run = subprocess.run(['cc',*flags,'-Daf_v3_save_check=af_console_canonical_check',
                '-Daf_v3_save_pack=af_console_canonical_pack','-Daf_v3_save_collect=af_console_canonical_collect',
                '-c','overlays/v3/save_codec.c','-o',str(out/'codec.o')],cwd=ROOT,
                capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run = subprocess.run(['cc',*flags,'-DAF_V3_CONSOLE_STORAGE=1','-Wl,--gc-sections',
                'tests/v3_diary_storage_test.c','overlays/v3/save_runtime.c','overlays/v3/console_storage.c',
                'overlays/v3/save_compressed.c','overlays/v3/diary.c',str(out/'codec.o'),
                '-o',str(out/'check')],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run = subprocess.run([str(out/'check')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_complete_source_category_and_monthly_consumers(self):
        source = Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        report = diaries.discover(source)
        self.assertEqual([r['parent_item_id'] for r in report['rows']], [f'{0x2B00+i:04X}' for i in range(16)])
        self.assertEqual([r['display_item_id'] for r in report['rows']], [f'{0x30FC+i*4:04X}' for i in range(16)])
        self.assertTrue(all(not r['selectable'] and not r['room_placement_uses_display'] for r in report['rows']))
        self.assertEqual(report['text_bytes'],4*12*992)
        self.assertEqual(report['serialized_bytes'],48048)
        altered = copy.copy(source)
        changed = bytearray(source.rel)
        changed[source.sections[1][0]+0x260E58+32] ^= 1
        altered.rel = bytes(changed)
        with self.assertRaisesRegex(ValueError,'complete diary consumer'):
            diaries.discover(altered)
        altered = copy.copy(source)
        changed = bytearray(source.data)
        changed[source.symbol('diary_price_table')[0]] ^= 1
        altered.data = bytes(changed)
        with self.assertRaisesRegex(ValueError,'complete diary resource'):
            diaries.discover(altered)

    def test_sanitized_edit_save_roundtrip_and_independent_decoder(self):
        # A saved town is fixture data only. No historical ROM is executed.
        payload = (ROOT/'build/rc2-existing-save-diagnostic-01/test.flash').read_bytes()[:65536]
        bank = bytearray(canonical(payload))
        struct.pack_into('>II',bank,0xF984,0x00080680,5)
        struct.pack_into('>I',bank,0xF990,0)
        struct.pack_into('>I',bank,0xF990,zlib.crc32(bank[0xF980:]))
        with tempfile.TemporaryDirectory(prefix='v3-diary-') as temp:
            out = Path(temp)
            (out/'input.bin').write_bytes(bank)
            run = subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-DAF_V3_DIARY_STORAGE=1','-DAF_V3_CREATURE_PROFILE=1','-DAF_V3_INSECT_SEASONS=1',
                'tests/v3_diary_test.c','overlays/v3/diary.c','overlays/v3/save_compressed.c',
                '-o',str(out/'check')],cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run = subprocess.run([str(out/'check'),str(out/'input.bin'),str(out/'packed.bin'),
                str(out/'decoded.bin')],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())
            packed = (out/'packed.bin').read_bytes()
            decoded = (out/'decoded.bin').read_bytes()
            length = struct.unpack_from('>I',packed,0xF990)[0]
            stream = packed[20:0x2F68]+packed[0x2F6A:0xF980]
            self.assertEqual(yaz0_decode(b'Yaz0'+struct.pack('>I',len(decoded))+bytes(8)+stream[:length]), decoded)
            self.assertEqual(decoded[:65536],bank)
            self.assertEqual(len(decoded),120112)
            self.assertEqual(stream[length:],bytes(len(stream)-length))


if __name__ == '__main__':
    unittest.main()
