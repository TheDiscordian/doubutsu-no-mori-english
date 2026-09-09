"""Complete shop/Redd name writers, guarded tail paths, and retained actor behaviour."""
import copy
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
from shop_units import PRICE_BIASES
from extended_items import VROM as ITEMS_VROM
import shop_item_names as s

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PREVIOUS = ROOT/'build/town-suffix-pilot'
BUILD = ROOT/'build/shop-item-names-pilot'


def tail_arguments(data, item, slot):
    """Decode only this adapter's integer instructions, including delay slots.

    This is an argument/branch check, not a native emulator or gameplay test.
    Unexpected instructions, memory accesses, and loops fail immediately.
    """
    regs = [0]*32
    regs[4], regs[5], regs[29], regs[31] = item, slot, 0x803FFF00, 0x80123450
    pc, pending = 0, None
    for _ in range(16):
        word = struct.unpack_from('>I', data, pc)[0]
        op, rs, rt, rd = word >> 26, (word >> 21) & 31, (word >> 16) & 31, (word >> 11) & 31
        previous, pending = pending, None
        if word == 0: pass
        elif op == 12: regs[rt] = regs[rs] & (word & 65535)
        elif op == 15: regs[rt] = (word & 65535) << 16
        elif op == 9:
            value = (word & 65535)-(65536 if word & 32768 else 0)
            regs[rt] = (regs[rs]+value) & 0xFFFFFFFF
        elif op == 0 and word & 63 == 37: regs[rd] = regs[rs] | regs[rt]
        elif op == 5:
            value = (word & 65535)-(65536 if word & 32768 else 0)
            pending = pc+4+value*4 if regs[rs] != regs[rt] else pc+8
        elif op == 2: pending = 0x80000000 | ((word & 0x3FFFFFF) << 2)
        else: raise ValueError('Unexpected shop adapter instruction')
        if previous is not None:
            if pending is not None: raise ValueError('Branch in shop adapter delay slot')
            if previous >= len(data): return previous, regs
            pc = previous
        else: pc += 4
    raise ValueError('Shop adapter did not tail-return within its instruction bound')


class ShopArgumentTests(unittest.TestCase):
    def test_full_names_and_empty_item_keep_slot_stack_and_return(self):
        for item in (0, 1, 0x1000, 0x2200, 0xFFFF, 0x10000, 0xFFFF1001, 0xFFFFFFFF):
            for slot in (0, 1, 2, 4, 5, 0x100, 0xFFFFFFFF):
                target, regs = tail_arguments(s.body(), item, slot)
                self.assertEqual((regs[5], regs[29], regs[31]), (slot, 0x803FFF00, 0x80123450))
                if item & 65535:
                    self.assertEqual(target, s.IMPORTS['af_quest_set_item'])
                    self.assertEqual(regs[4], item & 65535)
                else:
                    self.assertEqual(target, s.IMPORTS['af_set_item_str'])
                    self.assertEqual((regs[4], regs[6], regs[7]), (0x80142410, 0x80142410, 0))


