"""Immutable cartridge templates reconstruct full letters without save changes."""

import ctypes as C
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from mail_catalog import BANKS, COUNTS, VROM, resource, parse, templates, identity, verify_registered, install
from mail_record import Record, Field, pack
from mail_format import Letter, format_letter
from mail_reference import assembly_cases
from audit_mail_templates import template_fields
from test_mail_format import CText, inplace_reference
from test_retail import ROM_PATH

CATALOG_PATH = ROOT/'build/mail-catalog/catalog.bin'


class MailCatalogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.banks = {name: [b'']*count for name, count in zip(BANKS, COUNTS)}
        cls.banks['super'][0] = b'To \xcd!'
        cls.banks['mail'][0] = b'\x7f\x75Hello \x7f\x24.\xcd'
        cls.banks['ps'][0] = b'Your friend'
        cls.banks['mail'][1] = None
        cls.data = resource(cls.banks, 2)

    def test_all_indices_empty_missing_canonical_roundtrip_and_full_output(self):
        catalog, banks = parse(self.data, expected_catalog=2)
        self.assertEqual((catalog, banks), (2, self.banks))
        self.assertEqual(resource(banks, catalog), self.data)
        record = Record(2, 0, (0,), ((0, Field(b'friend', 4)),))
        parts = templates(self.data, record)
        self.assertEqual(format_letter(record, parts), inplace_reference(record, parts))
        with self.assertRaisesRegex(ValueError, 'Unavailable'):
            templates(self.data, replace(record, templates=(1,)))
        with self.assertRaisesRegex(ValueError, 'Unavailable'):
            templates(self.data, replace(record, templates=(982,)))
        with self.assertRaisesRegex(ValueError, 'snapshot kind'):
            templates(self.data, replace(record, kind=2))
        self.assertEqual(templates(self.data, replace(record, templates=(981,))).parts, (b'',)*3)

    def test_immutable_identity_requires_exact_registered_content(self):
        row = identity(self.data)
        registry = {'version': 1, 'catalogs': [row]}
        self.assertEqual(verify_registered(self.data, registry), row)
        for changed in ({'version': 2, 'catalogs': [row]}, {'version': 1, 'catalogs': []},
                        {'version': 1, 'catalogs': [row, row]},
                        {'version': 1, 'catalogs': [None]},
                        {'version': 1, 'catalogs': [{'catalog': []}]},
                        {'version': 1, 'catalogs': [{**row, 'semantics': 2}]}):
            with self.assertRaises(ValueError):
                verify_registered(self.data, changed)
        changed = {name: list(parts) for name, parts in self.banks.items()}
        changed['mail'][0] += b' '
        with self.assertRaisesRegex(ValueError, 'changed immutable'):
            verify_registered(resource(changed, 2), registry)
        for catalog in (0, 1, 65535, 65536, True):
            with self.assertRaises(ValueError):
                resource(self.banks, catalog)

    def test_corrupt_headers_tables_rows_payload_padding_and_commands_fail(self):
        # Recompute the outer hash so inner checks have independent coverage.
        table_start = 256
        row = struct.unpack_from('>IHHII', self.data, table_start)
        for offset in (0, 4, 12, 16, 20, 24, 28, 64, 128, 132, 136, 140,
                       table_start, table_start+4, table_start+6, table_start+8,
                       table_start+12, row[0], row[0]+row[1]):
            bad = bytearray(self.data)
            bad[offset] ^= 1
            bad[32:64] = hashlib.sha256(bad[128:]).digest()
            with self.subTest(offset=offset), self.assertRaises(ValueError):
                parse(bytes(bad))
        for data in (self.data[:100], self.data[:-1], self.data+bytes(16)):
            with self.assertRaises(ValueError):
                parse(data)
        for part in (b'\x7f', b'\x7f\x63', b'\x80', b'x'*1025):
            banks = {name: list(parts) for name, parts in self.banks.items()}
            banks['mail'][0] = part
            with self.assertRaises(ValueError):
                resource(banks, 2)

    @unittest.skipUnless(CATALOG_PATH.is_file() and ROM_PATH.is_file()
                         and (ROOT/'build/runtime-module/module.json').is_file(), 'Registered resource and module required')
    def test_installer_binds_registered_resource_and_all_configuration_words(self):
        from runtime_module import add_runtime_module, MODULE_VROM, verify_test_module
        from aflib import replace_dma, sha256
        from extended_items import install as items
        from display_names import install as names
        from catchphrases import install as catchphrases
        rom = ROM_PATH.read_bytes()
        additions, module = add_runtime_module(rom, {}, ROOT/'build/runtime-module')
        for installer, path in ((items, 'build/alias-items'), (names, 'build/display-names'),
                                (catchphrases, 'build/catchphrases')):
            if not (ROOT/path).is_dir():
                self.skipTest('Combined optional resources are local-only inputs')
            installer(rom, additions, module, ROOT/path)
        installed = dict(additions)
        report = install(rom, installed, module, CATALOG_PATH.parent)
        self.assertEqual(installed[VROM], CATALOG_PATH.read_bytes())
        self.assertEqual(installed[MODULE_VROM][56:72], struct.pack('>4I', 0x02A00000, 0x02C00000, 0x02E00000, VROM))
        self.assertEqual(report['configured_module_sha256'], sha256(installed[MODULE_VROM]))
        verify_test_module(replace_dma(rom, {}, additions=installed), module)
        with self.assertRaises(ValueError):
            install(rom, installed, module, CATALOG_PATH.parent)
        for values, metadata in (({}, module), (additions, None),
                                 (additions, {**module, 'symbols': {}})):
            with self.assertRaisesRegex(ValueError, 'capable resident'):
                install(rom, values, metadata, CATALOG_PATH.parent)
        changed = bytearray(additions[MODULE_VROM])
        changed[512] ^= 1
        with self.assertRaisesRegex(ValueError, 'verified module'):
            install(rom, {**additions, MODULE_VROM: bytes(changed)}, module, CATALOG_PATH.parent)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary)
            metadata = json.loads((CATALOG_PATH.parent/'catalog.json').read_text())
            (path/'catalog.bin').write_bytes(CATALOG_PATH.read_bytes())
            for invalid in ({**metadata, 'registered': False}, {**metadata, 'source_sha256': '0'*64},
                            {**metadata, 'sha256': '0'*64}):
                (path/'catalog.json').write_text(json.dumps(invalid))
                with self.assertRaisesRegex(ValueError, 'Stale, proposed'):
                    install(rom, dict(additions), module, path)


