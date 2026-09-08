"""Contextual labels retain complete approved dialogue and native answer routes."""

from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import sha256
from build import apply_translations
from contextual_choices import (canonical_candidate, contextualize_edits, display_candidate,
    load_contextual_choices, MissingChoiceLabels, unique_menu, validate_labels)
from contextual_choice_test_scenario import native_choice_width
from gc_adapter import adapt_reference
from reference_choices import adapt_choice_reference, validate_choice_candidate
from reference_matches import load_matches
from runtime_module import module_command_info
from textbanks import banks
from textcodec import decode, encode, tokenize
from textvalidate import validate_entry
from test_retail import ROM_PATH


class ContextualChoiceTests(unittest.TestCase):
    def setUp(self):
        self.info = [(2, 0)]*0x61
        self.info[0x16] = (6, 0)
        self.info[0x17] = (8, 0)
        self.info[0x0F] = self.info[0x10] = (4, 0)
        self.native = bytes.fromhex('7F1600CD00CE')
        self.display = bytes.fromhex('7F1600250026')
        ending = bytes.fromhex('7F0F12347F1056787F01')
        self.source = b'Native'+self.native+ending
        self.base = b'English\xcd'+self.native+ending
        self.final = b'English\xcd'+self.display+ending
        self.sources = [b'Original']*460
        self.edits = [dict(id='select:0025', source_sha256=sha256(b'Original'), translation="That's right!"),
                      dict(id='select:0026', source_sha256=sha256(b'Original'), translation="That's wrong!")]
        self.row = dict(id='message:0000', source_sha256=sha256(self.source),
            candidate_sha256=sha256(self.base), display_sha256=sha256(self.final),
            native_command=self.native.hex().upper(), display_command=self.display.hex().upper(),
            offset=8, evidence='Synthetic paired answer labels.',
            labels=[dict(id=e['id'],source_sha256=e['source_sha256'],
                         encoded_sha256=sha256(encode(e['translation'],self.info))) for e in self.edits])
        self.matches = {'message:0000':dict(source_sha256=sha256(self.source),native_choices={
            'native_command':self.row['native_command'],'adapted_sha256':sha256(self.base)})}
        self.approvals = {'message:0000':self.row}

    def load_rows(self, rows, matches=None):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'rules.json'; path.write_text(json.dumps(rows))
            return load_contextual_choices(self.matches if matches is None else matches,path)

    def test_complete_menu_only_transform_and_independent_reverse(self):
        self.assertEqual(self.load_rows([self.row]),self.approvals)
        self.assertEqual(display_candidate('message:0000',self.source,self.base,self.approvals,self.info),self.final)
        self.assertEqual(canonical_candidate('message:0000',self.source,self.final,self.approvals,self.info),self.base)
        self.assertEqual(len(self.base),len(self.final))
        validate_entry(self.source,self.base,self.info,'message','exact')
        with self.assertRaisesRegex(ValueError,'Control signature changed'):
            validate_entry(self.source,self.final,self.info,'message','exact')
        validate_labels(self.row,{r['id']:r for r in self.edits},self.sources,self.info)

    def test_schema_duplicates_counts_labels_and_complete_parent_binding(self):
        mutations=[{'offset':True},{'offset':-1},{'offset':1024},{'evidence':''},
                   {'display_command':'7F17002500260027'},{'display_command':self.row['native_command']},
                   {'display_sha256':'bad'},{'unknown':True},{'labels':[]},
                   {'labels':[self.row['labels'][0]]*2}]
        for mutation in mutations:
            with self.subTest(mutation=mutation),self.assertRaises(ValueError):
                self.load_rows([{**self.row,**mutation}])
        for rows in ({},[self.row,self.row],[None]):
            with self.assertRaises(ValueError):self.load_rows(rows)
        with self.assertRaisesRegex(ValueError,'complete native-menu approval'):
            self.load_rows([self.row],{})
        changed=deepcopy(self.row);changed['labels'][0]['id']='select:01CC'
        with self.assertRaises(ValueError):self.load_rows([changed])

    def test_source_text_layout_menu_and_payload_mutations_fail(self):
        for source,base in ((self.source+b' ',self.base),(self.source,self.base+b' '),
                            (self.source,self.base.replace(b'\xcd',b' '))):
            with self.assertRaises(ValueError):
                display_candidate('message:0000',source,base,self.approvals,self.info)
        for candidate in (self.base,self.final+b' ',self.final.replace(b'\x12\x34',b'\x12\x35'),
                          self.final.replace(self.display,bytes.fromhex('7F1600260025'))):
            with self.assertRaises(ValueError):
                canonical_candidate('message:0000',self.source,candidate,self.approvals,self.info)
        with self.assertRaises(ValueError):unique_menu(self.base+self.native,self.info)
        with self.assertRaises(ValueError):unique_menu(b'No menu',self.info)

    def test_destination_label_hashes_plain_text_and_presence_are_mandatory(self):
        edits={r['id']:r for r in self.edits}
        with self.assertRaises(MissingChoiceLabels):
            validate_labels(self.row,{'select:0025':edits['select:0025']},self.sources,self.info)
        for field,value in (('translation','Wrong'),('source_sha256','0'*64)):
            changed=deepcopy(edits);changed['select:0025'][field]=value
            with self.assertRaises(ValueError):validate_labels(self.row,changed,self.sources,self.info)
        with self.assertRaises(ValueError):validate_labels(self.row,edits,[b'Other']*460,self.info)
        for text in ('', 'A'*21, '{cmd:7F00}'):
            changed=deepcopy(edits);changed['select:0025']['translation']=text
            row=deepcopy(self.row);row['labels'][0]['encoded_sha256']=sha256(encode(text,self.info))
            with self.assertRaises(ValueError):validate_labels(row,changed,self.sources,self.info)

    def test_generation_changes_only_registered_edits_or_withholds_missing_labels(self):
        message=dict(id='message:0000',source_sha256=sha256(self.source),
                     translation=decode(self.base,self.info),control_policy='exact')
        edits=[message,*self.edits]
        result,changed,withheld=contextualize_edits(edits,[self.source],self.sources,self.approvals,self.info)
        self.assertEqual(changed,['message:0000']);self.assertEqual(withheld,[])
        self.assertEqual(encode(result[0]['translation'],self.info),self.final)
        self.assertEqual(result[1:],self.edits)
        self.assertEqual(edits[0],message)
        result,changed,withheld=contextualize_edits(edits[:-1],[self.source],self.sources,self.approvals,self.info)
        self.assertEqual(result,self.edits[:1]);self.assertEqual(changed,[])
        self.assertEqual(withheld,[dict(id='message:0000',reason='Contextual menu requires complete English labels')])
        with self.assertRaises(ValueError):contextualize_edits(edits+[message],[self.source],self.sources,self.approvals,self.info)
        self.assertEqual(display_candidate('message:0001',self.source,self.base,self.approvals,self.info),self.base)

    def test_native_width_rounds_up_to_even_pixels_without_changing_glyph_advances(self):
        advances={ord('A'):6,ord('.'):5,ord('i'):4}
        self.assertEqual(native_choice_width(b'A.',advances),12)
        self.assertEqual(native_choice_width(b'Ai',advances),10)
        self.assertEqual(native_choice_width(b'',advances),0)
        self.assertEqual(advances,{ord('A'):6,ord('.'):5,ord('i'):4})

    def test_original_parent_requires_explicit_kind_and_no_reference_collision(self):
        row = {**self.row, 'source_kind': 'native_original'}
        self.assertEqual(self.load_rows([row], {}), {'message:0000': row})
        with self.assertRaisesRegex(ValueError, 'cannot override'):
            self.load_rows([row])
        for kind in (None, '', 'draft', [], True):
            with self.assertRaises(ValueError):
                self.load_rows([{**row, 'source_kind': kind}], {})
        self.assertEqual(self.load_rows([{**self.row, 'source_kind': 'gamecube'}])['message:0000']['source_kind'],
                         'gamecube')

    def test_original_parent_still_checks_every_native_command_independent_of_hashes(self):
        row = {**self.row, 'source_kind': 'native_original'}
        approvals = self.load_rows([row], {})
        self.assertEqual(display_candidate('message:0000', self.source, self.base, approvals, self.info), self.final)
        for base in (self.base.replace(bytes.fromhex('7F0F1234'), bytes.fromhex('7F0F1235')),
                     self.base.replace(bytes.fromhex('7F01'), bytes.fromhex('7F00')),
                     b'\x7f\x04'+self.base, self.base+b'\x7f\x1a'):
            row = {**self.row, 'source_kind': 'native_original', 'candidate_sha256': sha256(base),
                   'offset': unique_menu(base, self.info).offset}
            approvals = self.load_rows([row], {})
            with self.assertRaisesRegex(ValueError, 'changes a native command'):
                display_candidate('message:0000', self.source, base, approvals, self.info)

    def test_unchanged_native_menu_requires_explicit_kind_and_exact_reference_parent(self):
        row = {**self.row, 'source_kind': 'gamecube_native_menu'}
        match = dict(id=row['id'], source_sha256=row['source_sha256'],
                     reference_id=row['id'], reference_sha256=row['candidate_sha256'])
        approvals = self.load_rows([row], {row['id']: match})
        self.assertEqual(display_candidate(row['id'], self.source, self.base, approvals, self.info), self.final)
        self.assertEqual(canonical_candidate(row['id'], self.source, self.final, approvals, self.info), self.base)
        for change in ({'source_sha256': '0'*64}, {'reference_id': 'message:0001'},
                       {'reference_sha256': '0'*64}, {'native_choices': {}}):
            with self.assertRaisesRegex(ValueError, 'complete unchanged native-menu reference'):
                self.load_rows([row], {row['id']: {**match, **change}})
        with self.assertRaises(ValueError):
            self.load_rows([row], {})
        with self.assertRaisesRegex(ValueError, 'complete native-menu approval'):
            self.load_rows([self.row], {row['id']: match})


