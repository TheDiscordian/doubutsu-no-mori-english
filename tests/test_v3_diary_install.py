"""Connected current-cartridge diary installation, not a gameplay claim."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
from v3_asset_loader import BLOB
from v3_furniture_install import inputs, reuse_resource_tail
from v3_diary_install import GUARD, LAYOUT, MEMORY
from v3_import_storage import jump
from npc_mail_show import relocate_verified_data
import v3_physical_resources as physical

OUT = ROOT/os.environ.get('V3_DIARY_INSTALLED', 'build/v3-diary-category-work-01/connected-03')


class DiaryInstallationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image, cls.report = inputs(OUT/'build-lock.json')
        cls.base, cls.prior = inputs(OUT/'base-lock.json')
        cls.files, cls.old_files = by_vrom(cls.image), by_vrom(cls.base)
        cls.blob = cls.files[BLOB].extract(cls.image)
        cls.diary = cls.report['equipment_resources']['diaries']

    def test_packets_startup_and_both_save_dispatch_routes(self):
        r, d = self.report, self.diary
        self.assertTrue(d['installed'])
        self.assertFalse(d['selectable'])
        self.assertFalse(d['native_execution_tested'])
        self.assertEqual(r['save_runtime']['profile_hex'], self.prior['save_runtime']['profile_hex'])
        self.assertEqual((r['save_codec']['format_version'], r['save_codec']['canonical_format_version'],
            r['save_codec']['registry_version']), (11, 8, 5))
        self.assertIn('earlier V3 builds cannot load', r['save_warning'])
        self.assertFalse(r['save_runtime']['native_save_reload_tested'])
        self.assertEqual(r['equipment_resources']['console_storage']['scratch'], LAYOUT['scratch'])
        physical.verify(self.image, r['physical_resources'])
        e = r['equipment_resources']; boot = e['surface_bootstrap']['code']
        self.assertLessEqual(boot['bytes'], 688)
        at = e['blob_offset']+boot['symbols']['packets']-e['ram']
        descriptors = list(struct.iter_unpack('>5I', self.blob[at:at+15*20]))
        for dest, source, size, crc_at, clear in descriptors:
            if source & 0x80000000:
                first = source & 0x7FFFFFFF; data = self.image[first:first+size]
            else:
                owner = next(f for f in self.files.values() if f.vstart <= source < source+size <= f.vend)
                data = owner.extract(self.image)[source-owner.vstart:source-owner.vstart+size]
            self.assertEqual(struct.unpack_from('>I', self.blob, e['blob_offset']+crc_at-e['ram'])[0], zlib.crc32(data))
            self.assertTrue(0x80400000 <= dest < dest+size <= 0x807DA800)
            self.assertIn(clear, (0, 0x804DC000, 0x804DC400))
        for i, name in enumerate(('storage', 'ui', 'art'), 12):
            p = d['packets'][name]
            raw = self.image[p['physical']:p['physical']+p['bytes']]
            self.assertEqual(descriptors[i][:3], (p['ram'], p['physical']|0x80000000, p['bytes']))
            self.assertEqual(raw, (OUT/('diary-'+name+'.bin')).read_bytes())
            self.assertEqual(sha256(raw), p['sha256'])
            self.assertEqual(raw[-16:], GUARD)
            if name == 'ui':
                self.assertEqual(raw[MEMORY['code'][1]-16:MEMORY['code'][1]], GUARD)
                self.assertEqual(raw[MEMORY['code'][1]:-16], bytes(MEMORY['state'][1]-16))
        # Both kinds of already linked caller must reach diary-aware storage.
        # Check the complete old packet outside the declared eight-byte entries.
        for key, packet, old_packet, physical_packet in (
                ('stable_storage_entries', e['console_storage']['packet'],
                 self.prior['equipment_resources']['console_storage']['packet'], False),
                ('embedded_storage_entries', e['creature_insects']['packet'],
                 self.prior['equipment_resources']['creature_insects']['packet'], True)):
            if physical_packet:
                data = self.image[packet['physical']:packet['physical']+packet['bytes']]
                before = self.base[old_packet['physical']:old_packet['physical']+old_packet['bytes']]
            else:
                data = self.blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
                old_blob = self.old_files[BLOB].extract(self.base)
                before = old_blob[old_packet['blob_offset']:old_packet['blob_offset']+old_packet['bytes']]
            expected = bytearray(before)
            self.assertEqual(len(d[key]), 23)
            for row in d[key]:
                start = row['address']-packet['ram']
                self.assertEqual(expected[start:start+8].hex(), row['before'])
                target = d['compiled']['symbols'][row['name']]
                patch = struct.pack('>2I', jump(target), 0)
                self.assertEqual(patch.hex(), row['after'])
                expected[start:start+8] = patch
            self.assertEqual(data, bytes(expected))
        self.assertEqual(r['save_codec']['active_codec_code'], e['creature_insects']['compiled'])
        self.assertEqual(r['save_codec']['active_storage_code'], d['compiled'])
        _, tail = reuse_resource_tail(self.image, r, self.blob)
        self.assertGreater(tail['reused_bytes'], 0)

    def test_native_menu_room_and_visit_installation(self):
        d = self.diary; core = self.files[CODE_VROM].extract(self.image)
        owner = self.files[0x7749C0].extract(self.image)
        prepared = ROOT/d['prepared']['ui']
        for name, r in d['hooks']['menus'].items():
            self.assertNotIn(r['vrom'], self.files)
            self.assertEqual(self.files[r['target_vrom']].index, self.old_files[r['vrom']].index)
            # The actual native overlay manager finds relocation at DMA index+1.
            self.assertEqual(self.files[r['target_reloc']].index, self.files[r['target_vrom']].index+1)
            self.assertEqual(self.files[r['target_vrom']].extract(self.image), (prepared/name/'prepared.bin').read_bytes())
            self.assertEqual(self.files[r['target_reloc']].extract(self.image), (prepared/name/'relocation.bin').read_bytes())
            self.assertEqual(list(struct.unpack_from('>7I', owner, r['owner_at'])), r['owner_after'])
            self.assertEqual(r['owner_after'][:2], [r['target_vrom'], r['target_vrom']+r['bytes']])
            self.assertEqual(r['owner_after'][3]-r['ram'], r['bytes'])
        self.assertEqual(d['hooks']['additional_pool_bytes'], 1600)
        for r in d['hooks']['arena_patches']+[d['hooks']['visit']]:
            at = r['address']-CODE_RAM; data = bytes.fromhex(r['after'])
            self.assertEqual(core[at:at+len(data)], data)
        r = d['room']; room = self.files[r['room_vrom']].extract(self.image)
        at = r['hook_address']-r['room_ram']
        self.assertEqual(room[at:at+8].hex(), r['hook_after'])
        self.assertEqual(sha256(room), r['installed_owner_sha256'])
        rel = self.files[0x844400].extract(self.image)
        count = struct.unpack_from('>I', rel, 16)[0]
        rows = struct.unpack_from('>'+str(count)+'I', rel, 20)
        old_rel = self.old_files[0x844400].extract(self.base)
        old_count = struct.unpack_from('>I', old_rel, 16)[0]
        old_rows = struct.unpack_from('>'+str(old_count)+'I', old_rel, 20)
        self.assertEqual(rows, tuple(x for x in old_rows if x != r['remove_relocation']))
        self.assertEqual(rel[-4:], old_rel[-4:])
        self.assertEqual(sha256(rel), r['installed_relocation_sha256'])
        old_room = self.old_files[r['room_vrom']].extract(self.base)
        before_sections = struct.unpack_from('>5I', old_rel)
        after_sections = struct.unpack_from('>5I', rel)
        before_image = SimpleNamespace(ram=r['room_ram'], resident_bytes=len(room)+before_sections[3], sections=before_sections)
        after_image = SimpleNamespace(ram=r['room_ram'], resident_bytes=len(room)+after_sections[3], sections=after_sections)
        for address in (0x801A0010, 0x80370010):
            before = relocate_verified_data(before_image, old_room, old_rel, address)
            after = relocate_verified_data(after_image, room, rel, address)
            expected = bytearray(before); expected[at:at+4] = bytes.fromhex(r['hook_after'])[:4]
            self.assertEqual(after, bytes(expected))
        # Previous menu allocations are not reclaimed or overwritten.
        for row in self.report['resource_growth']:
            e = self.old_files[row['vrom']]; start = e.pstart; end = e.pend or start+e.size
            self.assertEqual(self.image[start:end], self.base[start:end])

    def test_combined_startup_failure_gates_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-diary-startup-') as tmp:
            binary = Path(tmp)/'check'
            result = subprocess.run(['cc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fno-pie', '-no-pie', '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                'tests/v3_creature_startup_test.c', '-o', str(binary)], cwd=ROOT,
                capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            result = subprocess.run([str(binary)], capture_output=True, text=True, timeout=30)
            self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
            print(result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
