"""Complete donor content, stable links, bounds, and unchanged existing English."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,n64_checksum
from gc_text import decode_gc
from gc_adapter import remove_redundant_article_suppression
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import tokenize,encode
import v3_camper_text as runtime
OUTPUT=ROOT/'build/v3-camper-text-runtime-03'


class CamperTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.text=cls.report['camper_text'];cls.info=module_command_info(cls.rom)

    def bank(self,files,rom,data,table):
        return Bank('test',data,table,files[data].extract(rom),files[table].extract(rom)).entries()

    def test_complete_message_choice_installation_preserves_every_existing_record(self):
        extra,choices,report=runtime.convert(self.base)
        self.assertEqual((len(extra),len(choices)),(253,49))
        self.assertEqual(report['highest_expanded_bound'],827)
        self.assertEqual(report['messages'],self.text['messages'])
        self.assertEqual(report['choices'],self.text['choices'])
        self.assertEqual(report['trade_alias']['count'],8)
        for source,target,table,more,count in (
            (runtime.OLD_MESSAGE,runtime.MESSAGE,runtime.TABLE,extra,11754),
            (runtime.CHOICES,runtime.CHOICES,runtime.CHOICE_TABLE,choices,462)):
            old=self.bank(self.old,self.base,source,table)
            new=self.bank(self.files,self.rom,target,table)
            self.assertEqual(len(old),count);self.assertEqual(new,old+more)

    def test_every_donor_line_pause_page_expression_trade_and_ending_is_preserved(self):
        donor,_,tables=runtime.donor()
        new=self.bank(self.files,self.rom,runtime.MESSAGE,runtime.TABLE)[11754:]
        choices={r['id']:r['donor_id'] for r in self.text['choices']}
        alias_count=0
        for i,data in enumerate(new):
            number=runtime.DONOR_FIRST+i;restored=bytearray(data)
            for token in tokenize(data,self.info):
                if token.kind=='cmd' and 14<=token.data[1]<=24:
                    for at in range(2,len(token.data),2):
                        target=int.from_bytes(token.data[at:at+2],'big')
                        if token.data[1]<=21:
                            self.assertTrue(11754<=target<12007)
                            value=target-11754+runtime.DONOR_FIRST
                        else: value=choices[target]
                        struct.pack_into('>H',restored,token.offset+at,value)
            expected,_=remove_redundant_article_suppression(decode_gc(donor[number],tables))
            expected=encode(expected,self.info)
            alias_count+=expected.count(bytes.fromhex('7f0c030017'))
            expected=expected.replace(bytes.fromhex('7f0c030017'),bytes.fromhex('7f0c03000d'))
            self.assertEqual(restored,expected,number)
            for token in tokenize(data,self.info):
                if token.kind=='cmd' and token.data[:3]==bytes.fromhex('7f0c03'):
                    self.assertIn(int.from_bytes(token.data[3:],'big'),range(1,23))
        self.assertEqual(alias_count,8)

    def test_only_text_storage_native_limits_and_startup_change(self):
        self.assertEqual(len(self.files),len(self.old))
        self.assertEqual(set(self.files),(set(self.old)-{runtime.OLD_MESSAGE})|{runtime.MESSAGE})
        changed={runtime.BLOB,runtime.MODULE,CODE_VROM,0x19D40,runtime.TABLE,runtime.CHOICES,runtime.CHOICE_TABLE}
        for vrom in set(self.old)&set(self.files):
            if vrom not in changed:
                self.assertEqual(self.files[vrom].extract(self.rom),self.old[vrom].extract(self.base))
        code=bytearray(self.files[CODE_VROM].extract(self.rom))
        for hook in self.text['hooks']:
            at=hook['address']-CODE_RAM
            self.assertEqual(code[at:at+4],bytes.fromhex(hook['after']))
            code[at:at+4]=bytes.fromhex(hook['before'])
        self.assertEqual(code,self.old[CODE_VROM].extract(self.base))
        self.assertFalse(self.text['summer_selector_installed'])
        self.assertFalse(self.text['selected_camping_rewards_installed'])
        self.assertFalse(self.text['saved_format_changed'])

    def test_all_physical_storage_is_in_cartridge_and_old_sources_are_retained(self):
        for row in self.text['resources']:
            self.assertLessEqual(row['vrom']+row['bytes'],0x04000000)
            start,end=row['physical'],row['physical']+row['bytes']
            self.assertLessEqual(end,len(self.rom));self.assertEqual(self.base[start:end],bytes(end-start))
            self.assertEqual(sha256(self.rom[start:end]),row['sha256'])
            original=self.old[row['old_vrom']]
            self.assertEqual(self.rom[original.pstart:original.pstart+original.size],
                             self.base[original.pstart:original.pstart+original.size])
            self.assertEqual(self.files[row['vrom']].index,original.index)
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))

    def test_bank_tail_count_corruption_rejected(self):
        data=self.old[runtime.CHOICES].extract(self.base);table=self.old[runtime.CHOICE_TABLE].extract(self.base)
        with self.assertRaises(ValueError): runtime.extend_bank(data,table,[b'one'],461)
        with self.assertRaises(ValueError): runtime.extend_bank(data,table[:-1]+b'X',[b'one'],462)


if __name__=='__main__': unittest.main()
