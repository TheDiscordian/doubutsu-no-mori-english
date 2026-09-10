"""Museum source approvals, both receipt gates, retained ROM, and text credit."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256,verified_rom
from museum_letters import GUARDS,START,END,HOME_GATE,QUEUE_GATE,NAME,TABLE,TEMPLATES,FOSSILS,install,patches,verify_installation,verify_templates
from npc_mail_capture import source_hashes
from npc_mail_loader import VROM,CONFIG_OFFSET,configuration
from runtime_module import MODULE_VROM,verify_test_module
from translation_progress import measure

BUILD = ROOT/'build/museum-letters-pilot'
PREVIOUS = ROOT/'build/post-office-letters-pilot'
CURRENT = ROOT/'build/v0-hardware-fixes-02'
CREATOR = ROOT/'build/letter-runtime-fixtures-02/museum'


@unittest.skipUnless((CURRENT/'build.json').is_file() and (CREATOR/'overlay.json').is_file(),
                     'Current combined cartridge and source-built museum creator required')
class MuseumInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (CURRENT/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((CURRENT/'build.json').read_text());cls.module = cls.report['runtime_module']
        cls.files = by_vrom(cls.built)
        if sha256(cls.built) != cls.report['output_sha256']:
            raise ValueError('Changed combined museum fixture cartridge')
        original = by_vrom(cls.native)[CODE_VROM].extract(cls.native)
        before = bytearray(cls.files[CODE_VROM].extract(cls.built))
        # Restore only the three museum-owned ranges in memory. Reinstallation
        # must reproduce the full current code, including every other change.
        for at,value in patches(original,int(cls.module['symbols']['af_npc_mail_load'],16)).items():
            offset = at-CODE_RAM
            if before[offset:offset+len(value)] != value:
                raise ValueError('Current museum fixture does not contain the expected patch')
            before[offset:offset+len(value)] = original[offset:offset+len(value)]
        cls.base = {CODE_VROM:bytes(before)}
        cls.additions = {int(v,16):cls.files[int(v,16)].extract(cls.built) for v in cls.report['added_files']}

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_all_eighty_one_parts_and_only_three_native_ranges(self):
        replacements,additions,module = self.fixture();report = install(self.native,replacements,additions,module)
        self.assertEqual(json.loads(json.dumps(report)),self.report['museum_letters'])
        self.assertEqual(report['complete_templates'],list(TEMPLATES));self.assertEqual(len(report['parts']),81)
        self.assertEqual(report['fossil_templates'],list(FOSSILS));self.assertTrue(all(r['fields']==[] for r in report['parts']))
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        self.assertEqual(replacements[CODE_VROM],self.files[CODE_VROM].extract(self.built))
        old,new = self.base[CODE_VROM],replacements[CODE_VROM]
        changes = patches(old,int(module['symbols']['af_npc_mail_load'],16));allowed = set()
        self.assertEqual([(at,len(v)) for at,v in changes.items()],[(START,140),(HOME_GATE,52),(QUEUE_GATE,20)])
        for at,value in changes.items():
            offset = at-CODE_RAM;allowed.update(range(offset,offset+len(value)))
            self.assertEqual(new[offset:offset+len(value)],value)
        self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(old,new))))
        for at,target in ((HOME_GATE,0x800A35B4),(QUEUE_GATE,0x800A3644)):
            word = struct.unpack_from('>I',new,at-CODE_RAM)[0]
            self.assertEqual(word>>16,0x1040);self.assertEqual(at+4+4*(word&65535),target)
        # a1 is explicitly zeroed after the loader, before either caller can
        # reach the queue gate's original receipt. The pointer result survives.
        self.assertEqual(struct.unpack_from('>I',new,START-CODE_RAM+19*4)[0],0x00002825)
        self.assertEqual(struct.unpack_from('>I',new,QUEUE_GATE-CODE_RAM+12)[0],0x00402025)
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module)

    def test_failed_install_is_atomic_for_every_dependency_and_guard(self):
        for fault in ('variant','catalog','module','creator','config','name','table',*range(len(GUARDS))):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault=='variant': module['npc_mail_loader']['overlay'].pop('museum')
            elif fault in ('catalog','module','creator'):
                additions.pop({'catalog':0x030A0000,'module':MODULE_VROM,'creator':VROM}[fault])
            elif fault=='config':
                data = bytearray(additions[MODULE_VROM]);data[CONFIG_OFFSET+16] ^= 1;additions[MODULE_VROM] = bytes(data)
            else:
                at = NAME if fault=='name' else TABLE if fault=='table' else GUARDS[fault][0]
                code = bytearray(replacements[CODE_VROM]);code[at-CODE_RAM] ^= 1;replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises(ValueError): install(self.native,*fixture)
            self.assertEqual(fixture,before)

    def test_variant_binding_and_previous_postal_configuration(self):
        for directory,museum in ((CREATOR,True),(ROOT/'build/letter-runtime-fixtures-02/post-office',False)):
            data,reloc = ((directory/n).read_bytes() for n in ('overlay.bin','relocation.bin'))
            report = json.loads((directory/'overlay.json').read_text())
            self.assertEqual(configuration(data,reloc,report,self.module)[4],
                             report['symbols']['af_museum_mail_create' if museum else 'af_post_office_mail_create'])
            self.assertEqual(report['sources'],source_hashes(mother_letters=True,departed_letters=True,
                villager_events=True,academy_letters=True,academy_scores=True,post_office=True,museum=museum))
            for value in (False,None,0,1,'true'):
                with self.assertRaises(ValueError): configuration(data,reloc,{**report,'museum':value},self.module)
        with self.assertRaises(ValueError): source_hashes(museum=True)

    def test_current_complete_cartridge_installation_and_report_corruption(self):
        verify_test_module(self.built,self.module)
        verify_installation(self.built,self.native,self.module,self.report['museum_letters'])
        for name in ('complete_templates','fossil_templates','patches','catalog'):
            report = deepcopy(self.report['museum_letters']);report.pop(name)
            with self.assertRaises(ValueError): verify_installation(self.built,self.native,self.module,report)


@unittest.skipUnless((BUILD/'build.json').is_file() and (PREVIOUS/'build.json').is_file(),
                     'Preserved museum and preceding postal cartridges required')
class MuseumHistoricalArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.files = by_vrom(cls.built)

    def test_complete_rom_prior_text_resources_and_original_rom_patch(self):
        self.assertEqual(sha256(self.built),self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),self.built)
        # Preserve historical patch-retention evidence separately from current
        # source/installation approval and malformed-report rejection above.
        old,new = by_vrom(self.previous),self.files;self.assertEqual(old.keys(),new.keys())
        self.assertEqual({v for v in old if old[v].extract(self.previous)!=new[v].extract(self.built)},
                         {0x19D40,CODE_VROM,MODULE_VROM,VROM})
        self.assertEqual({v for v in old if old[v]!=new[v]},{VROM,0x03400000})
        self.assertEqual(new[VROM].size-old[VROM].size,736)
        self.assertEqual(new[0x03400000].pstart-old[0x03400000].pstart,736)
        table = bytearray(old[0x19D40].extract(self.previous))
        struct.pack_into('>I',table,16+old[VROM].index*16+4,new[VROM].vend)
        struct.pack_into('>I',table,16+old[0x03400000].index*16+8,new[0x03400000].pstart)
        self.assertEqual(bytes(table),new[0x19D40].extract(self.built))
        a,b = (bytearray(data) for data in (old[MODULE_VROM].extract(self.previous),new[MODULE_VROM].extract(self.built)))
        a[0x48:0x68] = b[0x48:0x68] = bytes(32);self.assertEqual(a,b)

    def test_counter_credits_only_installed_museum_ids_without_losing_prior_text(self):
        old = measure(self.native,self.previous,json.loads((PREVIOUS/'build.json').read_text()))
        new = measure(self.native,self.built,self.report)
        self.assertEqual(old.rows.keys(),new.rows.keys());self.assertEqual(new.summary()['total_source_characters'],751002)
        ids = {f'{bank}:{number:04X}' for bank in ('super','mail','ps') for number in TEMPLATES}
        credited = {k for k,r in new.rows.items() if any(v['route']=='museum_letters' for v in r['replacements'])}
        self.assertEqual(credited,ids)
        for key in old.rows:
            self.assertEqual(old.rows[key]['source_characters'],new.rows[key]['source_characters'])
            self.assertTrue(all(r in new.rows[key]['replacements'] for r in old.rows[key]['replacements']))
            if key not in ids: self.assertEqual(old.rows[key],new.rows[key])
        delta = sum(old.rows[k]['source_characters'] for k in ids if not old.rows[k]['replacements'])
        self.assertEqual(new.summary()['replaced_source_characters']-old.summary()['replaced_source_characters'],delta)
        for path in ('build/mail-catalog/catalog.bin','build/mail-glyph-catalog/catalog.bin'):
            self.assertEqual(len(verify_templates(self.native,(ROOT/path).read_bytes())['parts']),81)

    def test_clis_reject_missing_dependencies_before_inputs(self):
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-museum-letters'],'--english-museum-letters requires'),
                ('build_npc_mail_capture.py',['--museum'],'--museum requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn(expected,result.stderr)


if __name__=='__main__': unittest.main()
