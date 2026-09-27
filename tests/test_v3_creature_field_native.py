"""Changed connected field/capture/release consumers, not a replay of old builds."""
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
import v3_creature_field_native as field

OUTPUT=ROOT/os.environ.get('V3_CREATURE_FIELD_BUILD','build/v3-creature-field-runtime-02')


class FieldTests(unittest.TestCase):
    def test_complete_loader_and_startup_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-field-') as directory:
            for name in ('v3_creature_field_test','v3_creature_startup_test'):
                executable=Path(directory)/name
                subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    str(ROOT/'tests'/f'{name}.c'),'-o',str(executable)],check=True,capture_output=True)
                result=subprocess.run([str(executable)],check=True,capture_output=True,timeout=20)
                self.assertIn(b'pass',result.stdout)

    @unittest.skipUnless((OUTPUT/'build-lock.json').is_file(),'Connected current field build required')
    def test_complete_cartridge_and_changed_readers(self):
        image,report=inputs(OUTPUT/'build-lock.json');base,prior=inputs(OUTPUT/'base-lock.json')
        files=by_vrom(image);original=by_vrom(base);r=report['equipment_resources']['creature_field']
        blob=files[BLOB].extract(image);packet=r['packet'];start=packet['blob_offset']
        raw=blob[start:start+packet['bytes']]
        self.assertEqual(sha256(raw),packet['sha256']);self.assertEqual(len(raw),field.SIZE)
        self.assertEqual(raw[-16:],struct.pack('>4I',*([field.GUARD]*4)))
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        pool,rows,_=field.prepared_pool(source,ROOT/'build/v3-creature-field-prepared-01')
        self.assertEqual(rows,r['rows']);self.assertEqual(len(rows),17)
        p=r['pool'];self.assertEqual(image[p['physical']:p['physical']+p['bytes']],pool)
        tables={t['name']:raw[t['ram']-field.RAM:t['ram']-field.RAM+t['bytes']] for t in r['tables']}
        for t in r['tables']:self.assertEqual(sha256(tables[t['name']]),t['sha256'])
        self.assertEqual(struct.unpack('>45H',tables['fish-capture-identities']),
            (*range(0x2300,0x2320),0x250E,0x250F,0x2510,0x2316,*range(0x2320,0x2329)))
        self.assertEqual([x['actor_index'] for x in rows if x['category']=='fish'],list(range(36,45)))
        self.assertEqual([x['actor_index'] for x in rows if x['category']=='insect'],list(range(32,40)))
        for owner in r['owners']:
            data=files[owner['vrom']].extract(image);reloc=files[owner['reloc']].extract(image)
            self.assertEqual(sha256(data),owner['sha256']);self.assertEqual(sha256(reloc),owner['reloc_sha256'])
            old=original[owner['vrom']].extract(base);old_reloc=original[owner['reloc']].extract(base)
            restored=bytearray(data)
            for patch in owner['patches']:
                offset=patch['address']-owner['ram'];self.assertEqual(u32(data,offset),patch['after'])
                struct.pack_into('>I',restored,offset,patch['before'])
            self.assertEqual(restored,old)
            before=native_references(old,old_reloc,expected_sections=tuple(owner['sections']))
            after=native_references(data,reloc,expected_sections=tuple(owner['sections']))
            self.assertEqual(set(before[2])-set(after[2]),set(owner['removed_relocations']))
            self.assertFalse(set(after[2])-set(before[2]))
            # Resident references must not be offset again when this owner moves.
            locations=after[3]
            for patch in owner['patches']:
                if patch['address']-owner['ram'] in before[3]:
                    self.assertNotIn(patch['address']-owner['ram'],locations)
        self.assertEqual(tables['release-shadow-x'][-4:],tables['release-shadow-x'][-8:-4])
        self.assertEqual(tables['release-shadow-z'][-4:],tables['release-shadow-z'][-8:-4])
        self.assertEqual(struct.unpack('>7f',tables['release-shadow-scale'])[-1],struct.unpack('>f',bytes.fromhex('3F99999A'))[0])
        for v,_,_ in field.BANKS.values():self.assertEqual(files[v].extract(image),original[v].extract(base))
        for key in ('save_runtime','save_codec','translation_baseline'):
            self.assertEqual(report[key],prior[key])
        self.assertFalse(r['selectable']);self.assertFalse(r['native_execution_tested'])
        self.assertEqual(report['equipment_resources']['player_actions']['rod_effects'],
                         prior['equipment_resources']['player_actions']['rod_effects'])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (OUTPUT/'asset-loader.ups').read_bytes()),image)
        from v3_creature_items import checked
        checked(image,report,source)
        boot=report['equipment_resources']['surface_bootstrap']['code']
        self.assertIn(f'-DAF_CREATURE_FIELD_VROM=0x{packet["vrom"]:X}u',boot['flags'])
        self.assertLessEqual(boot['bytes'],688)
        from v3_furniture_pipeline import rig_import_plan
        parents=report['equipment_resources']['creature_items']
        inventory=dict(rows=[dict(item_id=p['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=p['source']['profile']) for p in parents['profiles']])
        pending=rig_import_plan(inventory,prior,{},selected=['1C48'],category='creature-profile-assets',source=source)
        self.assertTrue(pending['creature_field']);self.assertNotIn('creature_parents',pending)
        complete=rig_import_plan(inventory,report,{},category='creature-profile-assets',source=source)
        self.assertNotIn('creature_field',complete)
        import v3_optional_composition as composer
        old=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');catalogue=composer.catalogue(image,report)
            self.assertEqual(len(catalogue),167)
            self.assertFalse({row['id'] for row in parents['rows']}&set(catalogue))
            self.assertEqual(composer.compose(image,report,catalogue,composer.resolve(catalogue,list(catalogue)))[0],image)
            empty=composer.compose(image,report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=old


if __name__=='__main__':unittest.main()
