"""Focused inventory integration checks; no new exhaustive native harness."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
import inventory_english as inv
import mail_menu as old
from aflib import by_vrom, sha256, CODE_VROM
from npc_mail_show import relocate_verified_data
from aflib import apply_ups

OUT = ROOT/'build/inventory-english-overlay'
BUILD = ROOT/'build/inventory-english-pilot'
PREVIOUS = ROOT/'build/hboard-editor-pilot'


class InventoryCoreTests(unittest.TestCase):
    def test_real_helper_bounds_widths_and_sixteen_byte_destination_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-inventory-host-') as tmp:
            target = str(Path(tmp)/'check')
            subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            str(ROOT/'overlays/tag/labels.c'), str(ROOT/'tests/inventory_english_check.c'),
                            '-o', target], check=True, capture_output=True, timeout=30)
            subprocess.run([target], check=True, capture_output=True, timeout=10)


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Local inventory overlay required')
class InventoryArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()
        cls.original, cls.old_reloc, _, _ = inv.native_sources(cls.native)

    def test_complete_labels_native_actions_and_all_pointer_arrays(self):
        inv.validate(self.native, self.data, self.reloc, self.report, self.module)
        labels = inv.reference_labels()
        self.assertEqual(len(labels), 39)
        self.assertEqual(labels[20].rstrip(), b'Spread on Floor')
        self.assertEqual(labels[7].rstrip(), b'Put on Wall')
        self.assertEqual(labels[36].rstrip(), b'Delete')
        start = inv.APPROVED['symbols']['af_tag_labels']
        for i, label in enumerate(labels):
            self.assertEqual(self.data[start+i*20:start+i*20+16], label)
            at = inv.LABEL_FIRST-inv.RAM+i*12
            self.assertEqual(self.data[start+i*20+16:start+i*20+20], self.original[at+8:at+12])
        for definition in old.definitions(self.original):
            for i, row in enumerate(definition['options']):
                at = definition['pointer']-inv.RAM+i*4
                index = (row['pointer']-inv.LABEL_FIRST)//12
                self.assertEqual(struct.unpack_from('>I', self.data, at)[0], inv.RAM+start+index*20)
        # Full-name storage is the exact contiguous, cleared 10+6-byte span;
        # the original type-zero branch and separate mail/quest path stay intact.
        for a, b in ((0x8086FD90, 0x8086FDB8), (0x80870064, 0x808701C8)):
            self.assertEqual(self.data[a-inv.RAM:b-inv.RAM], self.original[a-inv.RAM:b-inv.RAM])

    def test_native_relocation_preserves_unchanged_code_bss_and_callbacks(self):
        spec = inv.validate(self.native, self.data, self.reloc, self.report, self.module)
        original_spec = inv.Image(inv.RAM, inv.START, old.SECTIONS)
        changes = {at for at in range(0, inv.PREFIX, 4)
                   if self.data[at:at+4] != self.original[at:at+4]}
        for base in (0x801A0000, 0x802F8010, (0x80400000-len(self.data)) & ~15):
            prior = relocate_verified_data(original_spec, self.original, self.old_reloc, base)
            moved = relocate_verified_data(spec, self.data, self.reloc, base)
            for at in range(0, inv.PREFIX, 4):
                if at not in changes: self.assertEqual(moved[at:at+4], prior[at:at+4])
            self.assertEqual(moved[inv.PREFIX:inv.START], bytes(inv.BSS))
            for at, (name, _) in inv.HOOKS.items():
                self.assertEqual(struct.unpack_from('>I', moved, at-inv.RAM)[0],
                                 0x0C000000 | ((base+inv.APPROVED['symbols'][name]) >> 2) & 0x3FFFFFF)
            for i in range(len(inv.LABEL_NAMES)):
                callback = struct.unpack_from('>I', self.original, inv.LABEL_FIRST-inv.RAM+i*12+8)[0]
                at = inv.APPROVED['symbols']['af_tag_labels']+i*20+16
                self.assertEqual(struct.unpack_from('>I', moved, at)[0], base+callback-inv.RAM if callback else 0)
            # Fixed main-code loader must not be shifted with the tag overlay.
            at = inv.APPROVED['symbols']['af_tag_load_item']
            self.assertEqual(moved[at:at+12], self.data[at:at+12])

    def test_rehashed_mutations_and_wrong_module_are_rejected(self):
        for at in (0, 0x80876D04-inv.RAM, inv.PREFIX, inv.START, inv.APPROVED['symbols']['af_tag_labels']):
            data = bytearray(self.data); data[at] ^= 1
            report = {**self.report, 'overlay_sha256': sha256(data)}
            with self.assertRaises(ValueError): inv.validate(self.native, bytes(data), self.reloc, report, self.module)
        reloc = self.reloc[:-1]+bytes([self.reloc[-1]^1])
        with self.assertRaises(ValueError):
            inv.validate(self.native, self.data, reloc, {**self.report, 'relocation_sha256': sha256(reloc)}, self.module)
        module = copy.deepcopy(self.module); module['symbols']['af_load_item_name'] = '801969CC'
        with self.assertRaises(ValueError): inv.validate(self.native, self.data, self.reloc, self.report, module)

    def test_actual_allocation_is_within_existing_reservation(self):
        pool = inv.allocation()
        self.assertEqual(pool, {'tag_growth': 896, 'editor_growth': 5568,
                               'shared_growth_used': 6464, 'shared_growth_reserved': 8192,
                               'combined_pool': 243072})


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete inventory pilot required')
class InventoryCartridgeTests(unittest.TestCase):
    def test_combined_counter_inventories_original_labels_once_and_requires_installation(self):
        from translation_progress import measure
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        ledgers = []
        for path in (PREVIOUS, BUILD):
            report = json.loads((path/'build.json').read_text())
            ledger = measure(native, (path/'animal-forest-halfwidth.z64').read_bytes(), report)
            ledgers.append(ledger)
        prior, current = ledgers
        ids = {f'ui_inventory_label:{i:04X}' for i in range(39)}
        self.assertEqual({k for k in current.rows if k.startswith('ui_inventory_label:')}, ids)
        self.assertEqual(prior.rows.keys(), current.rows.keys())
        for key in current.rows.keys()-ids:
            self.assertEqual(prior.rows[key], current.rows[key], key)
        weight = 0
        for key in ids:
            before, after = prior.rows[key], current.rows[key]
            for field in ('source_sha256', 'source_category', 'source_characters'):
                self.assertEqual(before[field], after[field])
            self.assertFalse(before['replacements'])
            self.assertEqual([r['route'] for r in after['replacements']], ['inventory_english'])
            weight += before['source_characters']
        self.assertGreater(weight, 0)
        self.assertEqual(current.summary()['total_source_characters'], prior.summary()['total_source_characters'])
        self.assertEqual(current.summary()['replaced_source_characters']-prior.summary()['replaced_source_characters'], weight)

    def test_full_patch_preserves_all_unrelated_translation_resources_and_shared_owners(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        inv.verify_shared_parts(built, native, report['runtime_module'], report['inventory_english'])
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old_files = by_vrom(built), by_vrom(previous)
        for vrom in files.keys() & old_files.keys():
            if vrom not in (0x19D40, inv.OWNER):
                self.assertEqual(files[vrom].extract(built), old_files[vrom].extract(previous), f'{vrom:08X}')
        self.assertEqual(files[CODE_VROM].extract(built), old_files[CODE_VROM].extract(previous))


if __name__ == '__main__': unittest.main()
