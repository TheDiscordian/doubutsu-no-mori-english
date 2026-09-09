"""English map wording, two-line layout, retained cache, and cartridge evidence."""
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
from aflib import by_vrom, apply_ups, sha256, CODE_VROM
from npc_mail_show import relocate_verified_data
import map_labels as l
import map_names as m

OUT, BUILD, PRIOR = (ROOT/'build'/name for name in ('map-labels-overlay', 'map-labels-pilot', 'guide-name-pilot'))


class MapLabelCoreTests(unittest.TestCase):
    def test_exact_lines_coordinates_arguments_and_bounds_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-map-labels-') as tmp:
            target = str(Path(tmp)/'check')
            subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            str(ROOT/'overlays/map/labels.c'), str(ROOT/'tests/map_labels_check.c'),
                            '-o', target], check=True, capture_output=True, timeout=30)
            subprocess.run([target], check=True, capture_output=True, timeout=10)


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Compiled map-label overlay required')
class MapLabelArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()
        cls.base = (ROOT/'build/map-names-overlay/overlay.bin').read_bytes()
        cls.base_reloc = (ROOT/'build/map-names-overlay/relocation.bin').read_bytes()
        cls.base_report = json.loads((ROOT/'build/map-names-overlay/overlay.json').read_text())

    def test_reference_words_line_positions_and_unchanged_name_cache(self):
        m.validate(self.native, self.data, self.reloc, self.report, self.module)
        self.assertEqual(self.data[m.PREFIX:l.BASE_SIZE], self.base[m.PREFIX:])
        self.assertEqual(self.data[l.EMPTY-m.RAM:l.EMPTY-m.RAM+6], b'free  ')
        self.assertEqual(struct.unpack_from('>I', self.data, l.OLD_POST_DRAW-m.RAM)[0], 0)
        for i, words in enumerate(l.WORDS, 2):
            at = 0x8088FF20+i*28-m.RAM
            x, y = struct.unpack_from('>2f', self.data, at+8)
            self.assertEqual((x, y), (-83.0, -19.0 if words[1] else -25.0))
            pointer, length = struct.unpack_from('>2I', self.data, at+20)
            self.assertEqual(length, len(words[0]))
            self.assertEqual(self.data[pointer-m.RAM:pointer-m.RAM+16],
                             words[0].ljust(8, b'\0')+words[1].ljust(8, b'\0'))
        allowed = set(range(l.EMPTY-m.RAM, l.EMPTY-m.RAM+6))
        for at in (l.DRAW, l.OLD_POST_DRAW): allowed.update(range(at-m.RAM, at-m.RAM+4))
        for i in range(2,8):
            at = 0x8088FF20+i*28-m.RAM
            for off, length in ((12,4), (20,8)): allowed.update(range(at+off, at+off+length))
        changed = {i for i in range(l.BASE_SIZE) if self.data[i] != self.base[i]}
        self.assertLessEqual(changed, allowed)

    def test_two_base_relocation_preserves_helpers_and_moves_new_data(self):
        old_spec = m.validate(self.native, self.base, self.base_reloc, self.base_report, self.module)
        spec = m.validate(self.native, self.data, self.reloc, self.report, self.module)
        for base in (0x801A0000, 0x802F8010):
            old = relocate_verified_data(old_spec, self.base, self.base_reloc, base)
            new = relocate_verified_data(spec, self.data, self.reloc, base)
            self.assertEqual(new[m.PREFIX:l.BASE_SIZE], old[m.PREFIX:])
            for i in range(2,8):
                at = 0x8088FF20+i*28-m.RAM+20
                self.assertEqual(struct.unpack_from('>I', new, at)[0], base+l.APPROVED['symbols']['af_map_labels']+(i-2)*16)
            self.assertEqual(struct.unpack_from('>I', new, l.DRAW-m.RAM)[0],
                             0x0C000000 | ((base+l.BASE_SIZE) >> 2) & 0x3FFFFFF)
            for at, kind, target, _ in l.APPROVED['elf_relocations']:
                if kind == 4: self.assertEqual(struct.unpack_from('>I', new, at)[0] & 0x3FFFFFF, target >> 2 & 0x3FFFFFF)
            high = struct.unpack_from('>I', new, 26820)[0] & 65535
            low = struct.unpack_from('>I', new, 26824)[0] & 65535
            self.assertEqual((high << 16)+(low-65536 if low & 32768 else low), base+27056)
            self.assertEqual(struct.unpack_from('>f', new, 27056)[0], 12.0)

    def test_forged_profiles_or_rehashed_damage_are_rejected(self):
        for at in (l.DRAW-m.RAM, l.EMPTY-m.RAM, m.START, l.BASE_SIZE, 26960):
            data = bytearray(self.data); data[at] ^= 1
            with self.assertRaises(ValueError):
                m.validate(self.native, bytes(data), self.reloc, {**self.report, 'overlay_sha256': sha256(data)}, self.module)
        report = copy.deepcopy(self.report); report['labels'] = False
        with self.assertRaises(ValueError): m.validate(self.native, self.data, self.reloc, report, self.module)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete map-label cartridge required')
class MapLabelCartridgeTests(unittest.TestCase):
    def test_new_labels_credit_eight_original_records_once(self):
        from translation_progress import measure
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        ledgers = []
        for path in (PRIOR, BUILD):
            report = json.loads((path/'build.json').read_text())
            ledgers.append(measure(native, (path/'animal-forest-halfwidth.z64').read_bytes(), report))
        before, after = ledgers
        ids = [key for key in after.rows if key.startswith('ui_map:')]
        self.assertEqual(len(ids), 8)
        self.assertEqual(sum(after.rows[key]['source_characters'] for key in ids), 28)
        self.assertTrue(all(not before.rows[key]['replacements'] and after.rows[key]['replacements'] for key in ids))
        self.assertEqual(before.summary()['total_source_characters'], after.summary()['total_source_characters'])
        self.assertEqual(after.summary()['replaced_source_characters']-before.summary()['replaced_source_characters'], 28)
        self.assertEqual(after.summary()['total_source_characters'], 751284)

    def test_whole_patch_and_every_other_translation_payload(self):
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        m.verify_shared_parts(built, native, report['runtime_module'], report['map_names'])
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(prior)
        self.assertEqual(set(files), set(old))
        for v in files:
            if v not in (0x19D40, m.OWNER, m.NEW_VROM, m.NEW_RELOC):
                self.assertEqual(files[v].extract(built), old[v].extract(prior), hex(v))
        owner = bytearray(old[m.OWNER].extract(prior))
        owner[m.OWNER_AT:m.OWNER_AT+32] = m.metadata(l.APPROVED['bytes'])
        self.assertEqual(files[m.OWNER].extract(built), owner)
        self.assertEqual(files[CODE_VROM].extract(built), old[CODE_VROM].extract(prior))


if __name__ == '__main__': unittest.main()
