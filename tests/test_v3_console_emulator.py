"""Focused native lifecycle adapter, installation, and private composition."""
from pathlib import Path
import copy
import os
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE
from v3_console_emulator import SOURCES,VROM,RELOC,CODE_BYTES,patch,install
from v3_furniture_install import inputs


class ConsoleEmulatorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_CONSOLE_EMULATOR_BUILD','build/v3-console-emulator-capacity-01')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.images=cls.report['equipment_resources']['console_images']

    def test_native_adapter_with_actual_images_and_save_executor(self):
        prepared=ROOT/'build/v3-console-games-prepared-06'
        with tempfile.TemporaryDirectory(prefix='v3-console-emulator-') as temp:
            binary=Path(temp)/'check'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                '-DAF_CONSOLE_METADATA_BYTES=6336','-DAF_CONSOLE_POOL_BYTES=770144',
                '-DAF_CONSOLE_POOL_ROM=0x03F43FA0',
                str(ROOT/'tests/v3_console_emulator_test.c'),
                *(str(ROOT/'overlays/v3'/name) for name in ('console_image_native.c','console_image.c','console_save.c')),
                '-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            run=subprocess.run([str(binary),str(prepared/'games-metadata.bin'),str(prepared/'games-pool.bin'),str(prepared/'games.bin')],
                               capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            print(run.stdout.strip())

    def test_checked_hooks_and_retained_resources(self):
        files=by_vrom(self.image);old=by_vrom(self.base);images=self.images;p=images['packet']
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes();original_files=by_vrom(original)
        expected_owner,expected_reloc,receipt=patch(original_files[VROM].extract(original),
            original_files[RELOC].extract(original),images['compiled']['symbols'])
        self.assertEqual(files[VROM].extract(self.image),expected_owner)
        self.assertEqual(files[RELOC].extract(self.image),expected_reloc)
        self.assertEqual(images['emulator']['native'],receipt)
        self.assertEqual(len(receipt['removed_relocations']),6)
        self.assertEqual(len(receipt['hooks']),7)
        self.assertEqual(set(files),set(old))
        for v in files:
            if v not in (BLOB,MODULE,0x19D40,VROM,RELOC):
                self.assertEqual(files[v].extract(self.image),old[v].extract(self.base),hex(v))
        blob=files[BLOB].extract(self.image);data=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(data),p['sha256']);self.assertEqual(zlib.crc32(data),p['crc32'])
        self.assertEqual(sha256(data[:images['compiled']['bytes']]),images['compiled']['sha256'])
        previous=self.prior['equipment_resources']['console_images'];q=previous['packet']
        prior_blob=old[BLOB].extract(self.base);prior_data=prior_blob[q['blob_offset']:q['blob_offset']+q['bytes']]
        self.assertEqual(data[CODE_BYTES:],prior_data[CODE_BYTES:])
        self.assertEqual(images['room'],previous['room'])
        pool=images['pool'];start=pool['physical'];end=start+pool['bytes']
        self.assertEqual(self.image[start:end],self.base[start:end])
        for path in SOURCES:self.assertEqual(images['emulator']['sources'][path],sha256((ROOT/path).read_bytes()),path)
        for key in ('console_storage','room_goods','room_carry'):
            self.assertEqual(self.report['equipment_resources'][key]['packet'],self.prior['equipment_resources'][key]['packet'])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['automatic_furniture']['imports'],self.prior['automatic_furniture']['imports'])
        self.assertTrue(images['launch_installed'])
        self.assertTrue(images['emulator']['arena_capacity_checked'])
        self.assertTrue(images['emulator']['room_launch_installed'])
        self.assertFalse(images['emulator']['save_format_changed'])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_refresh_rejects_changed_installed_code(self):
        # Failure must precede compilation or writing a new packet.
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        raw=by_vrom(self.image)[BLOB].extract(self.image)
        with tempfile.TemporaryDirectory(prefix='v3-console-refresh-') as temp:
            for field in ('sha256','relocation_sha256'):
                changed=copy.deepcopy(self.report)
                changed['equipment_resources']['console_images']['emulator']['native'][field]='0'*64
                blob=bytearray(raw)
                with self.assertRaisesRegex(ValueError,'Changed installed console lifecycle'):
                    install(self.image,changed,blob,Path(temp),original)
                self.assertEqual(blob,raw)
            changed=copy.deepcopy(self.report)
            changed['equipment_resources']['console_images']['compiled']['sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'Changed installed console lifecycle'):
                install(self.image,changed,bytearray(raw),Path(temp),original)

    def test_private_browser_composition(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
