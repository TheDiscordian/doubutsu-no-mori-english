"""Full initial announcements retain manual layout and the real N64 controls."""

import ctypes as C
from dataclasses import replace
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from audit_noticeboard import audit, initial_body, INITIAL_IDS, SCOPED_IDS
from mail_catalog import parse, templates
from mail_format import format_letter
from mail_record import Record, Field
from notice_record import pack

CATALOG = ROOT/'build/mail-glyph-resources/glyph-catalog.bin'
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


class NoticeText(C.Structure):
    _fields_ = [('length', C.c_uint), ('text', C.c_ubyte*1024)]


@unittest.skipUnless(CATALOG.is_file() and ROM.is_file(), 'Supplied local inputs required')
class NoticeInitialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = CATALOG.read_bytes()
        cls.report = audit(ROM.read_bytes(), cls.catalog)
        cls.banks = parse(cls.catalog)[1]
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-notice-initial-')
        library = Path(cls.temporary.name)/'initial.so'
        sources = ['runtime/mail/record.c', 'runtime/mail/format.c', 'runtime/mail/catalog.c',
                   'runtime/crc32.c', 'runtime/notice/record.c', 'runtime/notice/initial.c',
                   'tests/mail_catalog_mock.c', 'tests/notice_workspace_mock.c']
        flags = ['-fsanitize=address,undefined', '-fno-sanitize-recover=all',
                 '-fno-omit-frame-pointer', '-g'] if os.environ.get('AF_NOTICE_SANITIZE') == '1' else []
        compiler_env = dict(os.environ)
        compiler_env.pop('LD_PRELOAD', None)
        subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        *flags,
                        *(str(ROOT/name) for name in sources), '-o', str(library)],
                       check=True, capture_output=True, env=compiler_env)
        cls.lib = C.CDLL(str(library))
        cls.create = cls.lib.af_notice_initial_pack
        cls.create.argtypes = [C.c_void_p, C.c_uint, C.c_uint, C.c_uint]
        cls.restore = cls.lib.af_notice_initial_restore
        cls.restore.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_void_p]
        cls.workspace_size = cls.lib.af_notice_workspace_size()
        cls.rom = (C.c_ubyte*0x100000).in_dll(cls.lib, 'af_mail_catalog_rom')

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.rom[0xA0000:0xA0000+len(self.catalog)] = self.catalog
        for name, value in (('af_mail_catalog_enabled', 1), ('af_mail_catalog_reads', 0),
                            ('af_mail_catalog_fail_read', 0), ('af_mail_catalog_dma_error', 0)):
            C.c_uint.in_dll(self.lib, name).value = value

    def fixtures(self):
        output = C.create_string_buffer(b'!'*(C.sizeof(NoticeText)+32), C.sizeof(NoticeText)+32)
        work = C.create_string_buffer(b'?'*(self.workspace_size+32), self.workspace_size+32)
        self.assertEqual(C.addressof(work) & 15, 0)
        return output, work

    def restore_ok(self, record):
        wire = pack(record)
        expected = initial_body(record, self.banks)
        source = C.create_string_buffer(b'@'*16+wire+b'@'*24, 136)
        output, work = self.fixtures()
        self.assertEqual(self.restore(C.byref(output, 16), C.byref(source, 16), 96, C.byref(work, 16)), 1)
        text = NoticeText.from_buffer_copy(output.raw[16:-16])
        self.assertEqual(text.length, len(expected))
        self.assertEqual(bytes(text.text), expected.ljust(1024, b'\0'))
        self.assertEqual(source.raw, b'@'*16+wire+b'@'*24)
        self.assertEqual((output.raw[:16], output.raw[-16:]), (b'!'*16, b'!'*16))
        self.assertEqual((work.raw[:16], work.raw[-16:]), (b'?'*16, b'?'*16))
        self.assertEqual(C.c_uint.in_dll(self.lib, 'af_mail_catalog_dma_error').value, 0)
        return expected

    def test_all_initial_posts_and_capital_states_reconstruct_the_entire_reference(self):
        for case in self.report['cases']:
            record = Record(4, 0, (case['template'],), (), bool(case['capital']))
            body = self.restore_ok(record)
            self.assertEqual((sha256(body), len(body)), (case['body_sha256'], case['body_bytes']))
            original = format_letter(record, templates(self.catalog, record)).body
            expected = original.replace(b'C Stick', b'C Buttons') if case['template'] == 0x21 else original
            self.assertEqual(body, expected)
            # Replacement changes no manual newline, leading/trailing space, or punctuation.
            self.assertEqual(body.count(b'\xcd'), original.count(b'\xcd'))
            self.assertEqual(body.endswith(b'\xcd'), original.endswith(b'\xcd'))
        self.assertEqual([r['body_bytes'] for r in self.report['cases'][::2]], [141, 166, 137, 156])

    def test_creator_writes_exactly_the_message_in_all_fifteen_post_positions(self):
        for slot in range(15):
            for case in self.report['cases']:
                saved = C.create_string_buffer(b'!'*(15*104+32), 15*104+32)
                offset = 16+slot*104
                self.assertEqual(self.create(C.byref(saved, offset), 96, case['template'], case['capital']), 1)
                self.assertEqual(saved.raw, b'!'*offset+bytes.fromhex(case['wire'])
                                 + b'!'*(len(saved)-offset-96))

    def test_invalid_templates_capitals_and_capacity_leave_complete_posts_unchanged(self):
        for arg, values in ((1, (0, 95)), (2, (0, 0x1D, 0x22, 0xFFFF, 0xFFFFFFFF)),
                            (3, (2, 256, 0xFFFFFFFF))):
            for value in values:
                post = C.create_string_buffer(b'!'*136, 136)
                args = [C.byref(post, 16), 96, 0x1E, 0]
                args[arg] = value
                self.assertEqual(self.create(*args), 0)
                self.assertEqual(post.raw, b'!'*136)
        self.assertEqual(self.create(None, 96, 0x1E, 0), 0)

    def test_other_catalogues_templates_and_unclaimed_fields_do_not_gain_approval(self):
        base = Record(4, 0, (0x1E,), ())
        for record in (replace(base, catalog=2), replace(base, templates=(0x1A4,)),
                       replace(base, fields=((0, Field(b'ignored')),))):
            output, work = self.fixtures()
            self.assertEqual(self.restore(C.byref(output, 16), pack(record), 96, C.byref(work, 16)), 0)
            self.assertEqual(output.raw, b'!'*len(output))
            with self.assertRaises(ValueError):
                initial_body(record, self.banks)
        self.assertEqual(C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads').value, 0)

    def test_missing_corrupt_or_failed_cartridge_reads_retain_output_and_allow_retry(self):
        record = Record(4, 0, (0x21,), ())
        wire = pack(record)
        # Measure every read, including directories, rows, and body payloads.
        self.restore_ok(record)
        reads = C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads').value
        self.assertGreater(reads, 6)
        for failure in range(1, reads+1):
            C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads').value = 0
            C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read').value = failure
            output, work = self.fixtures()
            self.assertEqual(self.restore(C.byref(output, 16), wire, 96, C.byref(work, 16)), 0)
            self.assertEqual(output.raw, b'!'*len(output))
        C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read').value = 0
        C.c_uint.in_dll(self.lib, 'af_mail_catalog_enabled').value = 0
        output, work = self.fixtures()
        self.assertEqual(self.restore(C.byref(output, 16), wire, 96, C.byref(work, 16)), 0)
        self.assertEqual(output.raw, b'!'*len(output))
        C.c_uint.in_dll(self.lib, 'af_mail_catalog_enabled').value = 1
        self.rom[0xA0000] ^= 1
        self.assertEqual(self.restore(C.byref(output, 16), wire, 96, C.byref(work, 16)), 0)
        self.assertEqual(output.raw, b'!'*len(output))
        self.rom[0xA0000] ^= 1
        self.restore_ok(record)

    def test_invalid_sizes_nulls_alignment_and_workspace_aliases_are_rejected(self):
        wire = pack(Record(4, 0, (0x1E,), ()))
        for index, values in ((0, (None,)), (1, (None,)), (2, (0, 95, 97, 0xFFFFFFFF)), (3, (None,))):
            for value in values:
                output, work = self.fixtures()
                args = [C.byref(output, 16), wire, 96, C.byref(work, 16)]
                args[index] = value
                self.assertEqual(self.restore(*args), 0)
                self.assertEqual(output.raw, b'!'*len(output))
                self.assertEqual(work.raw, b'?'*len(work))
        for variant in ('output_unaligned', 'work_unaligned', 'output_in_work', 'input_in_work'):
            output, work = self.fixtures()
            args = [C.byref(output, 16), wire, 96, C.byref(work, 16)]
            if variant == 'output_unaligned': args[0] = C.byref(output, 17)
            if variant == 'work_unaligned': args[3] = C.byref(work, 17)
            if variant == 'output_in_work': args[0] = C.byref(work, 16)
            if variant == 'input_in_work': args[1] = C.byref(work, 32)
            self.assertEqual(self.restore(*args), 0)
            self.assertEqual(output.raw, b'!'*len(output))
            self.assertEqual(work.raw, b'?'*len(work))

    def test_initial_output_may_overlap_input_after_complete_decoding(self):
        record = Record(4, 0, (0x21,), ())
        output, work = self.fixtures()
        C.memmove(C.byref(output, 16), pack(record), 96)
        self.assertEqual(self.restore(C.byref(output, 16), C.byref(output, 16), 96, C.byref(work, 16)), 1)
        body = initial_body(record, self.banks)
        text = NoticeText.from_buffer_copy(output.raw[16:-16])
        self.assertEqual((text.length, bytes(text.text)), (len(body), body.ljust(1024, b'\0')))
        self.assertEqual((output.raw[:16], output.raw[-16:]), (b'!'*16, b'!'*16))

    def test_complete_reference_feasibility_is_not_seasonal_or_treasure_approval(self):
        self.assertEqual(len(self.report['parts']), 12)
        self.assertEqual(tuple(r['template'] for r in self.report['feasibility']), SCOPED_IDS)
        self.assertEqual(max(r['used_bytes'] for r in self.report['feasibility']), 84)
        self.assertEqual(sum(r['semantic_approval'] for r in self.report['feasibility']), 4)
        self.assertFalse(self.report['installed'])
        self.assertEqual(self.report['button_masks']['80894594'], '0002')
        self.assertEqual(self.report['button_masks']['808945D4'], '0001')
        for number in INITIAL_IDS:
            changed = {name: list(values) for name, values in self.banks.items()}
            changed['mail'][number] = changed['mail'][number][:-1]
            with self.assertRaisesRegex(ValueError, 'Changed complete'):
                initial_body(Record(4, 0, (number,), ()), changed)


if __name__ == '__main__':
    unittest.main()
