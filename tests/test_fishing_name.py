"""Save-safe exact fishing winner names, relocation, and cartridge retention."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from npc_mail_show import relocate_verified_data
import fishing_name as f

OUT, BUILD, PRIOR = (ROOT/'build'/name for name in ('fishing-name-overlay', 'fishing-name-pilot', 'map-labels-pilot'))
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Compiled fishing name reader required')
class FishingNameArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()

    def test_exact_lookup_type_guards_and_read_only_inputs_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-fishing-name-') as tmp:
            directory = Path(tmp); target = directory/'check'
            # Generated host fixture embeds the same locally verified alias resource.
            aliases = (OUT/'aliases.bin').read_bytes(); self.assertEqual(sha256(aliases), f.ALIASES_SHA)
            (directory/'aliases.bin').write_bytes(aliases)
            (directory/'aliases.s').write_text('.section .rodata\n.global af_fishing_aliases\n'
                'af_fishing_aliases:\n.incbin "aliases.bin"\n.section .note.GNU-stack,"",@progbits\n')
            subprocess.run(['gcc', '-std=c99', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                            '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                            str(ROOT/'overlays/fishing/name.c'), str(ROOT/'tests/fishing_name_check.c'),
                            'aliases.s', '-o', str(target)], cwd=directory, check=True, capture_output=True, timeout=30)
            subprocess.run([str(target)], check=True, capture_output=True, timeout=10)

    def test_only_display_call_changes_and_native_bss_is_preserved(self):
        f.validate(self.native, self.data, self.reloc, self.report)
        original, _ = f.source(self.native)
        changes = {f.RAM+i for i in range(0, f.PREFIX, 4) if self.data[i:i+4] != original[i:i+4]}
        self.assertEqual(changes, {f.CALL})
        self.assertEqual(self.data[f.PREFIX:f.START], bytes(16))
        word = lambda address: struct.unpack_from('>I', self.data, address-f.RAM)[0]
        self.assertEqual(word(0x80A90320), 0x24070006)
        self.assertEqual(word(0x80A90300), f.jump(0x8009D6D0, link=True))
        self.assertEqual(word(0x80A902CC), 0x27BDFFC8)
        self.assertIn('af_fishing_name\t24\tstatic', self.report['stack_usage'])
        self.assertIn('af_fishing_resolve\t0\tstatic', self.report['stack_usage'])

    def test_two_base_relocation_preserves_native_data_and_fixed_setter(self):
        original, original_reloc = f.source(self.native)
        spec = f.validate(self.native, self.data, self.reloc, self.report)
        for base in (0x801A0010, 0x802F8010):
            old = relocate_verified_data(f.Image(f.RAM, f.START, f.SECTIONS), original, original_reloc, base)
            new = relocate_verified_data(spec, self.data, self.reloc, base)
            for at in range(0, f.PREFIX, 4):
                if at != f.CALL-f.RAM: self.assertEqual(new[at:at+4], old[at:at+4])
            word = lambda at: struct.unpack_from('>I', new, at)[0]
            self.assertEqual(word(f.CALL-f.RAM), f.jump(base+3572, link=True))
            self.assertEqual(word(3612), f.jump(base+3312, link=True))
            self.assertEqual(word(3656), f.jump(0x8009D6D0))
            high, low = word(3600) & 65535, word(3604) & 65535
            self.assertEqual((high << 16)+(low-65536 if low & 32768 else low), base+3680+64)
            self.assertEqual(new[3680:], self.data[3680:])

    def test_altered_code_aliases_and_profiles_are_rejected(self):
        for at in (0, f.CALL-f.RAM, f.PREFIX, f.START, 3680, 4000):
            data = bytearray(self.data); data[at] ^= 1
            with self.assertRaises(ValueError):
                f.validate(self.native, data, self.reloc, {**self.report, 'overlay_sha256': sha256(data)})
        report = copy.deepcopy(self.report); report['symbols']['af_fishing_name'] += 4
        with self.assertRaises(ValueError): f.validate(self.native, self.data, self.reloc, report)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete fishing-name cartridge required')
class FishingNameCartridgeTests(unittest.TestCase):
    def test_complete_patch_and_every_prior_translation(self):
        native = ROM.read_bytes(); built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        f.verify_installation(built, native, report)
        from guide_name import verify_installation
        verify_installation(built, native, report)
        from text_extension import verify_installation
        verify_installation(built, native, report)
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(prior)
        self.assertEqual(set(old)-set(files), {f.VROM, f.RELOC})
        self.assertEqual(set(files)-set(old), {f.NEW_VROM, f.NEW_RELOC})
        for v in files.keys() & old.keys():
            if v not in (0x19D40, CODE_VROM): self.assertEqual(files[v].extract(built), old[v].extract(prior), hex(v))
        code = bytearray(old[CODE_VROM].extract(prior))
        code[f.METADATA-CODE_RAM:f.METADATA-CODE_RAM+32] = f.metadata()
        self.assertEqual(files[CODE_VROM].extract(built), code)

    def test_accounting_verifies_reader_without_duplicate_name_credit(self):
        from translation_progress import measure, pending_name_consumers
        native = ROM.read_bytes(); built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text()); ledger = measure(native, built, report)
        self.assertEqual(ledger.summary()['total_source_characters'], 751284)
        from item_name_readers import resource_only_weight
        self.assertEqual(ledger.summary()['replaced_source_characters'], 720689+resource_only_weight(ledger))
        self.assertIn('saved fishing-winner name is connected', pending_name_consumers(report)['display_names'])
        broken = copy.deepcopy(report); broken['fishing_name']['player_name_bytes'] = 8
        with self.assertRaises(ValueError): measure(native, built, broken)


if __name__ == '__main__': unittest.main()
