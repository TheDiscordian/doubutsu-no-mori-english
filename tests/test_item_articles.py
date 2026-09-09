"""Real supplied articles, every native ID, and exact complete-name binding."""

import copy
import ctypes as C
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from extended_items import COUNTS
from gc_names import symbol_data
from item_aliases import ordinary_item
from item_articles import build, verify, verify_names, DATA_HASH, NAMES_HASH, SIZE, UNKNOWN, ARTICLES

DIRECTORY = ROOT/'build/noticeboard-treasure/articles'


@unittest.skipUnless((DIRECTORY/'articles.bin').is_file(), 'Local supplied article resource required')
class ItemArticleTests(unittest.TestCase):
    directory = DIRECTORY
    names_directory = ROOT/'build/native-items-resource'
    data_hash, names_hash, known_slots = DATA_HASH, NAMES_HASH, 3563

    @classmethod
    def setUpClass(cls):
        cls.data = (cls.directory/'articles.bin').read_bytes()
        cls.report = json.loads((cls.directory/'articles.json').read_text())
        cls.names = (cls.names_directory/'names.bin').read_bytes()
        cls.names_report = json.loads((cls.names_directory/'names.json').read_text())
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
        cls.rom = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.originals = json.loads((ROOT/'translations/n64-item-articles.json').read_text())
        cls.temporary = tempfile.TemporaryDirectory(prefix='af-item-articles-')
        library = Path(cls.temporary.name)/'articles.so'
        sources = ['overlays/mail_generation/item_article.c', 'runtime/item_name.c', 'runtime/crc32.c',
                   'tests/item_article_mock.c', 'overlays/mail_generation/item_article_sources.s']
        flags = (['-fsanitize=address,undefined', '-fno-sanitize-recover=all', '-fno-omit-frame-pointer', '-g']
                 if os.environ.get('AF_ITEM_ARTICLE_SANITIZE') == '1' else [])
        env = dict(os.environ); env.pop('LD_PRELOAD', None)
        result = subprocess.run(['gcc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                                 '-Wa,-I'+str(cls.directory), '-Wl,-z,noexecstack', *flags,
                                 *(str(ROOT/p) for p in sources), '-o', str(library)],
                                capture_output=True, text=True, env=env, timeout=60)
        if result.returncode: raise ValueError(result.stderr)
        cls.lib = C.CDLL(str(library))
        cls.lib.af_notice_item_article.argtypes = [C.c_uint, C.c_void_p]

    @classmethod
    def tearDownClass(cls): cls.temporary.cleanup()

    def test_complete_source_rebuild_and_immutable_profile(self):
        data, report = build(self.rom, self.names, self.names_report, self.rel, self.symbols, self.originals)
        self.assertEqual((data, report), (self.data, self.report))
        self.assertEqual((len(data), sha256(data), sha256(self.names)), (SIZE, self.data_hash, self.names_hash))
        self.assertEqual((report['known_slots'], report['unknown_slots']), (self.known_slots, 4544-self.known_slots))
        verify(data)
        for offset in (0, 15, 16, 47, 48, len(data)-1):
            changed = bytearray(data); changed[offset] ^= 1
            with self.assertRaises(ValueError): verify(changed)
        with self.assertRaises(ValueError): verify(data[:-1])

    def test_each_reference_uses_its_own_supplied_article_and_full_name(self):
        edits = {row['id']: row for row in self.names_report['edits']}
        for row in self.report['entries']:
            edit = edits.get(row['id'])
            if edit is None:
                self.assertEqual((row['article'], row['references']), (UNKNOWN, []))
                continue
            reference = edit['provenance']['reference_id']
            if reference.startswith('native:'):
                expected = self.originals[edit['translation']]['article']
            else:
                family, index = reference.split(':'); index = int(index, 16)
                symbol = 'ftrArt' if family == 'furniture' else 'itemArt_'+ARTICLES[int(family[5:], 16)-0x20]
                expected = symbol_data(self.rel, self.symbols, symbol)[index]
            self.assertEqual(row['article'], expected, row['id'])
            self.assertEqual(row['name_sha256'], edit['provenance']['reference_sha256'])
        self.assertEqual(self.originals['N cube shirt']['article'], 2)
        self.assertEqual(self.originals['quest money']['article'], 4)
        self.assertEqual(self.originals['1,000 Bells']['article'], 0)

    def test_all_native_ids_use_same_conversion_as_complete_names(self):
        ledger = {row['id']: row['article'] for row in self.report['entries']}
        accepted = 0
        for item in range(65536):
            converted = ordinary_item(item)
            group, index = converted >> 8, converted & 255
            if 0x1000 <= converted < 0x1000+COUNTS[-1]:
                position = sum(COUNTS[:-1])+converted-0x1000
                key = f'item_10:{(converted-0x1000)&~3:04X}'
            elif 0x20 <= group <= 0x2F and index < COUNTS[group-0x20]:
                position = sum(COUNTS[:group-0x20])+index
                key = f'item_{group:02X}:{index:04X}'
            else:
                self.assertEqual(self.lib.af_notice_item_article(item, b'abcdefghijklmnop'), -1)
                continue
            name = self.names[32+position*16:32+(position+1)*16]
            expected = ledger[key]
            self.assertEqual(self.lib.af_notice_item_article(item, name), expected if expected != UNKNOWN else -1,
                             f'{item:04X} -> {converted:04X}')
            accepted += expected != UNKNOWN
        self.assertGreater(accepted, 3000)
        for item in (65536, 0xFFFFFFFF):
            self.assertEqual(self.lib.af_notice_item_article(item, b'abcdefghijklmnop'), -1)
        self.assertEqual(self.lib.af_notice_item_article(0x1000, None), -1)

    def test_every_known_name_rejects_changed_complete_field(self):
        for row in self.report['entries']:
            if row['article'] == UNKNOWN: continue
            group, index = row['id'].split(':'); index = int(index, 16)
            item = (0x1000+index) if group == 'item_10' else (int(group[5:], 16)<<8)|index
            converted = ordinary_item(item)
            # The converted ordinary field, not a placed decoration's old name,
            # is authoritative on the native name/treasure path.
            if converted != item: continue
            position = sum(COUNTS[:-1])+index if group == 'item_10' else sum(COUNTS[:(item>>8)-0x20])+index
            name = self.names[32+position*16:32+(position+1)*16]
            for offset in range(16):
                changed = bytearray(name); changed[offset] ^= 1
                self.assertEqual(self.lib.af_notice_item_article(item, bytes(changed)), -1)

    def test_changed_sources_names_provenance_and_missing_original_approval_fail(self):
        inputs = [self.rom, self.names, self.names_report, self.rel, self.symbols, self.originals]
        for which in (0, 1, 3):
            changed = list(inputs); changed[which] = changed[which][:-1]
            with self.assertRaises(ValueError): build(*changed)
        changed = list(inputs); changed[4] += '\n'
        with self.assertRaises(ValueError): build(*changed)
        changed = list(inputs); changed[5] = dict(self.originals); del changed[5]['N cube shirt']
        with self.assertRaises(ValueError): build(*changed)
        changed = list(inputs); changed[2] = copy.deepcopy(self.names_report)
        changed[2]['edits'][0]['provenance']['reference_id'] = 'furniture:FFFF'
        with self.assertRaises(ValueError): build(*changed)
        changed = list(inputs); changed[5] = copy.deepcopy(self.originals)
        changed[5]['N cube shirt']['article'] = 1
        data, _ = build(*changed)
        with self.assertRaises(ValueError): verify(data)

    def test_installer_requires_matching_enabled_full_name_resource(self):
        verify_names(self.names, 0x02A00000, self.names_hash)
        for data, address in ((b'', 0x02A00000), (self.names, 0), (self.names[:-1], 0x02A00000)):
            with self.assertRaises(ValueError): verify_names(data, address)


if __name__ == '__main__': unittest.main()
