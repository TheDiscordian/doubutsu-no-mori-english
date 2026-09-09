"""Full event/home names: original arguments, relocation, and complete ROM retention."""
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
import event_item_names as e

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PREVIOUS = ROOT/'build/player-item-names-pilot'
BUILD = ROOT/'build/event-item-names-pilot'


@unittest.skipUnless(ROM.is_file() and (PREVIOUS/'build.json').is_file(), 'Native source and complete player build required')
class EventItemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.prior = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((PREVIOUS/'build.json').read_text())
        cls.files = by_vrom(cls.prior)
        cls.original = {CODE_VROM: cls.files[CODE_VROM].extract(cls.prior)}
        cls.additions = {v: cls.files[v].extract(cls.prior) for v in (MODULE_VROM, ITEMS_VROM)}
        cls.module = cls.report['runtime_module']

    def test_original_item_and_slot_arguments_and_empty_field_are_preserved(self):
        for name, call in e.CALLS.items():
            spec = e.ACTORS[call.actor]
            data, _ = e.source(self.native, call.actor)
            old = struct.unpack_from(f'>{call.size//4}I', data, call.address-spec.ram)
            new = struct.unpack(f'>{call.size//4}I', e.call_body(name))
            self.assertEqual(old[0], e.jump(0x80096740, link=True))
            self.assertEqual(old[-2:], (e.jump(0x8009D88C, link=True), 0x2407000A))
            self.assertEqual(old[-4], 0x24050002 if call.slot == 2 else 0x00002825)
            if old[1] >> 26 == 37:  # Native delay-slot LHU a1 becomes LHU a0.
                self.assertEqual(new[0], (old[1] & ~0x1F0000) | (4 << 16))
            else:
                # Item was already in a1 at the sequence entry, including
                # the opening-Nook branch directly to that original entry.
                self.assertEqual(new[0], 0x00A02025)
            self.assertEqual(new[1:3], (e.jump(e.BRIDGE, link=True), 0x24050000 | call.slot))
            self.assertFalse(any(new[3:]))
            for item in (0, 0x1000, 0x2200, 0xFFFF):
                target, regs = tail_arguments(e.bridge_body(), item, call.slot)
                self.assertEqual((regs[5], regs[29], regs[31]), (call.slot, 0x803FFF00, 0x80123450))
                if item:
                    self.assertEqual((target, regs[4]), (e.IMPORTS['af_quest_set_item'], item))
                else:
                    self.assertEqual((target, regs[4], regs[6], regs[7]),
                                     (e.IMPORTS['af_set_item_str'], 0x80142410, 0x80142410, 0))

    def test_six_actors_change_only_seven_sequences_including_after_relocation(self):
        replacements = dict(self.original)
        evidence = e.install(self.native, replacements, self.additions, self.module)
        self.assertEqual(set(replacements), {CODE_VROM, *[s.vrom for s in e.ACTORS.values()]})
        self.assertEqual(replacements[CODE_VROM], self.original[CODE_VROM])
        self.assertEqual(evidence['extra_allocation_bytes'], 0)
        self.assertFalse(evidence['saved_layout_changes'])
        self.assertEqual(evidence['reference_audit']['external_interior_references'], [])
        for name, spec in e.ACTORS.items():
            old, reloc = e.source(self.native, name)
            expected = bytearray(old)
            for label, call in e.CALLS.items():
                if call.actor == name:
                    offset = call.address-spec.ram
                    expected[offset:offset+call.size] = e.call_body(label)
            self.assertEqual(replacements[spec.vrom], expected)
            for base in (0x801A0010, 0x802F8010):
                a, b = [relocate_verified_data(spec, data, reloc, base) for data in (old, bytes(expected))]
                for label, call in e.CALLS.items():
                    if call.actor != name: continue
                    offset = call.address-spec.ram
                    self.assertEqual(b[offset:offset+call.size], e.call_body(label))
                    a = a[:offset]+e.call_body(label)+a[offset+call.size:]
                self.assertEqual(a, b)

    def test_changed_dependencies_or_last_actor_are_rejected_without_partial_writes(self):
        for at in (e.BRIDGE-8, e.BRIDGE, 0x8009D1F0, 0x800A1820):
            code = bytearray(self.original[CODE_VROM]); code[at-CODE_RAM] ^= 1
            values = {CODE_VROM: bytes(code)}
            before = dict(values)
            with self.assertRaises(ValueError): e.install(self.native, values, self.additions, self.module)
            self.assertEqual(values, before)
        spec = e.ACTORS['opening_nook']
        old, reloc = e.source(self.native, 'opening_nook')
        for vrom, data in ((spec.vrom, old), (spec.relocation, reloc)):
            bad = bytearray(data); bad[0] ^= 1
            values = {**self.original, vrom: bytes(bad)}
            before = dict(values)
            with self.assertRaises(ValueError): e.install(self.native, values, self.additions, self.module)
            self.assertEqual(values, before)
        with self.assertRaises(ValueError): e.install(self.native, dict(self.original), {}, self.module)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete event/home build required')
    def test_complete_cartridge_retains_all_other_text_resources_and_saves(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        files = by_vrom(built)
        e.verify_installation(built, self.native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(files.keys(), self.files.keys())
        self.assertEqual({v for v in files if files[v].extract(built) != self.files[v].extract(self.prior)},
                         {0x19D40, *[s.vrom for s in e.ACTORS.values()]})
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
                    'town_suffix', 'shop_item_names', 'player_item_names'):
            self.assertEqual(report[key], self.report[key], key)
        with self.assertRaisesRegex(ValueError, 'application evidence'):
            e.verify_installation(built, self.native, {**report, 'event_item_names': {}})

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete event/home build required')
    def test_counter_checks_installed_connections_and_retains_unfinished_name_routes(self):
        from translation_progress import measure
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), report)
        pending = [row for row in ledger.rows.values() if row['source_characters']
                   and any(route['route'] == 'extended_items' for route in row['pending_replacements'])]
        self.assertTrue(pending)
        self.assertTrue(any(not row['replacements'] for row in pending))
        self.assertFalse(any(route['route'] == 'extended_items'
                             for row in pending for route in row['replacements']))


if __name__ == '__main__': unittest.main()
