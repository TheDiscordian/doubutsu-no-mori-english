"""Complete native credits, identity corrections, and owned overlay storage."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from build import apply_translations
import credits_strings as c
from runtime_module import module_command_info
from textbanks import Bank
from textcodec import encode
from textvalidate import validate_entry
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file() and (ROOT/'build/gamecube/text/string.jsonl').is_file(),
                     'Supplied retail sources stay local')
class CreditsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = ROM_PATH.read_bytes(); cls.info = module_command_info(cls.rom)
        cls.files = by_vrom(cls.rom)
        cls.refs = {r['id']:r for r in map(json.loads,(ROOT/'build/gamecube/text/string.jsonl').read_text().splitlines())}
        cls.inv = {r['id']:r for r in map(json.loads,(ROOT/'build/inventory/string.jsonl').read_text().splitlines())}
        cls.edits = c.candidates(cls.rom,cls.refs,cls.inv,cls.info)
        cls.originals = c.source_entries(cls.rom)
        cls.data = cls.files[c.VROM].extract(cls.rom)
        cls.reloc = cls.files[c.RELOCATION].extract(cls.rom)

    def test_complete_rows_and_scoped_capacity(self):
        self.assertEqual(len(self.edits),110)
        approvals = c.permits(self.rom,list(self.edits.values()),self.info)
        values = [encode(self.edits[id]['translation'],self.info) for id in c.IDS]
        self.assertEqual(sum(len(v)>15 for v in values),58)
        self.assertEqual(sum(not v for v in values),17)
        self.assertLessEqual(max(map(len,values)),25)
        grown = 0
        for id,value in zip(c.IDS,values):
            original = self.originals[int(id[7:],16)]
            validate_entry(original,value,self.info,'string',credits_permit=approvals[id])
            if len(value)>len(original):
                grown += 1
                with self.assertRaisesRegex(ValueError,'entry budget'):
                    validate_entry(original,value,self.info,'string')
        self.assertGreater(grown,50)

    def test_native_identities_not_legacy_substitutions(self):
        for native,reference in c.REFERENCES.items():
            self.assertEqual(self.edits[f'string:{native:04X}']['translation'],
                             self.refs[f'string:{reference:04X}']['text'])
        # Legacy has these two contributors swapped; active English spellings
        # also differ from the older unused reference credits.
        self.assertEqual(self.edits['string:0520']['translation'],'   Kenshirou Ueda')
        self.assertEqual(self.edits['string:0521']['translation'],'   Kunio Watanabe')
        self.assertEqual(self.edits['string:0539']['translation'],'   Atsushi Nishiwaki')
        self.assertEqual(self.edits['string:050B']['translation'],'')
        self.assertEqual(self.inv['string:050B']['source'],' ')
        self.assertEqual(self.edits['string:054A']['translation'],'   Keizo Kato')
        self.assertEqual(self.edits['string:054B']['translation'],'   Minoru Narita')
        self.assertEqual(self.edits['string:0552']['translation'],'   Sarugakucho')
        self.assertEqual(self.edits['string:0554']['translation'],'   Hiroshi Yamauchi')
        self.assertNotIn('   Satoru Iwata',[e['translation'] for e in self.edits.values()])
        self.assertEqual(self.edits['string:052A']['translation'],'Data Processing Program')

    def test_incomplete_changed_or_wrong_identity_groups_reject(self):
        edits = list(self.edits.values())
        for bad in (edits[:-1],edits+[edits[0]]):
            with self.assertRaises(ValueError):c.permits(self.rom,bad,self.info)
        for id,field,value in (('string:054A','translation','   Takao Sawano'),
                              ('string:050B','translation','   Yumi Yoshimi'),
                              ('string:0552','translation',''),
                              ('string:04EA','source_sha256','0'*64),
                              ('string:04EA','control_policy','presentation')):
            bad = deepcopy(self.edits);bad[id][field] = value
            with self.assertRaises(ValueError):c.permits(self.rom,list(bad.values()),self.info)
        refs = deepcopy(self.refs);refs['string:07C1']['text']='   Atsushi Nishikawa'
        refs['string:07C1']['sha256']=sha256(encode(refs['string:07C1']['text'],self.info))
        with self.assertRaisesRegex(ValueError,'reference group'):
            c.candidates(self.rom,refs,self.inv,self.info)

    def test_permit_does_not_authorise_other_banks_or_payloads(self):
        id = 'string:04EA';original = self.originals[c.FIRST]
        value = encode(self.edits[id]['translation'],self.info)
        permit = c.permits(self.rom,list(self.edits.values()),self.info)[id]
        for bank,policy,new in (('message','exact',value),('string','presentation',value),
                               ('string','exact',value+b'!'),('string','exact',b'x'*26)):
            with self.assertRaisesRegex(ValueError,'Credits capacity'):
                validate_entry(original,new,self.info,bank,policy,credits_permit=permit)
        for other in ('fortune_permit','resetti_permit','shop_unit_permit','resident_word_permit'):
            with self.assertRaisesRegex(ValueError,'Credits capacity'):
                validate_entry(original,value,self.info,'string',credits_permit=permit,**{other:object()})

    def test_exact_seven_instruction_changes_and_one_bss_length(self):
        output,reloc = c.patch(self.data,self.reloc)
        self.assertEqual(len(output),len(self.data));self.assertEqual(len(reloc),len(self.reloc))
        restored = bytearray(output)
        for address,before,after in c.CHANGES:
            self.assertEqual(struct.unpack_from('>I',output,address-c.RAM)[0],after)
            struct.pack_into('>I',restored,address-c.RAM,before)
        self.assertEqual(restored,self.data)
        self.assertEqual(struct.unpack_from('>5I',reloc),(4496,176,16,480,98))
        self.assertEqual(reloc[:12]+reloc[16:],self.reloc[:12]+self.reloc[16:])
        # The real structure allocator ignores requested size and supplies one
        # existing 8192-byte slot. Include loader relocation workspace too.
        self.assertLess(c.RESIDENT_BYTES+len(reloc),8192)
        self.assertEqual(c.RESIDENT_BYTES,5168)
        self.assertEqual(c.BUFFER,c.RAM+4912)
        self.assertLessEqual(c.BUFFER+250,c.RAM+c.RESIDENT_BYTES)

    def test_relocated_buffer_and_all_prior_bss_addresses(self):
        from npc_mail_show import relocate_verified_data
        for base in (0x801A0000,0x802F8000):
            loaded = c.relocated(self.data,self.reloc,base)
            original = relocate_verified_data(c.CreditsOverlay(),self.data,self.reloc,base)
            self.assertEqual(len(loaded),c.RESIDENT_BYTES)
            self.assertEqual(loaded[c.FILE_BYTES:],bytes(c.OLD_BSS+c.EXTRA_BSS))
            # Decode the two actual relocated HI/LO pointer pairs, including
            # carry into HI at a relocation base whose low half crosses 8000.
            for hi,lo in ((0x188,0x18C),(0x244,0x248)):
                high=struct.unpack_from('>I',loaded,hi)[0]&0xFFFF
                low=struct.unpack_from('>h',loaded,lo+2)[0]
                self.assertEqual((high<<16)+low,base+c.BUFFER-c.RAM)
            restored=bytearray(loaded[:len(original)])
            for address,_,_ in c.CHANGES:
                at=address-c.RAM;restored[at:at+4]=original[at:at+4]
            for at in (0x188,0x244):restored[at:at+4]=original[at:at+4]
            self.assertEqual(restored,original)

    def test_every_page_and_terminal_load_clamp(self):
        seen = set(); loaded_ids = set()
        self.assertEqual(len(c.PAGES),17)
        for page in range(16):
            start,end = c.PAGES[page:page+2]
            self.assertLessEqual(end-start,10)
            seen.update(range(c.FIRST+start,c.FIRST+end))
            loaded_ids.update(min(c.FIRST+start+i,c.END-1) for i in range(10))
        self.assertEqual(seen,set(range(c.FIRST,0x555)))
        self.assertEqual(loaded_ids,set(range(c.FIRST,c.END)))
        self.assertEqual([min(c.FIRST+c.PAGES[15]+i,c.END-1) for i in range(10)][-5:],
                         [c.END-1]*5)

    def test_unknown_ownership_or_controller_changes_fail_before_publish(self):
        for vrom in (c.VROM,c.RELOCATION,*(v for v,_ in c.DEPENDENCIES)):
            data=bytearray(self.files[vrom].extract(self.rom));data[-1]^=1
            replacements={vrom:bytes(data)};saved=dict(replacements)
            with self.assertRaises(ValueError):c.install(self.rom,replacements)
            self.assertEqual(replacements,saved)
        for address in (c.METADATA+12,0x80057940,0x80057E24,0x80090E1C):
            code=bytearray(self.files[CODE_VROM].extract(self.rom));code[address-CODE_RAM]^=1
            with self.assertRaises(ValueError):c.install(self.rom,{CODE_VROM:bytes(code)})

    def test_builder_complete_bank_actor_and_metadata_no_other_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'edits.json';path.write_text(json.dumps(list(self.edits.values())))
            code=self.files[CODE_VROM].extract(self.rom);replacements={CODE_VROM:code}
            count,relocations=apply_translations(self.rom,replacements,path,english_credits=True)
            self.assertEqual(count,110);self.assertEqual(relocations,{0xD16000:0x2600000})
            self.assertEqual(set(replacements),{CODE_VROM,c.VROM,c.RELOCATION,0xD16000,0xD18000})
            expected=list(self.originals)
            for id,e in self.edits.items():expected[int(id[7:],16)]=encode(e['translation'],self.info)
            self.assertEqual(Bank('string',0,0,replacements[0xD16000],replacements[0xD18000]).entries(),expected)
            final=bytearray(replacements[CODE_VROM])
            self.assertEqual(struct.unpack_from('>I',final,c.METADATA-CODE_RAM+12)[0],c.RAM+c.RESIDENT_BYTES)
            for address,length in ((c.METADATA+12,4),(0x800C3F1C,8)):
                at=address-CODE_RAM;final[at:at+length]=code[at:at+length]
            self.assertEqual(final,code)
            with self.assertRaisesRegex(ValueError,'entry budget'):
                apply_translations(self.rom,{CODE_VROM:code},path)


if __name__=='__main__':unittest.main()
