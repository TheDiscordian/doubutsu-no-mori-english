"""Numeric answers keep complete references and native selection meanings."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, verified_rom
from build import apply_translations
from contextual_choices import (canonical_candidate, contextualize_edits, display_candidate,
    load_contextual_choices, validate_labels, MissingChoiceLabels)
from extended_choices import (COUNT, DATA_VROM, TABLE_VROM, LIMITS, append_labels,
    bindings, payloads, verify_reference_labels, validate_binding, install)
from reference_choices import adapt_choice_reference, validate_choice_approval
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import Bank, banks
from textcodec import decode, encode, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH

IDS = ('message:2D01', 'message:2D06', 'message:2D0B')


class ExtendedChoiceTests(unittest.TestCase):
    def test_only_complete_registered_labels_have_extended_bindings(self):
        info = [(2, 0)]*0x61
        refs = {b['reference_id']: {'id': b['reference_id'], 'sha256': b['source_sha256'],
                 'text': payloads()[id].decode()} for id,b in bindings().items()}
        self.assertEqual(verify_reference_labels(refs,info),payloads())
        self.assertEqual(list(payloads().values()),[b'Less',b'More'])
        for id, binding in bindings().items():
            validate_binding(binding)
            for key,value in (('id','select:01CE'),('id',None),('id',[]),('reference_id','select:0000'),
                              ('source_sha256','0'*64),('encoded_sha256','0'*64),
                              ('source_kind','native')):
                with self.assertRaises(ValueError):validate_binding({**binding,key:value})
            for changed in ({}, {**refs,binding['reference_id']:{**refs[binding['reference_id']],'text':'X'}}):
                with self.assertRaises(ValueError):verify_reference_labels(changed,info)

    def test_extension_retains_all_original_entries_and_aligned_tail(self):
        table=struct.pack('>464I',*range(1,461),0,0,0,0)
        data=b'A'*460+bytes(4)
        output,indices=append_labels(data,table)
        self.assertEqual(Bank('select',0,0,output,indices).entries(),[b'A']*460+[b'Less',b'More'])
        self.assertEqual(len(output)%16,0)
        self.assertEqual(indices[:460*4],table[:460*4])
        self.assertEqual(indices[462*4:],bytes(8))
        for bad_data,bad_table in ((data[:-1]+b'X',table),(data,table[:460*4]+struct.pack('>I',460)+bytes(12)),
                                   (data,table[:-8]),(output,indices)):
            with self.assertRaises(ValueError):append_labels(bad_data,bad_table)
        with self.assertRaisesRegex(ValueError,'entry count'):
            Bank('select',0,0,data,table).rebuild([b'A']*462,allow_expand=True)


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/message.jsonl').is_file(),
                     'Supplied cartridge and disc data stays local')
class NumberGameRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=verified_rom(ROM_PATH.read_bytes());cls.info=module_command_info(cls.rom)
        cls.sources={b.name:b.entries() for b in banks(cls.rom)}
        cls.matches=load_matches(ROOT/'translations/reference_matches.json')
        cls.approvals=load_contextual_choices(cls.matches)
        cls.refs={r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/message.jsonl').read_text().splitlines())}

    def edited(self,id):
        source=self.sources['message'][int(id[8:],16)]
        text,_=adapt_choice_reference(self.refs[id],source,self.matches[id],self.info)
        base=encode(text,self.info);final=display_candidate(id,source,base,self.approvals,self.info)
        return source,base,final

    def test_complete_questions_keep_all_words_and_native_answer_destinations(self):
        for id in IDS:
            source,base,final=self.edited(id);ref=encode(self.refs[id]['text'],self.info)
            row=self.approvals[id];offset=row['offset']
            rebuilt=bytearray(final);rebuilt[offset:offset+6]=ref[offset:offset+6]
            if id=='message:2D01':rebuilt[125:133]=ref[125:133]
            self.assertEqual(bytes(rebuilt),ref)
            self.assertEqual(sha256(ref),self.refs[id]['sha256'])
            self.assertEqual(canonical_candidate(id,source,final,self.approvals,self.info),base)
            validate_entry(source,base,self.info,'message','reference_layout')
            branches=lambda raw:[t.data for t in tokenize(raw,self.info) if t.kind=='cmd' and 0x0F<=t.data[1]<=0x12]
            self.assertEqual(branches(final),branches(source))
            self.assertEqual(final[offset:offset+6],bytes.fromhex('7F1601CC01CD'))
            with self.assertRaises(MissingChoiceLabels):validate_labels(row,{},self.sources['select'],self.info)
            validate_labels(row,{},self.sources['select'],self.info,extended_labels=payloads())

    def test_answer_permutation_cannot_change_routes_or_drop_answers(self):
        record=deepcopy(self.matches[IDS[0]]);source=self.sources['message'][0x2D01]
        for permutation in ([0,1],[0,0],[1],[1,0,2],[True,0],None):
            changed=deepcopy(record);changed['native_choices']['answer_permutation']=permutation
            with self.assertRaises(ValueError):validate_choice_approval(changed)
        raw=encode(self.refs[IDS[0]]['text'],self.info)
        for before,after in (('7F0F2D03','7F0F2D04'),('7F102D02',''),
                             ('7F0F2D03','7F0F2D037F0301'),('7F102D02','7F112D02')):
            changed_raw=raw.replace(bytes.fromhex(before),bytes.fromhex(after));ref={**self.refs[IDS[0]],
                'text':decode(changed_raw,self.info),'sha256':sha256(changed_raw)}
            changed=deepcopy(record);changed['reference_sha256']=ref['sha256']
            with self.assertRaisesRegex(ValueError,'permutation'):
                adapt_choice_reference(ref,source,changed,self.info)

    def test_builder_installs_labels_and_count_only_for_validated_contexts(self):
        source,base,final=self.edited(IDS[0]);original=by_vrom(self.rom)[CODE_VROM].extract(self.rom)
        edit={'id':IDS[0],'source_sha256':sha256(source),'translation':decode(final,self.info),
              'control_policy':'reference_layout'}
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edits.json';path.write_text(json.dumps([edit]))
            replacements={CODE_VROM:original}
            count,_=apply_translations(self.rom,replacements,path)
            self.assertEqual(count,1)
            labels=Bank('select',DATA_VROM,TABLE_VROM,replacements[DATA_VROM],replacements[TABLE_VROM]).entries()
            self.assertEqual(labels,self.sources['select']+list(payloads().values()))
            for address,word in LIMITS.items():
                self.assertEqual(struct.unpack_from('>I',replacements[CODE_VROM],address-CODE_RAM)[0],
                                 (word&0xFFFF0000)|462)
            for bad in (base,final+b'!',final.replace(bytes.fromhex('7F0F2D02'),bytes.fromhex('7F0F2D03'))):
                path.write_text(json.dumps([{**edit,'translation':decode(bad,self.info)}]))
                with self.assertRaises(ValueError):apply_translations(self.rom,{CODE_VROM:original},path)
            replacements={CODE_VROM:original};apply_translations(self.rom,replacements,None)
            self.assertNotIn(DATA_VROM,replacements)
            self.assertEqual(replacements[CODE_VROM],original)

    def test_count_patch_overlap_fails_without_mutating_input(self):
        original=by_vrom(self.rom)[CODE_VROM].extract(self.rom)
        for address in LIMITS:
            code=bytearray(original);struct.pack_into('>I',code,address-CODE_RAM,0)
            replacements={CODE_VROM:bytes(code)};before=deepcopy(replacements)
            with self.assertRaisesRegex(ValueError,'count limit'):install(self.rom,replacements)
            self.assertEqual(replacements,before)

    def test_missing_labels_withhold_all_questions_and_metadata_cannot_override(self):
        edits=[]
        for id in IDS:
            source,base,_=self.edited(id)
            edits.append({'id':id,'source_sha256':sha256(source),'translation':decode(base,self.info)})
        approvals={id:self.approvals[id] for id in IDS}
        args=(edits,self.sources['message'],self.sources['select'],approvals,self.info)
        result,changed,withheld=contextualize_edits(*args)
        self.assertEqual(result,[]);self.assertEqual(changed,[])
        self.assertEqual({r['id'] for r in withheld},set(IDS))
        result,changed,withheld=contextualize_edits(*args,extended_labels=payloads())
        self.assertEqual(changed,list(IDS));self.assertEqual(withheld,[])
        row=self.approvals[IDS[0]]
        for extra in ({**payloads(),'select:01CC':b'Less!'},):
            with self.assertRaises(ValueError):validate_labels(row,{},self.sources['select'],self.info,extended_labels=extra)
        with self.assertRaises(ValueError):
            validate_labels(row,{'select:01CC':{'translation':'Less'}},self.sources['select'],self.info,extended_labels=payloads())
        self.assertNotIn('message:1772',self.approvals)


if __name__=='__main__':unittest.main()
