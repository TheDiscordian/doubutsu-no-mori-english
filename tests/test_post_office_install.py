"""Source bindings, exact delivery patches, whole-ROM retention, and accounting."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256
from post_office_letters import GUARDS,START,END,ORDER_GATE,TICKET_GATE,TEMPLATES,install,patches,verify_installation,verify_templates
from npc_mail_capture import source_hashes
from npc_mail_loader import VROM,CONFIG_OFFSET,configuration
from runtime_module import MODULE_VROM,verify_test_module
from translation_progress import measure

BUILD = ROOT/'build/post-office-letters-pilot'
PREVIOUS = ROOT/'build/mail-shared-guards-pilot'


@unittest.skipUnless((BUILD/'build.json').is_file() and (PREVIOUS/'build.json').is_file(),
                     'Completed postal and preceding guard builds required')
class PostOfficeInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.module = cls.report['runtime_module']
        cls.files = by_vrom(cls.built)
        cls.base = {CODE_VROM:by_vrom(cls.previous)[CODE_VROM].extract(cls.previous)}
        cls.additions = {int(v,16):cls.files[int(v,16)].extract(cls.built) for v in cls.report['added_files']}

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_all_fifteen_parts_and_only_three_native_ranges_change(self):
        replacements,additions,module = self.fixture();report = install(self.native,replacements,additions,module)
        self.assertEqual(json.loads(json.dumps(report)),self.report['post_office_letters'])
        self.assertEqual(report['complete_templates'],list(TEMPLATES));self.assertEqual(len(report['parts']),15)
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        self.assertEqual(replacements[CODE_VROM],self.files[CODE_VROM].extract(self.built))
        old,new = self.base[CODE_VROM],replacements[CODE_VROM]
        changes = patches(old,int(module['symbols']['af_npc_mail_load'],16));allowed = set()
        self.assertEqual([(at,len(value)) for at,value in changes.items()],[(START,END-START),(ORDER_GATE,28),(TICKET_GATE,28)])
        for at,value in changes.items():
            offset = at-CODE_RAM;allowed.update(range(offset,offset+len(value)))
            self.assertEqual(new[offset:offset+len(value)],value)
        self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(old,new))))
        for at in (ORDER_GATE,TICKET_GATE):
            word = struct.unpack_from('>I',new,at-CODE_RAM)[0]
            self.assertEqual(word,0x10400003);self.assertEqual(at+4+4*(word&65535),at+16)
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module)

    def test_failed_install_is_atomic_for_every_dependency_and_guard(self):
        for fault in ('variant','catalog','module','creator','items','item_config','config',*range(len(GUARDS))):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault == 'variant': module['npc_mail_loader']['overlay'].pop('post_office')
            elif fault in ('catalog','module','creator','items'):
                additions.pop({'catalog':0x030A0000,'module':MODULE_VROM,'creator':VROM,'items':0x02A00000}[fault])
            elif fault in ('config','item_config'):
                value = bytearray(additions[MODULE_VROM]);value[CONFIG_OFFSET+16 if fault=='config' else 56] ^= 1
                additions[MODULE_VROM] = bytes(value)
            else:
                code = bytearray(replacements[CODE_VROM]);code[GUARDS[fault][0]-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises(ValueError): install(self.native,*fixture)
            self.assertEqual(fixture,before)

    def test_compiled_variant_source_bindings_and_earlier_guard_build(self):
        for directory,postal in ((ROOT/'build/post-office-creator',True),(ROOT/'build/mail-shared-guards-creator',False)):
            data,reloc = ((directory/n).read_bytes() for n in ('overlay.bin','relocation.bin'))
            report = json.loads((directory/'overlay.json').read_text())
            config = configuration(data,reloc,report,self.module)
            self.assertEqual(config[4],report['symbols']['af_post_office_mail_create' if postal else 'af_academy_score_mail_create'])
            self.assertEqual(report['sources'],source_hashes(mother_letters=True,departed_letters=True,
                villager_events=True,academy_letters=True,academy_scores=True,post_office=postal))
            for value in (False,None,0,1,'true'):
                with self.assertRaises(ValueError): configuration(data,reloc,{**report,'post_office':value},self.module)
        with self.assertRaises(ValueError): source_hashes(post_office=True)

    def test_complete_rom_existing_resources_and_original_rom_patch(self):
        self.assertEqual(sha256(self.built),self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),self.built)
        verify_test_module(self.built,self.module)
        verify_installation(self.built,self.native,self.module,self.report['post_office_letters'])
        old,new = by_vrom(self.previous),self.files;self.assertEqual(old.keys(),new.keys())
        self.assertEqual({v for v in old if old[v].extract(self.previous)!=new[v].extract(self.built)},
                         {0x19D40,CODE_VROM,MODULE_VROM,VROM})
        # The creator grows by 800 stored bytes. Its DMA end and the physical
        # start of the following unchanged font blob are the only table edits.
        self.assertEqual({v for v in old if old[v]!=new[v]},{VROM,0x03400000})
        self.assertEqual(new[VROM].size-old[VROM].size,800)
        self.assertEqual(new[0x03400000].pstart-old[0x03400000].pstart,800)
        table = bytearray(old[0x19D40].extract(self.previous))
        struct.pack_into('>I',table,16+old[VROM].index*16+4,new[VROM].vend)
        struct.pack_into('>I',table,16+old[0x03400000].index*16+8,new[0x03400000].pstart)
        self.assertEqual(bytes(table),new[0x19D40].extract(self.built))
        old_module = bytearray(old[MODULE_VROM].extract(self.previous));new_module = bytearray(new[MODULE_VROM].extract(self.built))
        old_module[0x48:0x68] = new_module[0x48:0x68] = bytes(32)
        self.assertEqual(old_module,new_module)
        for name in ('complete_templates','item_resource_sha256','patches','catalog'):
            report = deepcopy(self.report['post_office_letters']);report.pop(name)
            with self.assertRaises(ValueError): verify_installation(self.built,self.native,self.module,report)

    def test_counter_credits_only_installed_postal_ids_and_retains_old_total(self):
        old_report = json.loads((PREVIOUS/'build.json').read_text())
        old = measure(self.native,self.previous,old_report);new = measure(self.native,self.built,self.report)
        self.assertEqual(old.rows.keys(),new.rows.keys())
        self.assertEqual(new.summary()['total_source_characters'],751002)
        identities = {f'{bank}:{number:04X}' for bank in ('super','mail','ps') for number in TEMPLATES}
        credited = {key for key,row in new.rows.items() if any(r['route']=='post_office_letters' for r in row['replacements'])}
        self.assertEqual(credited,identities)
        for key in old.rows:
            self.assertEqual(old.rows[key]['source_characters'],new.rows[key]['source_characters'])
            self.assertTrue(all(r in new.rows[key]['replacements'] for r in old.rows[key]['replacements']))
            if key not in identities: self.assertEqual(new.rows[key],old.rows[key])
        extra = sum(old.rows[k]['source_characters'] for k in identities if not old.rows[k]['replacements'])
        self.assertEqual(new.summary()['replaced_source_characters']-old.summary()['replaced_source_characters'],extra)
        for catalog in ('build/mail-catalog/catalog.bin','build/mail-glyph-catalog/catalog.bin'):
            self.assertEqual(len(verify_templates(self.native,(ROOT/catalog).read_bytes())['parts']),15)

    def test_clis_reject_missing_dependencies_before_inputs(self):
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-post-office-letters'],'--english-post-office-letters requires'),
                ('build_npc_mail_capture.py',['--post-office'],'--post-office requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn(expected,result.stderr)


if __name__=='__main__': unittest.main()
