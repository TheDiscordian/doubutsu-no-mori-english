"""Complete fortune-slip source identities, frozen catalogs, and transactions."""

import ctypes as C
from copy import deepcopy
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom, sha256
from fortune_slips import (CATALOG_HASH, CATALOG_VROM, IDS, WORDS_HASH,
                           catalog_three, words)
from mail_catalog import parse, templates, verify_registered
from mail_format import format_letter
from mail_record import Field, Record, pack, unpack
from runtime_module import module_command_info
from test_mail_format import CText

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
CATALOG = ROOT/'build/mail-catalog/catalog.bin'


class Choice(C.Structure):
    _fields_ = [('phrases',C.c_ubyte*4),('outcome',C.c_ubyte),
                ('template_index',C.c_ubyte),('reserved',C.c_ubyte*2)]


def inputs():
    rom = ROM.read_bytes()
    inventory = {r['id']:r for bank in ('string','super','mail','ps')
                 for r in map(json.loads,(ROOT/'build/inventory'/(bank+'.jsonl')).read_text().splitlines())}
    references = {r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
    return rom,inventory,references,module_command_info(rom)


@unittest.skipUnless(ROM.is_file() and CATALOG.is_file(),'Verified local ROM/catalog references required')
class FortuneSlipSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom,cls.inventory,cls.references,cls.info = inputs()

    def test_all_complete_phrases_in_native_order_and_capacity(self):
        data = words(self.rom,self.references,self.inventory,self.info)
        self.assertEqual((len(IDS),len(set(IDS)),len(data),sha256(data)),(68,68,1088,WORDS_HASH))
        self.assertEqual(data[64*16:],b''.join(value.ljust(16,b' ') for value in
                                             (b'great',b'good',b'pretty good',b'bad')))
        self.assertNotIn('string:02C5',IDS)
        for id in IDS:
            changed = dict(self.references)
            changed[id] = {**changed[id],'text':changed[id]['text']+' '}
            with self.assertRaises(ValueError): words(self.rom,changed,self.inventory,self.info)

    def test_three_new_signatures_preserve_every_previous_part_and_catalog_two(self):
        original = CATALOG.read_bytes()
        new = catalog_three(self.rom,original,self.inventory,self.info)
        self.assertEqual(sha256(new),CATALOG_HASH)
        self.assertEqual(verify_registered(original)['catalog'],2)
        self.assertEqual(verify_registered(new)['catalog'],3)
        old_parts,new_parts = parse(original)[1],parse(new)[1]
        changed = [(name,index) for name in old_parts for index,(a,b) in
                   enumerate(zip(old_parts[name],new_parts[name])) if a != b]
        self.assertEqual(changed,[('ps',0x72),('ps',0x73),('ps',0x74)])
        self.assertEqual(CATALOG.read_bytes(),original)
        # 2A names a native wave decoration, not an ASCII asterisk.
        for _,index in changed: self.assertEqual(new_parts['ps'][index],b'\x2aKatrina\x2a')
        with self.assertRaises(ValueError): catalog_three(self.rom,new,self.inventory,self.info)

    def test_changed_legacy_source_or_native_actor_is_rejected(self):
        for id,field in ((IDS[0],'legacy'),(IDS[-1],'source_sha256')):
            changed = dict(self.inventory);changed[id] = {**changed[id],field:'altered'}
            with self.assertRaises(ValueError): words(self.rom,self.references,changed,self.info)
        changed = bytearray(self.rom);changed[by_vrom(self.rom)[0x8C8F10].pstart] ^= 1
        with self.assertRaises(ValueError): words(bytes(changed),self.references,self.inventory,self.info)
        for id in ('ps:0072','mail:0073','super:0074'):
            changed = dict(self.inventory);changed[id] = {**changed[id],'legacy':changed[id]['legacy']+' '}
            with self.assertRaises(ValueError): catalog_three(self.rom,CATALOG.read_bytes(),changed,self.info)

    @unittest.skipUnless((ROOT/'build/runtime-module/module.json').is_file(),'Current native module required')
    def test_two_catalog_installation_is_explicit_guarded_and_transactional(self):
        from build_fortune_slips import build
        from mail_catalog import install
        from runtime_module import add_runtime_module, MODULE_VROM
        original = CATALOG.read_bytes()
        original_report = json.loads(CATALOG.with_suffix('.json').read_text())
        with tempfile.TemporaryDirectory(prefix='af-fortune-install-') as temporary:
            out = Path(temporary)
            build(self.rom,original,original_report,self.inventory,self.references,out)
            additions,module = add_runtime_module(self.rom,{},ROOT/'build/runtime-module')
            before = dict(additions)
            installed = dict(additions)
            report = install(self.rom,installed,module,out)
            self.assertEqual(installed[0x03000000],original)
            self.assertEqual(sha256(installed[CATALOG_VROM]),CATALOG_HASH)
            self.assertEqual(report['fortune_catalog']['catalog'],3)
            self.assertEqual(installed[MODULE_VROM][0x44:0x48],bytes.fromhex('03000000'))
            changed = deepcopy(module);changed['runtime_sources']['mail/catalog.h'] = '0'*64
            with self.assertRaises(ValueError): install(self.rom,additions,changed,out)
            self.assertEqual(additions,before)
            metadata = json.loads((out/'catalog.json').read_text())
            for mutation in ('untracked','identity','address'):
                bad = deepcopy(metadata)
                if mutation == 'untracked': del bad['fortune_catalog']
                elif mutation == 'identity': bad['fortune_catalog']['sha256'] = '0'*64
                else: bad['fortune_catalog']['vrom'] = '03000000'
                (out/'catalog.json').write_text(json.dumps(bad))
                with self.assertRaises(ValueError): install(self.rom,additions,module,out)
                self.assertEqual(additions,before)
            (out/'catalog.json').write_text(json.dumps(metadata))
            occupied = {**additions,CATALOG_VROM:b'occupied'}
            with self.assertRaises(ValueError): install(self.rom,occupied,module,out)
            self.assertEqual(occupied,{**before,CATALOG_VROM:b'occupied'})

    @unittest.skipUnless((ROOT/'build/fortune-slip-probe/generate.json').is_file(),
                         'Compiled native fortune-slip probe required')
    def test_native_probe_requires_its_variant_sources_complete_jumps_and_safe_ownership(self):
        from mail_generate_probe import validate,relocate
        directory = ROOT/'build/fortune-slip-probe'
        code = (directory/'generate.bin').read_bytes()
        report = json.loads((directory/'generate.json').read_text())
        module = json.loads((ROOT/'build/runtime-module/module.json').read_text())
        validate(code,report,module,fortune_slip=True)
        with self.assertRaises(ValueError): validate(code,report,module)
        for base in (0x801A0010,0x802F8010,0x803F0000):
            self.assertEqual(len(relocate(code,report,module,base,fortune_slip=True)),len(code))
        for key,value in (('variant',None),('sources',{}),('jump_relocations',[]),('module_sha256','0'*64)):
            bad = deepcopy(report);bad[key] = value
            with self.assertRaises(ValueError): validate(code,bad,module,fortune_slip=True)
        for base in (0,0x801948E0,0x80200001,0x80400000):
            with self.assertRaises(ValueError): relocate(code,report,module,base,fortune_slip=True)


@unittest.skipUnless(shutil.which('gcc') and ROM.is_file() and CATALOG.is_file(),
                     'Host GCC and verified local ROM/catalog references required')
class FortuneSlipRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom,inventory,references,info = inputs()
        cls.original = CATALOG.read_bytes()
        cls.catalog = catalog_three(rom,cls.original,inventory,info)
        cls.words = words(rom,references,inventory,info)
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-fortune-slip-')
        output = Path(cls.temporary.name)/'fortune.so'
        sources = ['overlays/mail_generation/generate.c','overlays/mail_generation/fortune_slip.c',
                   'runtime/mail/catalog.c','runtime/mail/format.c','runtime/mail/record.c','runtime/crc32.c',
                   'tests/mail_catalog_mock.c','tests/fortune_slip_mock.c']
        compiled = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                                   *(str(ROOT/p) for p in sources),'-o',str(output)],capture_output=True,text=True)
        if compiled.returncode: raise ValueError(compiled.stderr)
        cls.lib = C.CDLL(str(output))
        cls.lib.af_fortune_slip_create.argtypes = [C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p]
        cls.work_size = cls.lib.af_fortune_test_work_size()
        cls.text_offset = cls.lib.af_fortune_test_text_offset()

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def setUp(self):
        self.rom = (C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom')
        C.memset(self.rom,0,len(self.rom))
        C.memmove(self.rom,self.original,len(self.original))
        C.memmove(C.addressof(self.rom)+CATALOG_VROM-0x03000000,self.catalog,len(self.catalog))
        for name,value in (('enabled',1),('reads',0),('dma_error',0),('fail_read',0)):
            C.c_uint.in_dll(self.lib,'af_mail_catalog_'+name).value = value

    def fixture(self,phrases=(0,0,0,0),outcome=0,template=0,capital=0):
        choice = Choice((C.c_ubyte*4)(*phrases),outcome,template,(C.c_ubyte*2)(0,0))
        mail = C.create_string_buffer(b'!'*16+bytes(range(164))+b'!'*16,196)
        words_memory = C.create_string_buffer(self.words,len(self.words))
        state = C.c_uint(capital)
        memory = C.create_string_buffer(b'!'*(self.work_size+64),self.work_size+64)
        work = (C.addressof(memory)+31)&~15
        return mail,choice,words_memory,state,memory,work

    def invoke(self,fixture,success=True,changed=None):
        mail,choice,word_data,capital,memory,work = fixture
        before = mail.raw,bytes(choice),word_data.raw,capital.value,memory.raw
        args = [C.addressof(mail)+16,164,C.addressof(choice),C.addressof(word_data),1088,C.addressof(capital),work]
        if changed: args[changed[0]] = changed[1]
        self.assertEqual(self.lib.af_fortune_slip_create(*args),int(success))
        self.assertEqual((bytes(choice),word_data.raw),before[1:3])
        lead = work-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.work_size:],b'!'*64)
        self.assertEqual(mail.raw[:16]+mail.raw[180:],b'!'*32)
        if not success:
            self.assertEqual((mail.raw,capital.value),(before[0],before[3]))
            return
        fields = tuple((slot,Field(self.words[row*16:(row+1)*16],0)) for slot,row in
                       enumerate([slot*16+choice.phrases[slot] for slot in range(4)]+[64+choice.outcome]))
        record = Record(3,0,(0x72+choice.template_index,),fields,bool(before[3]))
        expected = bytearray(before[0][16:180]);expected[38:42] = bytes((0,128,5,25));expected[42:] = pack(record)
        self.assertEqual(mail.raw[16:180],bytes(expected))
        self.assertEqual(unpack(mail.raw[58:180],expected_catalog=3),record)
        self.assertEqual(mail.raw[60],97)  # Complete five sixteen-byte fields, no truncation.
        letter = format_letter(record,templates(self.catalog,record))
        actual = CText.from_address(work+self.text_offset)
        self.assertEqual(tuple(bytes(actual.text[o:o+n]) for o,n in zip(actual.offsets,actual.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(letter.body.count(b'\xcd'),6)
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_mail_catalog_dma_error').value,0)
        return record

    def test_all_64_phrases_four_outcomes_three_templates_and_both_capitals(self):
        for template in range(3):
            for outcome in range(4):
                for capital in range(2):
                    for index in range(16):
                        self.invoke(self.fixture(tuple((index+slot*3)%16 for slot in range(4)),outcome,template,capital))

    def test_maximum_phrase_lengths_and_reused_work_preserve_complete_text(self):
        indices = tuple(max(range(16),key=lambda i:len(self.words[(slot*16+i)*16:(slot*16+i+1)*16].rstrip(b' ')))
                        for slot in range(4))
        fixture = self.fixture(indices,2,2,1)
        first = self.invoke(fixture)
        for slot in range(4): fixture[1].phrases[slot] = 15-slot
        fixture[1].outcome,fixture[1].template_index = 3,0
        second = self.invoke(fixture)
        self.assertNotEqual(first,second)

    def test_each_cartridge_read_failure_and_missing_catalog_retain_mail_and_state(self):
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads')
        self.invoke(self.fixture());total = reads.value
        fail = C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read')
        for index in range(1,total+1):
            reads.value,fail.value = 0,index
            self.invoke(self.fixture(capital=1),False)
        fail.value = 0
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 0
        self.invoke(self.fixture(),False)
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
        C.memset(C.addressof(self.rom)+CATALOG_VROM-0x03000000,0,len(self.catalog))
        self.invoke(self.fixture(),False)

    def test_bad_choices_commands_sizes_alignment_and_aliases_cannot_publish(self):
        for field,value in (('outcome',4),('template_index',3)):
            fixture = self.fixture();setattr(fixture[1],field,value);self.invoke(fixture,False)
        for index in range(4):
            fixture = self.fixture();fixture[1].phrases[index] = 16;self.invoke(fixture,False)
        for index in range(2):
            fixture = self.fixture();fixture[1].reserved[index] = 1;self.invoke(fixture,False)
        self.invoke(self.fixture(capital=2),False)
        for byte in (0x7F,0x80):
            fixture = self.fixture();fixture[2][0] = bytes((byte,));self.invoke(fixture,False)
        fixture = self.fixture()
        for index in (0,2,3,5,6): self.invoke(fixture,False,(index,0))
        for index,value in ((1,163),(1,165),(4,1087),(4,1089),
                            (5,C.addressof(fixture[3])+1),(6,fixture[5]+1)):
            self.invoke(fixture,False,(index,value))
        addresses = {0:C.addressof(fixture[0])+16,2:C.addressof(fixture[1]),
                     3:C.addressof(fixture[2]),5:C.addressof(fixture[3]),6:fixture[5]}
        for index in (0,5,6):
            for other,address in addresses.items():
                if other != index: self.invoke(fixture,False,(index,address))

    def test_catalog_three_does_not_reinterpret_old_catalog_two_letters(self):
        old = Record(2,0,(0,),(),False)
        # Existing supported and unsupported rows retain their original identity.
        self.assertEqual(templates(self.original,old).catalog,2)
        with self.assertRaises(ValueError): templates(self.original,replace(old,templates=(0x72,)))
        self.assertEqual(templates(self.catalog,replace(old,catalog=3,templates=(0x72,))).parts[2],b'\x2aKatrina\x2a')


if __name__ == '__main__': unittest.main()