@unittest.skipUnless(CATALOG_PATH.is_file() and shutil.which('gcc'), 'Registered local catalog and host GCC required')
class MailCatalogRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = CATALOG_PATH.read_bytes()
        verify_registered(cls.data)
        cls.banks = parse(cls.data)[1]
        cls.temporary = tempfile.TemporaryDirectory()
        library = Path(cls.temporary.name)/'mail-catalog.so'
        subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O2', '-shared', '-fPIC',
                        *(str(ROOT/'runtime/mail'/name) for name in ('record.c', 'format.c', 'catalog.c')),
                        str(ROOT/'runtime/crc32.c'),
                        str(ROOT/'tests/mail_catalog_mock.c'), '-o', str(library)],
                       check=True, capture_output=True)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_mail_restore.argtypes = [C.c_void_p, C.c_void_p, C.c_uint, C.c_void_p]
        cls.lib.af_mail_catalog_header_valid.argtypes = [C.c_void_p, C.c_uint]
        cls.work_size = cls.lib.af_mail_catalog_workspace_size()

    @classmethod
    def tearDownClass(cls):
        cls.temporary.cleanup()

    def setUp(self):
        self.rom = (C.c_ubyte*0x100000).in_dll(self.lib, 'af_mail_catalog_rom')
        C.memset(self.rom,0,C.sizeof(self.rom))
        C.memmove(self.rom, self.data, len(self.data))
        self.enabled = C.c_uint.in_dll(self.lib, 'af_mail_catalog_enabled')
        self.enabled.value = 1
        self.reads = C.c_uint.in_dll(self.lib, 'af_mail_catalog_reads')
        self.reads.value = 0
        self.errors = C.c_uint.in_dll(self.lib, 'af_mail_catalog_dma_error')
        self.errors.value = 0
        self.fail_at = C.c_uint.in_dll(self.lib, 'af_mail_catalog_fail_read')
        self.fail_at.value = 0

    def call(self, record, expected=None, success=True, skew=0):
        wire = pack(record)
        source = C.create_string_buffer(b'!'*(16+skew)+wire+b'!'*16, 154+skew)
        output = C.create_string_buffer(b'!'*1072, 1072)
        workspace = C.create_string_buffer(b'!'*(self.work_size+64), self.work_size+64)
        work = (C.addressof(workspace)+31) & ~15
        lead = work-C.addressof(workspace)
        result = self.lib.af_mail_restore(C.byref(output, 16), C.byref(source, 16+skew), 122, work)
        self.assertEqual(result, int(success))
        self.assertEqual(source.raw, b'!'*(16+skew)+wire+b'!'*16)
        self.assertEqual(workspace.raw[:lead], b'!'*lead)
        self.assertEqual(workspace.raw[lead+self.work_size:], b'!'*(64-lead))
        self.assertEqual(output.raw[:16]+output.raw[-16:], b'!'*32)
        self.assertEqual(self.errors.value, 0)
        if not success:
            self.assertEqual(output.raw, b'!'*1072)
            return
        expected = format_letter(record, templates(self.data, record)) if expected is None else expected
        value = CText.from_buffer_copy(output.raw[16:-16])
        chunks = [bytes(value.text[o:o+n]) for o, n in zip(value.offsets, value.lengths)]
        self.assertEqual(Letter(*chunks, value.split, bool(value.capital)), expected)
        self.assertFalse(value.reserved or any(value.text[sum(value.lengths):]))

    @unittest.skipUnless(ROM_PATH.is_file(), 'Reference reply group audit requires native ROM')
    def test_all_reference_assembly_cases_and_unsupported_rows(self):
        assembled = rejected = 0
        for label, record, parts, limitation in assembly_cases(self.banks, ROM_PATH.read_bytes()):
            if record is None:
                rejected += 1
                continue
            record, parts = replace(record, catalog=2), replace(parts, catalog=2)
            with self.subTest(case=label, limitation=limitation):
                self.call(record, inplace_reference(record, parts), skew=assembled % 8)
            assembled += 1
        self.assertEqual((assembled, rejected), (6398, 58))
        for index in identity(self.data)['unavailable']['mail']:
            self.call(Record(2, 0, (index,), ()), success=False)

    def test_header_each_dma_failure_missing_fields_and_bad_ids_preserve_output(self):
        record = Record(2, 0, (0,), ())
        mask = set().union(*(template_fields(part) for part in templates(self.data, record).parts))
        record = replace(record, fields=tuple((i, Field(b'word')) for i in sorted(mask)))
        self.call(record)
        reads = self.reads.value
        for index in range(1, reads+1):
            self.reads.value, self.fail_at.value = 0, index
            self.call(record, success=False)
        self.fail_at.value = 0
        for word in range(32):
            self.rom[word*4+3] ^= 1
            self.call(record, success=False)
            self.rom[word*4+3] ^= 1
        for changed in (replace(record, catalog=5), replace(record, templates=(982,))):
            self.call(changed, success=False)
        self.enabled.value = 0
        self.reads.value = 0
        self.call(record, success=False)
        self.assertEqual(self.reads.value, 0)
        self.assertEqual(self.lib.af_mail_catalog_header_valid(None, 2), 0)

    def test_modified_selected_directories_rows_and_data_are_rejected(self):
        record = Record(2, 0, (0,), ())
        parts = templates(self.data, record)
        used = set().union(*(template_fields(part) for part in parts.parts))
        record = replace(record, fields=tuple((i, Field(b'word')) for i in sorted(used)))
        if used:
            self.call(replace(record, fields=()), success=False)
        for bank in range(3):
            directory = 128+bank*16
            table = struct.unpack_from('>I', self.data, directory+8)[0]
            offset, length, _, _, _ = struct.unpack_from('>IHHII', self.data, table)
            sites = [directory+i for i in range(16)]+[table+i for i in range(16)]
            sites += [offset+i for i in range((length+15) & ~15)]
            for index in sites:
                self.rom[index] ^= 1
                with self.subTest(offset=index):
                    self.call(record, success=False)
                self.rom[index] ^= 1

    @unittest.skipUnless((ROOT/'build/mail-glyph-catalog/catalog.bin').is_file(),'Complete glyph catalogue is locally generated')
    def test_complete_new_catalogue_reconstruction_and_old_snapshot_compatibility(self):
        original = self.data
        self.data = (ROOT/'build/mail-glyph-catalog/catalog.bin').read_bytes()
        verify_registered(self.data)
        C.memmove(C.addressof(self.rom)+0xA0000,self.data,len(self.data))
        banks = parse(self.data)[1]
        try:
            cases = 0
            for label,record,parts,limitation in assembly_cases(banks,ROM_PATH.read_bytes()):
                self.assertIsNotNone(record,label)
                record,parts = replace(record,catalog=4),replace(parts,catalog=4)
                with self.subTest(case=label):
                    self.call(record,inplace_reference(record,parts),skew=cases%8)
                cases += 1
            self.assertEqual(cases,6514)
            for word in range(32):
                self.rom[0xA0000+word*4+3] ^= 1
                self.call(Record(4,0,(0,),()),success=False)
                self.rom[0xA0000+word*4+3] ^= 1
        finally:
            self.data = original
        # Both resources coexist; restoring old letters still uses catalogue two.
        record = Record(2,0,(0,),())
        mask = set().union(*(template_fields(p) for p in templates(self.data,record).parts))
        self.call(replace(record,fields=tuple((i,Field(b'word')) for i in sorted(mask))))

    def test_invalid_pointers_sizes_and_workspace_aliases_do_not_write(self):
        storage = C.create_string_buffer(b'!'*12000, 12000)
        base = (C.addressof(storage)+31) & ~15
        for out, wire, size, work in ((0,base+4000,122,base), (base+8000,0,122,base),
                                     (base+8000,base+4000,122,0), (base+8000,base+4000,121,base),
                                     (base+8000,base+4000,123,base), (base+8000,base+4000,122,base+1),
                                     (base,base+4000,122,base), (base+8000,base,122,base),
                                     (base+8000,base+8000,122,base)):
            self.assertEqual(self.lib.af_mail_restore(out, wire, size, work), 0)
            self.assertEqual(storage.raw, b'!'*12000)
        self.assertEqual(self.reads.value, 0)
