"""Complete actor installation, rejected stale inputs, prior text, and accounting."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256,verified_rom,replace_dma
from snowman_actor import (VROM,RELOCATION,NEW_VROM,NEW_RELOCATION,METADATA,LIMIT,
                           native_sources,metadata,install,validate,verify_installation,relocation_bytes)
from translation_progress import measure

BUILD,PREVIOUS,LEGACY_ACTOR = (ROOT/'build'/p for p in ('snowman-letters-pilot','museum-letters-pilot','snowman-actor'))
CURRENT = ROOT/'build/v0-hardware-fixes-02'
ACTOR = ROOT/'build/shop-notice-snowman'


@unittest.skipUnless((CURRENT/'build.json').is_file() and (ACTOR/'overlay.json').is_file(),
                     'Current combined cartridge and matching Snowman actor required')
class SnowmanInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (CURRENT/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((CURRENT/'build.json').read_text())
        cls.module = cls.report['runtime_module'];cls.files = by_vrom(cls.built)
        if sha256(cls.built)!=cls.report['output_sha256']:
            raise ValueError('Changed combined Snowman fixture cartridge')
        cls.relocations = {int(k,16):int(v,16) for k,v in cls.report['vrom_relocations'].items()}
        cls.base = {int(v,16):cls.files[cls.relocations.get(int(v,16),int(v,16))].extract(cls.built)
                    for v in cls.report['replacement_files']}
        cls.additions = {int(v,16):cls.files[int(v,16)].extract(cls.built) for v in cls.report['added_files']}
        cls.data,cls.reloc = ((ACTOR/p).read_bytes() for p in ('overlay.bin','relocation.bin'))
        cls.actor = json.loads((ACTOR/'overlay.json').read_text())
        cls.catalog,cls.items = (cls.files[v].extract(cls.built) for v in (0x030A0000,0x02A00000))
        if (cls.actor!=cls.report['snowman_actor']['overlay'] or cls.base[VROM]!=cls.data
                or cls.base[RELOCATION]!=cls.reloc):
            raise ValueError('Snowman source-built fixture differs from the installed actor')
        # Recreate only the pre-Snowman ownership in memory; all other installed
        # code, readers, resources, and relocations remain current.
        code = bytearray(cls.base[CODE_VROM]);at = METADATA-CODE_RAM
        if code[at:at+32]!=metadata(len(cls.data)):
            raise ValueError('Changed installed Snowman fixture metadata')
        original = by_vrom(cls.native)[CODE_VROM].extract(cls.native)
        code[at:at+32] = original[at:at+32];cls.base[CODE_VROM] = bytes(code)
        for v in (VROM,RELOCATION):
            cls.base.pop(v);cls.relocations.pop(v)

    def fixture(self): return deepcopy((self.base,self.additions,self.relocations,self.module))

    def test_install_round_trips_persisted_manifest_and_owns_original_dma_rows(self):
        fixture = self.fixture();replacements,additions,relocations,module = fixture
        report = install(self.native,*fixture,ACTOR)
        self.assertEqual(report,self.report['snowman_actor']);self.assertEqual(additions,self.additions)
        self.assertEqual(module,self.module)
        self.assertEqual(replacements[VROM],self.data);self.assertEqual(replacements[RELOCATION],self.reloc)
        self.assertEqual(replacements[CODE_VROM],self.files[CODE_VROM].extract(self.built))
        self.assertEqual(relocations,{**self.relocations,VROM:NEW_VROM,RELOCATION:NEW_RELOCATION})
        self.assertEqual(len(self.data),18384);self.assertEqual(len(self.reloc),1104);self.assertLess(len(self.data),LIMIT)
        self.assertEqual(struct.unpack_from('>5I',self.reloc),(18384,0,0,0,270))
        self.assertEqual(replace_dma(self.native,replacements,relocations,additions),self.built)
        with self.assertRaises(ValueError): install(self.native,*fixture,ACTOR)

    def test_failed_install_is_atomic_before_any_output_mutation(self):
        for fault in ('module','catalog','items','overlap','metadata'):
            fixture = self.fixture();replacements,additions,relocations,module = fixture
            if fault in ('module','catalog','items'):
                additions.pop({'module':0x02800000,'catalog':0x030A0000,'items':0x02A00000}[fault])
            elif fault=='overlap': relocations[VROM] = NEW_VROM
            else:
                code = bytearray(replacements[CODE_VROM]);code[METADATA-CODE_RAM] ^= 1;replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)): install(self.native,*fixture,ACTOR)
            self.assertEqual(fixture,before)

    def test_actor_rejects_changed_text_code_sources_and_missing_relocation(self):
        for fault in ('table','code','source','snapshot','high','low','target','duplicate'):
            data,reloc,report = self.data,self.reloc,deepcopy(self.actor)
            if fault in ('table','code'):
                data = bytearray(data);data[-1 if fault=='table' else 0] ^= 1
                data = bytes(data);report['overlay_sha256'] = sha256(data)
            elif fault=='source': report['sources']['overlays/mail_generation/snowman_creator.c'] = '0'*64
            elif fault=='snapshot': report['snapshots']['cases'][0]['text'] = '00'*1040
            else:
                if fault in ('high','low'): report['elf_relocations'].pop(0 if fault=='high' else 1)
                elif fault=='target': report['elf_relocations'][1][2] += 4
                else: report['elf_relocations'].append(report['elf_relocations'][0])
                if fault!='duplicate':
                    reloc = relocation_bytes(native_sources(self.native)[1],report['elf_relocations'],len(data))
                    report.update(relocation_bytes=len(reloc),relocation_sha256=sha256(reloc))
            with self.subTest(fault=fault),self.assertRaises(ValueError):
                validate(self.native,data,reloc,report,self.module,self.catalog,self.items)

    def test_current_installed_actor_resources_and_source_bound_manifest(self):
        spec = verify_installation(self.built,self.native,self.module,self.report['snowman_actor'])
        self.assertEqual(spec.sections,(18384,0,0,0,270))
        self.assertEqual(self.data,self.files[NEW_VROM].extract(self.built))
        self.assertEqual(self.reloc,self.files[NEW_RELOCATION].extract(self.built))


@unittest.skipUnless((BUILD/'build.json').is_file() and (PREVIOUS/'build.json').is_file(),
                     'Preserved Snowman and preceding museum cartridges required')
class SnowmanHistoricalArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text());cls.prior = json.loads((PREVIOUS/'build.json').read_text())
        cls.files = by_vrom(cls.built);cls.old = by_vrom(cls.previous)
        cls.data = (LEGACY_ACTOR/'overlay.bin').read_bytes()

    def test_patch_retains_every_previous_file_and_changes_only_actor_metadata(self):
        self.assertEqual(sha256(self.built),self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),self.built)
        # Original patch/retention evidence, kept separate from current source
        # and complete installed-resource approval in the class above.
        self.assertEqual(self.old.keys()-self.files.keys(),{VROM,RELOCATION})
        self.assertEqual(self.files.keys()-self.old.keys(),{NEW_VROM,NEW_RELOCATION})
        self.assertEqual({v for v in self.old.keys()&self.files.keys()
                          if self.old[v].extract(self.previous)!=self.files[v].extract(self.built)},
                         {0x19D40,CODE_VROM})
        code = bytearray(self.old[CODE_VROM].extract(self.previous))
        code[METADATA-CODE_RAM:METADATA-CODE_RAM+32] = metadata(len(self.data))
        self.assertEqual(bytes(code),self.files[CODE_VROM].extract(self.built))
        for old,new in ((VROM,NEW_VROM),(RELOCATION,NEW_RELOCATION)):
            self.assertEqual(self.old[old].index,self.files[new].index)
        for name in ('overlay.bin','relocation.bin','overlay.json'):
            self.assertEqual((LEGACY_ACTOR/name).read_bytes(),(ROOT/'build/snowman-actor-repro'/name).read_bytes())

    def test_combined_counter_credits_all_thirty_six_parts_and_retains_denominator(self):
        old = measure(self.native,self.previous,self.prior);new = measure(self.native,self.built,self.report)
        ids = {f'{bank}:{number:04X}' for bank in ('super','mail','ps') for number in range(0x202,0x20E)}
        credited = {k for k,r in new.rows.items() if any(v['route']=='snowman_actor' for v in r['replacements'])}
        self.assertEqual(credited,ids);self.assertEqual(old.rows.keys(),new.rows.keys())
        self.assertEqual(old.summary()['total_source_characters'],new.summary()['total_source_characters'])
        for key in old.rows:
            if key not in ids: self.assertEqual(old.rows[key],new.rows[key])
            self.assertTrue(all(r in new.rows[key]['replacements'] for r in old.rows[key]['replacements']))
        delta = sum(old.rows[k]['source_characters'] for k in ids if not old.rows[k]['replacements'])
        self.assertEqual(new.summary()['replaced_source_characters']-old.summary()['replaced_source_characters'],delta)
        self.assertGreater(delta,0)

    def test_cli_rejects_missing_dependencies_before_reading_rom(self):
        result = subprocess.run([sys.executable,'tools/build.py','--rom','not-read.z64',
                                 '--english-snowman-letters','not-read'],cwd=ROOT,capture_output=True,text=True)
        self.assertEqual(result.returncode,2);self.assertIn('--english-snowman-letters requires',result.stderr)


if __name__=='__main__': unittest.main()
