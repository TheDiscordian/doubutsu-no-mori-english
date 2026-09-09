"""Complete native birthday meanings, RNG order, and actual extended item storage."""

import calendar
import ctypes
import json
import os
from pathlib import Path
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_DIR = Path(os.environ.get('AF_TEST_RUNTIME_MODULE',str(ROOT/'build/runtime-module')))
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256, verified_rom
from dialogue_dates import SPEC
from npc_mail_show import source
from test_retail import ROM_PATH
from birthday_fields import message_ids, verify_source, audit_references
from birthday_smoke import SEEDS, random_draw, prepared_tokens, RNG_START, RNG_END, RNG_SHA256
from contextual_choices import canonical_candidate, display_candidate, load_contextual_choices, unique_menu
from gc_adapter import adapt_reference
from reference_choices import adapt_choice_reference
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import encode, tokenize
from textvalidate import validate_entry, expanded_bound
from dialogue_dates import REQUIREMENT, verify_requirements, install
from runtime_layout import MODULE_VROM


class BirthdayFixtureTests(unittest.TestCase):
    def test_native_float_scaling_and_seed_batch_cover_both_complete_pools(self):
        for index,seed in enumerate(SEEDS):
            first,bits,animal = random_draw(seed)
            final,last_bits,sign = random_draw(first)
            self.assertEqual((animal,sign),(index,index))
            self.assertEqual(bits,(first>>9)|0x3F800000)
            self.assertEqual(last_bits,(final>>9)|0x3F800000)

    def test_only_fields_after_preparation_and_before_next_request_are_birthday_values(self):
        info = [(2,0)]*0x61;info[0x0C] = (5,0)
        data = bytes.fromhex('7F347F0C0900047F347F357F337F0C0900027F35')
        self.assertEqual([(t.offset,t.data[1]) for t in prepared_tokens(data,info)],
                         [(7,0x34),(9,0x35),(11,0x33)])

ANIMALS = 'Rat Ox Tiger Rabbit Dragon Snake Horse Ram Monkey Rooster Dog Boar'.split()
SIGNS = 'Aries Taurus Gemini Cancer Leo Virgo Libra Scorpio Sagittarius Capricorn Aquarius Pisces'.split()
ENDS = (19,18,20,19,20,21,22,22,22,23,21,21)


def native_sign(month, day):
    selected = 0
    for index, last in enumerate(ENDS):
        if month < index+1 or month == index+1 and day <= last:
            selected = index
            break
    return (selected-3) % 12


def ordinal(day):
    day = day if 1 <= day <= 31 else 1
    suffix = 'th' if 11 <= day <= 13 else {1:'st',2:'nd',3:'rd'}.get(day%10, 'th')
    return str(day)+suffix


