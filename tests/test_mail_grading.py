"""Bounded English scoring, independent GameCube checks, and loader ownership."""

import ctypes as C
from pathlib import Path
import random
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from mail_grading import GC_SOURCE_SHA256, load_prefixes
from mail_grade_model import grade as model_grade, legacy_grade

REL = ROOT/'build/gamecube/files/foresta.rel.szs.decoded'
SYMBOLS = ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt'


class Grade(C.Structure):
    _fields_ = [('components',C.c_int*7),('total',C.c_int),('rank',C.c_uint)]


def prefix_blob():
    if REL.is_file() and SYMBOLS.is_file():
        return load_prefixes(REL.read_bytes(),SYMBOLS.read_text())[0]
    # Synthetic dictionary with identical bounds; no extracted data committed.
    counts = [min(i*30,776) for i in range(27)]
    counts[-1] = 776
    return struct.pack('>27H',*counts)+b'bc'*776


@unittest.skipUnless(shutil.which('gcc'),'Host GCC required')
class MailGradingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temporary = tempfile.TemporaryDirectory()
        cls.directory = Path(cls.temporary.name)
        cls.prefixes = prefix_blob()
        definition = cls.directory/'prefixes.c'
        # The C declaration is const; tests deliberately use writable backing
        # to verify corrupted bounds without changing production sources.
        definition.write_text('unsigned char af_mail_prefixes[1606] = {'+
                              ','.join(map(str,cls.prefixes))+'};\n')
        library = cls.directory/'grade.so'
        cmd = ['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
               '-I'+str(ROOT/'runtime'),str(ROOT/'overlays/mail_check/grade.c'),
               str(ROOT/'runtime/mail_grade.c'),str(ROOT/'tests/mail_grade_mock.c'),str(definition),'-o',str(library)]
        subprocess.run(cmd,capture_output=True,check=True)
        cls.lib = C.CDLL(str(library))
        for name in ('af_mail_grade','af_mail_grade_body'):
            getattr(cls.lib,name).argtypes = [C.c_void_p,C.c_void_p,C.c_uint]
        cls.lib.af_mail_word_rate.argtypes = [C.c_void_p,C.c_void_p,C.c_uint]
        cls.lib.af_mail_grade_native.argtypes = [C.c_void_p]

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def setUp(self):
        (C.c_ubyte*1606).in_dll(self.lib,'af_mail_prefixes')[:] = self.prefixes
        for name in ('af_grade_allocated','af_grade_freed','af_grade_loaded','af_grade_invoked',
                     'af_grade_allocation_size','af_grade_fail_allocate','af_grade_wrong_overlay'):
            C.c_int.in_dll(self.lib,name).value = 0

    def grade(self,text,function='af_mail_grade'):
        body = C.create_string_buffer(b'GUARD'+text+b'GUARD')
        output = C.create_string_buffer(b'!'*16+b'?'*36+b'!'*16)
        self.assertEqual(getattr(self.lib,function)(C.byref(output,16),C.byref(body,5),len(text)),1)
        self.assertEqual(body.raw,b'GUARD'+text+b'GUARD\0')
        self.assertEqual(output.raw[:16]+output.raw[-17:],b'!'*32+b'\0')
        return Grade.from_buffer_copy(output.raw[16:52])

    def test_empty_boundaries_and_each_rule(self):
        self.assertEqual(list(self.grade(b'').components),[0,0,0,0,-20,0,0])
        for size in (0,1,2,3,31,32,33,75,76,77,96,191,192,193,1024):
            result = self.grade(b'x'*size)
            self.assertEqual(result.components[3],-50 if size >= 3 else 0)
            self.assertEqual(result.components[5],0)
            self.assertEqual(result.components[6],-20*(size//32))
        for text,score in ((b'Hello.',20),(b'Hello. End.',30),(b'Hello. end.',10),
                           (b'.  A!',30),(b'.   a',-10)):
            self.assertEqual(self.grade(text).components[0],score)
        self.assertEqual(self.grade(b'a'*191+b'.').components[0],0)
        self.assertEqual(self.grade(b'a'*95+b'.').components[0],20)
        for text,score in ((b'.'+b'x'*76,-150),(b'.'+b'x'*75,0),
                           (b'.'+b'x'*74+b'!'+b'x'*10,0)):
            self.assertEqual(self.grade(text).components[5],score)
        self.assertEqual(self.grade(b' abcde').components[4],20)
        self.assertEqual(self.grade(b' abcdef').components[4],-20)

    def test_native_padding_and_full_body_capacity_are_distinct(self):
        for text in (b'',b'Hello there!',b'x'*96,b'\xcd A. B! C?',bytes(range(96))):
            native = self.grade(text)
            padded = self.grade(text.ljust(192,b' '))
            self.assertEqual(bytes(native),bytes(padded))
        long = b'Hello! '+b'x'*230
        self.assertNotEqual(self.grade(long).total,self.grade(long[:96]).total)

    @unittest.skipUnless(REL.is_file() and SYMBOLS.is_file(),'Supplied English reference required')
    def test_exact_reply_rank_thresholds(self):
        for text,total,rank in ((b'The '*3,49,0), (b'AAA '+b'the '*20,50,2),
                                (b'AAA '+b'The '*25+b'. '+b'The '*8,99,2),
                                (b'The '*20,100,1)):
            result = self.grade(text)
            self.assertEqual((result.total,result.rank),(total,rank))

    def test_address_and_undefined_behaviour_sanitizers(self):
        executable = self.directory/'grade-sanitize'
        compiled = subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O1',
                                   '-g','-fsanitize=address,undefined','-fno-sanitize-recover=all',
                                   '-fno-omit-frame-pointer','-I'+str(ROOT/'runtime'),
                                   str(ROOT/'overlays/mail_check/grade.c'),
                                   str(ROOT/'tests/mail_grade_sanitize.c'),
                                   str(self.directory/'prefixes.c'),'-o',str(executable)],
                                  capture_output=True,text=True)
        self.assertEqual(compiled.returncode,0,compiled.stderr)
        run = subprocess.run([str(executable)],capture_output=True,text=True,timeout=60)
        self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_all_776_prefix_pairs_and_case_rules(self):
        offsets = struct.unpack_from('>27H',self.prefixes)
        for letter in range(26):
            for index in range(offsets[letter],offsets[letter+1]):
                pair = self.prefixes[54+index*2:56+index*2]
                for c in (97+letter,65+letter):
                    self.assertGreaterEqual(self.grade(bytes([c])+pair).components[1],3)
        rng = random.Random(1092)
        for _ in range(1000):
            text = bytes(rng.choice(b" .?!,aeiI'X\xcd\x85\0") for _ in range(rng.randrange(1025)))
            result = self.grade(text)
            self.assertEqual(list(result.components)+[result.total,result.rank],model_grade(text,self.prefixes))
            self.assertEqual(result.total,sum(result.components))
            self.assertEqual(result.rank,1 if result.total>=100 else 0 if result.total<50 else 2)

    def test_invalid_bounds_do_not_publish_or_allocate(self):
        output = C.create_string_buffer(b'!'*36)
        source = C.create_string_buffer(b'abc')
        for name in ('af_mail_grade','af_mail_grade_body'):
            func = getattr(self.lib,name)
            for args in ((None,source,3),(output,None,3),(output,source,1025),(output,source,0xFFFFFFFF)):
                self.assertEqual(func(*args),0)
                self.assertEqual(output.raw,b'!'*36+b'\0')
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_grade_allocated').value,0)
        table = (C.c_ubyte*1606).in_dll(self.lib,'af_mail_prefixes')
        for index in (0,1,2,3,50,51,52,53):
            old = table[index]
            table[index] = 255
            self.assertEqual(self.lib.af_mail_grade(output,source,3),0)
            self.assertEqual(output.raw,b'!'*36+b'\0')
            table[index] = old

    def test_loader_frees_each_allocation_and_rejects_disabled_or_failed_load(self):
        result = self.grade(b'Hello!','af_mail_grade_body')
        self.assertEqual(bytes(result),bytes(self.grade(b'Hello!')))
        self.assertEqual([C.c_uint.in_dll(self.lib,n).value for n in
                          ('af_grade_allocated','af_grade_loaded','af_grade_invoked','af_grade_freed')],[1]*4)
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_grade_allocation_size').value,6400)
        output = C.create_string_buffer(b'!'*36)
        C.c_int.in_dll(self.lib,'af_grade_wrong_overlay').value = 1
        self.assertEqual(self.lib.af_mail_grade_body(output,b'Hi',2),0)
        self.assertEqual(output.raw,b'!'*36+b'\0')
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_grade_freed').value,2)
        C.c_int.in_dll(self.lib,'af_grade_fail_allocate').value = 1
        self.assertEqual(self.lib.af_mail_grade_body(output,b'Hi',2),0)
        self.assertEqual(C.c_uint.in_dll(self.lib,'af_grade_loaded').value,2)
        self.assertEqual(self.lib.af_mail_grade_native(b' '*96),2)

    @unittest.skipUnless(REL.is_file() and SYMBOLS.is_file(),'Supplied English reference required')
    def test_independent_reference_components_and_legacy_word_rate(self):
        reference = (ROOT/'local/ac-decomp/src/game/m_mail_check_ovl.c').read_text()
        self.assertEqual(sha256(reference.encode()),GC_SOURCE_SHA256)
        reference = re.sub(r'^#include[^\n]*\n','',reference,flags=re.M)
        unsafe = '(u8*)(len + (int)str)'
        self.assertEqual(reference.count(unsafe),1)
        reference = reference.replace(unsafe,'str + len')
        # The reference's BUGFIXES branch still omits x's terminator. Complete
        # that one bound as well; otherwise "Xen" can spill into y's table.
        reference, count = re.subn(r'(static u8 str_x_table\[\] = \{.*?)(\n\};)',
                                   r'\1\n  CHAR_CONTROL_CODE, 0\2',reference,flags=re.S)
        self.assertEqual(count,1)
        font = (ROOT/'local/ac-decomp/include/m_font.h').read_text()
        self.assertEqual(sha256(font.encode()),'7a6354cc7d29d0d8fef7579d26fe40e58a19b0bbde40ca8c20f604f1b4134ded')
        defines = '\n'.join(re.findall(r'^#define CHAR_\w+ \d+$',font,re.M))
        prefix = ('#include <stddef.h>\n#define BUGFIXES\n#define TRUE 1\n#define FALSE 0\n'
                  '#define MAIL_BODY_LEN 192\ntypedef unsigned char u8;\n'
                  'enum { mMck_CASE_LOWER,mMck_CASE_UPPER,mMck_CASE_NUM };\n'
                  '#define mMck_CHECK_KEY_TYPE_NUM 7\n')+defines+'\n'
        wrapper = '\nvoid components(int *out,u8 *body) { int n=mMck_strlen_new(body,192);\n'+''.join(
            f'out[{i}]=mMck_check_key_type_{c}(body,n);\n' for i,c in enumerate('ABCDEFG'))+'}\n'
        npc = (ROOT/'local/ac-decomp/src/game/m_npc.c').read_text()
        self.assertEqual(sha256(npc.encode()),'53fa38241f3fe71aae861fc5ecc60d57a1457c9912be1977578d8a40ee6698c0')
        npc = npc[npc.index('static int mNpc_CheckMailChar('):npc.index('extern u8 mNpc_CheckNormalMail_nes(')]
        wrapper += ('#define mNpc_LETTER_RANK_NUM 2\n#define mNpc_LETTER_RANK_BAD 0\n#define mNpc_LETTER_RANK_OK 1\n'
                    'int mMC_get_mail_hit_rate(int *n,u8 *b,void *g) { (void)g; return mMck_check_key_hit(n,b); }\n')+npc
        path = self.directory/'gc-reference.c'
        path.write_text(prefix+reference+wrapper)
        library = self.directory/'gc-reference.so'
        run = subprocess.run(['gcc','-std=c99','-O2','-shared','-fPIC',str(path),'-o',str(library)],
                             capture_output=True,text=True)
        self.assertEqual(run.returncode,0,run.stderr)
        gc = C.CDLL(str(library))
        gc.components.argtypes = [C.c_void_p,C.c_void_p]
        gc.mMck_check_key_hit.argtypes = [C.c_void_p,C.c_void_p]
        gc.mNpc_CheckNormalMail_length.argtypes = [C.c_void_p,C.c_void_p]
        rng = random.Random(924)
        for _ in range(3000):
            text = bytes(rng.choice(b" .?!,aeiI'XAbcothen\xcd\x85\0") for _ in range(rng.randrange(193))).ljust(192,b' ')
            # The leading space safely supplies the reference's body[-1] for
            # the empty-body case; the port itself never makes that read.
            body = C.create_string_buffer(b' '+text)
            scores = (C.c_int*7)()
            gc.components(scores,C.byref(body,1))
            self.assertEqual(list(self.grade(text).components),list(scores),repr(text.rstrip(b' ')))
            words, our_words = C.c_int(-1),C.c_int(-1)
            gc_rate = gc.mMck_check_key_hit(C.byref(words),C.byref(body,1))
            rate = self.lib.af_mail_word_rate(C.byref(our_words),C.byref(body,1),192)
            self.assertEqual((our_words.value,rate),(words.value,gc_rate))
            length = C.c_int(-1)
            rank = gc.mNpc_CheckNormalMail_length(C.byref(length),C.byref(body,1))
            self.assertEqual(legacy_grade(text,self.prefixes),(rank,length.value,words.value,gc_rate))


if __name__ == '__main__': unittest.main()
