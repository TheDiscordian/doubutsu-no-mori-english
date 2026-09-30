"""Complete linked bank packet, real lifecycle entries, and bounded art pointers."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from v3_bank_link import layout,relocate_art,RAM,ART,END,CODE_GUARD,ART_GUARD
from v3_furniture_install import inputs
from v3_post_office_install import native_entries,ENTRIES

LINKED=ROOT/'build/v3-post-office-bank-linked-02'


class BankLinkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base,cls.prior=inputs(ROOT/'build/v3-holiday-card-prize-imports-01/password-destinations/build-lock.json')
        cls.report=json.loads((LINKED/'linked.json').read_bytes())
        cls.prepared=ROOT/cls.report['prepared']
        cls.preparation=json.loads((cls.prepared/'prepared.json').read_bytes())

    def test_complete_packet_real_entries_initialized_state_and_guards(self):
        r=self.report;packet=(LINKED/'bank-packet.bin').read_bytes();code=(LINKED/'bank-code.bin').read_bytes()
        self.assertTrue(r['fully_linked']);self.assertFalse(r['installed']);self.assertFalse(r['native_execution_verified'])
        self.assertTrue(r['native_services_bound_once'])
        self.assertEqual(r['base_sha256'],sha256(self.base));self.assertEqual(r['memory'],layout(self.prior))
        self.assertEqual(len(packet),END-RAM);self.assertEqual(sha256(packet),r['packet']['sha256'])
        self.assertEqual(sha256(code),r['code']['sha256']);self.assertEqual(packet[:len(code)],code)
        self.assertEqual(packet[ART-RAM-16:ART-RAM],CODE_GUARD);self.assertEqual(packet[-16:],ART_GUARD)
        begin,end=r['code']['bss_start'],r['code']['bss_end']
        self.assertFalse(any(packet[begin-RAM:end-RAM]));self.assertLessEqual(end,ART-16)
        self.assertEqual(packet[r['account_mode']['address']-RAM],0)
        for name,digest in r['original_objects'].items():
            self.assertEqual(sha256((self.prepared/name).read_bytes()),digest)
        self.assertEqual(sha256((LINKED/'checked-post-office.o').read_bytes()),self.preparation['object']['sha256'])
        changes,entry=native_entries(self.base,r['symbols'],code_bounds=(RAM,ART-16))
        self.assertEqual(entry,r['entries'])
        for row in r['owners']:
            data=changes[row['vrom']]
            self.assertEqual(data,(LINKED/f'owner-{row["vrom"]:08X}.bin').read_bytes())
            self.assertEqual(sha256(data),row['sha256'])
        for name in ENTRIES:
            address=r['symbols'][name];self.assertTrue(RAM<=address<RAM+len(code))
            self.assertNotEqual(code[address-RAM:address-RAM+8],bytes(8))
        modified=copy.deepcopy(self.prior);modified['bank_collision']={'ram':ART-16,'bytes':32}
        with self.assertRaisesRegex(ValueError,'overlaps retained'):layout(modified)

    def test_full_art_resources_rebased_without_changing_segment_six(self):
        receipt=self.preparation['artwork'];original=(self.prepared/'bank-art.bin').read_bytes()
        data,r=relocate_art(original,receipt);self.assertEqual(r,self.report['artwork'])
        self.assertEqual(data,(LINKED/'bank-art-linked.bin').read_bytes())
        packet=(LINKED/'bank-packet.bin').read_bytes();self.assertEqual(packet[ART-RAM:ART-RAM+len(data)],data)
        self.assertTrue(r['native_segment_six_unchanged']);self.assertTrue(r['resource_bytes_preserved'])
        self.assertTrue(r['pointer_bindings'])
        for resource in receipt['resources']:
            at,n=resource['native_offset'],resource['bytes']
            self.assertEqual(data[at:at+n],original[at:at+n])
        for hook in r['pointer_bindings']:
            target=struct.unpack_from('>I',data,hook['offset'])[0]
            self.assertEqual(target,hook['after']);self.assertEqual(target>>24,0)
            self.assertTrue((ART&0x1FFFFFFF)<=target<(ART&0x1FFFFFFF)+len(data))
        changed=bytearray(original);changed[0]^=1
        with self.assertRaisesRegex(ValueError,'complete prepared bank artwork'):relocate_art(changed,receipt)
        changed=bytearray(original);modified=copy.deepcopy(receipt)
        row=modified['compiled_models'][0];at=row['native_offset']
        position=next(i for i in range(at,at+row['bytes'],8) if changed[i] in (1,0xFD))
        struct.pack_into('>I',changed,position+4,0x067FFFFF)
        modified['sha256']=sha256(changed)
        row['output_sha256']=sha256(changed[at:at+row['bytes']])
        with self.assertRaisesRegex(ValueError,'escapes complete resources'):relocate_art(changed,modified)


if __name__=='__main__':unittest.main()
