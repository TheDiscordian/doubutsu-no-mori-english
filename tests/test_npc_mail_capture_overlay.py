"""Synthetic native relocation validation and exact original call-site guards."""

from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from npc_mail_capture import RAM,IMPORTS,HOOKS,relocate,validate,call_patches
from runtime_layout import MODULE_RAM,RESERVATION
from test_retail import ROM_PATH


class CaptureRelocationTests(unittest.TestCase):
    def setUp(self):
        self.imports = [MODULE_RAM+0x300+i*16 for i in range(3)]
        # Original synthetic instructions: one internal call, one imported
        # call, and a paired pointer to the small read-only data section.
        self.data = struct.pack('>8I',0x0C000000|((RAM+16)&0xFFFFFFF)>>2,
                                0x0C000000|(self.imports[0]&0xFFFFFFF)>>2,
                                0x3C0880B0,0x25080020,0x03E00008,0,0,0)+b'source bytes!!!!'
        self.entries = [0x44000000,0x45000008,0x4600000C]
        self.reloc = self.table(self.entries)

    @staticmethod
    def table(entries):
        return struct.pack('>5I',32,0,16,0,len(entries))+struct.pack('>'+str(len(entries))+'I',*entries)+struct.pack('>I',24+4*len(entries))

    def test_internal_jump_signed_low_pointer_and_retained_import(self):
        for base in (MODULE_RAM+RESERVATION,0x802F7FF0,0x802F8010,0x80400000-len(self.data)):
            result = relocate(self.data,self.reloc,base,self.imports)
            words = struct.unpack_from('>8I',result)
            self.assertEqual(0x80000000|((words[0]&0x3FFFFFF)<<2),base+16)
            low = (words[3]&65535)-(65536 if words[3]&32768 else 0)
            self.assertEqual(((words[2]&65535)<<16)+low,base+32)
            self.assertEqual(result[4:8]+result[16:],self.data[4:8]+self.data[16:])

    def test_invalid_buffers_headers_and_allocation_bounds(self):
        for base in (None,True,0,MODULE_RAM,MODULE_RAM+RESERVATION-16,
                     MODULE_RAM+RESERVATION+1,0x80400000,0xA0200000):
            with self.assertRaises(ValueError): relocate(self.data,self.reloc,base,self.imports)
        for data in (b'',self.data[:-1],self.data+bytes(16)*2048):
            with self.assertRaises(ValueError): relocate(data,self.reloc,0x80200000,self.imports)
        for reloc in (b'',self.reloc[:4],self.reloc[:-1],self.reloc[:-4],self.reloc+bytes(4096)):
            with self.assertRaises(ValueError): relocate(self.data,reloc,0x80200000,self.imports)

    def test_floating_load_relocation_requires_aligned_read_only_word(self):
        data = bytearray(self.data);struct.pack_into('>I',data,12,0xC5000020)
        for base in (0x80200000,0x802F7FF0,0x802F8010):
            out = relocate(bytes(data),self.reloc,base,self.imports)
            high,low = struct.unpack_from('>2I',out,8)
            self.assertEqual((high&65535)*65536+(low&65535)-(65536 if low&32768 else 0),base+32)
            self.assertEqual(low>>26,49)
        for target in (0,16,31,33,46,48):
            struct.pack_into('>I',data,12,0xC5000000|target)
            with self.assertRaises(ValueError): relocate(bytes(data),self.reloc,0x80200000,self.imports)
        for at,value in ((0,16),(4,16),(8,32),(12,16),(16,999),(len(self.reloc)-4,0)):
            reloc = bytearray(self.reloc);struct.pack_into('>I',reloc,at,value)
            with self.assertRaises(ValueError): relocate(self.data,reloc,0x80200000,self.imports)

    def test_order_pair_opcode_target_and_inventory_rejections(self):
        for entries in ([],[0x45000008,0x4600000C],self.entries[::-1],self.entries*2,
                        [0x44000002],[0x44000020],[0x84000000],
                        [0x44000000,0x4600000C],[0x44000000,0x45000008],[0x42000000]):
            with self.assertRaises(ValueError): relocate(self.data,self.table(entries),0x80200000,self.imports)
        for at,word in ((0,0),(0,0x0C000000|((RAM+48)&0xFFFFFFF)>>2),(8,0x3C080000),
                        (12,0x25080040),(12,0x25280020),(12,0x35080020),(4,0x0C000000)):
            data = bytearray(self.data);struct.pack_into('>I',data,at,word)
            with self.assertRaises(ValueError): relocate(data,self.reloc,0x80200000,self.imports)

    @unittest.skipUnless((ROOT/'build/npc-mail-capture-runtime-followup-01/overlay.json').is_file(),'Local native capture overlay required')
    def test_native_artifact_and_stale_metadata_are_checked(self):
        directory = ROOT/'build/npc-mail-capture-runtime-followup-01'
        data,reloc = (directory/'overlay.bin').read_bytes(),(directory/'relocation.bin').read_bytes()
        report = json.loads((directory/'overlay.json').read_text())
        module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        validate(data,reloc,report,module)
        for base in (MODULE_RAM+RESERVATION,0x802F8010,0x80400000-len(data)):
            self.assertEqual(len(relocate(data,reloc,base,report['imports'].values())),len(data))
        for key,value in (('version',0),('ram',RAM+16),('bytes',1),('relocation_bytes',0),
                          ('sources',{}),('module_sha256','0'*64),('imports',{}),('word_sha256','0'*64),
                          ('alias_sha256','0'*64),('symbols',{})):
            bad = deepcopy(report);bad[key] = value
            with self.assertRaises(ValueError): validate(data,reloc,bad,module)
        for at in (True,'0',-4,2,len(data),int.from_bytes(reloc[:4],'big')):
            bad = deepcopy(report);bad['symbols']['af_mail_generate'] = at
            with self.assertRaises(ValueError): validate(data,reloc,bad,module)
        bad = deepcopy(report);bad['relocation_bytes'] = 0;bad['relocation_sha256'] = sha256(b'')
        with self.assertRaises(ValueError): validate(data,b'',bad,module)


@unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
class CaptureHookTests(unittest.TestCase):
    def test_exact_guarded_calls_and_unchanged_delay_slots(self):
        rom = ROM_PATH.read_bytes();code = by_vrom(rom)[CODE_VROM].extract(rom)
        module = {'linked_bytes':0x1000,'symbols':{name:f'{MODULE_RAM+0x300+i*16:08X}' for i,(_,_,name) in enumerate(HOOKS)}}
        patches = call_patches(code,module)
        self.assertEqual(len(patches),8)
        for (at,before,after),(_,original,name) in zip(patches,HOOKS):
            self.assertEqual(before,code[at-CODE_RAM:at-CODE_RAM+4])
            self.assertEqual(int.from_bytes(before,'big'),0x0C000000|((original&0xFFFFFFF)>>2))
            self.assertEqual(int.from_bytes(after,'big'),0x0C000000|((int(module['symbols'][name],16)&0xFFFFFFF)>>2))
            bad = bytearray(code);bad[at-CODE_RAM+4] ^= 1
            with self.assertRaises(ValueError): call_patches(bad,module)
        for target in (0,MODULE_RAM,MODULE_RAM+0x302,MODULE_RAM+0x1000,0x80400000):
            bad = deepcopy(module);bad['symbols']['af_npc_mail_prepare'] = f'{target:08X}'
            with self.assertRaises(ValueError): call_patches(code,bad)


if __name__ == '__main__': unittest.main()
