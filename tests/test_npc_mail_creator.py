"""Whole native-metadata/English-text transaction and scoped publication."""

import ctypes as C
from dataclasses import replace
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from audit_mail_templates import template_fields
from mail_catalog import templates,verify_registered
from mail_format import format_letter
from mail_record import Field,Record,pack,unpack
from npc_mail_capture import WORD_HASH,ALIAS_HASH
from npc_mail_generation import GROUPS,BAD_BASES
from npc_mail_names import unpack_aliases
from npc_mail_words import unpack_words
from test_mail_format import CText
from test_npc_mail_capture import Work,Session

CATALOG = ROOT/'build/mail-catalog/catalog.bin'
WORDS = ROOT/'build/npc-mail-words/words.bin'
ALIASES = ROOT/'build/npc-mail-names/aliases.bin'


@unittest.skipUnless(shutil.which('gcc') and all(p.is_file() for p in (CATALOG,WORDS,ALIASES)),
                     'Host GCC and verified local complete sources required')
class NpcMailCreatorTests(unittest.TestCase):
    extra_sources = ()
    @classmethod
    def setUpClass(cls):
        cls.catalog = CATALOG.read_bytes();verify_registered(cls.catalog)
        cls.words,cls.aliases = WORDS.read_bytes(),ALIASES.read_bytes()
        cls.word_rows = unpack_words(cls.words,WORD_HASH);cls.alias_rows = unpack_aliases(cls.aliases,ALIAS_HASH)
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-npc-mail-creator-')
        library = Path(cls.temporary.name)/'creator.so'
        sources = ['overlays/mail_generation/'+name for name in ('digest.c','npc_capture.c','generate.c','npc_creator.c')]
        sources += list(cls.extra_sources)
        sources += ['runtime/mail/'+name for name in ('record.c','format.c','catalog.c','npc_generation.c')]
        sources += ['tests/'+name for name in ('mail_catalog_mock.c','npc_mail_capture_mock.c','npc_mail_creator_mock.c')]
        flags = ['-fsanitize=address,undefined','-fno-sanitize-recover=all','-fno-omit-frame-pointer','-g'] if os.environ.get('AF_NPC_CREATOR_SANITIZE') == '1' else []
        compiler_env = dict(os.environ);compiler_env.pop('LD_PRELOAD',None)
        compiled = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',*flags,
                        *(str(ROOT/p) for p in sources),'-o',str(library)],capture_output=True,text=True,env=compiler_env)
        if compiled.returncode: raise ValueError(compiled.stderr)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_npc_mail_create.argtypes = [C.c_void_p]*4
        cls.size = cls.lib.af_npc_creator_size()
        cls.stage = cls.lib.af_npc_creator_stage_offset()
        cls.text = cls.lib.af_npc_creator_text_offset()

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def setUp(self):
        self.active = C.c_void_p.in_dll(self.lib,'af_npc_mail_session');self.active.value = None
        self.words_memory = (C.c_ubyte*len(self.words)).in_dll(self.lib,'af_npc_word_data')
        self.alias_memory = (C.c_ubyte*len(self.aliases)).in_dll(self.lib,'af_npc_alias_data')
        C.memmove(self.words_memory,self.words,len(self.words));C.memmove(self.alias_memory,self.aliases,len(self.aliases))
        C.memmove((C.c_ubyte*0x100000).in_dll(self.lib,'af_mail_catalog_rom'),self.catalog,len(self.catalog))
        for name in ('af_npc_creator_calls','af_npc_creator_clear_calls','af_npc_creator_fault',
                     'af_npc_creator_nested_result','af_npc_creator_nested_capital',
                     'af_mail_catalog_reads','af_mail_catalog_dma_error','af_mail_catalog_fail_read'):
            C.c_uint.in_dll(self.lib,name).value = 0
        C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled').value = 1
        self.calls = C.c_uint.in_dll(self.lib,'af_npc_creator_calls')
        self.clear_calls = C.c_uint.in_dll(self.lib,'af_npc_creator_clear_calls')
        self.fault = C.c_uint.in_dll(self.lib,'af_npc_creator_fault')
        self.ids = (C.c_uint*5).in_dll(self.lib,'af_npc_creator_ids')
        self.offsets = (C.c_uint*11).in_dll(self.lib,'af_npc_test_offsets');self.offsets[:] = [0]*11
        (C.c_ubyte*12).in_dll(self.lib,'af_npc_test_other')[:] = b'\xe0\x01'+bytes(10)

    def tearDown(self): self.active.value = None

    def fixture(self,foreign=0,good=1,looks=0,capital=0):
        memory = C.create_string_buffer(b'!'*(self.size+64),self.size+64)
        address = (C.addressof(memory)+31)&~15
        capture = Work.from_address(address)
        player = C.create_string_buffer(b'PLAYER' + b'TOWN  '+bytes.fromhex('12343001'),16)
        animal = C.create_string_buffer(b'\xe0\0'+bytes(9)+bytes((looks,)),12)
        key = next(row.key for row in self.alias_rows if row.npc_index == 0)
        remail = C.create_string_buffer(bytes(4)+key+b'AWAY  '+bytes((looks,0)),18)
        capture.session = Session(None,None,C.addressof(player),C.addressof(animal),
                                  C.addressof(remail) if foreign else None,good,foreign,1234)
        destination = C.create_string_buffer(b'!'*196,196)
        state = C.c_uint(capital)
        self.ids[:] = [GROUPS[foreign][looks]]*5 if good else [BAD_BASES[foreign]+looks*3]+[0]*4
        return memory,address,capture,player,animal,remail,destination,state

    def invoke(self,fixture,success=True,preflight=False):
        memory,address,capture,player,animal,remail,destination,capital = fixture
        before = bytes(destination);old_capital = capital.value
        before_inputs = player.raw,animal.raw,remail.raw
        before_work = memory.raw
        calls = self.calls.value
        self.assertEqual(self.lib.af_npc_mail_create(address,C.byref(destination,16),C.byref(self.active),C.byref(capital)),int(success))
        self.assertIsNone(self.active.value)
        self.assertEqual((player.raw,animal.raw,remail.raw),before_inputs)
        lead = address-C.addressof(memory)
        self.assertEqual(memory.raw[:lead]+memory.raw[lead+self.size:],b'!'*64)
        self.assertEqual(destination.raw[:16]+destination.raw[180:],b'!'*32)
        self.assertEqual(bytes(self.words_memory),self.words);self.assertEqual(bytes(self.alias_memory),self.aliases)
        if not success:
            self.assertEqual(destination.raw,before);self.assertEqual(capital.value,old_capital)
            if preflight:
                self.assertEqual(memory.raw,before_work);self.assertEqual(self.calls.value,calls)
            return
        self.assertEqual(self.calls.value,calls+1)
        cleared = bytearray(164);cleared[38] = 255;cleared[42:] = b' '*122
        self.assertEqual(bytes((C.c_ubyte*164).in_dll(self.lib,'af_npc_creator_before')),bytes(cleared))
        selected = capture.selection
        fields = tuple((slot,Field(bytes(field.text[:field.length]),field.article))
                       for slot,field in enumerate(capture.capture.fields) if capture.capture.valid&(1<<slot))
        result = Record(2,selected.kind,tuple(selected.templates[:5 if selected.kind else 1]),fields,bool(old_capital))
        parts = templates(self.catalog,result)
        needed = set().union(*(template_fields(part) for part in parts.parts))
        result = replace(result,fields=tuple((slot,field) for slot,field in result.fields if slot in needed))
        expected = bytearray(164);expected[:16] = player.raw
        expected[18:24] = remail.raw[4:10] if capture.session.foreign else b'SENDER'
        expected[24:30] = b'AWAY  ' if capture.session.foreign else b'TOWN  '
        expected[30:36] = bytes.fromhex('1234e0000100')
        expected[36:42] = bytes((16 if selected.kind else 0,int(bool(selected.kind)),0,128,0,7+capture.session.foreign))
        expected[42:] = pack(result)
        self.assertEqual(destination.raw[16:180],bytes(expected))
        self.assertEqual(unpack(destination.raw[58:180],expected_catalog=2),result)
        letter = format_letter(result,parts)
        native = CText.from_address(address+self.text)
        self.assertEqual(tuple(bytes(native.text[o:o+n]) for o,n in zip(native.offsets,native.lengths)),
                         (letter.header,letter.body,letter.footer))
        self.assertEqual(capital.value,int(letter.final_capital))
        self.assertEqual(capture.session.initial_capital,old_capital)
        self.assertEqual((capture.phase,capture.failed),(3,0))
        return result

    def test_all_personalities_origins_conditions_and_initial_capitals_publish_complete_records(self):
        for foreign in range(2):
            for good in range(2):
                for looks in range(6):
                    for capital in range(2):
                        with self.subTest(foreign=foreign,good=good,looks=looks,capital=capital):
                            self.invoke(self.fixture(foreign,good,looks,capital))

    def test_reused_workspace_resets_stale_capture_and_retains_shared_capital_semantics(self):
        fixture = self.fixture(capital=1)
        previous = fixture[-1].value
        for i in range(16):
            capture = fixture[2]
            capture.session.initial_capital = 99
            capture.phase,capture.failed = 99,99
            capture.capture.valid = 0xFFFFFFFF
            self.offsets[:] = [i]*11
            result = self.invoke(fixture)
            self.assertEqual(result.initial_capital,bool(previous))
            previous = fixture[-1].value

    def test_missing_preparation_selection_or_lost_scope_cannot_publish(self):
        for fault in (1,3,4):
            fixture = self.fixture(capital=1);self.fault.value = fault
            self.invoke(fixture,False)
        self.fault.value = 0
        fixture = self.fixture(foreign=1)
        C.memmove(C.addressof(fixture[5])+4,b'??????',6)
        self.invoke(fixture,False)
        fixture = self.fixture()
        (C.c_ubyte*12).in_dll(self.lib,'af_npc_test_other')[0] = 0
        self.invoke(fixture,False)

    def test_nested_creator_is_rejected_without_losing_outer_capture(self):
        outer,nested = self.fixture(),self.fixture()
        self.fault.value = 2
        C.c_void_p.in_dll(self.lib,'af_npc_creator_nested_work').value = nested[1]
        nested_mail = (C.c_ubyte*164).in_dll(self.lib,'af_npc_creator_nested_destination');nested_mail[:] = b'!'*164
        self.invoke(outer)
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_npc_creator_nested_result').value,0)
        self.assertEqual(bytes(nested_mail),b'!'*164)
        self.assertEqual(self.calls.value,1)
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_npc_creator_nested_capital').value,0)

    def test_resources_unavailable_templates_and_every_catalog_read_failure_retain_destination(self):
        for resource in (self.words_memory,self.alias_memory):
            fixture = self.fixture(capital=1);last = resource[-1];resource[-1] ^= 1
            before = fixture[6].raw
            calls,clears = self.calls.value,self.clear_calls.value
            self.assertEqual(self.lib.af_npc_mail_create(fixture[1],C.byref(fixture[6],16),C.byref(self.active),C.byref(fixture[7])),0)
            self.assertEqual(fixture[6].raw,before);self.assertEqual(fixture[7].value,1)
            self.assertEqual((self.calls.value,self.clear_calls.value),(calls,clears))
            self.assertIsNone(self.active.value);resource[-1] = last
        fixture = self.fixture(good=1,looks=1,capital=1);self.ids[4] = 77
        self.invoke(fixture,False)
        enabled = C.c_uint.in_dll(self.lib,'af_mail_catalog_enabled');enabled.value = 0
        self.invoke(self.fixture(capital=1),False);enabled.value = 1
        reads = C.c_uint.in_dll(self.lib,'af_mail_catalog_reads');reads.value = 0
        self.invoke(self.fixture())
        count = reads.value
        for index in range(1,count+1):
            fixture = self.fixture(capital=1);reads.value = 0
            C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read').value = index
            self.invoke(fixture,False)

    def test_invalid_requests_alignment_and_intersecting_buffers_are_preflight_failures(self):
        self.assertEqual(self.lib.af_npc_creator_small_control_overlap(),1)
        for field,value in (('player',None),('animal',None),('condition',2),('foreign',1)):
            fixture = self.fixture();setattr(fixture[2].session,field,value)
            self.invoke(fixture,False,True)
        fixture = self.fixture();fixture[-1].value = 2;self.invoke(fixture,False,True)
        fixture = self.fixture();C.c_ubyte.from_address(C.addressof(fixture[4])+11).value = 6
        self.invoke(fixture,False,True)
        fixture = self.fixture()
        args = [fixture[1],C.addressof(fixture[6])+16,C.addressof(self.active),C.addressof(fixture[7])]
        before = fixture[0].raw,fixture[6].raw,fixture[-1].value
        for index in range(4):
            values = [0]
            if index != 1: values.append(args[index]+1)
            for value in values:
                changed = args.copy();changed[index] = value
                self.assertEqual(self.lib.af_npc_mail_create(*changed),0)
        for i in range(4):
            for j in range(4):
                if i == j: continue
                changed = args.copy();changed[i] = args[j]
                self.assertEqual(self.lib.af_npc_mail_create(*changed),0)
        for i in range(4):
            for source in (C.addressof(fixture[3]),C.addressof(fixture[4]),C.addressof(self.words_memory),C.addressof(self.alias_memory)):
                # A work pointer must still describe the real session before
                # overlap checks can read its inputs; test work/input overlap
                # separately by pointing session inputs into the owned work.
                if i == 0: continue
                changed = args.copy();changed[i] = source
                self.assertEqual(self.lib.af_npc_mail_create(*changed),0)
        for field in ('player','animal','remail'):
            old = getattr(fixture[2].session,field);setattr(fixture[2].session,field,fixture[1]+512)
            self.assertEqual(self.lib.af_npc_mail_create(*args),0)
            setattr(fixture[2].session,field,old)
        self.assertEqual((fixture[0].raw,fixture[6].raw,fixture[-1].value),before)
        self.assertEqual(self.calls.value,0)


if __name__ == '__main__': unittest.main()
