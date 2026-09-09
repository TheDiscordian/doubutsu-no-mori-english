"""Complete identity display helper and four retained-layout conversations."""
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
import conversation_names as n
import text_extension as t
import text_names as p
import secret_actor as s

OUT, BUILD, PRIOR = (ROOT/'build'/name for name in ('text-names', 'conversation-names-pilot', 'fishing-name-pilot'))
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


class IdentityHostTests(unittest.TestCase):
    def test_fallback_bounds_identity_guards_and_atomic_startup(self):
        with tempfile.TemporaryDirectory(prefix='af-text-names-') as tmp:
            target = str(Path(tmp)/'check')
            subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-I', str(ROOT/'overlays/text_extension'),
                str(ROOT/'overlays/text_names/names.c'), str(ROOT/'tests/text_names_check.c'), '-o', target],
                check=True, capture_output=True, timeout=30)
            subprocess.run([target], check=True, capture_output=True, timeout=10)


@unittest.skipUnless((OUT/'extension.json').is_file(), 'Compiled identity text variant required')
class IdentityArtifactTests(unittest.TestCase):
    def test_profile_and_earlier_variants_remain_independently_valid(self):
        for name in ('text-extension', 'text-choices', 'text-names'):
            directory = ROOT/'build'/name; report = json.loads((directory/'extension.json').read_text())
            t.validate((directory/'blob.bin').read_bytes(), (directory/'loader.bin').read_bytes(), report)
        report = json.loads((OUT/'extension.json').read_text())
        for change in ({'identities': False}, {'choices': False}, {'identities': 1}, {'imports': {}}):
            with self.assertRaises(ValueError):
                t.validate((OUT/'blob.bin').read_bytes(), (OUT/'loader.bin').read_bytes(), {**report, **change})
        self.assertEqual(report['blob_bytes'] + 15, 3583)

    def test_original_conversation_frame_colour_and_relocation_are_preserved(self):
        native = ROM.read_bytes(); original, reloc = t.source(native, 'letter'); spec = t.ACTORS['letter']
        data = n.patch('conversation', original); n.validate_relocations('conversation', reloc)
        expected_changes = {address - spec.ram for pair in n.CALLS['conversation'] for address in pair}
        self.assertEqual({i for i in range(0, len(data), 4) if original[i:i+4] != data[i:i+4]}, expected_changes)
        self.assertEqual(n.patch('conversation', data, reverse=True), original)
        word = lambda at: struct.unpack_from('>I', data, at-spec.ram)[0]
        self.assertEqual(word(0x80919BC4), 0x27BDFFA8)
        for at in (0x80919C28, 0x80919D18): self.assertEqual(word(at) & 65535, 1)
        self.assertEqual(0x38+8, 0x40); self.assertEqual(0x40+8, 0x48)
        for base in (0x801A0010, 0x802F8010):
            old = relocate_verified_data(spec, original, reloc, base)
            new = relocate_verified_data(spec, data, reloc, base)
            self.assertEqual(n.patch('conversation', new, reverse=True), old)
        with self.assertRaises(ValueError): n.patch('conversation', data)

    def test_resident_name_uses_existing_sixteen_byte_temporary(self):
        native = ROM.read_bytes(); original, reloc = s.native_sources(native)
        data = n.patch('resident', original); n.validate_relocations('resident', reloc)
        self.assertEqual(n.patch('resident', data, reverse=True), original)
        word = lambda at: struct.unpack_from('>I', data, at-s.RAM)[0]
        self.assertEqual(word(0x8091EA94), 0x27BDFFE0)
        self.assertEqual(word(0x8091EB20), 0x2405000D)
        self.assertEqual(word(0x8091EAE4), 0x24070006)  # Stored player name remains six.
        self.assertLessEqual(0x80921E08+8, 0x80921E18)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete conversation-name cartridge required')
class IdentityCartridgeTests(unittest.TestCase):
    def test_whole_cartridge_patch_and_prior_resources(self):
        native = ROM.read_bytes(); built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes(); report = json.loads((BUILD/'build.json').read_text())
        t.verify_installation(built, native, report)
        from fishing_name import verify_installation
        verify_installation(built, native, report)
        from guide_name import verify_installation
        verify_installation(built, native, report)
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(prior); self.assertEqual(set(files), set(old))
        for vrom in files:
            before, after = old[vrom].extract(prior), files[vrom].extract(built)
            if vrom in (0x19D40, t.VROM): continue
            if vrom == CODE_VROM:
                after = bytearray(after)
                after[t.SETTER-CODE_RAM:t.SETTER_END-CODE_RAM] = before[t.SETTER-CODE_RAM:t.SETTER_END-CODE_RAM]
            elif vrom == n.VROMS['conversation']: after = n.patch('conversation', after, reverse=True)
            elif vrom == n.VROMS['resident']: after = n.patch('resident', after, reverse=True)
            self.assertEqual(after, before, hex(vrom))

    def test_accounting_requires_both_complete_readers_and_no_duplicate_credit(self):
        from translation_progress import measure
        native = ROM.read_bytes(); built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text()); ledger = measure(native, built, report)
        self.assertEqual(ledger.summary()['total_source_characters'], 751284)
        from item_name_readers import resource_only_weight
        self.assertEqual(ledger.summary()['replaced_source_characters'], 720689+resource_only_weight(ledger))
        broken = copy.deepcopy(report); broken['conversation_names']['name_bytes'] = 6
        with self.assertRaises(ValueError): measure(native, built, broken)


if __name__ == '__main__': unittest.main()
