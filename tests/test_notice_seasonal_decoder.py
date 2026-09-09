"""Compiled seasonal decoder: every complete body, full fields, and atomic failure."""

import ctypes as C
from dataclasses import replace
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from mail_record import Field, Record
from notice_record import pack
from notice_seasonal import IDS, audit, compiled_resource, complete_body
from test_notice_initial import NoticeText


@unittest.skipUnless((ROOT/'build/mail-glyph-resources/glyph-catalog.bin').is_file(), 'Local sources required')
class SeasonalDecoderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        catalog = (ROOT/'build/mail-glyph-resources/glyph-catalog.bin').read_bytes()
        cls.resource = compiled_resource(native, catalog)
        cls.review = audit(native, catalog)
        cls.entries = {e['template']: e for e in cls.review['templates']}
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-seasonal-decoder-')
        directory = Path(cls.temporary.name)
        # Only the host fixture makes resource bytes writable to inject faults.
        # Production compilation uses the generated const declarations unchanged.
        header = cls.resource['header'].replace('const unsigned char af_notice_seasonal_data',
                                                'unsigned char af_notice_seasonal_data')
        (directory/'seasonal_data.h').write_text(header)
        sources = ['runtime/mail/record.c', 'runtime/mail/format.c', 'runtime/crc32.c',
                   'runtime/notice/record.c', 'runtime/notice/seasonal.c', 'tests/notice_workspace_mock.c']
        flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g'] \
            if os.environ.get('AF_NOTICE_SANITIZE') == '1' else []
        environment = dict(os.environ); environment.pop('LD_PRELOAD', None)
        result = subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                                 *flags, '-I'+str(directory), *(str(ROOT/p) for p in sources),
                                 '-o', str(directory/'decoder.so')], capture_output=True, text=True, env=environment)
        if result.returncode: raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(directory/'decoder.so'))
        cls.restore = cls.lib.af_notice_seasonal_restore
        cls.restore.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_void_p]
        cls.lib.af_notice_seasonal_decode.argtypes = [C.c_void_p, C.c_void_p, C.c_uint]
        cls.lib.af_notice_seasonal_mask.argtypes = [C.c_uint]
        cls.lib.af_notice_seasonal_mask.restype = C.c_uint
        cls.lib.af_notice_seasonal_shop.argtypes = [C.c_void_p, C.c_uint, C.c_uint]
        cls.workspace_size = cls.lib.af_notice_workspace_size()
        cls.data = (C.c_ubyte*len(cls.resource['data'])).in_dll(cls.lib, 'af_notice_seasonal_data')

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def setUp(self): self.data[:] = self.resource['data']

    def fixtures(self):
        output = C.create_string_buffer(b'!'*(C.sizeof(NoticeText)+32), C.sizeof(NoticeText)+32)
        work = C.create_string_buffer(b'?'*(self.workspace_size+32), self.workspace_size+32)
        self.assertEqual(C.addressof(work) & 15, 0)
        return output, work

    def record(self, number, capital=0):
        sample = {0: Field(b'town  '), 1: Field(b'abcdefghijklmnop'),
                  2: Field(b'September 30th'), 3: Field(b'September 30th'), 4: Field(b'October 14th')}
        return Record(4, 0, (number,), tuple((i, sample[i]) for i in self.entries[number]['fields']), bool(capital))

    def restored(self, value):
        wire = pack(value)
        source = C.create_string_buffer(b'@'*16+wire+b'@'*16, 128)
        output, work = self.fixtures()
        self.assertEqual(self.restore(C.byref(output, 16), C.byref(source, 16), 96, C.byref(work, 16)), 1)
        result = NoticeText.from_buffer_copy(output.raw[16:-16])
        expected = complete_body(value, self.entries[value.templates[0]])
        self.assertEqual(result.length, len(expected))
        self.assertEqual(bytes(result.text), expected.ljust(1024, b'\0'))
        self.assertEqual(source.raw, b'@'*16+wire+b'@'*16)
        self.assertEqual(output.raw[:16]+output.raw[-16:], b'!'*32)
        self.assertEqual(work.raw[:16]+work.raw[-16:], b'?'*32)
        return expected

    def rejected(self, wire, size=96):
        source = C.create_string_buffer(wire, len(wire))
        output, work = self.fixtures()
        self.assertEqual(self.restore(C.byref(output, 16), source, size, C.byref(work, 16)), 0)
        self.assertEqual(output.raw, b'!'*len(output))
        self.assertEqual(source.raw, wire)
        self.assertEqual(work.raw[:16]+work.raw[-16:], b'?'*32)

    def test_all_41_bodies_both_capitals_and_complete_native_fields(self):
        for number in IDS:
            self.assertEqual(self.lib.af_notice_seasonal_mask(number), sum(1 << i for i in self.entries[number]['fields']))
            for capital in (0, 1): self.restored(self.record(number, capital))
        for number in (0, 0x1A3, 0x1CD, 0x101A4, 0xFFFFFFFF):
            self.assertEqual(self.lib.af_notice_seasonal_mask(number), 0xFFFFFFFF)

    def test_every_compiled_body_byte_is_checked_before_publication_then_recovers(self):
        offset = 0
        for number in IDS:
            value = self.record(number)
            length = len(bytes.fromhex(self.entries[number]['body']))
            for index in range(offset, offset+length):
                self.data[index] ^= 1
                self.rejected(pack(value))
                self.data[index] ^= 1
            self.restored(value)
            offset += length
        self.assertEqual(bytes(self.data), self.resource['data'])

    def test_wrong_ids_catalogues_and_semantic_fields_leave_output_unchanged(self):
        for number in IDS:
            value = self.record(number)
            for field_id, field in value.fields:
                limit = 6 if field_id == 0 else 16 if field_id == 1 else 14
                for text in (b'', b' '*limit, b'A\xcdB', b'A'*(limit+1)):
                    if len(text) > 16: continue  # The structural codec rejects this before decoding.
                    changed = replace(value, fields=((field_id, Field(text)),))
                    self.rejected(pack(changed))
                self.rejected(pack(replace(value, fields=((field_id, Field(b'name', 1)),))))
                self.rejected(pack(replace(value, fields=())))
            self.rejected(pack(replace(value, fields=value.fields+((19, Field(b'extra')),))))
        for value in (Record(2, 0, (0x1A4,), ()), Record(4, 0, (0x1A3,), ()),
                      Record(4, 0, (0x1CD,), ()), Record(4, 0, (0x1F0,), ())):
            self.rejected(pack(value))
        wire = pack(self.record(0x1A4))
        for at in (0, 3, 15, 95):
            broken = bytearray(wire); broken[at] ^= 1
            self.rejected(bytes(broken))
        for size in (0, 95, 97, 0xFFFFFFFF): self.rejected(wire, size)

    def test_output_can_overlap_input_but_not_workspace_or_unaligned_memory(self):
        value = self.record(0x1BA, 1); wire = pack(value)
        output, work = self.fixtures()
        C.memmove(C.byref(output, 16), wire, 96)
        self.assertEqual(self.restore(C.byref(output, 16), C.byref(output, 16), 96, C.byref(work, 16)), 1)
        text = NoticeText.from_buffer_copy(output.raw[16:-16])
        self.assertEqual(bytes(text.text[:text.length]), complete_body(value, self.entries[0x1BA]))
        for out, scratch in ((C.byref(output, 17), C.byref(work, 16)),
                             (C.byref(output, 16), C.byref(work, 17)),
                             (C.byref(work, 16), C.byref(work, 16)),
                             (None, C.byref(work, 16)), (C.byref(output, 16), None)):
            before = output.raw, work.raw
            self.assertEqual(self.restore(out, wire, 96, scratch), 0)
            self.assertEqual((output.raw, work.raw), before)
        before = work.raw
        self.assertEqual(self.lib.af_notice_seasonal_decode(C.byref(work, 16), C.byref(work, 32), 96), 0)
        self.assertEqual(work.raw, before)

    def test_compiled_payload_and_manifest_reconstruct_from_verified_sources(self):
        self.assertEqual(bytes(self.data), self.resource['data'])
        offset = 0
        for entry in self.resource['templates']:
            body = bytes.fromhex(entry['body'])
            self.assertEqual(sha256(bytes(self.data[offset:offset+len(body)])), entry['body_sha256'])
            offset += len(body)
        self.assertEqual(offset, len(self.data))
        self.assertEqual(len(self.resource['table']), 41*12)

    def test_complete_shop_names_keep_the_actual_supplied_notice_spelling(self):
        self.assertEqual(tuple(s.rstrip() for s in self.resource['shops']),
                         (b"Nook's Cranny", b"Stop 'n Nook", b'Nookway', b"Nookington's"))
        for level in range(4):
            output = C.create_string_buffer(b'!'*48, 48)
            self.assertEqual(self.lib.af_notice_seasonal_shop(C.byref(output, 16), 16, level), 1)
            self.assertEqual(output.raw, b'!'*16+self.resource['shops'][level]+b'!'*16)
        for size, level in ((0, 0), (15, 0), (16, 4), (16, 0xFFFFFFFF)):
            output = C.create_string_buffer(b'!'*48, 48)
            self.assertEqual(self.lib.af_notice_seasonal_shop(C.byref(output, 16), size, level), 0)
            self.assertEqual(output.raw, b'!'*48)
        self.assertEqual(self.lib.af_notice_seasonal_shop(None, 16, 0), 0)


if __name__ == '__main__': unittest.main()
