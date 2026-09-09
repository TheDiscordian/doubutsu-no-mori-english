"""Full secret-letter installation, retained text fixes, and combined counting."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import apply_ups,by_vrom,sha256
from secret_actor import (VROM,RELOCATION,NEW_VROM,NEW_RELOCATION,OWNER_VROM,METADATA,
                          RESIDENT_BYTES,LIMIT,START,END,RAM,TEMPLATES,baseline,metadata,
                          install,validate,verify_installation,relocation_bytes)
from secret_scenario import scenario,choice_for_seed
from translation_progress import measure

BUILD,PREVIOUS,ACTOR = (ROOT/'build'/p for p in ('secret-letters-pilot','shop-notice-letters-pilot','secret-actor'))


@unittest.skipUnless((BUILD/'build.json').is_file(),'Completed local secret-letter build required')
class SecretInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes();cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text());cls.prior = json.loads((PREVIOUS/'build.json').read_text())
        cls.module = cls.report['runtime_module'];cls.files = by_vrom(cls.built);cls.old = by_vrom(cls.previous)
        cls.relocations = {int(k,16):int(v,16) for k,v in cls.prior['vrom_relocations'].items()}
        cls.base = {int(v,16):cls.old[cls.relocations.get(int(v,16),int(v,16))].extract(cls.previous) for v in cls.prior['replacement_files']}
        cls.additions = {int(v,16):cls.old[int(v,16)].extract(cls.previous) for v in cls.prior['added_files']}
        cls.data,cls.reloc = ((ACTOR/p).read_bytes() for p in ('overlay.bin','relocation.bin'))
        cls.actor = json.loads((ACTOR/'overlay.json').read_text());cls.catalog = cls.files[0x030A0000].extract(cls.built)

    def fixture(self): return deepcopy((self.base,self.additions,self.relocations,self.module))

    def test_atomic_installer_and_original_dma_ownership(self):
        fixture = self.fixture();replacements,additions,relocations,module = fixture
        self.assertEqual(install(self.native,*fixture,ACTOR),self.report['secret_actor'])
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        self.assertEqual(replacements[VROM],self.data);self.assertEqual(replacements[RELOCATION],self.reloc)
        self.assertEqual(replacements[OWNER_VROM],self.files[OWNER_VROM].extract(self.built))
        self.assertEqual(relocations,{**self.relocations,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
        self.assertEqual(len(self.data),19392);self.assertEqual(len(self.reloc),2192);self.assertLess(len(self.data),LIMIT)
        self.assertEqual(struct.unpack_from('>4I',self.reloc),(19392,0,0,0))
        with self.assertRaises(ValueError): install(self.native,*fixture,ACTOR)

    def test_failures_leave_all_installation_maps_untouched(self):
        for fault in ('module','catalog','overlap','metadata','dates','bss'):
            fixture = self.fixture();replacements,additions,relocations,module = fixture
            if fault in ('module','catalog'): additions.pop({'module':0x02800000,'catalog':0x030A0000}[fault])
            elif fault=='overlap': relocations[VROM] = NEW_VROM
            else:
                key,at = (OWNER_VROM,METADATA) if fault=='metadata' else (VROM,0 if fault=='dates' else len(replacements[VROM])-1)
                data = bytearray(replacements[key]);data[at] ^= 1;replacements[key] = bytes(data)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)): install(self.native,*fixture,ACTOR)
            self.assertEqual(fixture,before)

    def test_rehashed_mutations_cannot_replace_code_text_or_retained_prefix(self):
        for at in (0,START-RAM,END-RAM,17968,RESIDENT_BYTES,18784,len(self.data)-1):
            data = bytearray(self.data);data[at] ^= 1;report = deepcopy(self.actor);report['overlay_sha256'] = sha256(data)
            with self.subTest(at=at),self.assertRaises(ValueError):
                validate(self.native,bytes(data),self.reloc,report,self.module,self.catalog)
        for fault in ('source','snapshot','high','low','target','duplicate'):
            report,reloc = deepcopy(self.actor),self.reloc
            if fault=='source': report['sources']['overlays/mail_generation/secret_creator.c'] = '0'*64
            elif fault=='snapshot': report['snapshots']['cases'][0]['text'] = '00'*1040
            else:
                if fault in ('high','low'): report['elf_relocations'].pop(0 if fault=='high' else 1)
                elif fault=='target': report['elf_relocations'][1][2] += 4
                else: report['elf_relocations'].append(report['elf_relocations'][0])
                if fault!='duplicate':
                    reloc = relocation_bytes(baseline(self.native,self.module)[1],report['elf_relocations'],len(self.data))
                    report.update(relocation_bytes=len(reloc),relocation_sha256=sha256(reloc))
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                validate(self.native,self.data,reloc,report,self.module,self.catalog)

    def test_full_rom_patch_preserves_every_unrelated_dma_file_and_owner_word(self):
        self.assertEqual(sha256(self.built),self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),self.built)
        verify_installation(self.built,self.native,self.module,self.report['secret_actor'])
        self.assertEqual(self.old.keys()-self.files.keys(),{VROM,RELOCATION})
        self.assertEqual(self.files.keys()-self.old.keys(),{NEW_VROM,NEW_RELOCATION})
        self.assertEqual({v for v in self.old.keys()&self.files.keys() if self.old[v].extract(self.previous)!=self.files[v].extract(self.built)},
                         {0x19D40,OWNER_VROM})
        owner = bytearray(self.old[OWNER_VROM].extract(self.previous));owner[METADATA:METADATA+20] = metadata(len(self.data))
        self.assertEqual(bytes(owner),self.files[OWNER_VROM].extract(self.built))
        before = self.old[VROM].extract(self.previous)
        self.assertEqual(before[:START-RAM],self.data[:START-RAM]);self.assertEqual(before[END-RAM:],self.data[END-RAM:len(before)])
        for old,new in ((VROM,NEW_VROM),(RELOCATION,NEW_RELOCATION)): self.assertEqual(self.old[old].index,self.files[new].index)
        for name in ('overlay.bin','relocation.bin','overlay.json'):
            self.assertEqual((ACTOR/name).read_bytes(),(ROOT/'build/secret-actor-repro'/name).read_bytes())

    def test_combined_counter_adds_only_forty_five_parts_without_changing_denominator(self):
        old,new = measure(self.native,self.previous,self.prior),measure(self.native,self.built,self.report)
        ids = {f'{bank}:{number:04X}' for bank in ('super','mail','ps') for number in TEMPLATES}
        credited = {k for k,r in new.rows.items() if any(v['route']=='secret_actor' for v in r['replacements'])}
        self.assertEqual(credited,ids);self.assertEqual(old.rows.keys(),new.rows.keys())
        self.assertEqual(old.summary()['total_source_characters'],new.summary()['total_source_characters'])
        for key in old.rows:
            if key not in ids: self.assertEqual(old.rows[key],new.rows[key])
            self.assertTrue(all(r in new.rows[key]['replacements'] for r in old.rows[key]['replacements']))
        delta = sum(old.rows[k]['source_characters'] for k in ids if not old.rows[k]['replacements'])
        self.assertEqual(new.summary()['replaced_source_characters']-old.summary()['replaced_source_characters'],delta)
        self.assertGreater(delta,0)

    def test_scenario_binds_all_native_choices_and_rejects_changed_rom(self):
        actions = scenario(self.native,self.built,self.report);request = next(a['test_secret_letters'] for a in actions if 'test_secret_letters' in a)
        self.assertEqual(len(request['cases']),30)
        self.assertEqual({(c['choice'],c['capital']) for c in request['cases']},{(i,c) for i in range(15) for c in (0,1)})
        for case in request['cases']: self.assertEqual(choice_for_seed(case['seed']),(case['choice'],case['rng_first']))
        self.assertEqual(actions[1],{'save_state':True});self.assertEqual(actions[4],{'load_state':True})
        with self.assertRaises(ValueError): scenario(self.native,self.built[:-1],self.report)

    def test_cli_rejects_missing_dependencies_before_reading_rom(self):
        result = subprocess.run([sys.executable,'tools/build.py','--rom','not-read.z64','--english-secret-letters','not-read'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertIn('--english-secret-letters requires',result.stderr)


if __name__=='__main__': unittest.main()
