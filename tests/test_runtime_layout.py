"""Module growth cannot overlap native test buffers or signed-immediate bounds."""

import json
from pathlib import Path
import re
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from runtime_layout import MODULE_RAM, RESERVATION, LINKED_LIMIT, TEST_RETURN, TEST_STACK, GUARD_ADDRESS
from runtime_module import runtime_source_hashes
from mail_runtime_test_scenario import fixtures, record_bytes, template_bytes, output_bytes, SOURCE, OUTPUT, STACK_LOW
from mail_record import unpack, pack


class RuntimeLayoutTests(unittest.TestCase):
    def test_region_arithmetic_and_mail_abi_sizes(self):
        self.assertEqual((RESERVATION, LINKED_LIMIT), (32768, 24576))
        self.assertEqual(TEST_RETURN, 0x8019A8E0)
        self.assertEqual((TEST_STACK, GUARD_ADDRESS), (0x8019C880, 0x8019C8D0))
        self.assertEqual(MODULE_RAM+RESERVATION+0x263720, 0x80400000)
        for record, templates in fixtures():
            self.assertEqual(len(record_bytes(record)), 380)
            descriptors, raw = template_bytes(templates)
            self.assertEqual(len(descriptors), 68)
            self.assertLess(SOURCE+len(raw)+16, OUTPUT-16)
            data = output_bytes(record, templates)
            self.assertEqual(len(data), 1040)
            self.assertLess(OUTPUT+len(data)+16, STACK_LOW)
            self.assertEqual(unpack(pack(record), expected_catalog=record.catalog), record)

    def test_no_stale_fixture_addresses_in_generators_or_json(self):
        paths = list((ROOT/'tests').glob('*.json'))+list((ROOT/'tools').glob('*_test_scenario.py'))
        for path in paths:
            text = path.read_text()
            for match in re.finditer(r'8019[0-9A-Fa-f]{4}', text):
                self.assertFalse(0x801968E0 <= int(match[0], 16) <= 0x801988E0, (path.name, match[0]))
            self.assertNotIn('AF16C0DE', text, path.name)
            if path.suffix == '.json':
                def visit(value):
                    if type(value) is int:
                        self.assertFalse(0x801968E0 <= value <= 0x801988E0, (path.name, value))
                    elif isinstance(value, list):
                        for item in value:
                            visit(item)
                    elif isinstance(value, dict):
                        for item in value.values():
                            visit(item)
                visit(json.loads(text))

    def test_nested_mail_sources_are_part_of_module_inventory(self):
        sources = runtime_source_hashes(ROOT/'runtime')
        for name in ('mail/record.c', 'mail/record.h', 'mail/format.c', 'mail/format.h',
                     'mail/catalog.c', 'mail/catalog.h', 'mail/view.c', 'mail/view.h',
                     'mail/page.c', 'mail/page.h', 'mail/reader.c', 'mail/reader.h', 'mail_view_hooks.s'):
            self.assertIn(name, sources)

    @unittest.skipUnless((ROOT/'build/runtime-module/bootstrap.bin').is_file(), 'Build the resident module first')
    def test_assembled_bootstrap_loads_unsigned_reservation_and_mail_symbols_fit(self):
        directory = ROOT/'build/runtime-module'
        data = (directory/'bootstrap.bin').read_bytes()
        words = struct.unpack('>'+str(len(data)//4)+'I', data)
        self.assertIn(0x34068000, words)  # ori a2,zero,8000, DMA length
        self.assertEqual(words.count(0x34058000), 2)  # Both cache lengths.
        self.assertEqual(words.count(0x34088000), 2)  # Header and heap arithmetic.
        self.assertIn(0x02082021, words)  # addu a0,s0,t0
        self.assertIn(0x02282823, words)  # subu a1,s1,t0
        self.assertFalse(any(word >> 26 == 9 and word & 0xFFFF == 0x8000 for word in words))
        module = (directory/'module.bin').read_bytes()
        report = json.loads((directory/'module.json').read_text())
        self.assertEqual(len(module), RESERVATION)
        self.assertEqual(struct.unpack_from('>I', module, 8)[0], RESERVATION)
        self.assertLessEqual(report['linked_bytes'], LINKED_LIMIT)
        self.assertFalse(any(module[LINKED_LIMIT:]))
        for name in ('af_mail_record_pack', 'af_mail_record_unpack', 'af_mail_format',
                     'af_mail_restore', 'af_mail_catalog_header_valid', 'af_mail_next_line',
                     'af_mail_body_hook', 'af_mail_footer_hook', 'af_mail_read_body', 'af_mail_read_footer',
                     'af_mail_header_hook', 'af_mail_copy_hook', 'af_mail_reader_copy', 'af_mail_reader_trigger',
                     'af_mail_page', 'af_mail_snapshot_header', 'af_mail_snapshot_body', 'af_mail_snapshot_footer'):
            address = int(report['symbols'][name], 16)
            self.assertTrue(MODULE_RAM+0x300 <= address < MODULE_RAM+report['linked_bytes'])