@unittest.skipUnless(shutil.which('gcc'), 'Host GCC executes the original birthday code')
class BirthdayFieldsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        output = Path(cls.temp.name)/'birthday.so'
        sources = ('runtime/birthday.c','runtime/dateformat.c','runtime/item_fields.c',
                   'runtime/item_name.c','tests/item_name_mock.c','tests/birthday_mock.c')
        subprocess.run(['gcc','-std=c99','-Wall','-Wextra','-Werror','-O2','-shared','-fPIC',
            '-I',str(ROOT/'runtime'),*[str(ROOT/p) for p in sources],'-o',str(output)],
            check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(output))
        cls.lib.af_birthday_constellation.argtypes = [ctypes.c_uint,ctypes.c_uint]
        cls.lib.af_birthday_constellation.restype = ctypes.c_uint
        cls.lib.af_birthday_fields.restype = None
        cls.lib.af_copy_item_string.argtypes = [ctypes.c_void_p,ctypes.c_int,ctypes.c_void_p,ctypes.c_int,ctypes.c_int]
        cls.lib.af_copy_item_string.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def setUp(self):
        self.window = (ctypes.c_ubyte*0x300).in_dll(self.lib,'af_test_window')
        self.player = (ctypes.c_ubyte*0xB00).in_dll(self.lib,'af_birthday_player')
        self.draws = (ctypes.c_float*2).in_dll(self.lib,'af_birthday_draws')
        self.count = ctypes.c_uint.in_dll(self.lib,'af_birthday_draw_count')
        self.enabled = ctypes.c_uint.in_dll(self.lib,'af_birthday_player_enabled')
        self.first = (ctypes.c_ubyte*10).in_dll(self.lib,'af_birthday_first_row_before_second_draw')
        self.enabled.value = 1

    def check(self, month, day, first=0, second=8):
        ctypes.memset(self.window,0x47,len(self.window))
        ctypes.memset(self.player,0x50,len(self.player))
        self.player[0xA92],self.player[0xA93] = month,day
        source_player = bytes(self.player)
        self.draws[0],self.draws[1] = (first+0.25)/12,(second+0.25)/12
        self.count.value = 0
        self.lib.af_birthday_fields()
        self.assertEqual(self.count.value,2)
        expected = [ANIMALS[first],SIGNS[second],SIGNS[native_sign(month,day)],
                    calendar.month_name[month if 1 <= month <= 12 else 1],ordinal(day)]
        self.assertEqual(bytes(self.first),expected[0].encode().ljust(10,b' '))
        self.assertEqual(bytes(self.player),source_player)
        self.assertEqual(bytes(self.window),b'G'*0x100+
            b''.join(v.encode()[:10].ljust(10,b' ') for v in expected)+b'G'*(0x300-0x100-50))
        for slot,value in enumerate(expected):
            # Execute the real wider reader; its native mirror alone cannot prove
            # that the eleventh character of Sagittarius survives insertion.
            data = ctypes.create_string_buffer(b'!'*16+b'X\x7f\x31Y'+b' '*1020+b'!'*16,1056)
            result = self.lib.af_copy_item_string(self.window,slot,ctypes.byref(data,16),1,4)
            self.assertEqual(result,len(value)+2)
            self.assertEqual(data.raw[16:16+result],b'X'+value.encode()+b'Y')
            self.assertEqual(data.raw[:16],b'!'*16)
            self.assertEqual(data.raw[1040:],b'!'*16)

    def test_every_random_pool_pair_retains_full_names_and_draw_order(self):
        for first in range(12):
            for second in range(12):
                self.check(12,1,first,second)

    def test_all_date_boundaries_and_native_invalid_bytes(self):
        for month in range(1,13):
            for day in range(1,32): self.check(month,day)
        for month in (0,13,255):
            for day in (0,1,31,32,255): self.check(month,day)
        for day in (0,32,255): self.check(1,day)

    def test_all_byte_pairs_preserve_the_original_sign_index(self):
        for month in range(256):
            for day in range(256):
                self.assertEqual(self.lib.af_birthday_constellation(month,day),native_sign(month,day))

    def test_missing_player_does_not_read_rng_or_change_fields(self):
        self.enabled.value = 0
        self.count.value = 0
        before = bytes(self.window)
        self.lib.af_birthday_fields()
        self.assertEqual(self.count.value,0)
        self.assertEqual(bytes(self.window),before)

    @unittest.skipUnless((ROOT/'build/gamecube/text/string.jsonl').is_file(), 'English disc stays local')
    def test_complete_common_names_match_the_supplied_english_labels(self):
        refs = {r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        for start,names in ((0x458,ANIMALS),(0x494,SIGNS)):
            for i,name in enumerate(names): self.assertEqual(refs[f'string:{start+i:04X}']['text'],name)


@unittest.skipUnless(ROM_PATH.is_file(), 'Retail ROM stays local')
class NativeBirthdaySourceTests(unittest.TestCase):
    def test_complete_native_body_table_dispatch_and_nonrelocated_entry(self):
        rom = verified_rom(ROM_PATH.read_bytes()); data,reloc = source(rom,'ordinary')
        body = data[0x80921324-SPEC.ram:0x80921464-SPEC.ram]
        self.assertEqual(sha256(body),'770b3dbb0270671fe82acf1804887c667dd60e4c1ebd6f07c95b95be35a05440')
        pairs = bytes(v for i,day in enumerate(ENDS) for v in (i+1,day))
        self.assertEqual(data[0x80921D58-SPEC.ram:0x80921D70-SPEC.ram],pairs)
        self.assertEqual(struct.unpack_from('>I',data,0x80921D78+3*4-SPEC.ram)[0],0x80921324)
        self.assertEqual(body[:8],bytes.fromhex('27BDFFC8AFBF0034'))
        self.assertFalse([r for r in struct.unpack_from('>552I',reloc,20)
            if 0x80921324-SPEC.ram <= r&0xFFFFFF < 0x8092132C-SPEC.ram])

    def test_original_body_table_dispatch_and_entry_relocations_reject_mutations(self):
        rom = verified_rom(ROM_PATH.read_bytes());data,reloc = source(rom,'ordinary')
        verify_source(data,reloc)
        for address in (0x80921324,0x80921460,0x80921D58,0x80921D78+12):
            changed = bytearray(data);changed[address-SPEC.ram] ^= 1
            with self.assertRaises(ValueError): verify_source(changed,reloc)
        changed = bytearray(reloc)
        struct.pack_into('>I',changed,20,0x44000000|(0x80921324-SPEC.ram))
        with self.assertRaisesRegex(ValueError,'entry unexpectedly'):
            verify_source(data,changed)
        audit = audit_references(rom)
        self.assertEqual(audit['entry_references'],[['00815B70','0045D4']])
        self.assertEqual(audit['external_interior_references'],[])
        at = 0x1060+RNG_START-0x80025C60
        self.assertEqual(sha256(rom[at:at+RNG_END-RNG_START]),RNG_SHA256)

    def test_all_native_preparation_requests_own_the_build_dependency(self):
        rom = verified_rom(ROM_PATH.read_bytes());ids = message_ids(rom)
        expected = '084A 0854 085E 0872 087E 0882 0886 088A 088B 088C 088E 0892 0893 0894 0F12 0F32 0F91 152E 153F 1541 16CC 16D7 20A1 23D3 23D5 2530 2580 2586 25B6 262E 29F9 29FA 2A76'.split()
        self.assertEqual(ids,{'message:'+n for n in expected})
        for id in ids:
            for metadata in ({},{'runtime_requirements':[]}):
                with self.assertRaisesRegex(ValueError,'complete unconfigured resident module'):
                    verify_requirements([{'id':id,**metadata}],rom,{},None,None,matches={})

    @unittest.skipUnless((MODULE_DIR/'module.json').is_file(), 'Compiled module stays local')
    def test_preparation_dependency_requires_new_entry_hook_even_if_metadata_is_absent(self):
        rom = verified_rom(ROM_PATH.read_bytes());data,_ = source(rom,'ordinary')
        module = json.loads((MODULE_DIR/'module.json').read_text())
        additions = {MODULE_VROM:(MODULE_DIR/'module.bin').read_bytes()}
        installed = {};install(rom,installed,additions,module)
        verify_requirements([{'id':'message:084A'}],rom,installed,additions,module)
        damaged = bytearray(installed[SPEC.vrom]);at = 0x80921324-SPEC.ram
        damaged[at:at+8] = data[at:at+8]
        with self.assertRaisesRegex(ValueError,'complete English dialogue-date patch'):
            verify_requirements([{'id':'message:084A'}],rom,{**installed,SPEC.vrom:bytes(damaged)},additions,module)

    @unittest.skipUnless((ROOT/'build/gamecube/text/message.jsonl').is_file(), 'English disc stays local')
    def test_complete_birthday_references_preserve_every_nonmenu_byte_and_branch(self):
        rom = verified_rom(ROM_PATH.read_bytes());info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == 'message').entries()
        refs = {r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}
        matches = load_matches(ROOT/'translations/reference_matches.json')
        contexts = load_contextual_choices(matches)
        for n in ('088A','088B','088C','2586'):
            id = 'message:'+n;record = matches[id];src = sources[int(n,16)]
            self.assertEqual(record['runtime_requirements'],[REQUIREMENT])
            text,_ = adapt_choice_reference(refs[id],src,record,info)
            text,_ = adapt_reference(text,src,info,'reference_layout',True)
            base = encode(text,info);output = display_candidate(id,src,base,contexts,info)
            self.assertEqual(canonical_candidate(id,src,output,contexts,info),base)
            reference = encode(refs[id]['text'],info)
            menu = unique_menu(reference,info)
            self.assertEqual(output[:menu.offset],reference[:menu.offset])
            self.assertEqual(output[menu.offset+len(menu.data):],reference[menu.offset+len(menu.data):])
            self.assertEqual(unique_menu(output,info).data,bytes.fromhex(
                '7F170127016200C4' if n == '2586' else '7F16002100C4'))
            validate_entry(src,base,info,'message','reference_layout',resident_runtime=True)
            self.assertLessEqual(expanded_bound(output,info),1024)
        self.assertIn('{cmd:7F32}',refs['message:2586']['text'])
        self.assertNotIn('{cmd:7F33}',refs['message:2586']['text'])
        for n,value in (('259D','0005'),('259E','0003'),('259F','0069')):
            self.assertTrue(refs['message:'+n]['text'].startswith('{cmd:7F0C05'+value+'}'))

    def test_original_letter_question_retains_both_native_answers_and_complete_controls(self):
        rom = verified_rom(ROM_PATH.read_bytes());info = module_command_info(rom)
        sources = next(b for b in banks(rom) if b.name == 'message').entries()
        rows = json.loads((ROOT/'translations/n64-letter-question.json').read_text())
        self.assertEqual(len(rows),1);row = rows[0]
        self.assertEqual(row['id'],'message:1C6F')
        self.assertEqual(sha256(sources[0x1C6F]),row['source_sha256'])
        output = encode(row['translation'],info)
        controls = lambda data:[t.data for t in tokenize(data,info) if t.kind == 'cmd']
        self.assertEqual(controls(output),controls(sources[0x1C6F]))
        self.assertEqual(sources[0x1C72],b'\x7f\x00')
        self.assertEqual(unique_menu(output,info).data,bytes.fromhex('7F1600DA00EC'))
        validate_entry(sources[0x1C6F],output,info,'message','exact')
