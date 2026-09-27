"""Complete selected-palette lifecycle, installed resources, and composition."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups,CODE_VROM,CODE_RAM
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
import v3_furniture_roofs as roofs
import v3_room_rig_runtime as runtime


class RoofRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_ROOF_BUILD','build/v3-selected-palette-runtime-04')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-parent-needle-imports-02/cartridge/build-lock.json')
        cls.files=by_vrom(cls.image);cls.blob=cls.files[BLOB].extract(cls.image)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_actual_dispatch_and_full_art_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-roof-runtime-') as directory:
            binary=Path(directory)/'test'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-pointer-to-int-cast','-ffp-contract=off','-fsanitize=address,undefined',
                '-fno-omit-frame-pointer','-fno-pie','-no-pie','-DAF_V3_SELECTED_PALETTE',
                '-DAF_V3_SHARED_PALETTE_FADE','-DAF_V3_ROOM_RIG_PACKET',
                'tests/v3_room_palettes_test.c','overlays/v3/room_palettes.c','-o',str(binary)],
                cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary),*(str(ROOT/'build/v3-selected-palette-assets-01'/name)
                for name in ('3024.n64obj.bin','3028.n64obj.bin'))],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)
            self.assertIn('4800 frames',run.stdout)

    def test_installed_full_models_selector_profiles_and_preservation(self):
        bindings=runtime.bind_profiles(self.source,self.image,self.report)
        e=self.report['equipment_resources'];room=e['room_rigs']
        self.assertEqual(room['roof_contract'],roofs.native_contract(self.source,self.image))
        self.assertEqual(len(room['roof_contract']['colour_correspondence']),12)
        for donor in ('3024','3028'):
            binding=bindings[donor];self.assertTrue(binding['staged'])
            row=next(r for r in room['rows'] if r['source_item_id']==donor)
            self.assertEqual((row['mode'],row['first'],row['last']),(7,12,0))
            self.assertTrue(row['profile_installed']);self.assertFalse(row['parent_selectable'])
            art=(ROOT/'build/v3-selected-palette-assets-01'/f'{donor}.n64obj.bin').read_bytes()
            self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],art)
            self.assertEqual(row['roof_lifecycle'],roofs.lifecycle(self.source.profile(int(donor,16))))
        self.assertLessEqual(room['code']['bytes'],32768);self.assertLessEqual(room['bootstrap']['bytes'],1536)
        for row in self.prior['equipment_resources']['room_rigs']['rows']:
            self.assertEqual(next(r for r in room['rows'] if r['source_item_id']==row['source_item_id']),row)
        for key in ('room_carry','room_goods'):
            self.assertEqual(e[key],self.prior['equipment_resources'][key])
        for vrom in (0x82D7F0,0x844400,0x8576C0,0x858960,0x8D4A20,0xD5B000,0xD5D000):
            self.assertEqual(self.files[vrom].extract(self.image),by_vrom(self.base)[vrom].extract(self.base))
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        self.assertEqual(self.report['save_runtime']['profile_hex'],self.prior['save_runtime']['profile_hex'])
        provenance=json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']
        for donor in ('3024','3028'):
            name=next(r for r in provenance if r['id']==f'GAFE01-r0/item/{donor}/name')
            self.assertEqual(name['locales']['en']['credit'],'official')
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_changed_native_selector_or_colour_correspondence_reject(self):
        for vrom,offset in ((CODE_VROM,0x80087C88-CODE_RAM),(CODE_VROM,0x80094BF4-CODE_RAM),
                (0x8D4A20,0x114),(0xD5D000,8+25*4+3),(0xD5B000,0x65C)):
            files=dict(self.files);bad=bytearray(files[vrom].extract(self.image));bad[offset]^=1
            entry=mock.Mock(wraps=files[vrom]);entry.extract.return_value=bytes(bad);files[vrom]=entry
            with mock.patch.object(roofs,'by_vrom',return_value=files),self.assertRaises(ValueError):
                roofs.native_contract(self.source,self.image)
        room=self.report['equipment_resources']['room_rigs']
        row=copy.deepcopy(next(r for r in room['rows'] if r.get('mode')==7));row['first']=1
        with self.assertRaises(ValueError):runtime.encode_packet([row])

    def test_private_browser_and_offline_selections_match(self):
        from tests.test_v3_room_rig_runtime import CurrentImportedRigTests
        # No new choice is enabled until the real HRA reward route is installed.
        self.rows=self.report['automatic_furniture']['imports']
        CurrentImportedRigTests.test_private_browser_selection_matches_offline_and_keeps_translation_only(self)


if __name__=='__main__':unittest.main()
