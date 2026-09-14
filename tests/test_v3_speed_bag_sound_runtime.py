"""Additive sound resources, physical ROM binding, and complete audio capacity."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256, u32
from v3_speed_bag_audio import bind_program, extract
from v3_speed_bag_sound_runtime import RELOCATIONS, SOUND_ID, append_instrument, permanent_budget, prepare
from v3_villager_audio import NATIVE_HEADERS, header_entry, read_audio_donor

OUTPUT = ROOT/'build/v3-speed-bag-sound-03'
PARENT = ROOT/'build/v3-clothing-catalogue-01'


@unittest.skipUnless((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').exists(), 'Verified local donors required')
class SoundDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.files = by_vrom(cls.native)
        cls.original = cls.files[CODE_VROM].extract(cls.native)
        cls.donor = read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        cls.parts, _ = extract(cls.native, *cls.donor)
        cls.code = bytearray(cls.original)
        cls.changed, cls.report = prepare(cls.native, cls.code, cls.donor)

    def test_all_original_audio_bytes_and_original_group_entries_are_retained(self):
        for old, data in self.changed.items():
            original = self.files[old].extract(self.native)
            self.assertEqual(data[:len(original)], original)
        row = self.report['files']['seq']
        original = self.files[0x27130].extract(self.native)
        src_at = u32(self.original, NATIVE_HEADERS['seq']-CODE_RAM+16+199*16)
        main = original[src_at:src_at+0x4C30]
        new = self.changed[0x27130][row['header_offset']:]
        restored = bytearray(new[:len(main)])
        restored[0x18A:0x18C] = main[0x18A:0x18C]
        self.assertEqual(restored, main)
        table = self.report['sequence_table_offset']
        self.assertEqual(new[table:table+194], main[0x27C:0x33E])
        entries = struct.unpack_from('>106H', new, table)
        no_op = self.report['reserved_no_op_offset']
        self.assertEqual(entries[97:105], (no_op,)*8)
        self.assertEqual(new[no_op], 255)
        self.assertEqual(entries[105], 0x4D05)
        self.assertEqual(new[entries[105]:entries[105]+27], bind_program(self.parts, 0x4D05, 1, 71))
        envelope = struct.unpack_from('>H', new, entries[105]+8)[0]
        self.assertEqual(envelope, 0x4D14)
        self.assertEqual(envelope % 2, 0)
        self.assertEqual(new[envelope:envelope+12], self.parts['program'][15:])

    def test_complete_old_font_offsets_and_new_instrument(self):
        row = self.report['files']['bank']
        file = self.files[0xE4D10].extract(self.native)
        entry = self.original[NATIVE_HEADERS['bank']-CODE_RAM+16+140*16:][:16]
        bank = file[u32(entry, 0):u32(entry, 0)+u32(entry, 4)]
        new = self.changed[0xE4D10][row['header_offset']:]
        restored = bytearray(new[:len(bank)]); restored[0x124:0x128] = bytes(4)
        self.assertEqual(restored, bank)
        self.assertEqual(u32(new, 0x124), len(bank))
        self.assertEqual(new[0x29F0:0x29F4], self.parts['instrument'][:4])
        self.assertEqual(u32(new, 0x29F4), 0x2A10)
        self.assertEqual(u32(new, 0x2A00), 0x2A1C)
        self.assertEqual(u32(new, 0x2A20), self.report['instrument']['wave_offset'])
        self.assertEqual(new[0x2A10:0x2A1C], self.parts['envelope'])
        self.assertEqual(new[0x2A2C:0x2A5C], self.parts['loop'])
        self.assertEqual(new[0x2A5C:0x2AA4], self.parts['book'])
        bad = bytearray(bank); bad[0x124] = 1
        with self.assertRaises(ValueError): append_instrument(bytes(bad), self.parts, 0)
        bad = bytearray(bank); struct.pack_into('>I', bad, 8, 0x124)
        with self.assertRaises(ValueError): append_instrument(bytes(bad), self.parts, 0)

    def test_complete_permanent_budget_and_actual_donor_priority(self):
        before, after = self.report['before_budget'], self.report['after_budget']
        self.assertEqual((before['conservative_spare'], after['conservative_spare']), (1024, 608))
        self.assertEqual(after, permanent_budget(self.code))
        self.assertEqual(len(after['all_permanent_resources']), 7)
        self.assertEqual(after['audio_heap_growth'], 0)
        self.assertEqual(SOUND_ID, 0x169)
        self.assertEqual(self.original[0x80113B84-CODE_RAM+(SOUND_ID & 255)], self.donor[0].read(0x800A9A90, 128)[0x76])
        self.assertEqual(self.report['trigger_priority'], 70)
        bad = bytearray(self.code)
        struct.pack_into('>I', bad, NATIVE_HEADERS['bank']-CODE_RAM+16+140*16+4, 0x10000)
        with self.assertRaises(ValueError): permanent_budget(bad)


@unittest.skipUnless((OUTPUT/'build.json').exists(), 'Current sound cartridge required')
class SoundCartridgeTests(unittest.TestCase):
    def test_current_physical_binding_retention_and_patch_reconstruction(self):
        rom = (OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        previous = (PARENT/'animal-forest-v3-asset-loader.z64').read_bytes()
        report, old_report = (json.loads((p/'build.json').read_text()) for p in (OUTPUT, PARENT))
        data = report['speed_bag_sound']
        files, old = by_vrom(rom), by_vrom(previous)
        self.assertEqual(sha256(rom), report['output_sha256'])
        self.assertEqual(set(files), (set(old)-set(RELOCATIONS)) | set(RELOCATIONS.values()))
        code = files[CODE_VROM].extract(rom)
        self.assertEqual(report['save_runtime'], old_report['save_runtime'])
        self.assertEqual(report['clothing'], old_report['clothing'])
        for kind, row in data['files'].items():
            entry = files[row['vrom']]
            self.assertEqual(entry.index, old[row['old_vrom']].index)
            self.assertEqual(entry.pend, 0)
            self.assertEqual(entry.pstart, row['physical_rom'])
            self.assertEqual(sha256(entry.extract(rom)), row['sha256'])
            self.assertEqual(entry.extract(rom)[:row['original_file_bytes']], old[row['old_vrom']].extract(previous))
        # Independently emulate LUI + signed ADDIU for all three arguments.
        for kind, hi, lo in (('seq', 0x800D28E8, 0x800D28F4), ('bank', 0x800D28EC, 0x800D28F0),
                             ('wave', 0x800D28DC, 0x800D28E0)):
            upper = (u32(code, hi-CODE_RAM) & 65535) << 16
            lower = struct.unpack_from('>h', code, lo-CODE_RAM+2)[0]
            self.assertEqual(upper+lower, data['files'][kind]['physical_rom'])
        restored = bytearray(code)
        for patch in data['header_patches']:
            at = patch['address']-CODE_RAM
            self.assertEqual(restored[at:at+16].hex(), patch['after'])
            restored[at:at+16] = bytes.fromhex(patch['before'])
        for patch in data['initializer_patches']:
            at = patch['address']-CODE_RAM
            self.assertEqual(u32(restored, at), patch['after'])
            struct.pack_into('>I', restored, at, patch['before'])
        self.assertEqual(bytes(restored), old[CODE_VROM].extract(previous))
        for at in set(old)-{*RELOCATIONS, 0x19D40, CODE_VROM, 0x02800000, 0x03F00000}:
            self.assertEqual(files[at].extract(rom), old[at].extract(previous))
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUTPUT/'asset-loader.ups').read_bytes()), rom)
        self.assertFalse(data['furniture_callback_installed'])
        self.assertFalse(data['save_format_changed'])


if __name__ == '__main__':
    unittest.main()
