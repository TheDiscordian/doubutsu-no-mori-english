"""Reported RC4 menu labels, safe price text, relocation, and complete retention."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, apply_ups, by_vrom
from rc4_menu_labels import (ASSET, CAT, CAT_REL, PARENT, PARENT_AT, RAM, REPAY, REPAY_REL,
                            START, TEXT, build, checked_adapter, compile_adapter, references)
from texture_preview import decode
from title_assets import DATA_BASE


@unittest.skipUnless((ROOT/'build/v1rc4/Animal Forest English V1RC4.z64').is_file(),
                     'Exact RC4 and supplied sources required')
class RC4MenuLabelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1rc4/Animal Forest English V1RC4.z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.files = by_vrom(cls.base)
        with tempfile.TemporaryDirectory(prefix='af-rc4-menu-') as temporary:
            cls.adapter = compile_adapter(Path(temporary)/'adapter')
        cls.image, cls.patch, cls.report = build(cls.native, cls.base, cls.rel, cls.symbols, cls.adapter)
        cls.installed = by_vrom(cls.image)

    def test_currency_matches_complete_gc_image_and_preserves_native_geometry(self):
        old, new = [f[ASSET].extract(r) for f, r in ((self.files, self.base), (self.installed, self.image))]
        self.assertEqual(decode(new[0x4888:0x4988], 32, 16, 'i4'),
                         decode(self.rel[DATA_BASE+0x3E88A0:DATA_BASE+0x3E89A0], 32, 16, 'i4', gamecube=True))
        self.assertEqual(old[:0x4888]+old[0x4988:], new[:0x4888]+new[0x4988:])
        self.assertNotEqual(old[0x4888:0x4988], new[0x4888:0x4988])

    def test_price_buffer_and_numeric_path_are_not_widened(self):
        old, new = self.files[CAT].extract(self.base), self.installed[CAT].extract(self.image)
        self.assertEqual(len(new), START+96)
        self.assertEqual(new[:0x2244]+new[0x2248:START], old[:0x2244]+old[0x2248:])
        self.assertEqual(new[0x2180:0x2188], bytes.fromhex('240600050C026630'))
        self.assertEqual(new[0x2224:0x222C], bytes.fromhex('27A5005024060005'))
        # The adapter's nonzero-price branch skips every argument change and
        # reaches the fixed native font jump directly; no new stack frame.
        code = new[START:START+84]
        words = struct.unpack('>21I', code)
        self.assertEqual(words[:3], (0x8FAE0040, 0x15C00011, 0))
        branch_target = 4+4+4*(words[1] & 65535)
        self.assertEqual(branch_target, 76)
        self.assertEqual(words[branch_target//4:], (0x080243A6, 0))
        self.assertEqual(new[START+84:], b'Not for Sale')
        self.assertEqual(words[5], 0x2406000C)
        writes = [(w >> 26, (w >> 21) & 31, w & 65535) for w in words if w >> 26 in (43, 57)]
        self.assertEqual(writes, [(57, 29, 16), (43, 29, 44), (43, 29, 48)])
        # Only Y and both scale arguments change on the stack; the old text
        # buffer, saved registers, return address, price, and all colours stay.
        self.assertEqual(self.report['catalogue_allocation']['stack_growth'], 0)

    def test_catalogue_relocation_parent_and_reserved_capacity(self):
        old, new = self.files[CAT_REL].extract(self.base), self.installed[CAT_REL].extract(self.image)
        self.assertEqual(struct.unpack_from('>5I', new), (START+96, 0, 0, 0, 152))
        self.assertEqual(new[20:616], old[20:616])
        self.assertEqual(struct.unpack_from('>3I', new, 616),
                         (0x44002244, 0x45000000 | START+12, 0x46000000 | START+16))
        self.assertEqual(len(new), 640)
        before = self.files[PARENT].extract(self.base)
        after = self.installed[PARENT].extract(self.image)
        allowed = set(range(PARENT_AT+4, PARENT_AT+8)) | set(range(PARENT_AT+12, PARENT_AT+16))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(before, after))))
        self.assertEqual(struct.unpack_from('>4I', after, PARENT_AT), (CAT, CAT+START+96, RAM, RAM+START+96))
        allocation = self.report['catalogue_allocation']
        self.assertEqual((allocation['conservative_required_bytes'], allocation['reserved_bytes']), (271168, 274560))
        self.assertEqual(self.installed[CODE_VROM].extract(self.image), self.files[CODE_VROM].extract(self.base))

    def test_repayment_complete_words_length_and_centres_without_transaction_changes(self):
        old = self.files[REPAY].extract(self.base)
        new = self.installed[REPAY].extract(self.image)
        self.assertEqual(new[0xDB4:0xDBD], b'Your Loan')
        self.assertEqual(new[0xDC0:0xDC4], b'OK\0\0')
        self.assertEqual(struct.unpack_from('>I', new, 0x838)[0], 0x24060009)
        self.assertEqual(struct.unpack_from('>I', new, 0x9C4)[0], 0x24060002)
        for at, value in ((0x7C8, 0x3C01431E), (0x988, 0x3C014286)):
            self.assertEqual(struct.unpack_from('>I', new, at)[0], value)
        self.assertLess(abs((158+54*.9375/2)-(133+108*.9375/2)), .5)
        self.assertLess(abs((224+12*.9375/2)-(213+36*.9375/2)), .5)
        allowed = set(range(0xDB4, 0xDBD)) | set(range(0xDC0, 0xDC3))
        for at in (0x7C8, 0x988, 0x9C4): allowed.update(range(at, at+4))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(old, new))))
        self.assertEqual(self.installed[REPAY_REL].extract(self.image), self.files[REPAY_REL].extract(self.base))
        self.assertEqual(self.installed[0xACC000].extract(self.image), self.files[0xACC000].extract(self.base))

    def test_complete_patch_retention_and_source_rejections(self):
        self.assertEqual(apply_ups(self.native, self.patch), self.image)
        self.assertEqual(set(self.files), set(self.installed))
        changed = {CAT, CAT_REL, PARENT, ASSET, REPAY, 0x19D40}
        for v, entry in self.files.items():
            self.assertEqual(entry.index, self.installed[v].index)
            if v not in changed:
                self.assertEqual(entry.extract(self.base), self.installed[v].extract(self.image), hex(v))
        self.assertFalse(self.report['save_format_changed'])
        self.assertFalse(self.report['price_and_repayment_arithmetic_changed'])
        with self.assertRaises(ValueError): references(self.rel, self.symbols+b'\n')
        for offset in (0, 4, 20, 60, 76, 84):
            broken = bytearray(self.adapter); broken[offset] ^= 1
            with self.assertRaises(ValueError): checked_adapter(bytes(broken))
        with self.assertRaises(ValueError): build(self.native, self.native, self.rel, self.symbols, self.adapter)


if __name__ == '__main__':
    unittest.main()
