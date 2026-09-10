"""Reported RC1 text readers, PM edge wrapping, and complete resource retention."""
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from map_artwork import compile_commands
from rc1_text_hud_fix import (ACTOR, RELOC, NEW_ACTOR, NEW_RELOC, HUD, LABEL, META,
                             RAM, SECTIONS, SOURCE, build, patch_player, patch_hud)
from texture_preview import decode
from title_assets import DATA_BASE


@unittest.skipUnless((ROOT/'build/v1-shop-notice-fix-03/animal-forest-title-preview.z64').is_file(),
                     'Checked RC1 follow-up and supplied sources required')
class RC1TextHudTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1-shop-notice-fix-03/animal-forest-title-preview.z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.files = by_vrom(cls.base)
        with tempfile.TemporaryDirectory(prefix='af-rc1-hud-') as temp:
            cls.commands = compile_commands(Path(temp), SOURCE, (('clock', 56),))['clock']
        cls.image, cls.patch, cls.report = build(cls.native, cls.base, cls.rel, cls.symbols, cls.commands)
        cls.installed = by_vrom(cls.image)

    def test_cash_is_exact_english_gc_pixels_with_native_amount_spacing(self):
        old = self.files[HUD].extract(self.base); new = self.installed[HUD].extract(self.image)
        source = self.rel[DATA_BASE+0x8968A0:DATA_BASE+0x8969A0]
        self.assertEqual(decode(new[0xB7D0:0xB8D0], 32, 16, 'i4'),
                         decode(source, 32, 16, 'i4', gamecube=True))
        self.assertEqual(new[0xB2E0:0xB7D0], old[0xB2E0:0xB7D0])

    def test_pm_descender_does_not_wrap_to_the_right_of_m(self):
        old = self.files[HUD].extract(self.base); new = self.installed[HUD].extract(self.image)
        # PM's first column has p's descender at rows 14/15; its last column
        # is blank there. Bilinear wrap blends in p; clamp blends blank edges.
        pm = old[0x3488:0x3508]
        for y in (14, 15):
            self.assertGreater(pm[y*8] >> 4, 0)
            self.assertEqual(pm[y*8+7] & 15, 0)
        self.assertEqual(new[0x3408:0x3518], old[0x3408:0x3518])
        self.assertEqual(new[0x29E0:0x2B60], old[0x29E0:0x2B60])
        for at in (0x2B8C, 0x2BAC):
            a, b = struct.unpack_from('>I', old, at)[0], struct.unpack_from('>I', new, at)[0]
            self.assertEqual(a ^ b, 0x80200)
            self.assertEqual((b >> 18 & 3, b >> 8 & 3), (2, 2))

    def test_complete_gc_new_player_label_and_native_choice_contract(self):
        old = self.files[ACTOR].extract(self.base); new = self.installed[NEW_ACTOR].extract(self.image)
        self.assertEqual(LABEL, self.rel[DATA_BASE+0x71010:DATA_BASE+0x71017])
        self.assertEqual(new[len(old):], LABEL+bytes(9))
        self.assertEqual(len(new)-len(old), 16)
        self.assertEqual(new[0xC30:0xC34], old[0xC30:0xC34])
        self.assertEqual(new[0xC38:0xC40], old[0xC38:0xC40])
        self.assertEqual(struct.unpack_from('>I', new, 0xC40)[0], 0x24060007)
        reloc = self.installed[NEW_RELOC].extract(self.image)
        self.assertEqual(struct.unpack_from('>5I', reloc), (9376, 592, 64, 0, 188))
        self.assertEqual(reloc[12:], self.files[RELOC].extract(self.base)[12:])
        code = self.installed[CODE_VROM].extract(self.image)
        self.assertEqual(struct.unpack_from('>4I', code, META),
                         (NEW_ACTOR, NEW_ACTOR+len(new), RAM, RAM+len(new)))
        self.assertEqual(self.report['relocation_bases'], ['80200010', '80378010'])

    def test_complete_patch_and_only_the_reviewed_changes(self):
        self.assertEqual(apply_ups(self.native, self.patch), self.image)
        self.assertEqual(len(self.image), 0x2000000)
        moves = {ACTOR: NEW_ACTOR, RELOC: NEW_RELOC}
        self.assertEqual(set(self.installed), {moves.get(v, v) for v in self.files})
        for v, entry in self.files.items():
            new = self.installed[moves.get(v, v)]
            self.assertEqual(entry.index, new.index)
            if v not in (ACTOR, RELOC, HUD, CODE_VROM, 0x19D40):
                self.assertEqual(entry.extract(self.base), new.extract(self.image), hex(v))
        old = self.files[HUD].extract(self.base); new = self.installed[HUD].extract(self.image)
        allowed = set(range(0xB7D0, 0xB8D0)) | set(range(0x2B80, 0x2BB8))
        self.assertTrue(all(a == b or i in allowed for i, (a, b) in enumerate(zip(old, new))))
        old = self.files[CODE_VROM].extract(self.base); new = self.installed[CODE_VROM].extract(self.image)
        self.assertEqual(old[:META]+old[META+16:], new[:META]+new[META+16:])
        self.assertFalse(self.report['save_format_changed'])
        for args in ((self.native, self.base, self.rel, self.symbols+b'\n', self.commands),
                     (self.native, self.base, self.rel, self.symbols, self.commands[:-8]),
                     (self.native, self.native, self.rel, self.symbols, self.commands)):
            with self.assertRaises(ValueError): build(*args)
        with self.assertRaises(ValueError):
            patch_player(self.files[ACTOR].extract(self.base)[:-1], self.files[RELOC].extract(self.base))


if __name__ == '__main__':
    unittest.main()
