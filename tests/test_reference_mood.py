"""Native mood effects cannot erase or reorder complete English references."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_VROM, by_vrom, sha256, verified_rom
from reference_content import adapt_content_reference, validate_content_approval, validate_content_candidate
from reference_mood import restore, validate_rule
from textcodec import encode
from textcodec import tokenize
from gc_adapter import adapt_reference, remove_redundant_article_suppression
from reference_matches import load_matches
from reference_animations import verify_native_consumer, NPC_RAM
from runtime_module import module_command_info
from textbanks import banks
from textvalidate import validate_entry, expanded_bound
from test_retail import ROM_PATH

PAIR = '{cmd:7F09020001}{cmd:7F09080001}'
IDS = set('1788 1F88 1FAD 1FB6 2067 207D 25E0 25EA 25F4 25F6 2621 2623 '
          '2628 2630 2634 263C 264F 2655 27B5 203A 262B 2637 264B 266B'.split())


class NativeMoodTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x77
        self.info[9] = (5, 0)
        self.prefix = 'First{cmd:7F04}\n{cmd:7F02}'
        self.source = encode(self.prefix+PAIR+'Native{cmd:7F0900000A}{cmd:7F00}', self.info)
        self.text = self.prefix+'Full English!{cmd:7F0900000A}{cmd:7F00}'
        self.rule = {'source_offset': len(encode(self.prefix, self.info)),
                     'reference_offset': len(self.prefix), 'commands': '7F090200017F09080001'}

    def test_exact_insertion_retains_the_entire_reference(self):
        text, changes = restore(self.text, self.source, self.rule, self.info)
        self.assertEqual(text, self.prefix+PAIR+self.text[len(self.prefix):])
        self.assertEqual(text.replace(PAIR, '', 1), self.text)
        self.assertEqual(changes[0]['operation'], 'restore_complete_native_mood_pair')

    def test_start_of_message_and_second_native_duration_are_supported(self):
        pair = PAIR.replace('7F09080001', '7F09080002')
        source = encode(pair+'Native{cmd:7F00}', self.info)
        rule = {'source_offset': 0, 'reference_offset': 0, 'commands': '7F090200017F09080002'}
        self.assertEqual(restore('English{cmd:7F00}', source, rule, self.info)[0], pair+'English{cmd:7F00}')

    def test_schema_rejects_other_orders_offsets_and_partial_pairs(self):
        for change in ({'commands': '7F09020001'}, {'commands': '7F090200027F09080001'},
                       {'commands': None}, {'source_offset': True}, {'reference_offset': -1},
                       {'reference_offset': 8192}, {'extra': True}, {'anchor': None},
                       {'anchor': 'anywhere'}, {'anchor': []}, {'anchor': True}):
            with self.assertRaises(ValueError): validate_rule({**self.rule, **change})

    def test_missing_duplicate_or_stale_native_pair_fails(self):
        for source in (self.source.replace(bytes.fromhex('7F09080001'), b''),
                       self.source+bytes.fromhex(self.rule['commands'])):
            with self.assertRaises(ValueError): restore(self.text, source, self.rule, self.info)
        with self.assertRaises(ValueError):
            restore(self.text, self.source, {**self.rule, 'source_offset': self.rule['source_offset']+1}, self.info)
        with self.assertRaises(ValueError):
            restore(self.text, self.source, {**self.rule, 'commands': '7F090200017F09080002'}, self.info)

    def test_mid_page_insertion_or_native_pair_is_not_approved(self):
        for offset in (1, len(self.prefix)-1, len(self.prefix)+1, len(self.text)+1):
            with self.assertRaises(ValueError):
                restore(self.text, self.source, {**self.rule, 'reference_offset': offset}, self.info)
        source = encode('X'+PAIR+'Native{cmd:7F0900000A}{cmd:7F00}', self.info)
        with self.assertRaisesRegex(ValueError, 'native page'):
            restore(self.text, source, {**self.rule, 'source_offset': 1}, self.info)

    def test_reference_pair_and_wrong_actor_order_cannot_be_hidden_by_adapter(self):
        with self.assertRaisesRegex(ValueError, 'already contains'):
            restore(PAIR+self.text, self.source, self.rule, self.info)
        text = '{cmd:7F0900000A}'+self.text.replace('{cmd:7F0900000A}', '')
        rule = {**self.rule, 'reference_offset': len(self.prefix)+len('{cmd:7F0900000A}')}
        with self.assertRaisesRegex(ValueError, 'actor order'):
            restore(text, self.source, rule, self.info)

    def test_complete_hash_binding_and_combination_restrictions(self):
        output = encode(restore(self.text, self.source, self.rule, self.info)[0], self.info)
        reference = {'id': 'message:0000', 'text': self.text, 'sha256': sha256(encode(self.text, self.info))}
        record = {'id': reference['id'], 'reference_id': reference['id'],
                  'source_sha256': sha256(self.source), 'reference_sha256': reference['sha256'],
                  'complete_reference': {'adapted_sha256': sha256(output), 'native_mood': self.rule}}
        text, _ = adapt_content_reference(reference, self.source, record, self.info)
        self.assertEqual(encode(text, self.info), output)
        validate_content_candidate(record['id'], self.source, output, {record['id']: record})
        with self.assertRaises(ValueError):
            validate_content_candidate(record['id'], self.source, output[:-3], {record['id']: record})
        with self.assertRaisesRegex(ValueError, 'Stale'):
            adapt_content_reference({**reference, 'text': self.text+'extra'}, self.source, record, self.info)
        for key in ('spans', 'omit_startup_storage_location'):
            changed = deepcopy(record); changed['complete_reference'][key] = []
            with self.assertRaises(ValueError): validate_content_approval(changed)
        with self.assertRaises(ValueError):
            validate_content_approval({**record, 'reference_id': 'message:0001'})

    def test_phrase_anchor_requires_the_same_immediate_native_expression(self):
        prefix = 'First\n'; following = '{cmd:7F0900000E}Next{cmd:7F00}'
        source = encode(prefix+PAIR+following, self.info)
        rule = {**self.rule, 'source_offset': len(encode(prefix, self.info)),
                'reference_offset': len(prefix), 'anchor': 'before_expression_0E'}
        self.assertEqual(restore(prefix+following, source, rule, self.info)[0], prefix+PAIR+following)
        for changed in ({**rule, 'reference_offset': len(prefix)+1},
                        {k: v for k, v in rule.items() if k != 'anchor'}):
            with self.assertRaises(ValueError): restore(prefix+following, source, changed, self.info)
        for text, raw in ((prefix+' '+following, source),
                          (prefix+following, source.replace(bytes.fromhex('7F0900000E'), bytes.fromhex('7F0900000A')))):
            with self.assertRaisesRegex(ValueError, 'exact original expression'):
                restore(text, raw, rule, self.info)

    def test_final_anchor_keeps_every_word_and_the_exact_normal_ending(self):
        source = encode('Native'+PAIR+'\n{cmd:7F00}', self.info)
        text = 'Complete English\n{cmd:7F00}'
        rule = {**self.rule, 'source_offset': 6, 'reference_offset': len('Complete English'),
                'anchor': 'before_final_end'}
        self.assertEqual(restore(text, source, rule, self.info)[0], 'Complete English'+PAIR+'\n{cmd:7F00}')
        for changed in (text+'\n', text.replace('7F00', '7F01'), text.replace('\n', ' \n')):
            with self.assertRaises(ValueError): restore(changed, source, rule, self.info)
        with self.assertRaises(ValueError):
            restore(text, source.replace(b'\x7f\x00', b'\x7f\x01'), rule, self.info)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Retail native/English sources stay local')
class NativeMoodRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = verified_rom(ROM_PATH.read_bytes()); cls.info = module_command_info(cls.rom)
        cls.sources = next(b for b in banks(cls.rom) if b.name == 'message').entries()
        cls.refs = {r['id']: r for r in map(json.loads, (ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        cls.matches = load_matches(ROOT/'translations/reference_matches.json')
        cls.approved = [r for r in cls.matches.values() if 'native_mood' in r.get('complete_reference', {})]

    def test_all_complete_references_keep_original_actors_and_full_english(self):
        self.assertEqual({r['id'][8:] for r in self.approved}, IDS)
        for record in self.approved:
            source = self.sources[int(record['id'][8:], 16)]; reference = self.refs[record['reference_id']]
            restored, changes = adapt_content_reference(reference, source, record, self.info)
            rule = record['complete_reference']['native_mood']; raw = bytes.fromhex(rule['commands'])
            tags = ''.join('{cmd:'+raw[n:n+5].hex().upper()+'}' for n in (0, 5))
            self.assertEqual(restored.replace(tags, '', 1), reference['text'])
            self.assertEqual(changes[0]['source_offset'], rule['source_offset'])
            final, adapted = adapt_reference(restored, source, self.info, 'reference_layout', True)
            self.assertFalse(any(r['operation'] == 'preserve_n64_demo_arguments' for r in adapted))
            self.assertEqual(final.replace(tags, '', 1), remove_redundant_article_suppression(reference['text'])[0])
            output = encode(final, self.info)
            validate_content_candidate(record['id'], source, output, self.matches)
            for resident in (False, True):
                validate_entry(source, output, self.info, 'message', 'reference_layout', resident_runtime=resident)
            self.assertLessEqual(expanded_bound(output, self.info), 1024)

    def test_sun_contest_uses_corresponding_semantic_page_not_equal_page_numbers(self):
        record = self.matches['message:1FAD']; rule = record['complete_reference']['native_mood']
        source = self.sources[0x1FAD]; reference = self.refs[record['reference_id']]
        self.assertEqual(sum(t.data == b'\x7f\x02' for t in tokenize(source[:rule['source_offset']], self.info)), 3)
        self.assertEqual(reference['text'][:rule['reference_offset']].count('{cmd:7F02}'), 4)
        text = reference['text']; wrong = sum(len(p)+len('{cmd:7F02}') for p in text.split('{cmd:7F02}')[:3])
        with self.assertRaisesRegex(ValueError, 'actor order'):
            restore(text, source, {**rule, 'reference_offset': wrong}, self.info)

    def test_native_consumer_is_the_pinned_order_reader_and_original_mood_setter(self):
        data, _ = verify_native_consumer(self.rom)
        consumer = data[0x80976588-NPC_RAM:0x80976604-NPC_RAM]
        self.assertEqual(sha256(consumer), '7e62d55be66039121b422ad0e3ca9a18ab0c1d92f21f90bcd6e5f0d15d4a2c29')
        self.assertEqual(consumer.count(bytes.fromhex('0C01ED27')), 2)
        self.assertEqual(consumer.count(bytes.fromhex('0C01ED13')), 2)
        self.assertIn(bytes.fromhex('0C25E200'), consumer)
        changed = bytearray(data); changed[0x80976598-NPC_RAM] ^= 1
        with self.assertRaises(ValueError): verify_native_consumer(self.rom, {0x8681F0: bytes(changed)})

    def test_builder_rejects_changed_text_even_without_mood_metadata(self):
        from build import apply_translations
        import tempfile
        record = self.matches['message:1F88']
        source = self.sources[0x1F88]
        text, _ = adapt_content_reference(self.refs[record['reference_id']], source, record, self.info)
        edit = {'id': record['id'], 'source_sha256': record['source_sha256'],
                'translation': text, 'control_policy': 'reference_layout'}
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'; path.write_text(json.dumps([edit]))
            code = by_vrom(self.rom)[CODE_VROM].extract(self.rom)
            count, _ = apply_translations(self.rom, {CODE_VROM: code}, path)
            self.assertEqual(count, 1)
            for replacement in ('Changed{cmd:7F00}', text.replace('Heh heh', '')):
                path.write_text(json.dumps([{**edit, 'translation': replacement}]))
                with self.assertRaisesRegex(ValueError, 'reviewed payload'):
                    apply_translations(self.rom, {}, path)


if __name__ == '__main__':
    unittest.main()
