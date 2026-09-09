"""Focused complete menu text, relocation, and installed-credit checks."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_VROM
import inventory_english as inv
import inventory_menu_text as menu
import catalogue_names as catalogue
from npc_mail_show import relocate_verified_data

OUT = ROOT/'build/inventory-menu-text-overlay'
BUILD = ROOT/'build/inventory-menu-text-pilot'
PREVIOUS = ROOT/'build/catalogue-names-pilot'


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Compiled menu text required')
class MenuTextArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()
        cls.base = (ROOT/'build/inventory-english-overlay/overlay.bin').read_bytes()
        cls.base_reloc = (ROOT/'build/inventory-english-overlay/relocation.bin').read_bytes()

    def test_complete_text_native_buffers_and_preserved_base(self):
        inv.validate(self.native, self.data, self.reloc, self.report, self.module)
        self.assertEqual(menu.change_prefix(self.native, self.data[:menu.BASE_SIZE], reverse=True), self.base)
        values = menu.reference_texts()
        self.assertEqual(len(values), 13)
        self.assertEqual(values[5], b'Stationery')
        self.assertEqual(values[9:], [b'Present', b'Throw it out?', b'Are you', b'really sure?'])
        for source, value in zip(menu.SOURCES, values):
            self.assertEqual(self.data[source[3]:source[3]+source[4]], value)
        # The old initializer, saved/sender fields, and action records stay intact.
        self.assertEqual(self.data[inv.PREFIX:menu.CODE_AT], self.base[inv.PREFIX:])
        for a, b in ((0x8086FD90, 0x8086FDB8), (0x80870064, 0x808701C8)):
            self.assertEqual(self.data[a-inv.RAM:b-inv.RAM], self.base[a-inv.RAM:b-inv.RAM])
        for index in range(9):
            # Bound arithmetic changed from index*6 to index*10; all rows fit
            # the unchanged ten-byte destination plus original cleared padding.
            at = menu.CATEGORY_AT+((index << 2)+index)*2
            destination = bytearray(b'!'+b' '*16+b'!')
            destination[1:11] = self.data[at:at+10]
            self.assertEqual(destination, b'!'+values[index]+b' '*6+b'!')
        self.assertEqual(menu.cells(self.native, values[10]), 7)
        self.assertTrue(all(menu.cells(self.native, v) <= 6 for v in values[11:]))

    def test_assembled_width_clamp_only_enlarges_question_window(self):
        words = struct.unpack('>8I', (OUT/'clamp.bin').read_bytes())
        self.assertEqual(words, (0x8C880000, 0x29010007, 0x10200003, 0, 0x24080007,
                                 0xAC880000, 0x0821BEE2, 0))
        # Execute the actual fixed arithmetic/branch words on the host. This
        # small instruction model is not native-emulator execution evidence.
        for original_width in range(17):
            reg = [0]*32; reg[4] = 0x100; memory = {0xFC: 0xA5, 0x100: original_width, 0x104: 123}
            pc, destination, written = 0, None, []
            for _ in range(8):
                word = words[pc//4]; op, rs, rt, imm = word >> 26, (word >> 21) & 31, (word >> 16) & 31, word & 65535
                if op == 35: reg[rt] = memory[reg[rs]+imm]
                elif op == 10: reg[rt] = int(reg[rs] < imm)
                elif op == 4:
                    self.assertEqual(words[pc//4+1], 0)
                    pc += 4+imm*4 if reg[rs] == reg[rt] else 8
                    continue
                elif op == 9: reg[rt] = reg[rs]+imm
                elif op == 43:
                    memory[reg[rs]+imm] = reg[rt]; written.append(reg[rs]+imm)
                elif op == 2:
                    self.assertEqual(words[pc//4+1], 0)
                    destination = 0x80000000 | (word & 0x3FFFFFF) << 2
                    break
                else: self.fail('Unexpected instruction in bounded width clamp')
                pc += 4
            self.assertEqual(destination, 0x8086FB88)
            self.assertEqual(memory, {0xFC: 0xA5, 0x100: max(original_width, 7), 0x104: 123})
            self.assertEqual(written, [0x100] if original_width < 7 else [])
        self.assertEqual(self.data[0x8086FB7C-inv.RAM:0x8086FB80-inv.RAM], bytes.fromhex('ace90000'))

    def test_three_relocation_bases_preserve_native_prefix_and_all_string_pointers(self):
        spec = menu.validate(self.native, self.data, self.reloc, self.report, self.module)
        old_spec = inv.Image(inv.RAM, menu.BASE_SIZE, struct.unpack_from('>5I', self.base_reloc))
        patched = set(menu.patched_words(self.native))
        for base in (0x801A0000, 0x802F8010, (0x80400000-menu.SIZE) & ~15):
            new = relocate_verified_data(spec, self.data, self.reloc, base)
            old = relocate_verified_data(old_spec, self.base, self.base_reloc, base)
            for at in range(0, menu.BASE_SIZE, 4):
                if at+inv.RAM not in patched: self.assertEqual(new[at:at+4], old[at:at+4])
            for hi, lo, _, target in menu.POINTERS:
                h, l = (struct.unpack_from('>I', new, at-inv.RAM)[0] for at in (hi, lo))
                pointer = ((h & 65535) << 16)+(l & 65535)-(65536 if l & 32768 else 0)
                self.assertEqual(pointer, base+target)
            for at, target, link in ((0x8086FB78-inv.RAM, menu.CODE_AT, False),
                                      (0x808702AC-inv.RAM, inv.APPROVED['symbols']['af_tag_cells'], True),
                                      (menu.CODE_AT+24, 0x8086FB88-inv.RAM, False)):
                self.assertEqual(struct.unpack_from('>I', new, at)[0],
                                 (0x0C000000 if link else 0x08000000) | ((base+target) >> 2) & 0x3FFFFFF)

    def test_rehashed_partial_profiles_and_unsafe_allocation_are_rejected(self):
        for at in (0, 0x808781D4-inv.RAM, inv.START, menu.CODE_AT, menu.CATEGORY_AT, menu.PRESENT_AT, menu.SIZE-1):
            data = bytearray(self.data); data[at] ^= 1
            report = copy.deepcopy(self.report); report['overlay_sha256'] = sha256(data)
            with self.assertRaises(ValueError): menu.validate(self.native, data, self.reloc, report, self.module)
        report = copy.deepcopy(self.report); report['menu_text'] = False
        with self.assertRaises(ValueError): inv.validate(self.native, self.data, self.reloc, report, self.module)
        self.assertEqual(inv.allocation(menu.SIZE)['tag_growth'], 1088)
        self.assertEqual(inv.allocation(menu.SIZE)['shared_growth_used'], 6656)
        self.assertEqual(catalogue.allocation(menu.SIZE)['alternative_required'], 202432)
        with self.assertRaises(ValueError): inv.allocation(menu.SIZE+8192)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete menu text cartridge required')
class MenuTextCartridgeTests(unittest.TestCase):
    def test_current_rom_patch_and_all_unrelated_data_are_retained(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        prior = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        inv.verify_shared_parts(built, native, report['runtime_module'], report['inventory_english'])
        catalogue.verify_shared_parts(built, native, report['runtime_module'], report['catalogue_names'])
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(prior)
        self.assertEqual(files.keys(), old.keys())
        for v in files:
            if v not in (0x19D40, inv.OWNER, inv.NEW_VROM, inv.NEW_RELOC):
                self.assertEqual(files[v].extract(built), old[v].extract(prior), hex(v))
        self.assertEqual(files[CODE_VROM].extract(built), old[CODE_VROM].extract(prior))

    def test_all_thirteen_original_ids_gain_credit_once_and_other_credit_is_unchanged(self):
        from translation_progress import measure
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        ledgers = [measure(native, (p/'animal-forest-halfwidth.z64').read_bytes(),
                           json.loads((p/'build.json').read_text())) for p in (PREVIOUS, BUILD)]
        before, after = ledgers
        ids = {'ui_inventory_text:'+s[0] for s in menu.SOURCES}
        self.assertEqual(len(ids), 13)
        self.assertEqual(before.rows.keys(), after.rows.keys())
        for key in before.rows.keys()-ids: self.assertEqual(before.rows[key], after.rows[key], key)
        weight = 0
        for key in ids:
            a, b = before.rows[key], after.rows[key]
            self.assertFalse(a['replacements'])
            self.assertEqual([r['route'] for r in b['replacements']], ['inventory_menu_text'])
            for field in ('source_sha256', 'source_category', 'source_characters'): self.assertEqual(a[field], b[field])
            self.assertGreater(a['source_characters'], 0); weight += a['source_characters']
        self.assertEqual(before.summary()['total_source_characters'], after.summary()['total_source_characters'])
        self.assertEqual(after.summary()['replaced_source_characters']-before.summary()['replaced_source_characters'], weight)


if __name__ == '__main__': unittest.main()
