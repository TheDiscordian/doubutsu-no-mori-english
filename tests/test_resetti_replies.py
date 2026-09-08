"""Complete English dictionary and native substring-length preservation."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from build import apply_translations
from resetti_replies import (FIRST,END,IDS,VROM,RAM,RELOC_VROM,CHANGES,TABLE,TABLE_RAM,
                             TRANSITIONS,candidates,permits,patch,install,source_entries)
from textbanks import Bank
from textcodec import encode
from textvalidate import validate_entry
from runtime_module import module_command_info
from test_retail import ROM_PATH
from resetti_reply_smoke import relocated,cases


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/string.jsonl').is_file(),
                     'Supplied retail inputs remain local')
class ResettiReplyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM_PATH.read_bytes();cls.info=module_command_info(cls.rom)
        cls.refs={r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        cls.inventory={r['id']:r for r in map(json.loads,(ROOT/'build/inventory/string.jsonl').read_text().splitlines())}
        cls.edits=candidates(cls.rom,cls.refs,cls.inventory,cls.info)
        cls.originals=source_entries(cls.rom);cls.files=by_vrom(cls.rom)
        cls.data,cls.reloc=(cls.files[v].extract(cls.rom) for v in (VROM,RELOC_VROM))

    def test_complete_english_lengths_and_scoped_native_ten_byte_budget(self):
        approvals=permits(self.rom,list(self.edits.values()),self.info)
        self.assertEqual(len(approvals),32)
        grown=0
        for index,(id,edit) in enumerate(self.edits.items()):
            original=self.originals[int(id[7:],16)];value=encode(edit['translation'],self.info)
            self.assertEqual(len(value),2+sum(index>=edge for edge in TRANSITIONS))
            validate_entry(original,value,self.info,'string',resetti_permit=approvals[id])
            if len(value)>len(original):
                grown+=1
                with self.assertRaisesRegex(ValueError,'entry budget'):
                    validate_entry(original,value,self.info,'string')
            for bank,policy,data in (('message','exact',value),('string','presentation',value),
                                     ('string','exact',value+b'!')):
                with self.assertRaisesRegex(ValueError,'Resetti capacity'):
                    validate_entry(original,data,self.info,bank,policy,resetti_permit=approvals[id])
        self.assertEqual(grown,31)

    def test_generation_requires_all_source_legacy_reference_values(self):
        for container,field,value in (('refs','sha256','0'*64),('refs','text','Changed'),
                                      ('inventory','legacy','Short'),('inventory','source_sha256','0'*64)):
            refs,inventory=deepcopy(self.refs),deepcopy(self.inventory)
            (refs if container=='refs' else inventory)[IDS[0]][field]=value
            with self.assertRaises(ValueError): candidates(self.rom,refs,inventory,self.info)
        with self.assertRaises(ValueError): candidates(self.rom,{},self.inventory,self.info)

    def test_complete_group_cannot_be_dropped_shortened_or_reordered(self):
        edits=list(self.edits.values())
        for bad in (edits[:-1],edits+[edits[0]]):
            with self.assertRaises(ValueError):permits(self.rom,bad,self.info)
        for field,value in (('translation','no'),('source_sha256','0'*64),('control_policy','presentation')):
            bad=deepcopy(edits);bad[-1][field]=value
            with self.assertRaises(ValueError):permits(self.rom,bad,self.info)
        bad=deepcopy(edits)
        bad[2]['translation'],bad[3]['translation']=bad[3]['translation'],bad[2]['translation']
        with self.assertRaises(ValueError):permits(self.rom,bad,self.info)

    def test_only_two_words_and_existing_table_change(self):
        output=patch(self.data,self.reloc);restored=bytearray(output)
        self.assertEqual(len(output),len(self.data))
        for address,before,after in CHANGES:
            self.assertEqual(struct.unpack_from('>I',output,address-RAM)[0],after)
            struct.pack_into('>I',restored,address-RAM,before)
        at=TABLE_RAM-RAM;self.assertEqual(output[at:at+24],TABLE)
        restored[at:at+24]=self.data[at:at+24]
        self.assertEqual(restored,self.data)
        for v,blob in ((VROM,output),(RELOC_VROM,bytes(len(self.reloc)))):
            replacements={v:blob};before=deepcopy(replacements)
            with self.assertRaisesRegex(ValueError,'overlap'):install(self.rom,replacements)
            self.assertEqual(replacements,before)
        for data,reloc in ((bytes(len(self.data)),self.reloc),(self.data,bytes(len(self.reloc)))):
            with self.assertRaises(ValueError):patch(data,reloc)

    def test_byte_transition_table_drives_every_complete_word_length(self):
        values=[encode(self.edits[id]['translation'],self.info)for id in IDS]
        pointer,length=0,2
        for index,value in enumerate(values):
            if index==TABLE[pointer]:length+=1;pointer+=1
            self.assertEqual(length,len(value))
        self.assertEqual(pointer,8);self.assertEqual(TABLE[pointer],255)
        probes=cases(values)
        self.assertEqual(len(probes),227)
        self.assertEqual(sum(' at 'in label for label,_,_,_ in probes),126)
        for _,reply,_,expected in probes:
            self.assertEqual(len(reply),10)
            self.assertEqual(expected,int(any(reply[i:i+len(word)]==word
                for word in values for i in range(11-len(word)))))

    def test_two_native_relocation_bases_keep_the_compact_table_and_code(self):
        for base in (0x801A0000,0x802F8010):
            output=relocated(self.data,self.reloc,base)
            self.assertEqual(len(output),len(self.data))
            for address,_,after in CHANGES:
                self.assertEqual(struct.unpack_from('>I',output,address-RAM)[0],after)
            at=TABLE_RAM-RAM;self.assertEqual(output[at:at+24],TABLE)

    def test_builder_installs_without_growing_input_or_requiring_resident_code(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edits.json';path.write_text(json.dumps(list(self.edits.values())))
            original=self.files[CODE_VROM].extract(self.rom);replacements={CODE_VROM:original}
            count,relocations=apply_translations(self.rom,replacements,path,english_resetti_replies=True)
            self.assertEqual(count,32);self.assertEqual(relocations,{0xD16000:0x02600000})
            self.assertEqual(replacements[VROM],patch(self.data,self.reloc))
            self.assertNotIn(RELOC_VROM,replacements)
            entries=Bank('string',0,0,replacements[0xD16000],replacements[0xD18000]).entries()
            expected=list(self.originals)
            for id,edit in self.edits.items():expected[int(id[7:],16)]=encode(edit['translation'],self.info)
            self.assertEqual(entries,expected)
            code=bytearray(replacements[CODE_VROM]);at=0x800C3F1C-CODE_RAM
            code[at:at+8]=original[at:at+8];self.assertEqual(code,original)
            with self.assertRaisesRegex(ValueError,'entry budget'):
                apply_translations(self.rom,{CODE_VROM:original},path)
            bad=list(self.edits.values())+[{'id':'string:0001','source_sha256':sha256(self.originals[1]),'translation':'x'*10}]
            path.write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'entry budget'):
                apply_translations(self.rom,{CODE_VROM:original},path,english_resetti_replies=True)


if __name__=='__main__':unittest.main()
