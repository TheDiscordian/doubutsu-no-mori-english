"""Capture/dig name sources, safe inactive-tail reuse, and complete cartridge retention."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, by_vrom, sha256, apply_ups
from npc_mail_show import relocate_verified_data
from runtime_module import MODULE_VROM
from extended_items import VROM as ITEMS_VROM
from test_shop_item_names import tail_arguments
import player_item_names as p

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PREVIOUS = ROOT/'build/shop-item-names-pilot'
BUILD = ROOT/'build/player-item-names-pilot'


@unittest.skipUnless(ROM.is_file() and (PREVIOUS/'build.json').is_file(), 'Native source and complete shop build required')
class PlayerItemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.prior = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((PREVIOUS/'build.json').read_text())
        cls.files = by_vrom(cls.prior)
        cls.original_code, cls.actor, cls.reloc = p.source(cls.native)
        cls.current_code = cls.files[CODE_VROM].extract(cls.prior)
        cls.additions = {v: cls.files[v].extract(cls.prior) for v in (MODULE_VROM, ITEMS_VROM)}
        cls.module = cls.report['runtime_module']

    def test_each_native_item_expression_keeps_its_source_and_zero_safe_field(self):
        for name, (at, _, _) in p.CALLS.items():
            old = struct.unpack_from('>7I', self.actor, at-p.SPEC.ram)
            new = struct.unpack('>7I', p.call_body(name))
            # Only the destination of the native unsigned item expression
            # changes from a1 to a0; its actor/callback source is unchanged.
            self.assertEqual(new[0], (old[1] & ~0x1F0000) | (4 << 16))
            self.assertEqual(new[1], p.jump(p.BRIDGE, link=True))
            self.assertEqual(new[2:], (0x00002825, 0, 0, 0, 0))
            self.assertIn(new[0] >> 26, (12, 37))  # ANDI or unsigned halfword load.
            for item in (0, 0x1000, 0x2200, 0x2301, 0x2D01, 0xFFFF):
                target, regs = tail_arguments(p.bridge_body(), item, 0)
                self.assertEqual(regs[5], 0)
                if item:
                    self.assertEqual((target, regs[4]), (p.IMPORTS['af_quest_set_item'], item))
                else:
                    self.assertEqual((target, regs[4], regs[6], regs[7]),
                                     (p.IMPORTS['af_set_item_str'], 0x80142410, 0x80142410, 0))

    def test_only_three_sequences_and_inactive_tail_change(self):
        replacements = {CODE_VROM: self.current_code}
        result = p.install(self.native, replacements, self.additions, self.module)
        self.assertEqual(set(replacements), {CODE_VROM, p.SPEC.vrom})
        self.assertEqual(result['extra_allocation_bytes'], 0)
        self.assertFalse(result['saved_layout_changes'])
        lo, hi = p.BRIDGE-CODE_RAM, p.BRIDGE_END-CODE_RAM
        current = replacements[CODE_VROM]
        self.assertEqual(current[:lo]+current[hi:], self.current_code[:lo]+self.current_code[hi:])
        self.assertEqual(current[lo:hi], p.bridge_body())
        expected = bytearray(self.actor)
        for name, (at, _, _) in p.CALLS.items():
            expected[at-p.SPEC.ram:at-p.SPEC.ram+p.PATCH_BYTES] = p.call_body(name)
        self.assertEqual(replacements[p.SPEC.vrom], expected)
        self.assertEqual(result['reference_audit']['external_interior_references'], [])
        for base in (0x801A0010, 0x802F8010):
            a, b = [relocate_verified_data(p.SPEC, value, self.reloc, base)
                    for value in (self.actor, bytes(expected))]
            for name, (at, _, _) in p.CALLS.items():
                offset = at-p.SPEC.ram
                self.assertEqual(b[offset:offset+p.PATCH_BYTES], p.call_body(name))
                a = a[:offset]+p.call_body(name)+a[offset+p.PATCH_BYTES:]
            self.assertEqual(a, b)

    def test_changed_live_entry_tail_actor_or_reader_is_rejected_atomically(self):
        for at in (p.BRIDGE-8, p.BRIDGE, 0x800A1820):
            code = bytearray(self.current_code); code[at-CODE_RAM] ^= 1
            values = {CODE_VROM: bytes(code)}
            before = dict(values)
            with self.assertRaises(ValueError): p.install(self.native, values, self.additions, self.module)
            self.assertEqual(values, before)
        actor = bytearray(self.actor); actor[0] ^= 1
        values = {CODE_VROM: self.current_code, p.SPEC.vrom: bytes(actor)}
        before = dict(values)
        with self.assertRaises(ValueError): p.install(self.native, values, self.additions, self.module)
        self.assertEqual(values, before)
        with self.assertRaises(ValueError): p.install(self.native, {CODE_VROM: self.current_code}, {}, self.module)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete player-name build required')
    def test_complete_cartridge_preserves_text_saves_resources_and_patch(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        files = by_vrom(built)
        p.verify_installation(built, self.native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(files.keys(), self.files.keys())
        self.assertEqual({v for v in files if files[v].extract(built) != self.files[v].extract(self.prior)},
                         {0x19D40, CODE_VROM, p.SPEC.vrom})
        tables = [bytearray(f[0x19D40].extract(rom)) for f, rom in ((files, built), (self.files, self.prior))]
        for vrom in files:
            a, b = files[vrom], self.files[vrom]
            self.assertEqual((a.index, a.vstart, a.vend), (b.index, b.vstart, b.vend))
            offset = DMA_START-0x19D40+a.index*16+8
            for table in tables: table[offset:offset+8] = bytes(8)
        self.assertEqual(*tables)
        self.assertEqual(report['translation_edits'], self.report['translation_edits'])
        for key in ('runtime_module', 'extended_font', 'extended_items', 'display_names', 'catchphrases',
                    'npc_mail_loader', 'noticeboard', 'inventory_english', 'catalogue_names',
                    'town_suffix', 'shop_item_names'):
            self.assertEqual(report[key], self.report[key], key)
        with self.assertRaisesRegex(ValueError, 'application evidence'):
            p.verify_installation(built, self.native, {**report, 'player_item_names': {}})

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete player-name build required')
    def test_counter_verifies_new_readers_without_premature_family_credit(self):
        from translation_progress import measure
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), report)
        pending = [row for row in ledger.rows.values() if row['source_characters']
                   and any(route['route'] == 'extended_items' for route in row['pending_replacements'])]
        self.assertTrue(pending)
        self.assertTrue(any(not row['replacements'] for row in pending))
        self.assertFalse(any(route['route'] == 'extended_items'
                             for row in pending for route in row['replacements']))
        self.assertEqual(ledger.rows['string:01E4']['replacements'][0]['route'], 'town_suffix')


if __name__ == '__main__': unittest.main()
