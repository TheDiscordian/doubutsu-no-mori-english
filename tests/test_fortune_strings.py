"""Full fortune groups cannot bypass native caller or source checks."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from build import apply_translations
from fortune_strings import (IDS, VROM, RAM, RELOC_VROM, CHANGES, STRING_RELOCATION,
                             candidates, permits, source_entries, patch, install)
from runtime_module import add_runtime_module, module_command_info
from textbanks import Bank
from textcodec import encode
from textvalidate import validate_entry
from test_retail import ROM_PATH
from fortune_smoke import seed_for, relocated


class FortuneSeedTests(unittest.TestCase):
    def test_all_native_random_pool_indices_without_extra_draws(self):
        for index in range(32):
            seed, final, bits = seed_for(index)
            self.assertEqual((seed*0x19660D+0x3C6EF35F) & 0xFFFFFFFF, final)
            fraction = struct.unpack('>f',struct.pack('>I',bits))[0]-1.0
            self.assertEqual(fraction*32,index)
        for value in (-1,32,True,'0'):
            with self.assertRaises(ValueError): seed_for(value)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/string.jsonl').is_file()
                     and (ROOT/'build/runtime-module/module.json').is_file(),
                     'Supplied retail inputs and compiled module remain local')
class FortuneTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes()
        cls.info = module_command_info(cls.rom)
        cls.refs = {r['id']: r for r in map(json.loads,
            (ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        cls.inventory = {r['id']: r for r in map(json.loads,
            (ROOT/'build/inventory/string.jsonl').read_text().splitlines())}
        cls.edits = candidates(cls.rom, cls.refs, cls.inventory, cls.info)
        cls.originals = source_entries(cls.rom)
        cls.files = by_vrom(cls.rom)
        cls.data, cls.reloc = (cls.files[v].extract(cls.rom) for v in (VROM, RELOC_VROM))

    def test_all_complete_references_fit_only_the_scoped_capacity(self):
        approvals = permits(self.rom, list(self.edits.values()), self.info)
        self.assertEqual(len(approvals), 128)
        grown = 0
        for id, edit in self.edits.items():
            source = self.originals[int(id[7:], 16)]
            value = encode(edit['translation'], self.info)
            self.assertEqual(value, encode(self.refs[id]['text'], self.info))
            validate_entry(source, value, self.info, 'string', resident_runtime=True,
                           fortune_permit=approvals[id])
            if len(value) > len(source):
                grown += 1
                with self.assertRaisesRegex(ValueError, 'entry budget'):
                    validate_entry(source, value, self.info, 'string', resident_runtime=True)
            for bank, runtime, policy, data in (('select', True, 'exact', value),
                    ('string', False, 'exact', value), ('string', True, 'presentation', value),
                    ('string', True, 'exact', value+b'!')):
                with self.assertRaisesRegex(ValueError, 'Fortune capacity'):
                    validate_entry(source, data, self.info, bank, policy,
                                   resident_runtime=runtime, fortune_permit=approvals[id])
        self.assertEqual(grown, 108)

    def test_generation_requires_complete_source_legacy_and_reference(self):
        id = IDS[0]
        for source, field, value in (('refs', 'sha256', '0'*64), ('refs', 'text', 'Changed'),
                ('inventory', 'source_sha256', '0'*64), ('inventory', 'legacy', 'Short')):
            refs, inventory = deepcopy(self.refs), deepcopy(self.inventory)
            (refs if source == 'refs' else inventory)[id][field] = value
            with self.assertRaises(ValueError): candidates(self.rom, refs, inventory, self.info)
        with self.assertRaises(ValueError): candidates(self.rom, {}, self.inventory, self.info)

    def test_builder_permission_rejects_partial_duplicate_or_changed_values(self):
        edits = list(self.edits.values())
        for bad in (edits[:-1], edits+[edits[0]]):
            with self.assertRaisesRegex(ValueError, 'complete unique'):
                permits(self.rom, bad, self.info)
        for field, value in (('translation', 'Short'), ('source_sha256', '0'*64),
                             ('control_policy', 'presentation')):
            bad = deepcopy(edits); bad[0][field] = value
            with self.assertRaises(ValueError): permits(self.rom, bad, self.info)
        bad = deepcopy(edits)
        bad[0]['translation'], bad[1]['translation'] = bad[1]['translation'], bad[0]['translation']
        with self.assertRaises(ValueError): permits(self.rom, bad, self.info)

    def test_seven_frame_words_change_without_code_or_relocation_growth(self):
        output = patch(self.data, self.reloc)
        self.assertEqual(len(output), len(self.data))
        restored = bytearray(output)
        for address, before, after in CHANGES:
            self.assertEqual(struct.unpack_from('>I', output, address-RAM)[0], after)
            struct.pack_into('>I', restored, address-RAM, before)
        self.assertEqual(restored, self.data)
        self.assertEqual(len(CHANGES), 7)
        for i in (0, 16, len(self.reloc)-1):
            changed = bytearray(self.reloc); changed[i] ^= 1
            with self.assertRaises(ValueError): patch(self.data, bytes(changed))
        for address, _, _ in CHANGES:
            changed = bytearray(self.data); changed[address-RAM] ^= 1
            with self.assertRaises(ValueError): patch(bytes(changed), self.reloc)
        for vrom, changed in ((VROM, output), (RELOC_VROM, bytes(len(self.reloc)))):
            replacements = {vrom: changed}; before = deepcopy(replacements)
            with self.assertRaisesRegex(ValueError, 'overlaps'): install(self.rom, replacements)
            self.assertEqual(replacements, before)

    def test_changed_frame_survives_both_native_relocation_bases(self):
        for base in (0x801A0000,0x802F8010):
            output = relocated(self.data,self.reloc,base)
            self.assertEqual(len(output),len(self.data))
            for address,_,after in CHANGES:
                self.assertEqual(struct.unpack_from('>I',output,address-RAM)[0],after)
            self.assertEqual(output[0x809DCAB0-RAM:0x809DCAC0-RAM],
                             self.data[0x809DCAB0-RAM:0x809DCAC0-RAM])

    def test_real_builder_relocates_bank_and_installs_scoped_caller(self):
        edits = list(self.edits.values())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'edits.json'; path.write_text(json.dumps(edits))
            replacements = {}
            additions, _ = add_runtime_module(self.rom, replacements, ROOT/'build/runtime-module')
            before = deepcopy(replacements)
            count, relocations = apply_translations(self.rom, replacements, path,
                runtime_module=ROOT/'build/runtime-module', module_additions=additions, english_fortunes=True)
            self.assertEqual(count, 128)
            self.assertEqual(relocations, {0xD16000: STRING_RELOCATION[0]})
            entries = Bank('string', 0xD16000, 0xD18000,
                          replacements[0xD16000], replacements[0xD18000]).entries()
            expected = list(self.originals)
            for id, edit in self.edits.items(): expected[int(id[7:],16)] = encode(edit['translation'], self.info)
            self.assertEqual(entries, expected)
            self.assertEqual(replacements[VROM], patch(self.data, self.reloc))
            at = STRING_RELOCATION[1]-CODE_RAM
            self.assertEqual(replacements[CODE_VROM][at:at+8], bytes.fromhex(STRING_RELOCATION[3]))
            restored = bytearray(replacements[CODE_VROM]); restored[at:at+8] = before[CODE_VROM][at:at+8]
            self.assertEqual(restored, before[CODE_VROM])
            with self.assertRaisesRegex(ValueError, 'entry budget'):
                apply_translations(self.rom, deepcopy(before), path,
                    runtime_module=ROOT/'build/runtime-module', module_additions=additions)
            with self.assertRaisesRegex(ValueError, 'resident runtime'):
                apply_translations(self.rom, {}, path, english_fortunes=True)
            # A different string cannot borrow this group's capacity.
            path.write_text(json.dumps(edits+[{'id':'string:0001',
                'source_sha256':sha256(self.originals[1]), 'translation':'x'*16}]))
            with self.assertRaisesRegex(ValueError, 'entry budget'):
                apply_translations(self.rom, deepcopy(before), path,
                    runtime_module=ROOT/'build/runtime-module', module_additions=additions, english_fortunes=True)


if __name__ == '__main__': unittest.main()
