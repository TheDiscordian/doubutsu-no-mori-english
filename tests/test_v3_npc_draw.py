"""Focused tests of imported draw routing and constructor voice transport."""
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from aflib import by_vrom, sha256, apply_ups, CODE_RAM, CODE_VROM
from v3_asset_loader import BLOB, CONFIG, MODULE, compose, STARTUP, STARTUP_END, STARTUP_CALL
from v3_npc_draw import ABI, BLOB_SIZE, DRAW_OFFSET, STRIDE, OWNERS, patch_owners
from v3_registry import villager_actor, VILLAGERS
from v3_npc_draw_smoke import boot_proofs
from npc_mail_show import relocate_verified_data


class HostTests(unittest.TestCase):
    def test_native_lookup_and_wide_voice_contract(self):
        self.sanitized('v3_npc_draw_test.c', [], 'full voice IDs pass')

    def test_larger_blob_startup_contract(self):
        self.sanitized('v3_asset_loader_test.c', ['-DAF_V3_BLOB_SIZE=16384', '-DAF_V3_ABI=2',
            str(ROOT / 'runtime/crc32.c')], 'rejection paths pass')

    def sanitized(self, source, extra, message):
        with tempfile.TemporaryDirectory(prefix='af-v3-draw-') as temp:
            binary = Path(temp) / 'check'
            subprocess.run(['gcc', '-std=c11', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(ROOT / 'tests' / source), *extra, '-o', str(binary)], check=True, capture_output=True)
            result = subprocess.run([str(binary)], check=True, capture_output=True, text=True, timeout=20)
            self.assertIn(message, result.stdout)

    def test_fixed_ids_leave_native_tests_and_sentinel_alone(self):
        self.assertEqual(villager_actor(232), 0xE0EA)
        self.assertEqual(villager_actor(235), 0xE0ED)
        self.assertEqual(set(VILLAGERS.values()), set(range(218, 238)))
        for invalid in (0, 215, 236, 237, 255):
            with self.assertRaises(ValueError):
                villager_actor(invalid)


@unittest.skipUnless((ROOT / 'build/v3-npc-draw-02/build.json').exists(), 'Local V3 draw build required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out = ROOT / 'build/v3-npc-draw-02'
        cls.report = json.loads((cls.out / 'build.json').read_text())
        cls.rom = (cls.out / 'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.base = (ROOT / 'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.native = (ROOT / 'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.files, cls.old = by_vrom(cls.rom), by_vrom(cls.base)

    def test_complete_draw_rows_voice_ids_and_guarded_blob(self):
        blob = self.files[BLOB].extract(self.rom)
        self.assertEqual(len(blob), BLOB_SIZE)
        self.assertEqual(struct.unpack_from('>5I', blob), (0x41465633, ABI, BLOB_SIZE, 430, 410))
        self.assertEqual(struct.unpack_from('>4I', self.files[MODULE].extract(self.rom), CONFIG),
                         (BLOB, BLOB_SIZE, zlib.crc32(blob), ABI))
        self.assertEqual(blob[-16:], bytes.fromhex('AF33C0DE') * 4)
        used = set()
        for row in self.report['npc_draw']['imports']:
            actor, voice = int(row['actor_id'], 16), row['voice_id']
            slot = actor - 0xE0DA
            record = blob[DRAW_OFFSET + slot * STRIDE:DRAW_OFFSET + (slot + 1) * STRIDE]
            self.assertEqual(struct.unpack_from('>HH', record), (actor, voice))
            self.assertEqual(sha256(record[4:]), row['record_sha256'])
            self.assertEqual(struct.unpack_from('>H', record, 6)[0], row['object_bank'])
            self.assertEqual(record[4 + 95], 255)
            self.assertFalse(row['audio_playback_ready'])
            used.add(slot)
        self.assertEqual(used, {16, 19})
        for slot in set(range(20)) - used:
            self.assertEqual(blob[DRAW_OFFSET + slot * STRIDE:DRAW_OFFSET + (slot + 1) * STRIDE], bytes(STRIDE))

    def test_only_reviewed_hooks_change_and_relocations_remain_valid(self):
        changes, _ = patch_owners(self.native, self.base, self.report['asset']['symbols'])
        allowed = {MODULE: set(range(STARTUP, STARTUP_END)),
                   CODE_VROM: set(range(STARTUP_CALL - CODE_RAM, STARTUP_CALL - CODE_RAM + 4))}
        for vrom, reloc, ram, draw, tail, frame, helper in OWNERS:
            self.assertEqual(changes[vrom], self.files[vrom].extract(self.rom))
            allowed[vrom] = set(range(draw - ram, draw - ram + 8)) | set(range(tail - ram, tail - ram + 8))
            self.assertEqual(self.files[reloc].extract(self.rom), self.old[reloc].extract(self.base))
        for vrom, entry in self.old.items():
            before, after = entry.extract(self.base), self.files[vrom].extract(self.rom)
            self.assertEqual(entry.index, self.files[vrom].index)
            if vrom == 0x19D40:
                self.assertEqual(before[:16], after[:16])
                continue
            self.assertEqual(len(before), len(after))
            self.assertTrue(all(a == b or i in allowed.get(vrom, ())
                                for i, (a, b) in enumerate(zip(before, after))), hex(vrom))

    def test_owned_sources_patch_reconstruction_and_no_import_path(self):
        for path, digest in self.report['sources'].items():
            self.assertEqual(sha256((ROOT / path).read_bytes()), digest, path)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (self.out / 'asset-loader.ups').read_bytes()), self.rom)
        self.assertEqual(compose(self.native, self.base, {}, {}), self.base)

    def test_native_fixture_boot_proofs_and_overlay_relocation(self):
        self.assertEqual(set(boot_proofs(self.rom)), {0x800262D0, 0x8002FE00, 0x80034CE0})
        for vrom, reloc_vrom, ram, draw, tail, frame, helper in OWNERS:
            source, reloc = self.files[vrom].extract(self.rom), self.files[reloc_vrom].extract(self.rom)
            sections = struct.unpack_from('>5I', reloc)
            spec = SimpleNamespace(ram=ram, resident_bytes=len(source) + sections[3], sections=sections)
            constants = (0x80969690 if vrom == 0x8681F0 else 0x80989060,
                         ram + spec.resident_bytes)
            relocated = relocate_verified_data(spec, source, reloc, 0x802DC000, address_constants=constants)
            self.assertEqual(len(relocated), spec.resident_bytes)
            for address in (draw, tail):
                self.assertEqual(relocated[address - ram:address - ram + 8], source[address - ram:address - ram + 8])


if __name__ == '__main__':
    unittest.main()
