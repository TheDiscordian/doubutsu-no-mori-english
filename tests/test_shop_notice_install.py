"""Complete installed shop text, enlarged creator bounds, and retained content."""

from copy import deepcopy
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,apply_ups,by_vrom,sha256
from npc_mail_capture import IMAGE_BYTES_MAX,relocate,source_hashes
from npc_mail_loader import VROM,configuration
from runtime_layout import MODULE_VROM,MODULE_RAM,RESERVATION
from runtime_module import verify_test_module
from shop_notice_letters import START,END,REGIONS,GUARDS,TEMPLATES,install,validate,verify_installation
from translation_progress import measure

BUILD = ROOT/'build/shop-notice-letters-pilot'
PREVIOUS = ROOT/'build/snowman-letters-pilot'
OWNERS = ROOT/'build/shop-notice-owners'


@unittest.skipUnless((BUILD/'build.json').is_file(),'Complete local shop notice ROM required')
class ShopNoticeInstallTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text());cls.module = cls.report['runtime_module']
        cls.files = by_vrom(cls.built)
        original = by_vrom(cls.native)[CODE_VROM].extract(cls.native)
        code = bytearray(cls.files[CODE_VROM].extract(cls.built))
        for a,b in REGIONS: code[a-CODE_RAM:b-CODE_RAM] = original[a-CODE_RAM:b-CODE_RAM]
        cls.base = {CODE_VROM:bytes(code)}
        cls.additions = {int(v,16):cls.files[int(v,16)].extract(cls.built) for v in cls.report['added_files']}

    def fixture(self): return dict(self.base),dict(self.additions),deepcopy(self.module)

    def test_complete_install_changes_only_two_native_owners(self):
        replacements,additions,module = self.fixture()
        report = install(self.native,replacements,additions,module,OWNERS)
        self.assertEqual(json.loads(json.dumps(report)),self.report['shop_notices'])
        self.assertEqual(report['complete_templates'],list(TEMPLATES));self.assertEqual(len(report['parts']),27)
        self.assertEqual(report['native_reopening_table'],[29,27,28,29])
        self.assertEqual(report['reference_reopening_table'],[27,27,28,29])
        self.assertEqual(additions,self.additions);self.assertEqual(module,self.module)
        self.assertEqual(replacements[CODE_VROM],self.files[CODE_VROM].extract(self.built))
        allowed = {i for a,b in REGIONS for i in range(a-CODE_RAM,b-CODE_RAM)}
        self.assertTrue(all(i in allowed or a==b for i,(a,b) in enumerate(zip(self.base[CODE_VROM],replacements[CODE_VROM]))))
        with self.assertRaises(ValueError): install(self.native,replacements,additions,module,OWNERS)

    def test_failed_install_retains_inputs_and_native_selectors(self):
        for fault in ('variant','catalog','module','creator','items','config',*range(len(GUARDS)),0x8010DC3C,0x8010DC5C):
            fixture = self.fixture();replacements,additions,module = fixture
            if fault=='variant': module['npc_mail_loader']['overlay'].pop('shop_notices')
            elif fault in ('catalog','module','creator','items'):
                additions.pop({'catalog':0x030A0000,'module':MODULE_VROM,'creator':VROM,'items':0x02A00000}[fault])
            elif fault=='config':
                value = bytearray(additions[MODULE_VROM]);value[0x58] ^= 1;additions[MODULE_VROM] = bytes(value)
            else:
                at = GUARDS[fault][0] if fault<len(GUARDS) else fault
                value = bytearray(replacements[CODE_VROM]);value[at-CODE_RAM] ^= 1;replacements[CODE_VROM] = bytes(value)
            before = deepcopy(fixture)
            with self.subTest(fault=fault),self.assertRaises((ValueError,KeyError)):
                install(self.native,*fixture,OWNERS)
            self.assertEqual(fixture,before)

    def test_real_creator_over_old_limit_and_bound_agreement(self):
        directory = ROOT/'build/shop-notice-creator'
        data,reloc = ((directory/n).read_bytes() for n in ('overlay.bin','relocation.bin'))
        report = json.loads((directory/'overlay.json').read_text())
        self.assertGreater(len(data),0x8000);self.assertLessEqual(len(data),IMAGE_BYTES_MAX)
        self.assertEqual(IMAGE_BYTES_MAX,0x10000)
        header = (ROOT/'runtime/mail/npc_loader.h').read_text()
        self.assertEqual(int(re.search(r'#define AF_NPC_MAIL_IMAGE_BYTES_MAX (0x[0-9A-Fa-f]+)u',header)[1],16),IMAGE_BYTES_MAX)
        for path in (ROOT/'overlays/mail_generation').glob('*capture.ld'):
            self.assertIn('__capture_end - __capture_start <= AF_CREATOR_IMAGE_MAX',path.read_text())
        self.assertEqual(configuration(data,reloc,report,self.module)[4],report['symbols']['af_shop_notice_mail_create'])
        for base in (MODULE_RAM+RESERVATION,0x802F8010,0x80400000-len(data)):
            self.assertEqual(len(relocate(data,reloc,base,report['imports'].values())),len(data))
        with self.assertRaises(ValueError): relocate(data+bytes(0x10000),reloc,0x80200000,report['imports'].values())
        for value in (False,None,0,1,'true'):
            with self.assertRaises(ValueError): configuration(data,reloc,{**report,'shop_notices':value},self.module)
        with self.assertRaises(ValueError): source_hashes(shop_notices=True)

    def test_complete_rom_patch_and_all_earlier_text_retained(self):
        verify_test_module(self.built,self.module)
        verify_installation(self.built,self.native,self.module,self.report['shop_notices'])
        self.assertEqual(apply_ups(self.native,(BUILD/'animal-forest-halfwidth.ups').read_bytes()),self.built)
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes();old = by_vrom(previous)
        self.assertEqual(old.keys(),self.files.keys())
        self.assertEqual({v for v in old if old[v].extract(previous)!=self.files[v].extract(self.built)},
                         {0x19D40,CODE_VROM,MODULE_VROM,VROM})
        a,b = (bytearray(v) for v in (old[MODULE_VROM].extract(previous),self.files[MODULE_VROM].extract(self.built)))
        a[0x48:0x68] = b[0x48:0x68] = bytes(32)
        self.assertEqual([(i,a[i:i+4].hex(),b[i:i+4].hex()) for i in range(0,len(a),4) if a[i:i+4]!=b[i:i+4]],
                         [(0x3408,'34038000','3c030001')])

    def test_counter_credits_only_installed_complete_shop_parts(self):
        ledger = measure(self.native,self.built,self.report)
        baseline = deepcopy(self.report);baseline.pop('shop_notices')
        uncredited = measure(self.native,self.built,baseline)
        self.assertEqual(ledger.summary()['total_source_characters'],751284)
        ids = {f'{bank}:{number:04X}' for bank in ('super','mail','ps') for number in TEMPLATES}
        actual = {k for k,r in ledger.rows.items() if any(v['route']=='shop_notices' for v in r['replacements'])}
        self.assertEqual(actual,ids)
        for key,row in uncredited.rows.items():
            if key not in ids: self.assertEqual(row,ledger.rows[key])
            self.assertTrue(all(r in ledger.rows[key]['replacements'] for r in row['replacements']))

    def test_changed_owner_bytes_sources_and_cli_requirements_rejected(self):
        data = (OWNERS/'owners.bin').read_bytes();report = json.loads((OWNERS/'owners.json').read_text())
        for key in ('sources','sha256','module_sha256','symbols','loader_ram'):
            bad = deepcopy(report);bad.pop(key)
            with self.assertRaises(ValueError): validate(data,bad,self.module)
        for offset in (0,REGIONS[1][0]-START,len(data)-1):
            bad = bytearray(data);bad[offset] ^= 1
            with self.assertRaises(ValueError): validate(bytes(bad),report,self.module)
        for script,args,expected in (
                ('build.py',['--rom','not-read.z64','--english-shop-notices','not-read'],'--english-shop-notices requires'),
                ('build_npc_mail_capture.py',['--shop-notices'],'--shop-notices requires')):
            result = subprocess.run([sys.executable,str(ROOT/'tools'/script),*args],capture_output=True,text=True)
            self.assertEqual(result.returncode,2);self.assertIn(expected,result.stderr)


if __name__=='__main__': unittest.main()
