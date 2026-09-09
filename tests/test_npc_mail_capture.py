"""Full source integrity, ordered capture, and native-call forwarding contracts."""

import ctypes as C
import hashlib
from pathlib import Path
import random
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from npc_mail_names import unpack_aliases
from npc_mail_words import unpack_words
from npc_mail_generation import WORD_BASES,GROUPS,BAD_BASES
from test_mail_generate import Capture,Selection
from test_mail_format import CField


class Sources(C.Structure):
    _fields_ = [('words',C.c_void_p),('aliases',C.c_void_p),('ready',C.c_uint)]


class Session(C.Structure):
    _fields_ = [('event',C.c_void_p),('stage',C.c_void_p),('player',C.c_void_p),('animal',C.c_void_p),
               ('remail',C.c_void_p),('condition',C.c_uint),('foreign',C.c_uint),('initial_capital',C.c_uint)]


class Work(C.Structure):
    _fields_ = [('session',Session),('sources',Sources),('capture',Capture),('selection',Selection),
               ('phase',C.c_uint),('failed',C.c_uint),('words_seen',C.c_uint),('names_seen',C.c_uint)]


@unittest.skipUnless(shutil.which('gcc'),'Host GCC required')
class NpcMailCaptureTests(unittest.TestCase):
    compiler_flags = ()
    word_path = ROOT/'build/npc-mail-words/words.bin'
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-npc-mail-capture-')
        output = Path(cls.temporary.name)/'capture.so'
        sources = ['overlays/mail_generation/digest.c','overlays/mail_generation/npc_capture.c',
                   'overlays/mail_generation/generate.c','runtime/mail/npc_generation.c',
                   'runtime/mail/record.c','runtime/mail/format.c','runtime/mail/catalog.c','runtime/crc32.c',
                   'tests/mail_catalog_mock.c','tests/npc_mail_capture_mock.c']
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                        *cls.compiler_flags,*(str(ROOT/path) for path in sources),'-o',str(output)],check=True,capture_output=True)
        cls.lib = C.CDLL(str(output))
        for name,args in {
            'af_mail_source_digest':[C.c_void_p,C.c_void_p,C.c_uint],
            'af_npc_mail_sources_init':[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p,C.c_uint],
            'af_npc_mail_source_word':[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint],
            'af_npc_mail_source_name':[C.c_void_p,C.c_void_p,C.c_uint],
            'af_npc_mail_source_alias':[C.c_void_p,C.c_void_p,C.c_void_p],
            'af_npc_mail_capture_event':[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint],
            'af_npc_mail_prepare':[C.c_void_p]*3,
            'af_npc_mail_sender_name':[C.c_void_p]*2,
            'af_npc_mail_other_name':[C.c_void_p]*2,
            'af_npc_mail_word':[C.c_void_p,C.c_uint,C.c_uint],
            'af_npc_mail_composite':[C.c_void_p]+[C.c_uint]*5,
            'af_npc_mail_classic':[C.c_void_p]*4+[C.c_uint],
        }.items(): getattr(cls.lib,name).argtypes = args

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def setUp(self):
        self.active = C.c_void_p.in_dll(self.lib,'af_npc_mail_session');self.active.value = None
        self.calls = (C.c_uint*5).in_dll(self.lib,'af_npc_test_calls');self.calls[:] = [0]*5
        self.offsets = (C.c_uint*11).in_dll(self.lib,'af_npc_test_offsets');self.offsets[:] = [0]*11
        self.other = (C.c_ubyte*12).in_dll(self.lib,'af_npc_test_other');self.other[:] = [0xE0,1]+[0]*10
        self.arguments = (C.c_size_t*6).in_dll(self.lib,'af_npc_test_arguments')
        self.fields = (C.c_ubyte*200).in_dll(self.lib,'af_npc_test_fields')
        self.fields[:] = b'!'*200

    def tearDown(self): self.active.value = None

    def sources(self):
        wp,ap = self.word_path,ROOT/'build/npc-mail-names/aliases.bin'
        if not wp.is_file() or not ap.is_file(): self.skipTest('Verified local full-word and name resources required')
        self.word_bytes,self.alias_bytes = wp.read_bytes(),ap.read_bytes()
        self.words = C.create_string_buffer(self.word_bytes,len(self.word_bytes))
        self.aliases = C.create_string_buffer(self.alias_bytes,len(self.alias_bytes))
        sources = Sources()
        self.assertEqual(self.lib.af_npc_mail_sources_init(C.byref(sources),self.words,len(self.words),
                                                        self.aliases,len(self.aliases)),1)
        return sources

    def fixture(self,foreign=0,condition=1,looks=0,capital=0):
        sources = self.sources()
        aliases = unpack_aliases(self.alias_bytes,hashlib.sha256(self.alias_bytes).hexdigest())
        key = next(row.key for row in aliases if row.npc_index == 0)
        self.player = C.create_string_buffer(b'PLAYER'+bytes(10),16)
        self.animal = C.create_string_buffer(bytes((0xE0,0))+bytes(9)+bytes((looks,)),12)
        self.remail = C.create_string_buffer(bytes(4)+key+b'AWAY  '+bytes((looks,0)),18)
        self.stage = C.create_string_buffer(b'!'*196,196)
        work = Work()
        work.session = Session(C.cast(self.lib.af_npc_mail_capture_event,C.c_void_p).value,
                               C.addressof(self.stage)+16,C.addressof(self.player),C.addressof(self.animal),
                               C.addressof(self.remail) if foreign else None,condition,foreign,capital)
        work.sources = sources
        self.active.value = C.addressof(work)
        return work

    def prepare(self,work):
        self.lib.af_npc_mail_prepare(work.session.player,work.session.animal,work.session.remail)
        self.assertEqual((work.phase,work.failed,work.words_seen),(2,0,11))
        self.assertEqual(work.capture.valid,0xFFFF if work.session.foreign else 0x3FFF)
        self.assertEqual(work.capture.capital,work.session.initial_capital)
        self.assertEqual(self.stage.raw,b'!'*196)

    def test_digest_matches_hashlib_all_padding_edges_unaligned_inputs_and_rejects_overlap(self):
        rng = random.Random(821)
        for size in list(range(260))+[6368,11328,65536,1048576]:
            value = rng.randbytes(size)
            source = C.create_string_buffer(b'!'*7+value+b'!'*19,size+26)
            out = C.create_string_buffer(b'!'*64,64)
            self.assertEqual(self.lib.af_mail_source_digest(C.byref(out,16),C.byref(source,7),size),1)
            self.assertEqual(out.raw,b'!'*16+hashlib.sha256(value).digest()+b'!'*16)
            self.assertEqual(source.raw,b'!'*7+value+b'!'*19)
        data = C.create_string_buffer(b'!'*128,128)
        for out,source,size in ((data,None,1),(data,data,32),(C.byref(data,8),data,32),
                                (data,C.byref(data,8),32),(data,data,1048577),(None,data,1)):
            self.assertEqual(self.lib.af_mail_source_digest(out,source,size),0)
            self.assertEqual(data.raw,b'!'*128)
        self.assertEqual(self.lib.af_mail_source_digest(data,None,0),1)
        self.assertEqual(data.raw[:32],hashlib.sha256(b'').digest())

    def test_complete_hashes_reject_changes_even_with_updated_embedded_digests(self):
        sources = self.sources();before = bytes(sources)
        for label,value in (('word',self.word_bytes),('alias',self.alias_bytes)):
            for at in (0,31,32,63,64,len(value)-1):
                changed = bytearray(value);changed[at] ^= 1
                if not 32 <= at < 64:
                    changed[32:64] = hashlib.sha256(changed[64:]).digest()
                buffer = C.create_string_buffer(bytes(changed),len(changed))
                words,aliases = (buffer,self.aliases) if label == 'word' else (self.words,buffer)
                self.assertEqual(self.lib.af_npc_mail_sources_init(C.byref(sources),words,len(self.words),
                                                                aliases,len(self.aliases)),0)
                self.assertEqual(bytes(sources),before)
        for size in (0,11327,11329):
            self.assertEqual(self.lib.af_npc_mail_sources_init(C.byref(sources),self.words,size,
                                                            self.aliases,len(self.aliases)),0)
        self.assertEqual(self.lib.af_npc_mail_sources_init(self.words,self.words,len(self.words),
                                                        self.aliases,len(self.aliases)),0)
        self.assertEqual(self.words.raw,self.word_bytes)

    def test_all_full_word_values_keep_sixteen_byte_padding_and_all_names_resolve_exactly(self):
        sources = self.sources();out = CField()
        words = unpack_words(self.word_bytes,hashlib.sha256(self.word_bytes).hexdigest())
        for row in words:
            self.assertEqual(self.lib.af_npc_mail_source_word(C.byref(out),C.byref(sources),row.slot,row.native_id),1)
            self.assertEqual((out.length,out.article,bytes(out.text)),(16,0,row.text.ljust(16,b' ')))
        aliases = unpack_aliases(self.alias_bytes,hashlib.sha256(self.alias_bytes).hexdigest())
        for row in aliases:
            self.assertEqual(self.lib.af_npc_mail_source_alias(C.byref(out),C.byref(sources),row.key),1)
            self.assertEqual((out.length,out.article,bytes(out.text)),(8,0,row.name+bytes(8)))
            self.assertEqual(self.lib.af_npc_mail_source_name(C.byref(out),C.byref(sources),0xE000+row.npc_index),1)
            self.assertEqual(bytes(out.text),row.name+bytes(8))
        before = bytes(out)
        for slot,id in ((2,WORD_BASES[0]),(14,WORD_BASES[-1]),(3,WORD_BASES[0]-1),(3,WORD_BASES[0]+32)):
            self.assertEqual(self.lib.af_npc_mail_source_word(C.byref(out),C.byref(sources),slot,id),0)
            self.assertEqual(bytes(out),before)
        for id in (0,0xDFFF,0xE0D8,0xE100,0x1E000):
            self.assertEqual(self.lib.af_npc_mail_source_name(C.byref(out),C.byref(sources),id),0)
        for key in (b'OTHER ',b'      ',b'\x80'*6):
            self.assertEqual(self.lib.af_npc_mail_source_alias(C.byref(out),C.byref(sources),key),0)
            self.assertEqual(bytes(out),before)

    def test_complete_ordered_local_and_foreign_capture_preserves_native_temporary_fields(self):
        for foreign in range(2):
            for capital in range(2):
                for offset in range(32):
                    work = self.fixture(foreign,capital=capital)
                    self.offsets[:] = [offset]*11
                    self.prepare(work)
                    observed_native = bytes(self.fields)
                    self.assertEqual(bytes(work.capture.fields[0].text),b'PLAYER'+bytes(10))
                    words = unpack_words(self.word_bytes,hashlib.sha256(self.word_bytes).hexdigest())
                    for family in range(11):
                        self.assertEqual(bytes(work.capture.fields[family+3].text),words[family*32+offset].text.ljust(16,b' '))
                    self.active.value = None
                    self.fields[:] = b'!'*200
                    self.lib.af_npc_mail_prepare(work.session.player,work.session.animal,work.session.remail)
                    self.assertEqual(bytes(self.fields),observed_native)
                    self.assertEqual(self.stage.raw,b'!'*196)

    def test_selected_native_ids_are_captured_without_assembling_or_writing_staging(self):
        for foreign in range(2):
            for condition in range(2):
                for looks in range(6):
                    work = self.fixture(foreign,condition,looks)
                    self.prepare(work)
                    before_calls = list(self.calls)
                    if condition:
                        start = GROUPS[foreign][looks];ids = (start,start+31,start+16,start+1,start+30)
                        self.assertEqual(self.lib.af_npc_mail_composite(work.session.stage,*ids),1)
                    else:
                        ids = (BAD_BASES[foreign]+looks*3+2,0,0,0,0)
                        split = C.c_uint(123)
                        self.lib.af_npc_mail_classic(None,C.byref(split),None,work.session.stage+0x34,ids[0])
                        self.assertEqual(split.value,0)
                    self.assertEqual((work.phase,work.failed),(3,0))
                    self.assertEqual((work.selection.catalog,work.selection.kind,tuple(work.selection.templates)),(2,condition,ids))
                    self.assertEqual(list(self.calls),before_calls)
                    self.assertEqual(self.stage.raw,b'!'*196)
                    self.assertEqual(self.lib.af_npc_mail_composite(work.session.stage,0,0,0,0,0),0)
                    self.assertEqual(work.failed,1)

    def test_inactive_adapters_forward_all_original_arguments_and_results(self):
        mail = C.create_string_buffer(196);base = C.addressof(mail)
        self.assertEqual(self.lib.af_npc_mail_composite(base,11,22,33,44,55),37)
        self.assertEqual(list(self.arguments),[base,11,22,33,44,55])
        split = C.c_uint()
        self.lib.af_npc_mail_classic(base,C.byref(split),base+10,base+30,246)
        self.assertEqual(split.value,19)
        self.assertEqual(list(self.arguments)[:5],[base,C.addressof(split),base+10,base+30,246])
        self.lib.af_npc_mail_word(mail,10,717)
        self.assertEqual(list(self.arguments)[:3],[base,10,717])

    def test_bad_order_unknown_name_and_wrong_destination_poison_the_session(self):
        for event in range(1,8):
            work = self.fixture()
            self.assertEqual(self.lib.af_npc_mail_capture_event(C.byref(work),event,None,0),0)
            self.assertEqual(work.failed,1)
        work = self.fixture(foreign=1)
        C.memmove(C.addressof(self.remail)+4,b'OTHER ',6)
        self.lib.af_npc_mail_prepare(work.session.player,work.session.animal,work.session.remail)
        self.assertEqual(work.failed,1)
        self.assertEqual(self.stage.raw,b'!'*196)
        work = self.fixture();self.prepare(work)
        self.assertEqual(self.lib.af_npc_mail_composite(work.session.stage+1,32,32,32,32,32),0)
        self.assertEqual(work.failed,1)
        work = self.fixture();self.offsets[0] = 32
        self.lib.af_npc_mail_prepare(work.session.player,work.session.animal,work.session.remail)
        self.assertEqual(work.failed,1)


if __name__ == '__main__': unittest.main()
