"""Current V2 correction ownership, branch ABI, text, and patch retention."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
import v2_performance_fix as fix
from letter_ui_fix import PARTS

OUT = ROOT/'build/v2-performance-fix-08'


@unittest.skipUnless((OUT/'build.json').is_file(), 'Current local V2 correction required')
class PerformanceFixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (ROOT/'build/v2-map-suffix-07/Animal Forest English V2.z64').read_bytes()
        cls.rom = (OUT/'Animal Forest English V2.z64').read_bytes()
        cls.report = json.loads((OUT/'build.json').read_text())
        cls.old, cls.new = by_vrom(cls.base), by_vrom(cls.rom)

    def test_original_patch_and_complete_unrelated_resource_retention(self):
        self.assertEqual(sha256(self.base), fix.BASE_SHA)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUT/'Animal Forest English V2.ups').read_bytes()), self.rom)
        changed = {int(v,16) for v in self.report['changed_resources']} | {0x19D40}
        self.assertEqual(set(self.old), set(self.new))
        for v, entry in self.old.items():
            self.assertEqual(entry.index, self.new[v].index)
            if v not in changed:
                self.assertEqual(entry.extract(self.base), self.new[v].extract(self.rom), hex(v))
        self.assertFalse(self.report['save_format_changed'])

    def test_only_credits_call_and_unused_tail_change(self):
        old, new = self.old[fix.VROM].extract(self.base), self.new[fix.VROM].extract(self.rom)
        allowed = set(range(fix.CALL-fix.RAM, fix.CALL-fix.RAM+4))
        allowed.update(range(fix.CAVE-fix.RAM, fix.CAVE_END-fix.RAM))
        self.assertEqual(len(old), len(new))
        self.assertTrue(all(a == b or i in allowed for i,(a,b) in enumerate(zip(old,new))))
        word = struct.unpack_from('>I',new,fix.CALL-fix.RAM)[0]
        self.assertEqual(word >> 16, 0x0411)
        self.assertEqual(fix.CALL+4+4*(word&0xFFFF), fix.CAVE)
        self.assertEqual(self.old[fix.RELOCATION].extract(self.base),self.new[fix.RELOCATION].extract(self.rom))
        self.assertEqual(new[fix.CAVE_END-fix.RAM:],old[fix.CAVE_END-fix.RAM:])

    def test_complete_text_and_existing_address_allocation(self):
        self.assertEqual(fix.credits_rows(self.base),fix.credits_rows(self.rom))
        spec = PARTS['address']; old = self.old[spec['new_vrom']].size; new = self.new[spec['new_vrom']].size
        self.assertEqual((old+63)//64,(new+63)//64)
        owner = self.new[0x7749C0].extract(self.rom)
        self.assertEqual(struct.unpack_from('>4I',owner,spec['owner_at']),
            (spec['new_vrom'],spec['new_vrom']+new,spec['ram'],spec['ram']+new))

    def test_reject_changed_credit_owner_and_adapter_size(self):
        actor, reloc = self.old[fix.VROM].extract(self.base), self.old[fix.RELOCATION].extract(self.base)
        adapter = self.new[fix.VROM].extract(self.rom)[fix.CAVE-fix.RAM:fix.CAVE_END-fix.RAM]
        for source, relocation, code in ((bytes([actor[0]^1])+actor[1:],reloc,adapter),
                                         (actor,reloc[:-1]+b'x',adapter),(actor,reloc,adapter[:-4])):
            with self.assertRaises(ValueError): fix.patch_credits(source,relocation,code)


if __name__ == '__main__': unittest.main()
