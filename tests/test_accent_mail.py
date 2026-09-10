"""Literal accents preserve saved letters, complete fields, and atomic publication."""
import ctypes as C
from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
import accent_mail_catalog as catalog
from accent_mail_format import format_letter
from mail_format import Letter
from mail_record import Record,Field,pack,unpack
from mail_catalog import templates as old_templates
from audit_mail_templates import template_fields
import test_mail_format as fm
import test_mail_generate as gm

NAMES=(b'caf\x80\x7c shirt',b'Pok\x80\x7cmon Pikachu',b'Caf\x80\x7c K.K.',b'Se\x80\x87or K.K.')


class AccentMailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='af-accent-mail-')
        output=Path(cls.temp.name)/'mail.so'
        sources=[f'overlays/accent_mail/{n}.c' for n in ('format','catalog','generate','literal','view','install')]
        sources+=['runtime/mail/record.c','runtime/crc32.c','tests/accent_mail_mock.c','tests/mail_generate_mock.c']
        sources+=['overlays/accent_mail/treasure.c','runtime/notice/record.c','runtime/notice/treasure.c']
        subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
                        '-Daf_mail_restore=af_accent_mail_restore','-Daf_mail_format=af_accent_mail_format',
                        *(str(ROOT/p) for p in sources),'-o',str(output)],check=True,capture_output=True)
        cls.lib=C.CDLL(str(output))
        for name,args in {
            'af_mail_record_unpack':[C.c_void_p,C.c_void_p,C.c_uint,C.c_uint],
            'af_accent_mail_format':[C.c_void_p]*3,
            'af_accent_capture_set':[C.c_void_p,C.c_uint,C.c_void_p,C.c_uint,C.c_uint],
            'af_accent_mail_generate':[C.c_void_p,C.c_uint,C.c_void_p,C.c_void_p,C.c_void_p],
            'af_accent_mail_restore':[C.c_void_p,C.c_void_p,C.c_uint,C.c_void_p],
            'af_accent_next_line':[C.c_void_p,C.c_void_p,C.c_uint],
            'af_accent_treasure_pack':[C.c_void_p,C.c_uint,C.c_void_p],
            'af_accent_treasure_decode_parts':[C.c_void_p,C.c_void_p,C.c_void_p,C.c_void_p,C.c_uint],
        }.items():getattr(cls.lib,name).argtypes=args
        cls.old=(ROOT/'build/mail-glyph-catalog/catalog.bin').read_bytes()
        cls.original=(ROOT/'build/mail-catalog/catalog.bin').read_bytes()
        cls.data=catalog.resource(cls.old)

    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()

    def setUp(self):
        self.rom=(C.c_ubyte*0x200000).in_dll(self.lib,'af_mail_catalog_rom')
        self.reads=C.c_uint.in_dll(self.lib,'af_mail_catalog_reads')
        self.fail=C.c_uint.in_dll(self.lib,'af_mail_catalog_fail_read')
        self.errors=C.c_uint.in_dll(self.lib,'af_mail_catalog_dma_error')
        self.reads.value=self.fail.value=self.errors.value=0
        C.memmove(self.rom,self.original,len(self.original))
        C.memmove(C.addressof(self.rom)+0xA0000,self.old,len(self.old))
        C.memmove(C.addressof(self.rom)+0x100000,self.data,len(self.data))

    def compare(self,record,parts,expected=None,success=True):
        native,templates,buffers=fm.MailFormatTests.inputs(self,record,parts)
        output=C.create_string_buffer(b'!'*(C.sizeof(fm.CText)+32),C.sizeof(fm.CText)+32)
        before=output.raw,bytes(native),bytes(templates),tuple(b.raw for b in buffers)
        result=self.lib.af_accent_mail_format(C.byref(output,16),C.byref(native),C.byref(templates))
        self.assertEqual(result,int(success))
        self.assertEqual((bytes(native),bytes(templates),tuple(b.raw for b in buffers)),before[1:])
        if not success:
            self.assertEqual(output.raw,before[0])
            with self.assertRaises(ValueError):format_letter(record,parts)
            return
        self.assertEqual(output.raw[:16]+output.raw[-16:],b'!'*32)
        value=fm.CText.from_buffer_copy(output.raw[16:-16])
        actual=Letter(*(bytes(value.text[o:o+n]) for o,n in zip(value.offsets,value.lengths)),value.split,bool(value.capital))
        self.assertEqual(actual,format_letter(record,parts))
        if expected is not None:self.assertEqual(actual.body,expected)

    def test_literals_capitals_articles_and_old_interpretations(self):
        for name in (*NAMES,b'\x80\x7cclair',b'\x80\x87ame'):
            for article in range(5):
                record,parts=fm.fixture((b'Dear\xcd',b'\x7f\x24!',b'From'),((0,Field(name,article)),),True)
                record,parts=replace(record,catalog=5),replace(parts,catalog=5)
                self.compare(record,parts)
                self.compare(replace(record,catalog=4),replace(parts,catalog=4),success=False)
        for name,upper in ((b'\x80\x7c',b'\x80\x0a'),(b'\x80\x87',b'\x80\x12')):
            record,parts=fm.fixture((b'',b'\x7f\x24!',b''),((0,Field(name)),),True)
            self.compare(replace(record,catalog=5),replace(parts,catalog=5),upper+b'!')
        for identity in (2,3,4):
            record,parts=fm.fixture((b'Dear\xcd',b'\x7f\x24\xcdNext line',b'From'),((0,Field(b'friend ',3)),),True)
            self.compare(replace(record,catalog=identity),replace(parts,catalog=identity),b'The friend\xcdNext line')

    def test_malformed_pairs_and_overflow_publish_nothing(self):
        for bad in (b'\x80',b'\x80\x00',b'\x7f\x24',b'x\x80',b'\x80\x87\x80'):
            record,parts=fm.fixture((b'',b'\x7f\x24',b''),((0,Field(bad)),))
            self.compare(replace(record,catalog=5),replace(parts,catalog=5),success=False)
        for body in (b'\x80',b'\x80\x00',b'x'*1024+b'x'):
            record,parts=fm.fixture((b'',body,b''))
            self.compare(replace(record,catalog=5),replace(parts,catalog=5),success=False)
        record,parts=fm.fixture((b'',b'\x80',b'\x87',b'',b''))
        self.compare(replace(record,catalog=5),replace(parts,catalog=5),success=False)

    def test_capture_only_accepts_complete_registered_item_names(self):
        capture=gm.Capture()
        for name in NAMES:
            for value in (name,name.ljust(16,b' ')):
                self.assertEqual(self.lib.af_accent_capture_set(C.byref(capture),3,value,len(value),2),1)
                self.assertEqual(bytes(capture.fields[3].text),value.ljust(16,b'\0'))
                self.assertEqual(capture.fields[3].length,len(value))
        for bad in (b'\x80\x87',b'\x7f\x24',NAMES[0]+b'!',NAMES[1][:-1],b'x'*17):
            before=gm.Capture.from_buffer_copy(capture)
            self.assertEqual(self.lib.af_accent_capture_set(C.byref(capture),3,bad,len(bad),0),0)
            before.valid &= ~(1<<3)
            self.assertEqual(bytes(capture),bytes(before))

    def test_startup_checks_all_resident_hooks_before_any_write(self):
        hooks=(C.c_uint*8).in_dll(self.lib,'af_accent_test_hooks')
        world=C.c_uint.in_dll(self.lib,'af_accent_test_world_calls')
        ready=C.c_uint.in_dll(self.lib,'af_accent_test_world_ok')
        flush=C.c_uint.in_dll(self.lib,'af_accent_test_flushes')
        original=(0x27BDFB38,0xAFBF04C4,0x14800003,0,0x1080003A,0x1025,0x14800003,0x1025)
        hooks[:]=original;world.value=flush.value=0;ready.value=1
        for slot in range(8):
            hooks[slot]^=1;before=tuple(hooks)
            self.assertEqual(self.lib.af_accent_font_install(),0)
            self.assertEqual(tuple(hooks),before)
            self.assertEqual((world.value,flush.value),(0,0))
            hooks[slot]^=1
        ready.value=0
        self.assertEqual(self.lib.af_accent_font_install(),0)
        self.assertEqual(tuple(hooks),original)
        self.assertEqual((world.value,flush.value),(1,0))
        ready.value=1
        self.assertEqual(self.lib.af_accent_font_install(),1)
        self.assertEqual((world.value,flush.value),(2,1))
        self.assertEqual([hooks[i]>>26 for i in range(0,8,2)],[2]*4)
        self.assertEqual([hooks[i] for i in range(1,8,2)],[0]*4)

    def generation(self,name,selected=True,success=True,source_catalog=4):
        base=Record(4,0,(2,),())
        used=sorted(set().union(*(template_fields(p) for p in old_templates(self.old,base).parts)))
        self.assertTrue(used)
        fields=tuple((i,Field(name if selected and i==used[0] else b'friend')) for i in used)
        record=replace(base,catalog=5 if selected else 4,fields=fields)
        capture=gm.Capture()
        for i,f in fields:
            self.assertEqual(self.lib.af_accent_capture_set(C.byref(capture),i,f.text,len(f.text),f.article),1)
        if not selected:
            unused=next(i for i in range(20) if i not in used)
            self.assertEqual(self.lib.af_accent_capture_set(C.byref(capture),unused,name,len(name),0),1)
        selection=gm.Selection(source_catalog,0,0,(C.c_ushort*5)(2,0,0,0,0))
        size=self.lib.af_mail_generate_work_size()
        storage=C.create_string_buffer(b'!'*(size+64),size+64)
        work=(C.addressof(storage)+31)&~15
        mail=C.create_string_buffer(b'!'*16+bytes(range(164))+b'!'*16,196)
        before=mail.raw,bytes(capture),bytes(selection)
        self.assertEqual(self.lib.af_accent_mail_generate(C.byref(mail,16),164,C.byref(capture),C.byref(selection),work),int(success))
        lead=work-C.addressof(storage)
        self.assertEqual(storage.raw[:lead]+storage.raw[lead+size:],b'!'*64)
        self.assertEqual(bytes(selection),before[2])
        self.assertEqual(self.errors.value,0)
        if not success:
            self.assertEqual((mail.raw,bytes(capture)),before[:2])
            return
        expected=bytearray(before[0]);expected[55]=128;expected[58:180]=pack(record)
        self.assertEqual(mail.raw,bytes(expected))
        self.assertEqual(unpack(mail.raw[58:180],expected_catalog=record.catalog),record)
        self.assertEqual(capture.capital,0)
        value=fm.CText.from_address(work+self.lib.af_mail_generate_text_offset())
        parts=catalog.templates(self.data,record) if selected else old_templates(self.old,record)
        reference=format_letter(record,parts)
        self.assertEqual(tuple(bytes(value.text[o:o+n]) for o,n in zip(value.offsets,value.lengths)),
                         (reference.header,reference.body,reference.footer))

    def test_generation_upgrade_restore_and_failure_atomicity(self):
        catalog.verify(self.data)
        self.assertEqual(catalog.verify_shop_compatibility(self.original,self.data),16)
        self.assertEqual(catalog.preceding(self.data),self.old)
        self.assertEqual(self.data[:8]+self.data[16:],self.old[:8]+self.old[16:])
        for name in NAMES:self.generation(name)
        self.generation(NAMES[0],source_catalog=2)
        self.generation(NAMES[-1],selected=False)
        self.reads.value=0
        self.generation(NAMES[1])
        total=self.reads.value
        for read in (1,5,total):
            self.reads.value=0;self.fail.value=read
            self.generation(NAMES[1],success=False)

    def test_pair_line_widths_and_newlines_remain_atomic(self):
        for code in (0x87,0x12,0x7c,0x0a):
            line=(C.c_uint*4)()
            text=b'x'*31+bytes((0x80,code))+b'\xcdnext'
            self.assertEqual(self.lib.af_accent_next_line(line,text,len(text)),1)
            self.assertEqual(tuple(line),(34,33,192,1))
        for text in (b'\x80',b'\x80\x00',b'\x7f'):
            line=(C.c_uint*4)(1,2,3,4)
            self.assertEqual(self.lib.af_accent_next_line(line,text,len(text)),0)
            self.assertEqual(tuple(line),(1,2,3,4))

    def test_treasure_notice_capture_and_read_keep_the_native_envelope(self):
        for name in (*NAMES,b'ordinary item'):
            fields=((1,Field(b'Bob')),(2,Field(name,1)),(3,Field(b'1')),(4,Field(b'2')))
            record=Record(4,0,(0x1F0,),fields)
            native=fm.CRecord()
            self.assertEqual(self.lib.af_mail_record_unpack(C.byref(native),pack(record),122,4),1)
            before=bytes(native)
            notice=C.create_string_buffer(b'!'*128,128)
            self.assertEqual(self.lib.af_accent_treasure_pack(C.byref(notice,16),96,C.byref(native)),1)
            self.assertEqual(bytes(native),before)
            self.assertEqual(notice.raw[:16]+notice.raw[-16:],b'!'*32)
            identity=5 if name in NAMES else 4
            self.assertEqual(notice.raw[23:25],bytes((0,identity)))
            size=self.lib.af_mail_catalog_workspace_size()
            storage=C.create_string_buffer(b'!'*(size+64),size+64)
            work=(C.addressof(storage)+31)&~15
            wire=C.create_string_buffer(122)
            output=C.create_string_buffer(b'!'*(C.sizeof(fm.CText)+32),C.sizeof(fm.CText)+32)
            self.assertEqual(self.lib.af_accent_treasure_decode_parts(work,C.byref(output,16),wire,C.byref(notice,16),96),1)
            lead=work-C.addressof(storage)
            self.assertEqual(storage.raw[:lead]+storage.raw[lead+size:],b'!'*64)
            self.assertEqual(output.raw[:16]+output.raw[-16:],b'!'*32)
            value=fm.CText.from_buffer_copy(output.raw[16:-16])
            expected=replace(record,catalog=identity)
            self.assertEqual(unpack(wire.raw,expected_catalog=identity),expected)
            parts=catalog.templates(self.data,expected) if identity==5 else old_templates(self.old,expected)
            reference=format_letter(expected,parts)
            self.assertEqual(bytes(value.text[value.offsets[1]:value.offsets[1]+value.lengths[1]]),reference.body)
        for field in (Field(b'\x80'),Field(b'\x80\x87'),Field(NAMES[0]+b'!')):
            bad=replace(record,catalog=5,fields=((1,Field(b'Bob')),(2,field),(3,Field(b'1')),(4,Field(b'2'))))
            self.assertEqual(self.lib.af_mail_record_unpack(C.byref(native),pack(bad),122,5),1)
            before=notice.raw
            self.assertEqual(self.lib.af_accent_treasure_pack(C.byref(notice,16),96,C.byref(native)),0)
            self.assertEqual(notice.raw,before)


if __name__=='__main__':unittest.main()