@unittest.skipUnless(ROM_PATH.is_file(),'Retail ROM remains local')
class ContextualChoiceRetailTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=ROM_PATH.read_bytes();cls.info=module_command_info(cls.rom)
        cls.sources={b.name:b.entries() for b in banks(cls.rom)}
        cls.matches=load_matches(ROOT/'translations/reference_matches.json')
        cls.approvals=load_contextual_choices(cls.matches)

    def reference_edits(self):
        path=ROOT/'build/gamecube/text/select.jsonl'
        if not path.is_file():self.skipTest('English disc extraction stays local')
        refs={r['id']:r for r in map(json.loads,path.read_text().splitlines())}
        overrides={r['id']:r for r in json.loads((ROOT/'translations/n64-native-menus.json').read_text())}
        result={}
        for row in self.approvals.values():
            for label in row['labels']:
                id=label['id'];source=self.sources['select'][int(id[7:],16)]
                result[id]=overrides.get(id,dict(id=id,source_sha256=sha256(source),translation=refs[id]['text']))
        return result

    def reference_base(self,id):
        path=ROOT/'build/gamecube/text/message.jsonl'
        if not path.is_file():self.skipTest('English disc extraction stays local')
        ref=next(r for r in map(json.loads,path.read_text().splitlines()) if r['id']==id)
        source=self.sources['message'][int(id[8:],16)]
        text,_=adapt_choice_reference(ref,source,self.matches[id],self.info)
        text,_=adapt_reference(text,source,self.info,'reference_layout',resident_runtime=True)
        return source,encode(text,self.info)

    def test_all_reference_display_labels_preserve_complete_base_and_actions(self):
        self.assertEqual(len(self.approvals),26)
        labels=self.reference_edits()
        self.assertEqual(len(labels),16)
        reference_approvals = {id: row for id, row in self.approvals.items()
                               if row.get('source_kind') != 'native_original'}
        self.assertEqual(len(reference_approvals), 24)
        for id,row in reference_approvals.items():
            source,base=self.reference_base(id)
            output=display_candidate(id,source,base,self.approvals,self.info)
            self.assertEqual(canonical_candidate(id,source,output,self.approvals,self.info),base)
            validate_choice_candidate(id,source,base,self.matches)
            validate_entry(source,base,self.info,'message','reference_layout',resident_runtime=True)
            validate_labels(row,labels,self.sources['select'],self.info)
            before=unique_menu(base,self.info);after=unique_menu(output,self.info)
            self.assertEqual(base[:before.offset],output[:after.offset])
            self.assertEqual(base[before.offset+len(before.data):],output[after.offset+len(after.data):])
            branches=lambda data:[t.data for t in tokenize(data,self.info) if t.kind=='cmd' and 0x0e<=t.data[1]<=0x15]
            self.assertEqual(branches(source),branches(output),id)

    def test_no_global_symbol_replacement_and_moderate_answer_is_retained(self):
        shape_ids='0B38 0B3D 0B3F 0B40 0B41 0B42 13E8 2C8F 2C91 2C92 2C93 2C95 2C96 2C98'.split()
        for number in shape_ids:self.assertNotIn('message:'+number,self.approvals)
        self.assertEqual(self.approvals['message:1FAE']['display_command'],'7F1600510103')
        self.assertEqual(self.approvals['message:136E']['display_command'],'7F16001E00F9')
        self.assertEqual(self.approvals['message:1868']['display_command'],'7F1600270056')
        self.assertEqual(self.approvals['message:20CA']['display_command'],'7F1600030004')

    def test_builder_rejects_unmapped_or_altered_payload_and_missing_label_without_metadata(self):
        source,base=self.reference_base('message:0B67')
        final=display_candidate('message:0B67',source,base,self.approvals,self.info)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edits.json'
            for data in (base,final+b' ',final):
                path.write_text(json.dumps([dict(id='message:0B67',source_sha256=sha256(source),
                    translation=decode(data,self.info),control_policy='reference_layout')]))
                with self.assertRaisesRegex(ValueError,'contextual display approval|complete English labels'):
                    apply_translations(self.rom,{},path)

    def test_four_connected_originals_keep_every_native_command_and_exit(self):
        drafts=json.loads((ROOT/'translations/n64-contextual-choice-replies.json').read_text())
        self.assertEqual({r['id'] for r in drafts},{'message:'+n for n in ('186E','187B','1880','1CE3')})
        commands=lambda data:[t.data for t in tokenize(data,self.info) if t.kind=='cmd']
        for row in drafts:
            source=self.sources['message'][int(row['id'][8:],16)];output=encode(row['translation'],self.info)
            self.assertEqual(sha256(source),row['source_sha256'])
            self.assertEqual(commands(source),commands(output))
            validate_entry(source,output,self.info,'message','exact')
        text={r['id']:r['translation'] for r in drafts}
        self.assertIn('{cmd:7F13187B1880}',text['message:186E'])
        self.assertIn('{cmd:7F10186E}',text['message:187B'])
        self.assertIn('{cmd:7F101872}',text['message:1880'])
        self.assertTrue(text['message:1CE3'].endswith('{cmd:7F00}'))


if __name__=='__main__':unittest.main()
