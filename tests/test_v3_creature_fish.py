"""One changed-category check: source values, relocation, preservation, and output."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,u32,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_player_actions import native_references
import v3_creature_fish as fish

OUTPUT=ROOT/os.environ.get('V3_CREATURE_FISH_BUILD','build/v3-creature-fish-runtime-02')


class FishTests(unittest.TestCase):
    def test_position_approach_and_origin_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-fish-') as directory:
            exe=Path(directory)/'check'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_creature_fish_test.c'),'-o',str(exe)],check=True,capture_output=True)
            result=subprocess.run([str(exe)],check=True,capture_output=True,timeout=20)
            self.assertIn(b'pass',result.stdout)

    @unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Current fish-world build required')
    def test_complete_current_category_installation(self):
        image,report=inputs(OUTPUT/'build-lock.json');base,prior=inputs(OUTPUT/'base-lock.json')
        files=by_vrom(image);old=by_vrom(base);e=report['equipment_resources'];r=e['creature_fish']
        field=e['creature_field'];p=field['packet'];blob=files[BLOB].extract(image)
        packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(sha256(packet),p['sha256']);self.assertLessEqual(r['compiled']['bytes'],0xC00)
        self.assertEqual(sha256(packet[fish.CODE:fish.CODE+r['compiled']['bytes']]),r['compiled']['sha256'])
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        arrays,receipts=fish.parameters(source)
        self.assertEqual(packet[fish.TABLE:fish.TABLE+len(arrays)],arrays)
        self.assertEqual(r['source_tables'][:len(receipts)],receipts)
        self.assertEqual(sha256(packet[fish.TABLE:fish.TABLE+r['table_bytes']]),r['table_sha256'])
        for row in r['owners']:
            data=files[row['vrom']].extract(image);reloc=files[row['reloc']].extract(image)
            previous=old[row['vrom']].extract(base);prev_rel=old[row['reloc']].extract(base)
            self.assertEqual(sha256(data),row['sha256']);self.assertEqual(sha256(reloc),row['reloc_sha256'])
            self.assertEqual(len(data),len(previous));self.assertEqual(reloc[:16],prev_rel[:16])
            restored=bytearray(data)
            for patch in row['patches']:
                at=patch['address']-row['ram'];self.assertEqual(u32(data,at),patch['after'])
                struct.pack_into('>I',restored,at,patch['before'])
            self.assertEqual(restored,previous)
            before=native_references(previous,prev_rel,expected_sections=tuple(row['sections']))
            after=native_references(data,reloc,expected_sections=tuple(row['sections']))
            self.assertEqual(set(before[2])-set(after[2]),set(row['removed_relocations']))
            self.assertFalse(set(after[2])-set(before[2]))
            if row['name']=='fish':
                for pc in (0x80A5B758,0x80A5B760,0x80A5B764,0x80A5B768):
                    self.assertIn(pc-row['ram'],after[3])
                for pc in (0x80A5B740,0x80A5B74C):self.assertNotIn(pc-row['ram'],after[3])
        # Original golden-rod paths are retained inside the changed owners.
        for owner in e['player_actions']['rod_effects']['owners']:
            data=files[owner['vrom']].extract(image)
            for patch in owner['patches']:
                at=patch['address']-owner['ram'];want=bytes.fromhex(patch['after'])
                self.assertEqual(data[at:at+len(want)],want)
        for key in ('save_runtime','save_codec','translation_baseline','physical_resources'):
            self.assertEqual(report[key],prior[key])
        for key in ('pool','rows'):self.assertEqual(field[key],prior['equipment_resources']['creature_field'][key])
        self.assertFalse(r['selectable']);self.assertEqual(r['additional_resident_bytes'],0)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (OUTPUT/'asset-loader.ups').read_bytes()),image)
        from v3_furniture_pipeline import rig_import_plan
        parents=e['creature_items']
        inventory=dict(rows=[dict(item_id=p['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=p['source']['profile']) for p in parents['profiles']])
        pending=rig_import_plan(inventory,prior,{},selected=['1C48'],category='creature-profile-assets',source=source)
        self.assertTrue(pending['creature_fish']);self.assertNotIn('creature_field',pending)
        self.assertNotIn('creature_fish',rig_import_plan(inventory,report,{},category='creature-profile-assets',source=source))
        import v3_optional_composition as composer
        old_config=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');catalogue=composer.catalogue(image,report)
            self.assertEqual(len(catalogue),167)
            self.assertEqual(composer.compose(image,report,catalogue,composer.resolve(catalogue,list(catalogue)))[0],image)
            empty=composer.compose(image,report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=old_config


if __name__=='__main__':unittest.main()
