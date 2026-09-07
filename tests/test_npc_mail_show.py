"""The NPC-show relocation proof is restricted to verified inputs and RAM."""

from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from npc_mail_show import OVERLAYS, source, relocated
from runtime_layout import MODULE_RAM, RESERVATION
from test_retail import ROM_PATH


@unittest.skipUnless(ROM_PATH.is_file(),'Local original ROM required')
class NpcMailShowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rom = ROM_PATH.read_bytes()
        cls.inputs = {name:source(rom,name) for name in OVERLAYS}

    def test_complete_layout_bss_and_all_pointer_relocations_at_multiple_bases(self):
        for name,spec in OVERLAYS.items():
            data,reloc = self.inputs[name]
            self.assertEqual(sum(spec.sections[:3]),len(data))
            self.assertLessEqual(spec.letter+164,spec.ram+spec.resident_bytes)
            self.assertGreaterEqual(spec.letter,spec.ram+spec.file_bytes)
            for base in (MODULE_RAM+RESERVATION,0x801F8010,0x80300000):
                output = relocated(spec,data,reloc,base)
                self.assertEqual(len(output),spec.resident_bytes)
                self.assertEqual(output[spec.file_bytes:],bytes(spec.sections[3]))
                starts = (0,0,spec.sections[0],sum(spec.sections[:2]))
                changed = set()
                for (entry,) in struct.iter_unpack('>I',reloc[20:20+4*spec.sections[4]]):
                    at = starts[entry>>30]+(entry&0xFFFFFF)
                    changed.update(range(at,at+4))
                    if entry>>24&63 == 2:
                        old,new = struct.unpack_from('>I',data,at)[0],struct.unpack_from('>I',output,at)[0]
                        self.assertEqual(new,base+old-spec.ram if not old&0x0F000000 else old)
                self.assertTrue(changed)
                self.assertEqual(bytes(v for i,v in enumerate(data) if i not in changed),
                                 bytes(v for i,v in enumerate(output[:len(data)]) if i not in changed))

    def test_altered_files_relocations_and_out_of_bounds_destinations_are_rejected(self):
        for name,spec in OVERLAYS.items():
            data,reloc = self.inputs[name]
            for index in (0,len(data)-1,spec.handler-spec.ram):
                edited = bytearray(data);edited[index] ^= 1
                with self.assertRaisesRegex(ValueError,'input'):
                    relocated(spec,bytes(edited),reloc,0x80200000)
            for index in (0,19,20,len(reloc)-1):
                edited = bytearray(reloc);edited[index] ^= 1
                with self.assertRaisesRegex(ValueError,'input'):
                    relocated(spec,data,bytes(edited),0x80200000)
            for base in (0,True,MODULE_RAM,0x801A0001,0x80400000-spec.resident_bytes+16):
                with self.assertRaisesRegex(ValueError,'base'):
                    relocated(spec,data,reloc,base)


if __name__ == '__main__': unittest.main()
