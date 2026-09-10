"""The N64 species correction agrees across complete word and dialogue sources."""

from copy import deepcopy
from dataclasses import replace
import json
import struct
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256, verified_rom
from gc_text import decoder_tables
from item_articles import SIZE
from native_species import NATIVE_ID, NATIVE_SHA256, DONOR, ENGLISH, correct_word
from npc_mail_capture import WORD_HASH, DESIGN_WORD_HASH, verified_resources, validate, word_guard_offset
from npc_mail_words import prepare, unpack_words, pack_words
from runtime_module import module_command_info
from shared_npc_words import validated_values
from textbanks import Bank, banks
from textcodec import encode, tokenize

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
BUILD = ROOT/'build/design-items-pilot'
CREATOR = ROOT/'build/design-items-creator'


@unittest.skipUnless((ROOT/'build/design-items-words/words.bin').is_file(), 'Local corrected complete words required')
class NativeSpeciesSourceTests(unittest.TestCase):
    def test_all_source_banks_rebuild_with_only_the_native_species_word_corrected(self):
        native = next(b for b in banks(ROM.read_bytes()) if b.name == 'string')
        legacy = next(b for b in banks((ROOT/'build/inspect/legacy.z64').read_bytes(), legacy=True) if b.name == 'string')
        path = ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
        reference = Bank('string', 0, 0, (path/'string_data.bin').read_bytes(), (path/'string_data_table.bin').read_bytes())
        tables = decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')
        old, _ = prepare(native, legacy, reference, tables)
        data, report = prepare(native, legacy, reference, tables, native_species=True)
        self.assertEqual(data, (ROOT/'build/design-items-words/words.bin').read_bytes())
        self.assertEqual((sha256(old), sha256(data)), (WORD_HASH, DESIGN_WORD_HASH))
        before, after = unpack_words(old), unpack_words(data)
        self.assertEqual(len(data), len(old))
        self.assertEqual(len(after), 352)
        changed = [(a, b) for a, b in zip(before, after, strict=True) if a != b]
        self.assertEqual(len(changed), 1)
        a, b = changed[0]
        self.assertEqual((a.native_id, a.text, b.text), (NATIVE_ID, DONOR, ENGLISH))
        self.assertEqual(replace(a, text=ENGLISH), b)
        self.assertEqual(sum(len(r.text)>10 for r in after), 82)
        entry = next(r for r in report['rows'] if r['native_id'] == NATIVE_ID)
        self.assertEqual(entry['match_basis'], 'reviewed_native_species_correction')
        self.assertEqual(entry['native_sha256'], NATIVE_SHA256)
        self.assertEqual(correct_word(0, b'unrelated', b'unchanged'), b'unchanged')
        for source, donor in ((b'wrong', DONOR), (native.entries()[NATIVE_ID], b'wrong')):
            with self.assertRaises(ValueError): correct_word(NATIVE_ID, source, donor)
        aliases = (ROOT/'build/npc-mail-aliases/aliases.bin')
        if not aliases.is_file(): aliases = CREATOR/'aliases.bin'
        verified_resources(data, aliases.read_bytes())
        forged = list(after); forged[0] = replace(forged[0], text=b'changed')
        with self.assertRaises(ValueError): verified_resources(pack_words(forged), aliases.read_bytes())

    def test_dialogue_keeps_native_controls_and_all_current_text_uses_native_species(self):
        native = verified_rom(ROM.read_bytes()); info = module_command_info(native)
        originals = next(b for b in banks(native) if b.name == 'message').entries()
        drafts = json.loads((ROOT/'translations/n64-herabuna-dialogue.json').read_text())
        current = json.loads((ROOT/'build/design-items-candidates/translations.json').read_text())
        index = {r['id']: r for r in current}
        for row in drafts:
            source = originals[int(row['id'].split(':')[1], 16)]
            self.assertEqual(sha256(source), row['source_sha256'])
            encoded = encode(row['translation'], info)
            commands = lambda value: [t.data for t in tokenize(value, info) if t.kind == 'cmd']
            self.assertGreater(len(commands(source)), 3)
            self.assertEqual(commands(encoded), commands(source))
            self.assertEqual(index[row['id']]['translation'], row['translation'])
            self.assertIn('herabuna', row['translation'])
        self.assertEqual(index['string:021A']['translation'], 'herabuna')
        self.assertFalse(any('brook trout' in r['translation'].lower() for r in current))
        values = validated_values(native, current, info)
        self.assertEqual(values['string:021A'], ENGLISH)
        words = unpack_words((ROOT/'build/design-items-words/words.bin').read_bytes())
        self.assertEqual(list(values.values()), [r.text for r in words])


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Completed native-design ROM required')
class NativeSpeciesInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = verified_rom(ROM.read_bytes())
        cls.built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((BUILD/'build.json').read_text())
        cls.module = cls.report['runtime_module']
        cls.approval = json.loads((CREATOR/'overlay.json').read_text())
        cls.image = (CREATOR/'overlay.bin').read_bytes()
        cls.reloc = (CREATOR/'relocation.bin').read_bytes()

    def test_manifest_must_match_actual_word_bytes_and_names_require_corrected_species(self):
        validate(self.image, self.reloc, self.approval, self.module)
        for wrong in (WORD_HASH, '0'*64, [], None):
            bad = deepcopy(self.approval); bad['word_sha256'] = wrong
            with self.assertRaises(ValueError): validate(self.image, self.reloc, bad, self.module)
        words = (ROOT/'build/npc-mail-words/words.bin').read_bytes()
        at = self.approval['symbols']['af_npc_word_data']
        changed = self.image[:at]+words+self.image[at+len(words):]
        bad = {**self.approval, 'overlay_sha256': sha256(changed), 'word_sha256': WORD_HASH}
        with self.assertRaisesRegex(ValueError, 'initializer rejects|corrected herabuna'):
            validate(changed, self.reloc, bad, self.module)

    def test_actual_initializer_digest_cannot_lag_behind_the_declared_resource(self):
        at = word_guard_offset(self.image, self.approval['symbols'], struct.unpack_from('>I', self.reloc)[0])
        self.assertEqual(self.image[at:at+32], bytes.fromhex(DESIGN_WORD_HASH))
        bad_image = self.image[:at]+bytes.fromhex(WORD_HASH)+self.image[at+32:]
        bad = {**self.approval, 'overlay_sha256': sha256(bad_image)}
        with self.assertRaisesRegex(ValueError, 'initializer rejects'):
            validate(bad_image, self.reloc, bad, self.module)

    def test_only_read_only_articles_word_data_and_bound_digest_change_in_creator(self):
        old = ROOT/'build/resolved-items-creator'
        first = (old/'overlay.bin').read_bytes()
        before = json.loads((old/'overlay.json').read_text())
        self.assertEqual(before['symbols'], self.approval['symbols'])
        self.assertEqual((self.approval['bytes'], self.approval['relocation_bytes']), (58144, 848))
        a, w = [self.approval['symbols'][name] for name in ('af_item_article_data', 'af_npc_word_data')]
        text = struct.unpack_from('>I', self.reloc)[0]
        digest = word_guard_offset(self.image, self.approval['symbols'], text)
        self.assertEqual(first[:text], self.image[:text])
        self.assertEqual(first[:digest], self.image[:digest])
        self.assertEqual(first[digest+32:a], self.image[digest+32:a])
        self.assertEqual(first[a+SIZE:w], self.image[a+SIZE:w])
        self.assertEqual(first[w+11328:], self.image[w+11328:])
        self.assertEqual((old/'relocation.bin').read_bytes(), self.reloc)

    def test_default_recompilation_retains_old_image_without_loosening_source_checks(self):
        from npc_mail_capture import source_report_matches, CAPTURE_SOURCE
        old, repeated = [ROOT/('build/'+p) for p in ('resolved-items-creator', 'design-items-legacy-check')]
        for name in ('overlay.bin', 'relocation.bin'):
            self.assertEqual((old/name).read_bytes(), (repeated/name).read_bytes())
        old_report = json.loads((old/'overlay.json').read_text())
        repeated_report = json.loads((repeated/'overlay.json').read_text())
        self.assertEqual(old_report['symbols'], repeated_report['symbols'])
        validate((old/'overlay.bin').read_bytes(), self.reloc, old_report, self.module)
        args = dict(article_names=old_report['item_names_sha256'], word_hash=WORD_HASH)
        self.assertTrue(source_report_matches(old_report['sources'], repeated_report['sources'], **args))
        for path in (CAPTURE_SOURCE, 'overlays/mail_generation/digest.c'):
            bad = {**repeated_report['sources'], path: '0'*64}
            self.assertFalse(source_report_matches(old_report['sources'], bad, **args))
        args['word_hash'] = DESIGN_WORD_HASH
        self.assertFalse(source_report_matches(old_report['sources'], repeated_report['sources'], **args))

    def test_full_rom_changes_only_expected_resources_and_retains_every_other_bank_entry(self):
        from dataclasses import replace as change_bank
        from runtime_module import verify_test_module
        old_path = ROOT/'build/resolved-items-pilot'
        old = (old_path/'animal-forest-halfwidth.z64').read_bytes()
        before, after = by_vrom(old), by_vrom(self.built)
        self.assertEqual(before.keys(), after.keys())
        changed = {v for v in before if before[v].extract(old) != after[v].extract(self.built)}
        self.assertEqual(changed, {0x19D40, 0x2000000, 0xCF9000, 0x2600000, 0xD18000,
                                   0x10F4000, 0x2800000, 0x2A00000, 0x3200000})
        # 00019D40 contains the DMA table, not the native code payload.
        a, b = [files[0x2800000].extract(rom) for files, rom in ((before, old), (after, self.built))]
        self.assertEqual(a[:0x60], b[:0x60]); self.assertEqual(a[0x64:], b[0x64:])
        original = {bank.name: bank for bank in banks(self.native)}
        for name, vrom, expected in (('message', 0x2000000, {0x10F7, 0x1328}),
                                     ('string', 0x2600000, {0x021A})):
            bank = original[name]
            entries = [change_bank(bank, data=files[vrom].extract(rom),
                                   table=files[bank.table_vrom].extract(rom)).entries()
                       for files, rom in ((before, old), (after, self.built))]
            self.assertEqual({i for i, pair in enumerate(zip(*entries, strict=True)) if pair[0] != pair[1]}, expected)
        self.assertEqual(sha256(self.built), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), self.built)
        verify_test_module(self.built, self.module)

    def test_new_native_batch_is_complete_and_source_bound(self):
        from design_item_scenario import scenario
        names = json.loads((ROOT/'build/design-items-resource/names.json').read_text())
        plan = scenario(self.native, self.built, self.module, names)
        self.assertEqual(plan, json.loads((ROOT/'build/design-items-scenario.json').read_text()))
        omitted = {**names, 'edits': [r for r in names['edits'] if r['id'] != 'item_23:0001']}
        with self.assertRaisesRegex(ValueError, '75 complete fields'):
            scenario(self.native, self.built, self.module, omitted)

    def test_combined_accounting_adds_only_the_74_new_native_name_fields(self):
        from translation_progress import measure
        old = ROOT/'build/resolved-items-pilot'
        previous = measure(self.native, (old/'animal-forest-halfwidth.z64').read_bytes(),
                           json.loads((old/'build.json').read_text()))
        current = measure(self.native, self.built, self.report)
        a, b = [{key for key, row in ledger.rows.items() if row['replacements']}
                for ledger in (previous, current)]
        names = [json.loads((ROOT/('build/'+kind+'-items-resource/names.json')).read_text())
                 for kind in ('resolved', 'design')]
        expected = {r['id'] for r in names[1]['edits']}-{r['id'] for r in names[0]['edits']}
        self.assertEqual(len(expected), 74)
        self.assertEqual(b-a, expected); self.assertFalse(a-b)
        self.assertEqual(previous.summary()['total_source_characters'], 751002)
        self.assertEqual(current.summary()['total_source_characters'], 751002)


if __name__ == '__main__': unittest.main()