@unittest.skipUnless(ROM.is_file() and (PREVIOUS/'build.json').is_file(), 'Supplied source and prior complete build required')
class ShopItemTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.prior = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((PREVIOUS/'build.json').read_text())
        cls.files, cls.source = by_vrom(cls.prior), by_vrom(cls.native)
        cls.original = {CODE_VROM: cls.files[CODE_VROM].extract(cls.prior)}
        cls.additions = {v: cls.files[v].extract(cls.prior) for v in (MODULE_VROM, ITEMS_VROM)}
        cls.module = cls.report['runtime_module']

    def test_six_helpers_and_all_other_actor_bytes_survive_relocation(self):
        replacements = dict(self.original)
        report = s.install(self.native, replacements, self.additions, self.module)
        self.assertEqual(set(replacements), {CODE_VROM, *[spec.vrom for spec in s.ACTORS.values()]})
        self.assertEqual(len(report['actors']), 6)
        self.assertEqual(report['extra_allocation_bytes'], 0)
        self.assertFalse(report['saved_layout_changes'])
        for name, spec in s.ACTORS.items():
            old, reloc = [self.source[v].extract(self.native) for v in (spec.vrom, spec.relocation)]
            at = s.start(spec)-spec.ram
            new = replacements[spec.vrom]
            self.assertEqual(old[:at]+old[at+s.BODY_BYTES:], new[:at]+new[at+s.BODY_BYTES:])
            self.assertEqual(new[at:at+s.BODY_BYTES], s.body())
            for base in (0x801A0010, 0x802F8010):
                a, b = [relocate_verified_data(spec, data, reloc, base,
                                              address_constants=((PRICE_BIASES[spec.vrom],)
                                                                 if spec.vrom in PRICE_BIASES else ()))
                        for data in (old, new)]
                self.assertEqual(a[:at]+a[at+s.BODY_BYTES:], b[:at]+b[at+s.BODY_BYTES:])
                self.assertEqual(b[at:at+s.BODY_BYTES], s.body())
                self.assertEqual(len(b), spec.resident_bytes)
        self.assertEqual(report['reference_audit']['external_interior_references'], [])

    def test_changed_actor_or_dependency_is_rejected_without_partial_writes(self):
        last = list(s.ACTORS.values())[-1]
        for vrom in (last.vrom, last.relocation, CODE_VROM):
            values = dict(self.original)
            raw = bytearray(self.source[vrom].extract(self.native) if vrom != CODE_VROM else values[vrom])
            at = 0x800A1820-CODE_RAM if vrom == CODE_VROM else 0
            raw[at] ^= 1
            values[vrom] = bytes(raw)
            before = dict(values)
            with self.assertRaises(ValueError): s.install(self.native, values, self.additions, self.module)
            self.assertEqual(values, before)
        for missing in (MODULE_VROM, ITEMS_VROM):
            with self.assertRaises(ValueError):
                s.install(self.native, dict(self.original), {k:v for k,v in self.additions.items() if k != missing}, self.module)
        altered = copy.deepcopy(self.module)
        altered['symbols']['af_quest_set_item'] = '80196818'
        with self.assertRaises(ValueError): s.install(self.native, dict(self.original), self.additions, altered)
        additions = dict(self.additions)
        raw = bytearray(additions[MODULE_VROM]); raw[0x500] ^= 1; additions[MODULE_VROM] = bytes(raw)
        with self.assertRaises(ValueError): s.install(self.native, dict(self.original), additions, self.module)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete shop-name build required')
    def test_complete_cartridge_retains_every_other_resource_and_patch(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        files = by_vrom(built)
        s.verify_installation(built, self.native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(files.keys(), self.files.keys())
        self.assertEqual({v for v in files if files[v].extract(built) != self.files[v].extract(self.prior)},
                         {0x19D40, *[spec.vrom for spec in s.ACTORS.values()]})
        # Appending the newly patched actors moves physical file addresses.
        # The self-containing DMA file may change only those address pairs;
        # every virtual identity, size, row, and other byte remains unchanged.
        tables = [bytearray(f[0x19D40].extract(rom)) for f, rom in ((files, built), (self.files, self.prior))]
        for vrom in files:
            a, b = files[vrom], self.files[vrom]
            self.assertEqual((a.index, a.vstart, a.vend), (b.index, b.vstart, b.vend))
            at = DMA_START-0x19D40+a.index*16+8
            for table in tables: table[at:at+8] = bytes(8)
        self.assertEqual(*tables)
        self.assertEqual(report['translation_edits'], self.report['translation_edits'])
        for key in ('runtime_module', 'extended_font', 'extended_items', 'display_names', 'catchphrases',
                    'npc_mail_loader', 'noticeboard', 'inventory_english', 'catalogue_names', 'town_suffix'):
            self.assertEqual(report[key], self.report[key], key)
        with self.assertRaisesRegex(ValueError, 'application evidence'):
            s.verify_installation(built, self.native, {**report, 'shop_item_names': {}})


if __name__ == '__main__': unittest.main()
