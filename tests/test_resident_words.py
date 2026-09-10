"""Complete resident words, shared temporary bounds, and composed native patches."""

from copy import deepcopy
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
MODULE_DIR=Path(os.environ.get('AF_TEST_RUNTIME_MODULE',str(ROOT/'build/notice-seasonal-runtime')))
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,sha256
from build import apply_translations
from dialogue_dates import patch as date_patch, install as install_dates
from fortune_strings import STRING_RELOCATION
from npc_mail_show import source
from resident_words import (SPEC,IDS,CHANGES,TABLES,SCRATCH,SCRATCH_END,CALLS,
    candidates,permits,capacity,patch,relocated,install,caller_evidence,source_entries)
from runtime_module import add_runtime_module,module_command_info
from textbanks import Bank
from textcodec import encode
from textvalidate import validate_entry
from test_retail import ROM_PATH
from fortune_smoke import seed_for
from resident_word_smoke import random_draw,expected_preparer,prepared_tokens


class ResidentWordFixtureTests(unittest.TestCase):
    def test_all_native_pool_indices_and_float_bits(self):
        for index in range(32):
            seed,final,bits=seed_for(index)
            self.assertEqual(random_draw(seed,32),(final,bits,index))

    def test_outer_draw_counts_original_ranges_and_four_shop_levels(self):
        entries=[f'{i:04X}'.encode() for i in range(1562)]
        for group,expected_count in ((1,5),(2,4),(3,3)):
            for shop in range(4):
                values,draws=expected_preparer(entries,group,0,shop)
                self.assertEqual(len(draws),expected_count)
                seed=0
                for final,bits in draws:
                    seed=(seed*1664525+1013904223)&0xFFFFFFFF
                    self.assertEqual(final,seed);self.assertEqual(bits,(seed>>9)|0x3F800000)
                if group==2:
                    self.assertTrue(1<=int(values[0])<10)
                    self.assertTrue(10<=int(values[1])<99)
                    self.assertTrue(0<=int(values[2])<9)
                    self.assertEqual(values[3],entries[0x454+shop])
                else:self.assertEqual(len(values),expected_count)

    def test_only_fields_within_the_selected_request_interval(self):
        info=[(2,0)]*0x61;info[0x0C]=(5,0)
        entry=bytes.fromhex('7F317F0C0900017F317F357F0C0900027F347F357F0C0900037F33')
        self.assertEqual([t.offset for t in prepared_tokens(entry,info,1)],[7,9])
        self.assertEqual([t.offset for t in prepared_tokens(entry,info,2)],[16,18])
        self.assertEqual([t.offset for t in prepared_tokens(entry,info,3)],[25])

    def test_owned_native_workspace_and_expanded_local_fit_guards(self):
        self.assertLess(0x10+SPEC.resident_bytes+20+SPEC.sections[4]*4+16,0x5500-16)
        self.assertLess(SCRATCH-SPEC.ram+16,SPEC.resident_bytes)
        self.assertEqual(0x24+16,52)
        self.assertLessEqual(52,56)
        self.assertLessEqual(24+24+56,0x800)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/string.jsonl').is_file()
                     and (MODULE_DIR/'module.json').is_file(),
                     'Supplied sources and compiled module remain local')
class ResidentWordTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM_PATH.read_bytes();cls.info=module_command_info(cls.rom)
        cls.refs={r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        cls.inventory={r['id']:r for r in map(json.loads,(ROOT/'build/inventory/string.jsonl').read_text().splitlines())}
        cls.edits=candidates(cls.rom,cls.refs,cls.inventory,cls.info)
        cls.originals=source_entries(cls.rom);cls.data,cls.reloc=source(cls.rom,'ordinary')
        cls.replacements={}
        cls.additions,cls.module=add_runtime_module(cls.rom,cls.replacements,MODULE_DIR)

    def test_every_complete_value_and_scoped_capacity(self):
        approvals=permits(self.rom,list(self.edits.values()),self.info)
        self.assertEqual(len(approvals),136)
        for id,edit in self.edits.items():
            original=self.originals[int(id[7:],16)];value=encode(edit['translation'],self.info)
            self.assertEqual(value,encode(self.refs[id]['text'],self.info))
            self.assertEqual(value,encode(self.inventory[id]['legacy'],self.info))
            self.assertLessEqual(len(value),capacity(id))
            validate_entry(original,value,self.info,'string',resident_runtime=True,resident_word_permit=approvals[id])
            if len(value)>len(original):
                with self.assertRaisesRegex(ValueError,'entry budget'):
                    validate_entry(original,value,self.info,'string',resident_runtime=True)
        self.assertEqual({capacity(id) for id in IDS[-4:]},{10})
        self.assertEqual({capacity(id) for id in IDS[:-4]},{16})
        with self.assertRaises(ValueError):capacity('string:0314')

    def test_partial_stale_changed_or_reordered_values_fail(self):
        edits=list(self.edits.values())
        for bad in (edits[:-1],edits+[edits[0]]):
            with self.assertRaisesRegex(ValueError,'complete unique'):permits(self.rom,bad,self.info)
        for field,value in (('translation','short'),('source_sha256','0'*64),('control_policy','presentation')):
            bad=deepcopy(edits);bad[0][field]=value
            with self.assertRaises(ValueError):permits(self.rom,bad,self.info)
        bad=deepcopy(edits);bad[0]['translation'],bad[1]['translation']=bad[1]['translation'],bad[0]['translation']
        with self.assertRaises(ValueError):permits(self.rom,bad,self.info)

    def test_full_legacy_and_reference_agreement_is_required(self):
        for selected,field,value in (('refs','text','short'),('refs','sha256','0'*64),
                                     ('inventory','legacy','short'),('inventory','source_sha256','0'*64)):
            refs,inv=deepcopy(self.refs),deepcopy(self.inventory)
            (refs if selected=='refs' else inv)[IDS[0]][field]=value
            with self.assertRaises(ValueError):candidates(self.rom,refs,inv,self.info)

    def test_permit_cannot_transfer_bank_runtime_policy_payload_or_group(self):
        approval=permits(self.rom,list(self.edits.values()),self.info)[IDS[0]]
        original=self.originals[int(IDS[0][7:],16)];value=encode(self.edits[IDS[0]]['translation'],self.info)
        for bank,runtime,policy,new in (('message',True,'exact',value),('string',False,'exact',value),
                ('string',True,'presentation',value),('string',True,'exact',value+b'!'),('string',True,'exact',b'')):
            with self.assertRaisesRegex(ValueError,'Resident-word capacity'):
                validate_entry(original,new,self.info,bank,policy,resident_runtime=runtime,resident_word_permit=approval)
        with self.assertRaisesRegex(ValueError,'Resident-word capacity'):
            validate_entry(original,value,self.info,'string',resident_runtime=True,
                           resident_word_permit=approval,shop_unit_permit=object())

    def test_seven_words_preserve_all_other_code_and_bss_and_relocations(self):
        self.assertEqual(len(CHANGES),7);self.assertEqual(SCRATCH_END-SCRATCH,16)
        self.assertEqual(caller_evidence(self.rom)['helper_calls'],[f'{pc:08X}' for pc in CALLS])
        for dates in (False,True):
            original,expected_reloc=date_patch(self.data,self.reloc,self.module) if dates else (self.data,self.reloc)
            output,actual_reloc=patch(self.data,self.reloc,module=self.module,dates=dates)
            self.assertEqual(actual_reloc,expected_reloc);self.assertEqual(len(output),len(original))
            restored=bytearray(output)
            for pc,before,after in CHANGES:
                self.assertEqual(struct.unpack_from('>I',output,pc-SPEC.ram)[0],after)
                struct.pack_into('>I',restored,pc-SPEC.ram,before)
            self.assertEqual(restored,original)
            for pc,values in TABLES:
                self.assertEqual(struct.unpack_from('>'+str(len(values))+'I',output,pc-SPEC.ram),values)
            for base in (0x801A0000,0x802F8010):
                loaded=relocated(self.data,self.reloc,base,module=self.module,dates=dates)
                self.assertEqual(len(loaded),SPEC.resident_bytes)
                self.assertEqual(loaded[SPEC.file_bytes:],bytes(SPEC.sections[3]))
                for pc,_,after in CHANGES:self.assertEqual(struct.unpack_from('>I',loaded,pc-SPEC.ram)[0],after)

    def test_changed_native_bytes_and_unknown_predecessors_reject(self):
        for offset in (0,len(self.data)-1,*[pc-SPEC.ram for pc,_,_ in CHANGES]):
            data=bytearray(self.data);data[offset]^=1
            with self.assertRaises(ValueError):patch(bytes(data),self.reloc)
        reloc=bytearray(self.reloc);reloc[-1]^=1
        with self.assertRaises(ValueError):patch(self.data,bytes(reloc))
        for replacements in ({SPEC.vrom:b'bad'},{SPEC.relocation:b'bad'}):
            before=deepcopy(replacements)
            with self.assertRaisesRegex(ValueError,'unknown overlay patch'):install(self.rom,replacements,self.module)
            self.assertEqual(replacements,before)
        with self.assertRaisesRegex(ValueError,'resident item-field'):install(self.rom,{},None)

    def test_real_builder_composes_dates_and_preserves_other_strings_and_module(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edits.json';path.write_text(json.dumps(list(self.edits.values())))
            for dates in (False,True):
                replacements=deepcopy(self.replacements);additions=deepcopy(self.additions)
                if dates:install_dates(self.rom,replacements,additions,self.module)
                before=deepcopy(replacements)
                count,mapping=apply_translations(self.rom,replacements,path,runtime_module=MODULE_DIR,
                    module_additions=additions,english_resident_words=True)
                self.assertEqual(count,136);self.assertEqual(mapping,{0xD16000:STRING_RELOCATION[0]})
                expected=list(self.originals)
                for id,e in self.edits.items():expected[int(id[7:],16)]=encode(e['translation'],self.info)
                self.assertEqual(Bank('string',0,0,replacements[0xD16000],replacements[0xD18000]).entries(),expected)
                self.assertEqual(replacements[SPEC.vrom],patch(self.data,self.reloc,module=self.module,dates=dates)[0])
                self.assertEqual(additions,self.additions)
                code=bytearray(replacements[CODE_VROM]);at=STRING_RELOCATION[1]-CODE_RAM
                code[at:at+8]=before[CODE_VROM][at:at+8];self.assertEqual(code,before[CODE_VROM])
            with self.assertRaisesRegex(ValueError,'resident runtime'):
                apply_translations(self.rom,{},path,english_resident_words=True)
            with self.assertRaisesRegex(ValueError,'entry budget'):
                apply_translations(self.rom,deepcopy(self.replacements),path,runtime_module=MODULE_DIR,
                                   module_additions=self.additions)
            extra={'id':'string:0001','source_sha256':sha256(self.originals[1]),'translation':'x'*16}
            path.write_text(json.dumps(list(self.edits.values())+[extra]))
            with self.assertRaisesRegex(ValueError,'entry budget'):
                apply_translations(self.rom,deepcopy(self.replacements),path,runtime_module=MODULE_DIR,
                                   module_additions=self.additions,english_resident_words=True)


if __name__=='__main__':unittest.main()
