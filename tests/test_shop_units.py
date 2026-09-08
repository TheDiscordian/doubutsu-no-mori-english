"""Native shop counters, complete imports, and the sapling identity correction."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,CODE_VROM,CODE_RAM,sha256
from build import apply_translations
from shop_unit_smoke import relocated
from runtime_module import module_command_info
from shop_units import (SHOPS,IDS,FIRST,END,BASES,GRAPH_OFFSETS,candidates,permits,
                        source_entries,verify_callers,verify_shop,unit_id)
from textbanks import Bank,banks
from textcodec import encode
from textvalidate import validate_entry
from test_retail import ROM_PATH

ITEMS=(0x1000,0x2000,0x2400,0x2200,0x2F00,0x2300,0x2901,0x2900)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/string.jsonl').is_file(),
                     'Supplied retail sources stay local')
class ShopUnitTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM_PATH.read_bytes();cls.info=module_command_info(cls.rom);cls.files=by_vrom(cls.rom)
        cls.refs={r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        cls.inv={r['id']:r for r in map(json.loads,(ROOT/'build/inventory/string.jsonl').read_text().splitlines())}
        cls.edits=candidates(cls.rom,cls.refs,cls.inv,cls.info);cls.originals=source_entries(cls.rom)

    def test_complete_group_including_thirty_intentional_empty_counters(self):
        self.assertEqual(len(self.edits),120)
        approvals=permits(self.rom,list(self.edits.values()),self.info)
        empty=[];grown=[]
        for id,edit in self.edits.items():
            original=self.originals[int(id[7:],16)];value=encode(edit['translation'],self.info)
            validate_entry(original,value,self.info,'string',shop_unit_permit=approvals[id])
            if not value:empty.append(int(id[7:],16))
            if len(value)>len(original):
                grown.append(id)
                with self.assertRaisesRegex(ValueError,'entry budget'):
                    validate_entry(original,value,self.info,'string')
        self.assertEqual(empty,list(range(0x593,0x5A2))+list(range(0x5B1,0x5C0)))
        self.assertEqual(len(grown),89)
        self.assertEqual(len(self.edits)-len(grown)-len(empty),1)

    def test_all_five_original_actors_and_every_family_count(self):
        verify_callers(self.rom)
        for spec in SHOPS.values():
            data,reloc=(self.files[v].extract(self.rom) for v in (spec.vrom,spec.relocation))
            self.assertLessEqual(0x10+spec.resident_bytes+len(reloc)+16,0x7000-16)
            categories=verify_shop(spec,data,reloc)
            self.assertEqual(set(b''.join(categories)),set(range(8)))
            for family,item in enumerate(ITEMS):
                for count in range(1,16):
                    self.assertEqual(unit_id(spec,data,reloc,item,count),BASES[family]+count-1)
            for item,count in ((0x1000,0),(0x1000,16),(0x21FF,1),(-1,1),(0x10000,1)):
                with self.assertRaises(ValueError):unit_id(spec,data,reloc,item,count)
            for base in (0x801A0000,0x802F0000):
                loaded=relocated(spec,data,reloc,base)
                at=spec.pointers-spec.ram
                self.assertEqual(struct.unpack_from('>16I',loaded,at),
                                 tuple(base+at-0x300+off for off in GRAPH_OFFSETS))
                self.assertEqual(loaded[at+0xA0:at+0xC0],struct.pack('>8I',*BASES))

    def test_complete_references_and_explicit_native_sapling_meaning(self):
        for index,id in enumerate(IDS):
            if index<105:
                self.assertEqual(self.edits[id]['translation'],self.refs[id]['text'])
                self.assertEqual(encode(self.inv[id]['legacy'],self.info),encode(self.refs[id]['text'],self.info))
            else:
                self.assertEqual(self.edits[id]['translation'],'sapling' if index==105 else 'saplings')
                self.assertEqual(self.edits[id]['status'],'draft')
                self.assertEqual(self.inv[id]['source'],'かぶ')
                self.assertEqual(self.refs[id]['text'],'turnip' if index==105 else 'turnips')
        native=next(b for b in banks(self.rom) if b.name=='item_29').entries()[0]
        self.assertEqual(native,encode('きのなえ',self.info).ljust(10,b' '))

    def test_partial_stale_changed_plural_or_wrong_sapling_values_fail(self):
        edits=list(self.edits.values())
        for bad in (edits[:-1],edits+[edits[0]]):
            with self.assertRaises(ValueError):permits(self.rom,bad,self.info)
        for index,field,value in ((0,'source_sha256','0'*64),(0,'control_policy','presentation'),
                                  (1,'translation','piece'),(45,'translation','tool'),
                                  (105,'translation','turnip'),(119,'translation','sapling')):
            bad=deepcopy(edits);bad[index][field]=value
            with self.assertRaises(ValueError):permits(self.rom,bad,self.info)
        for field,value in (('sha256','0'*64),('text','short')):
            refs=deepcopy(self.refs);refs[IDS[0]][field]=value
            with self.assertRaises(ValueError):candidates(self.rom,refs,self.inv,self.info)
        inventory=deepcopy(self.inv);inventory[IDS[0]]['legacy']='short'
        with self.assertRaises(ValueError):candidates(self.rom,self.refs,inventory,self.info)

    def test_capacity_cannot_transfer_to_another_bank_payload_or_policy(self):
        approval=permits(self.rom,list(self.edits.values()),self.info)[IDS[0]]
        original=self.originals[FIRST];value=encode(self.edits[IDS[0]]['translation'],self.info)
        for bank,policy,new in (('message','exact',value),('string','presentation',value),
                               ('string','exact',value+b's'),('string','exact',b'')):
            with self.assertRaisesRegex(ValueError,'Shop-unit capacity'):
                validate_entry(original,new,self.info,bank,policy,shop_unit_permit=approval)
        with self.assertRaisesRegex(ValueError,'Shop-unit capacity'):
            validate_entry(original,value,self.info,'string',shop_unit_permit=approval,resetti_permit=object())

    def test_changed_actors_relocations_or_free_string_helpers_reject(self):
        for spec in SHOPS.values():
            for vrom in (spec.vrom,spec.relocation):
                value=bytearray(self.files[vrom].extract(self.rom));value[-1]^=1
                with self.assertRaisesRegex(ValueError,'shop actor'):
                    verify_callers(self.rom,{vrom:bytes(value)})
        code=bytearray(self.files[CODE_VROM].extract(self.rom));code[0x8009D6D4-CODE_RAM]^=1
        with self.assertRaisesRegex(ValueError,'free-string'):
            verify_callers(self.rom,{CODE_VROM:bytes(code)})

    def test_independent_builder_no_resident_growth_and_every_other_entry_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edits.json';path.write_text(json.dumps(list(self.edits.values())))
            original=self.files[CODE_VROM].extract(self.rom);replacements={CODE_VROM:original}
            count,relocations=apply_translations(self.rom,replacements,path,english_shop_units=True)
            self.assertEqual(count,120);self.assertEqual(relocations,{0xD16000:0x2600000})
            self.assertEqual(set(replacements),{CODE_VROM,0xD16000,0xD18000})
            actual=Bank('string',0,0,replacements[0xD16000],replacements[0xD18000]).entries()
            expected=list(self.originals)
            for id,edit in self.edits.items():expected[int(id[7:],16)]=encode(edit['translation'],self.info)
            self.assertEqual(actual,expected)
            code=bytearray(replacements[CODE_VROM]);at=0x800C3F1C-CODE_RAM
            code[at:at+8]=original[at:at+8];self.assertEqual(code,original)
            with self.assertRaisesRegex(ValueError,'entry budget'):
                apply_translations(self.rom,{CODE_VROM:original},path)
            bad=list(self.edits.values())+[{'id':'string:0001','source_sha256':sha256(self.originals[1]),'translation':'x'*10}]
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'entry budget'):
                apply_translations(self.rom,{CODE_VROM:original},path,english_shop_units=True)


if __name__=='__main__':unittest.main()
