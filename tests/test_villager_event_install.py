"""Shared event/Christmas installer boundaries and optional creator dependencies."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,sha256
from departed_letters import START as DEPARTED_START,install as install_departed
from extended_items import VROM as ITEMS_VROM,install as install_items
from mail_catalog import VROM as CATALOG_VROM,install as install_catalog
from mail_view_patch import install as install_reader
from mother_letters import START as MOM_START,install as install_mother
from npc_mail_capture import creator_imports,source_hashes
from npc_mail_loader import VROM,CONFIG_OFFSET,configuration,install as install_loader
from runtime_module import MODULE_VROM,add_runtime_module,verify_test_module
from villager_event_letters import GUARDS,COMPLETE,install,patches,verify_installation

CREATOR = ROOT/'build/letter-runtime-fixtures-01/villager-event'
PILOT = ROOT/'build/v0-hardware-fixes-02'

@unittest.skipUnless((CREATOR/'overlay.json').is_file(),'Compiled event creator required')
class VillagerEventInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = {}
        cls.additions,cls.module = add_runtime_module(cls.native,cls.base,ROOT/'build/notice-seasonal-runtime')
        install_reader(cls.native,cls.base,cls.additions,cls.module,snapshots=True)
        install_items(cls.native,cls.additions,cls.module,ROOT/'build/design-items-resource')
        install_catalog(cls.native,cls.additions,cls.module,ROOT/'build/mail-catalog')
        install_loader(cls.native,cls.base,cls.additions,cls.module,CREATOR)
        install_mother(cls.native,cls.base,cls.additions,cls.module)
        install_departed(cls.native,cls.base,cls.additions,cls.module)

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_complete_parts_and_only_eight_native_ranges_change(self):
        replacements,additions,module = self.fixture()
        report = install(self.native,replacements,additions,module)
        self.assertEqual(report['complete_templates'],list(COMPLETE))
        self.assertEqual(report['unavailable_templates'],[0xF6]);self.assertEqual(len(report['parts']),165)
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        old,new = self.base[CODE_VROM],replacements[CODE_VROM]
        changes = patches(old,int(module['symbols']['af_npc_mail_load'],16));allowed = set()
        self.assertEqual(len(changes),8)
        for at,value in changes.items():
            offset = at-CODE_RAM;allowed.update(range(offset,offset+len(value)))
            self.assertEqual(new[offset:offset+len(value)],value)
        self.assertTrue(all(i in allowed or a == b for i,(a,b) in enumerate(zip(old,new))))
        for at,end in ((0x800A961C,0x800A969C),(0x800A9688,0x800A969C),
                       (0x800A9B3C,0x800A9BB0),(0x800A9B9C,0x800A9BB0),(0x800A9E08,0x800A9E40)):
            word = struct.unpack_from('>I',new,at-CODE_RAM)[0]
            self.assertEqual(word>>16,0x1040);self.assertEqual(at+4+4*(word&65535),end)
        self.assertEqual(new[0x800AC340-CODE_RAM:0x800AC344-CODE_RAM],bytes.fromhex('0002182B'))
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module)

    def test_missing_dependencies_or_changed_native_functions_are_atomic_failures(self):
        for fault in ('variant','catalog','module','creator','config','items','item_header','item_config','mother','departed',*range(len(GUARDS))):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault == 'variant': module['npc_mail_loader']['overlay'].pop('villager_events')
            elif fault in ('catalog','module','creator','items'):
                additions.pop({'catalog':CATALOG_VROM,'module':MODULE_VROM,'creator':VROM,'items':ITEMS_VROM}[fault])
            elif fault == 'item_header': additions[ITEMS_VROM] = b'!'+additions[ITEMS_VROM][1:]
            elif fault in ('config','item_config'):
                value = bytearray(additions[MODULE_VROM]);value[56 if fault == 'item_config' else CONFIG_OFFSET+16] ^= 1
                additions[MODULE_VROM] = bytes(value)
            else:
                at = MOM_START if fault == 'mother' else DEPARTED_START if fault == 'departed' else GUARDS[fault][0]
                code = bytearray(replacements[CODE_VROM]);code[at-CODE_RAM] ^= 1
                replacements[CODE_VROM] = bytes(code)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises(ValueError): install(self.native,*fixture)
            self.assertEqual(fixture,before)

    def test_optional_item_import_and_all_legacy_creator_variants_remain_valid(self):
        for folder,mother,departed,events,entry in (
                ('shared-npc-capture-runtime-followup-01',False,False,False,'af_npc_mail_create'),
                ('letter-runtime-fixtures-01/mother',True,False,False,'af_system_mail_create'),
                ('letter-runtime-fixtures-01/departed',True,True,False,'af_departed_mail_create'),
                ('letter-runtime-fixtures-01/villager-event',True,True,True,'af_villager_event_mail_create')):
            directory = ROOT/'build'/folder
            data,reloc = (directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes()
            report = json.loads((directory/'overlay.json').read_text())
            self.assertEqual(configuration(data,reloc,report,self.module)[4],report['symbols'][entry])
            self.assertEqual(report['sources'],source_hashes(mother_letters=mother,departed_letters=departed,villager_events=events))
            self.assertEqual(set(report['imports']),set(creator_imports(villager_events=events)))
        for value in (False,None,0,1,'true'):
            with self.assertRaises(ValueError): configuration(data,reloc,{**report,'villager_events':value},self.module)
        wrong = deepcopy(report);wrong['imports'].pop('af_load_item_name')
        with self.assertRaises(ValueError): configuration(data,reloc,wrong,self.module)
        with self.assertRaises(ValueError): source_hashes(mother_letters=True,villager_events=True)

    @unittest.skipUnless((PILOT/'build.json').is_file(),'Completed combined cartridge required')
    def test_actual_built_rom_has_complete_routes_and_unchanged_native_helpers(self):
        directory = PILOT
        built = (directory/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((directory/'build.json').read_text())
        self.assertEqual(sha256(built),report['output_sha256']);verify_test_module(built,report['runtime_module'])
        verify_installation(built,self.native,report['runtime_module'],report['villager_event_letters'])
        wrong = deepcopy(report['villager_event_letters']);wrong['complete_templates'].append(0xF6)
        with self.assertRaises(ValueError): verify_installation(built,self.native,report['runtime_module'],wrong)

    def test_clis_reject_missing_dependencies_before_opening_inputs(self):
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-villager-event-letters'],
                 '--english-villager-event-letters requires'),
                ('build_npc_mail_capture.py',['--villager-events'],'--villager-events requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn(expected,result.stderr)


if __name__ == '__main__': unittest.main()
