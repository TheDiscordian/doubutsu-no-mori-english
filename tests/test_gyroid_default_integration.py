"""Full default wording, exact scoped permission, actor growth, and cartridge pair."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256, verified_rom
import gyroid_default as text
import gyroid_default_actor as actor
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import Bank, banks
from textcodec import encode, has_japanese, tokenize
from textvalidate import expanded_bound, validate_entry

NATIVE = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/gyroid-default-pilot'


@unittest.skipUnless(NATIVE.is_file(), 'Supplied original cartridge required')
class GyroidDefaultSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(NATIVE.read_bytes()); cls.info = module_command_info(cls.native)
        cls.original = text.native_sources(cls.native)
        cls.full, cls.intro, cls.variant = text.reference_payloads(cls.native, cls.info)
        cls.edit = text.candidate(cls.native, cls.info)

    def test_actual_four_lines_and_complete_introduction_keep_commands_and_boundaries(self):
        self.assertEqual([len(v) for v in self.full.split(b'\xcd')], [18, 27, 22, 22])
        self.assertEqual((len(self.full), sha256(self.full)), (92, text.DEFAULT_SHA256))
        self.assertEqual(self.variant, self.intro.replace(b'\x7f\x40', self.full))
        self.assertEqual((len(self.variant), sha256(self.variant)), (206, text.VARIANT_SHA256))
        commands = lambda data: [t.data for t in tokenize(data, self.info) if t.kind == 'cmd']
        self.assertEqual(commands(self.variant), [c for c in commands(self.intro) if c != b'\x7f\x40'])
        self.assertEqual(self.variant.count(b'\xcd'), self.intro.count(b'\xcd')+3)
        self.assertTrue(self.variant.endswith(bytes.fromhex('CD7F0E0929CD7F01')))
        self.assertIn(b'\x7f\x26', self.variant)
        self.assertFalse(has_japanese(self.variant, self.info))
        self.assertLess(expanded_bound(self.variant, self.info), 1024)

    def test_scoped_permission_rejects_changed_unbound_or_mixed_payloads(self):
        original = self.original['message'][text.SLOT]
        validate_entry(original, self.variant, self.info, 'message', 'gyroid_default',
                       resident_runtime=True, gyroid_default_permit=text.GyroidDefaultPermit())
        for source, replacement, bank, policy, runtime, permit in (
                (original, self.variant, 'message', 'gyroid_default', True, None),
                (original, self.variant, 'message', 'gyroid_default', False, text.GyroidDefaultPermit()),
                (original, self.variant, 'string', 'gyroid_default', True, text.GyroidDefaultPermit()),
                (original, self.variant, 'message', 'exact', True, text.GyroidDefaultPermit()),
                (original+b' ', self.variant, 'message', 'gyroid_default', True, text.GyroidDefaultPermit()),
                (original, self.variant[:-1], 'message', 'gyroid_default', True, text.GyroidDefaultPermit()),
                (original, self.variant, 'message', 'gyroid_default', True,
                 text.GyroidDefaultPermit(encoded_sha256='0'*64))):
            with self.assertRaises(ValueError):
                validate_entry(source, replacement, self.info, bank, policy,
                               resident_runtime=runtime, gyroid_default_permit=permit)
        with self.assertRaises(ValueError):
            validate_entry(original, self.variant, self.info, 'message', 'gyroid_default', resident_runtime=True,
                           gyroid_default_permit=text.GyroidDefaultPermit(), field_permit=object())
        with self.assertRaises(ValueError):
            validate_entry(original, self.variant, self.info, 'message', 'presentation', resident_runtime=True)

    def test_reserve_and_partial_feature_approval_cannot_override_custom_messages(self):
        matches = load_matches(ROOT/'translations/reference_matches.json'); before = deepcopy(matches)
        revised = text.feature_matches(matches)
        self.assertEqual(matches, before); self.assertEqual(matches.keys()-revised.keys(), {text.ID})
        changed = deepcopy(matches); changed[text.ID]['reference_sha256'] = '0'*64
        with self.assertRaises(ValueError): text.feature_matches(changed)
        original = {'id': 'message:0928', 'translation': text.decode(self.intro, self.info)}
        edits = [original, self.edit]
        self.assertEqual(text.permits(self.native, edits, self.info, enabled=True),
                         {text.ID: text.GyroidDefaultPermit()})
        self.assertEqual(text.permits(self.native, [original], self.info, enabled=False), {})
        for rows, enabled in ((edits, False), ([original], True), ([self.edit], True)):
            with self.assertRaises(ValueError): text.permits(self.native, rows, self.info, enabled=enabled)
        changed = deepcopy(edits); changed[0]['translation'] += ' '
        with self.assertRaises(ValueError): text.permits(self.native, changed, self.info, enabled=True)
        changed = deepcopy(edits); changed[-1]['translation'] += ' '
        with self.assertRaises(ValueError): text.permits(self.native, changed, self.info, enabled=True)


@unittest.skipUnless((ROOT/'build/gyroid-default-actor/overlay.json').is_file(), 'Compiled gyroid actor required')
class GyroidDefaultActorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NATIVE.read_bytes(); directory = ROOT/'build/gyroid-default-actor'
        cls.data = (directory/'overlay.bin').read_bytes(); cls.reloc = (directory/'relocation.bin').read_bytes()
        cls.report = json.loads((directory/'overlay.json').read_text())

    def test_independent_compilation_and_relocated_original_prefix(self):
        spec = actor.validate(self.native, self.data, self.reloc, self.report)
        self.assertEqual(spec.resident_bytes, 6976); self.assertEqual(len(self.reloc), 464)
        self.assertEqual(self.report['symbols'], actor.SYMBOLS)
        self.assertEqual(struct.unpack_from('>5I', self.reloc), (6976, 0, 0, 0, 109))
        original, _ = actor.native_sources(self.native)
        self.assertEqual([i for i in range(0, len(original), 4)
                          if original[i:i+4] != self.data[i:i+4]], [actor.HOOK-actor.RAM])
        self.assertEqual(self.data[actor.PREFIX_BYTES:actor.PREFIX_BYTES+112], actor.expected_helper())
        self.assertEqual(sha256(self.data[-64:]), text.SOURCE_SHA256)
        repro = ROOT/'build/gyroid-default-actor-repro'
        for name in ('overlay.bin', 'relocation.bin', 'overlay.json'):
            self.assertEqual((ROOT/'build/gyroid-default-actor'/name).read_bytes(), (repro/name).read_bytes())

    def test_actor_data_instruction_relocation_and_metadata_mutations_fail(self):
        for at in (0, actor.HOOK-actor.RAM, actor.HOOK-actor.RAM+4,
                   actor.PREFIX_BYTES, actor.SYMBOLS['af_gyroid_default_demo'], len(self.data)-1):
            changed = bytearray(self.data); changed[at] ^= 1
            report = deepcopy(self.report); report['overlay_sha256'] = sha256(changed)
            with self.assertRaises(ValueError): actor.validate(self.native, bytes(changed), self.reloc, report)
        changed = bytearray(self.reloc); changed[24] ^= 1
        report = deepcopy(self.report); report['relocation_sha256'] = sha256(changed)
        with self.assertRaises(ValueError): actor.validate(self.native, self.data, bytes(changed), report)
        for key in ('symbols', 'sources', 'elf_relocations'):
            report = deepcopy(self.report); report[key] = {} if key != 'elf_relocations' else []
            with self.assertRaises(ValueError): actor.validate(self.native, self.data, self.reloc, report)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete gyroid-default ROM required')
class GyroidDefaultCartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = NATIVE.read_bytes(); cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.before_dir = ROOT/'build/message-diagnostic-pilot'
        cls.before = (cls.before_dir/'animal-forest-halfwidth.z64').read_bytes()
        cls.previous = json.loads((cls.before_dir/'build.json').read_text())

    def test_complete_pair_patch_only_changed_reserve_and_all_previous_resources_retained(self):
        spec, full = actor.verify_installation(self.built, self.native, self.report['runtime_module'],
                                                self.report['gyroid_default'])
        self.assertEqual((spec.resident_bytes, len(full)), (6976, 92))
        self.assertEqual(sha256(self.built), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)
        old, new = by_vrom(self.before), by_vrom(self.built)
        self.assertEqual(old.keys()-new.keys(), {actor.VROM, actor.RELOCATION})
        self.assertEqual(new.keys()-old.keys(), {actor.NEW_VROM, actor.NEW_RELOCATION})
        self.assertEqual({key for key in old.keys() & new.keys()
                          if old[key].extract(self.before) != new[key].extract(self.built)},
                         {0x19D40, CODE_VROM, 0x02000000, 0xCF9000})
        a, b = [Bank('message', 0x02000000, 0xCF9000, f[0x02000000].extract(rom),
                     f[0xCF9000].extract(rom)).entries() for f, rom in ((old, self.before), (new, self.built))]
        self.assertEqual([i for i, (x, y) in enumerate(zip(a, b, strict=True)) if x != y], [text.SLOT])
        old_code, new_code = old[CODE_VROM].extract(self.before), new[CODE_VROM].extract(self.built)
        lo = actor.METADATA-CODE_RAM
        self.assertEqual(new_code, old_code[:lo]+actor.metadata()+old_code[lo+32:])
        a, b = [{r['id']: r for r in json.loads((ROOT/f'build/{name}-candidates/translations.json').read_text())}
                for name in ('message-diagnostic', 'gyroid-default')]
        self.assertEqual(a.keys(), b.keys()); self.assertEqual([k for k in a if a[k] != b[k]], [text.ID])

    def test_actor_only_install_fails_without_mutating_translation_maps(self):
        files = by_vrom(self.before)
        moves = {int(a, 16): int(b, 16) for a, b in self.previous['vrom_relocations'].items()}
        replacements = {int(v, 16): files[moves.get(int(v, 16), int(v, 16))].extract(self.before)
                        for v in self.previous['replacement_files']}
        additions = {int(v, 16): files[int(v, 16)].extract(self.before) for v in self.previous['added_files']}
        saved = deepcopy((replacements, additions, moves))
        with self.assertRaisesRegex(ValueError, 'Missing complete gyroid default'):
            actor.install(self.native, replacements, additions, moves, self.previous['runtime_module'],
                          ROOT/'build/gyroid-default-actor')
        self.assertEqual((replacements, additions, moves), saved)

    def test_combined_accounting_credits_original_default_once_through_verified_pair(self):
        from translation_progress import measure
        before = measure(self.native, self.before, self.previous)
        after = measure(self.native, self.built, self.report)
        a, b = [{key for key, row in ledger.rows.items() if row['replacements']} for ledger in (before, after)]
        self.assertEqual(b-a, {'string:055C'}); self.assertFalse(a-b)
        self.assertEqual(before.summary()['total_source_characters'], after.summary()['total_source_characters'])
        row = after.rows['string:055C']
        self.assertEqual(row['replacements'], [{'route': 'gyroid_default', 'sha256': text.DEFAULT_SHA256}])
        self.assertEqual(after.summary()['replaced_source_characters']-before.summary()['replaced_source_characters'],
                         row['source_characters'])


if __name__ == '__main__': unittest.main()
