"""Current surface optional profiles, source guards, and browser equivalence."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_VROM,by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB,MODULE,MODULE_RAM
from v3_furniture_install import inputs
from v3_surface_selection import SOURCES,options,profile,checksum_fields,table_writes,update_report
from v3_surface_items import RAM
import v3_optional_composition as composer
import v3_browser_composition as browser

OUT=ROOT/'build/v3-surface-selection-runtime-02'


class SurfaceSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        composer.use_build_lock(OUT/'build-lock.json')
        cls.image,cls.report=composer.inputs();cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.blob=cls.files[BLOB].extract(cls.image)
        cls.surface=cls.report['room_surfaces'];cls.items=cls.surface['items']
        cls.catalogue=composer.catalogue(cls.image,cls.report)
    @classmethod
    def tearDownClass(cls):
        composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=cls.pin

    def test_source_bound_category_and_unchanged_resources(self):
        selected=options(self.blob,self.report)
        self.assertEqual(len(selected),6);self.assertEqual(len(self.catalogue),147)
        self.assertEqual(sorted(r['kind'] for r in selected.values()),['floor']*3+['wall']*3)
        self.assertEqual(len(self.surface['optional_selection']['pending']),4)
        self.assertFalse(set(selected)&set(self.surface['optional_selection']['pending']))
        for row in self.items['rows']:
            self.assertEqual(row['enabled'],row['id'] in selected)
        for key in ('stock','sound','scoring','application','banks','rows'):
            self.assertEqual(self.surface[key],self.prior['room_surfaces'][key])
        for key in ('save_codec','save_runtime','hra','staged_furniture','fire_sound'):
            self.assertEqual(self.report[key],self.prior[key])
        self.assertEqual(self.files[CODE_VROM].extract(self.image),by_vrom(self.base)[CODE_VROM].extract(self.base))
        self.assertFalse(self.report['saved_format_changed']);self.assertEqual(self.report['save_codec']['format_version'],4)
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)
        for path in SOURCES:self.assertEqual(sha256((ROOT/path).read_bytes()),self.surface['sources'][path])
        for row in self.surface['menu']['tables']:
            self.assertEqual(row['rows'],67);self.assertEqual(len(row['imports']),3)
            self.assertEqual(len(row['available_imports']),5)

    def test_data_crc_fields_native_reads_and_mutations(self):
        fields=checksum_fields(self.image,self.report);self.assertEqual(len(fields),2)
        owners=((self.items['bootstrap']['code'],self.report['equipment_resources']['ram'],
                    self.blob[self.report['equipment_resources']['blob_offset']:],self.items['bootstrap']['ram'],
                    'af_v3_surface_crc_expected'),
                (self.report['startup'],MODULE_RAM,self.files[MODULE].extract(self.image),0x8019A8E0,
                    'af_v3_equipment_crc_expected'))
        for code,ram,data,entry,symbol in owners:
            target=code['symbols'][symbol];raw=data[entry-ram:entry-ram+code['bytes']]
            self.assertEqual(sha256(raw),code['sha256'])
            self.assertGreaterEqual(target,entry);self.assertLess(target,entry+code['bytes'])
            words=list(struct.unpack('>'+str(len(raw)//4)+'I',raw))
            high=(target+0x8000)>>16;low=target&65535
            # Complete MIPS code must actually load the editable word, not
            # retain the compiler's old constant as an instruction immediate.
            self.assertTrue(any(w>>26==15 and w&65535==high for w in words))
            self.assertTrue(any(w>>26==35 and w&65535==low for w in words))
        self.assertLessEqual(self.report['startup']['bytes'],992)
        bad=bytearray(self.image);bad[fields[0]['offset']]^=1
        with self.assertRaisesRegex(ValueError,'checksum data'):checksum_fields(bad,self.report)
        bad=bytearray(self.blob);bad[self.items['blob_offset']+self.items['rows'][0]['offset']+4]^=1
        with self.assertRaisesRegex(ValueError,'packet/contract'):options(bad,self.report)
        with self.assertRaisesRegex(ValueError,'Duplicate'):profile([next(iter(options(self.blob,self.report).values()))]*2)
        report=copy.deepcopy(self.report);report['room_surfaces']['stock']['pending']=[]
        with self.assertRaisesRegex(ValueError,'dependencies'):options(self.blob,report)

    def test_selected_profiles_catalogue_and_report(self):
        chosen=['GAFE01-r0/item/261A','GAFE01-r0/item/2712']
        selection=composer.resolve(self.catalogue,chosen)
        result,writes,blob=composer.compose(self.image,self.report,self.catalogue,selection)
        self.assertFalse(any(bytes.fromhex(selection['profile_hex'])))
        wanted=bytearray(64);wanted[9]=4;wanted[41]=2
        self.assertEqual(bytes.fromhex(selection['surface_profile_hex']),wanted)
        _,tables=table_writes(self.image,self.report,set(chosen))
        current=copy.deepcopy(self.report);update_report(result,blob,current,selection,tables)
        self.assertEqual(current['room_surfaces']['items']['enabled_items'],2)
        self.assertEqual(current['room_surfaces']['optional_selection']['profile_hex'],wanted.hex())
        for row in current['room_surfaces']['menu']['tables']:self.assertEqual(row['rows'],65)
        for f in checksum_fields(result,current):
            self.assertEqual(int(f['before'],16),zlib.crc32(result[f['start']:f['start']+f['length']]))
        self.assertEqual(composer.compose(self.image,self.report,self.catalogue,
            composer.resolve(self.catalogue,list(self.catalogue)))[0],self.image)
        self.assertEqual(sha256(composer.compose(self.image,self.report,self.catalogue,
            composer.resolve(self.catalogue,[]))[0]),self.report['translation_baseline']['sha256'])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),self.image)

    def test_browser_current_full_rom_equivalence(self):
        plan=browser.rules(self.image,self.report);cases=[]
        for name,ids in (('all',list(self.catalogue)),('empty',[]),
                ('surfaces-only',['GAFE01-r0/item/261A','GAFE01-r0/item/2712']),
                ('mixed-surface-villager',['GAFE01-r0/item/2641','GAFE01-r0/villager/00EB'])):
            selection=composer.resolve(self.catalogue,ids)
            result,_,_=composer.compose(self.image,self.report,self.catalogue,selection)
            cases.append(dict(name=name,requested=ids,selection=selection,sha256=sha256(result)))
        with tempfile.TemporaryDirectory(prefix='v3-surface-browser-') as directory:
            path=Path(directory)/'fixture.json';path.write_bytes(composer.canonical(dict(plan=plan,cases=cases,
                base=str(OUT/'animal-forest-v3-asset-loader.z64'),stable=str(composer.stable_reference(self.report)[0]))))
            run=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(path)],
                capture_output=True,text=True,timeout=60)
        self.assertEqual(run.returncode,0,run.stderr);self.assertEqual(len(json.loads(run.stdout)['passed']),4)

    def test_editable_bootstrap_c_failure_paths(self):
        with tempfile.TemporaryDirectory(prefix='v3-surface-crc-') as directory:
            binary=Path(directory)/'test'
            run=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-DAF_V3_EDITABLE_CHECKSUMS=1','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_surface_items_test.c'),'-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(run.returncode,0,run.stderr)
            run=subprocess.run([str(binary)],capture_output=True,text=True,timeout=20)
            self.assertEqual(run.returncode,0,run.stderr)


if __name__=='__main__':unittest.main()
