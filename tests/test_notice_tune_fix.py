"""Bind tune note identities, remove only date slashes, and retain all other owners."""
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups, sha256
from notice_tune_fix import NOTICE, TUNE, OWNER, BANKS, NOTE_DEST, NOTE_SOURCE, patch_assets, build
from texture_preview import decode
from title_assets import DATA_BASE


@unittest.skipUnless((ROOT/'build/v1-hud-label-fix-02/animal-forest-title-preview.z64').is_file(),
                     'Checked HUD predecessor and supplied sources required')
class NoticeTuneFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/v1-hud-label-fix-02/animal-forest-title-preview.z64').read_bytes()
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        files = by_vrom(cls.base)
        cls.old = {v: files[v].extract(cls.base) for v in BANKS}
        cls.fixed, cls.notes = patch_assets(cls.old, cls.rel, cls.symbols)

    def test_sixteen_melody_indices_keep_pitch_and_use_exact_english_pixels(self):
        self.assertEqual([n['label'] for n in self.notes], list('GABCDEFGABCDE?')+['rest', 'off'])
        for index, (at, src) in enumerate(zip(NOTE_DEST, NOTE_SOURCE)):
            self.assertEqual(decode(self.fixed[TUNE][at:at+128], 16, 16, 'i4'),
                             decode(self.rel[DATA_BASE+src:DATA_BASE+src+128], 16, 16, 'i4', gamecube=True))
            if index >= 14:
                self.assertEqual(self.fixed[TUNE][at:at+128], self.old[TUNE][at:at+128])
        restored = bytearray(self.fixed[TUNE])
        for at in set(NOTE_DEST[:14]): restored[at:at+128] = self.old[TUNE][at:at+128]
        restored[0x3650:0x3690] = self.old[TUNE][0x3650:0x3690]
        self.assertEqual(restored, self.old[TUNE])

    def test_finish_quad_matches_gc_and_date_slash_alone_is_transparent(self):
        verts = list(struct.iter_unpack('>3hH2h4B', self.fixed[TUNE][0x3650:0x3690]))
        self.assertEqual(sorted({v[0] for v in verts}), [74, 106])
        self.assertEqual(sorted({v[1] for v in verts}), [-63, -47])
        for a, b in zip(struct.iter_unpack('>3hH2h4B', self.old[TUNE][0x3650:0x3690]), verts):
            self.assertEqual(a[3], b[3]); self.assertEqual(a[6:], b[6:])
        self.assertEqual(self.fixed[NOTICE][0xCE18:0xCE98], bytes(128))
        self.assertNotEqual(self.old[NOTICE][0xCE18:0xCE98], bytes(128))
        self.assertEqual(self.fixed[NOTICE][:0xCE18], self.old[NOTICE][:0xCE18])
        self.assertEqual(self.fixed[NOTICE][0xCE98:], self.old[NOTICE][0xCE98:])

    def test_complete_rom_patch_and_all_unrelated_data_and_code_retained(self):
        image, patch, report = build(self.native, self.base, self.rel, self.symbols)
        self.assertEqual(sha256(image), 'e968d09b30f29283086423fe29367026a70ce11a6272947c0cb92865b4b19c74')
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(len(image), len(self.base))
        old, new = by_vrom(self.base), by_vrom(image)
        self.assertEqual(set(old), set(new))
        for v, e in old.items():
            self.assertEqual((e.index, e.size), (new[v].index, new[v].size))
            if v != 0x19D40:
                self.assertEqual(new[v].extract(image), self.fixed[v] if v in self.fixed else e.extract(self.base))
        self.assertFalse(report['code_changed']); self.assertFalse(report['save_format_changed'])

    def test_changed_sources_and_active_reader_reject(self):
        changed = dict(self.old); changed[OWNER] = changed[OWNER][:-1]
        for files, rel, symbols in ((changed, self.rel, self.symbols),
                (self.old, self.rel[:-1], self.symbols), (self.old, self.rel, self.symbols+b'\n')):
            with self.assertRaises(ValueError): patch_assets(files, rel, symbols)


if __name__ == '__main__':
    unittest.main()
