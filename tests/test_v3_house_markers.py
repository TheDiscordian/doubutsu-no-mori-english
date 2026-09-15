"""Verify compiled marker leaves and the exact installed cartridge changes."""
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import DMA_START, apply_ups, by_vrom, n64_checksum, sha256
from v3_house_markers import (BASE, BASE_SHA, BLOB, CONFIG, HOUSE, HOUSE_RELOC,
    MARKER_OFFSET, MARKER_END, MODULE, NPC, NPC_RELOC, STARTUP)
from v3_registry import villager_house_marker

OUTPUT = ROOT/'build/v3-house-markers-01'
MASK64 = (1 << 64)-1


def run_leaf(words, entry, registers):
    """Only the seven instructions used here; include branch delay execution.

    Word arithmetic sign-extends on VR4300; SLTIU compares unsigned 64-bit GPRs.
    No memory instruction is accepted, so a leaf cannot silently grow a stack.
    """
    regs = list(registers)
    pc, pending = entry, None
    for _ in range(32):
        word = words[pc]
        op, rs, rt, rd = word >> 26, (word >> 21)&31, (word >> 16)&31, (word >> 11)&31
        imm = word & 65535
        signed = imm if imm < 32768 else imm-65536
        branch = None
        if word == 0:
            pass
        elif op == 9 or op == 0 and word & 63 == 33:
            value = (regs[rs]+(signed if op == 9 else regs[rt])) & 0xFFFFFFFF
            regs[rt if op == 9 else rd] = (value if value < 0x80000000 else value-(1 << 32)) & MASK64
        elif op == 11:
            regs[rt] = int(regs[rs] < (signed & MASK64))
        elif op == 12:
            regs[rt] = regs[rs] & imm
        elif op == 13:
            regs[rt] = regs[rs] | imm
        elif op in (4, 5):
            taken = (regs[rs] == regs[rt]) == (op == 4)
            branch = pc+1+signed if taken else pc+2
        elif op == 0 and word & 63 == 8:
            branch = regs[rs]
        else:
            raise AssertionError(f'Unexpected marker opcode {word:08X}')
        regs[0] = 0
        if pending is not None:
            if branch is not None:
                raise AssertionError('Branch in delay slot')
            if pending == registers[31]:
                return regs
            pc, pending = pending, None
        else:
            pc, pending = pc+1, branch
    raise AssertionError('Marker leaf did not return')


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current marker cartridge required')
class HouseMarkerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report = json.loads((OUTPUT/'build.json').read_text())
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)

    def test_compiled_leaves_preserve_all_other_ids_and_registers(self):
        report = self.report['house_markers']['code']
        data = (OUTPUT/'house_markers/code.bin').read_bytes()
        self.assertEqual(sha256(data), report['sha256'])
        self.assertEqual(len(data), 116)
        self.assertLessEqual(len(data), MARKER_END-MARKER_OFFSET)
        words = struct.unpack('>'+str(len(data)//4)+'I', data)
        for label, register in (('af_v3_house_marker_v1', 3), ('af_v3_house_marker_a0', 4),
                                ('af_v3_is_house_marker_v1', None)):
            entry = (report['symbols'][label]-0x80460000-MARKER_OFFSET)//4
            seed = [0]+[(0x123456789ABC0000+i*0x10101)&MASK64 for i in range(1, 32)]
            for item in range(65536):
                regs = list(seed)
                regs[register or 3] = item
                wanted = list(regs)
                if register:
                    wanted[register] = (0xF200+item-0x50DA if 0x50DA <= item < 0x50EE
                                        else (item+0xA005)&65535)
                    wanted[1] = 0xA005
                else:
                    wanted[1] = int(0xF005 <= item < 0xF0DF or 0xF200 <= item < 0xF214)
                actual = run_leaf(words, entry, regs)
                if actual != wanted:
                    self.fail(f'{label} failed for {item:04X}: {actual} != {wanted}')
        self.assertEqual([villager_house_marker(i) for i in range(216, 236)], list(range(0xF200, 0xF214)))
        for donor in (215, 236):
            with self.assertRaises(ValueError):
                villager_house_marker(donor)

    def test_only_declared_native_windows_change(self):
        hooks = self.report['house_markers']['hooks']
        self.assertEqual(len(hooks), 3)
        self.assertEqual([(int(r['vrom'], 16), r['offset']) for r in hooks],
                         [(HOUSE, 0x97C), (HOUSE, 0x10C4), (NPC, 0x3B84)])
        for owner, reloc in ((HOUSE, HOUSE_RELOC), (NPC, NPC_RELOC)):
            expected = bytearray(self.old[owner].extract(self.base))
            for row in hooks:
                if int(row['vrom'], 16) == owner:
                    at, before, after = row['offset'], bytes.fromhex(row['before']), bytes.fromhex(row['after'])
                    self.assertEqual(expected[at:at+len(before)], before)
                    expected[at:at+len(after)] = after
            self.assertEqual(self.files[owner].extract(self.rom), expected)
            self.assertEqual(self.files[reloc].extract(self.rom), self.old[reloc].extract(self.base))
        # Native player-house marker constants and complete actor stay unchanged.
        self.assertEqual(self.files[NPC].extract(self.rom)[0x3B44:0x3B48].hex(), '3412f0df')
        self.assertEqual(self.files[0x8D4A20].extract(self.rom), self.old[0x8D4A20].extract(self.base))

    def test_full_storage_profile_checksum_and_patch(self):
        blob = self.files[BLOB].extract(self.rom)
        expected_blob = bytearray(self.old[BLOB].extract(self.base))
        helper = (OUTPUT/'house_markers/code.bin').read_bytes()
        self.assertEqual(expected_blob[MARKER_OFFSET:MARKER_END], bytes(MARKER_END-MARKER_OFFSET))
        expected_blob[MARKER_OFFSET:MARKER_OFFSET+len(helper)] = helper
        struct.pack_into('>I', expected_blob, 4, 60)
        self.assertEqual(len(expected_blob), self.report['house_markers']['house_blob_offset'])
        expected_blob.extend(self.files[HOUSE].extract(self.rom))
        self.assertEqual(blob, expected_blob)
        self.assertEqual(len(self.rom), 0x4000000)
        self.assertEqual(len(blob), 0x132DD0)
        self.assertEqual(self.files[HOUSE].pstart, self.files[BLOB].pstart+0x131690)
        self.assertEqual(self.files[HOUSE].pend, 0)
        self.assertEqual(blob[0x20:0xE0], bytes.fromhex(self.report['save_runtime']['profile_hex']))
        expected = bytearray(self.base)+bytes(len(self.rom)-len(self.base))
        for vrom in (BLOB, MODULE, NPC):
            entry = self.files[vrom]
            self.assertEqual(entry.pstart, self.old[vrom].pstart)
            expected[entry.pstart:entry.pstart+entry.size] = entry.extract(self.rom)
        for vrom in (BLOB, HOUSE):
            at = DMA_START+self.files[vrom].index*16
            expected[at:at+16] = self.rom[at:at+16]
        expected[0x10:0x18] = self.rom[0x10:0x18]
        self.assertEqual(self.rom, expected)
        module = self.files[MODULE].extract(self.rom)
        old_module = bytearray(self.old[MODULE].extract(self.base))
        old_module[STARTUP:CONFIG+16] = module[STARTUP:CONFIG+16]
        self.assertEqual(module, old_module)
        self.assertEqual(struct.unpack_from('>4I', module, CONFIG),
                         (BLOB, 0xC000, zlib.crc32(blob[:0xC000]), 60))
        self.assertEqual(sha256(self.base), BASE_SHA)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(n64_checksum(self.rom), struct.unpack_from('>2I', self.rom, 0x10))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), self.rom)


if __name__ == '__main__':
    unittest.main()
