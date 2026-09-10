"""Separate title data preview retains the complete base translation and code."""
from copy import deepcopy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, apply_ups
from title_assets import extract
from title_press_start import ACTOR, ASSETS, POSITIONS, TEXTURE_OFFSETS, replacements, assemble, build


@unittest.skipUnless((ROOT/'build/classic-letters-pilot/build.json').is_file(), 'Combined v0 candidate required')
class TitlePressStartTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base = (ROOT/'build/classic-letters-pilot/animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((ROOT/'build/classic-letters-pilot/build.json').read_text())
        cls.rel = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols = (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.english = extract(cls.rel, cls.symbols)[0]

    def test_only_literal_positions_and_three_complete_tiles_change(self):
        files = by_vrom(self.native)
        changed = replacements(self.native, self.base, self.english)
        self.assertEqual(set(changed), {ACTOR, ASSETS})
        actor = bytearray(changed[ACTOR]); native_actor = files[ACTOR].extract(self.native)
        self.assertEqual(struct.unpack_from('>6I', actor, POSITIONS), (96, 160, 224, 159, 159, 159))
        self.assertGreaterEqual(POSITIONS, 0x22D0)  # Native text section ends before these literals.
        actor[POSITIONS:POSITIONS+24] = native_actor[POSITIONS:POSITIONS+24]
        self.assertEqual(actor, native_actor)
        bank = bytearray(changed[ASSETS]); native_bank = files[ASSETS].extract(self.native)
        for at, expected in zip(TEXTURE_OFFSETS, (self.english['005E5020.ia8.bin'], self.english['005E5420.ia8.bin'], bytes(1024))):
            self.assertEqual(bank[at:at+1024], expected)
            bank[at:at+1024] = native_bank[at:at+1024]
        self.assertEqual(bank, native_bank)

    def test_changed_predecessor_incomplete_tile_or_lost_previous_resource_reject(self):
        with self.assertRaises(ValueError): replacements(self.native, self.native, self.english)
        with self.assertRaises(ValueError): replacements(self.native, self.base, {**self.english, '005E5020.ia8.bin': b''})
        changed = replacements(self.native, self.base, self.english)
        stale = deepcopy(self.report); stale['replacement_files'].remove('00D07000')
        with self.assertRaisesRegex(ValueError, 'previous resource|identity/size'):
            assemble(self.native, self.base, stale, changed)

    def test_complete_cartridge_and_ups_retain_the_original_v0_candidate(self):
        image, patch, report = build(self.native, self.base, self.report, self.rel, self.symbols)
        self.assertEqual(apply_ups(self.native, patch), image)
        self.assertEqual(len(image), len(self.base))
        self.assertFalse(report['actor_code_changed'])
        self.assertFalse(report['allocation_changed'])
        self.assertFalse(report['relocation_changed'])
        self.assertFalse(report['v0_candidate_changed'])


@unittest.skipUnless((ROOT/'build/title-press-start-preview/preview.json').is_file(), 'Separate title preview required')
class TitleMemoryObservationTests(unittest.TestCase):
    def fixture(self):
        from catalogue_names import Image
        from npc_mail_show import relocate_verified_data
        from title_press_start import RELOC, RAM
        rom = (ROOT/'build/title-press-start-preview/animal-forest-title-preview.z64').read_bytes()
        files = by_vrom(rom)
        overlay = files[ACTOR].extract(rom)
        relocated = relocate_verified_data(Image(RAM, len(overlay), (8912, 992, 48, 0, 145)),
            overlay, files[RELOC].extract(rom), 0x80210000)
        game, actor = bytearray(0x1CA4), bytearray(0x328)
        struct.pack_into('>2I', game, 0x1C9C, 1, 0x80203000)
        struct.pack_into('>H', actor, 0, 0xAB); actor[2] = 4
        struct.pack_into('>I', actor, 0x164, 0x80210000+0x80AA1E58-RAM)
        struct.pack_into('>I', actor, 0x2FC, 0x80220000)
        regions = {0x8010EF90: bytes.fromhex('80200000'), 0x80200000: game,
                   0x80203000: actor, 0x80210000: bytearray(relocated),
                   0x80220000: bytearray(files[ASSETS].extract(rom))}
        class ReadOnly:
            def read_memory(self, address, size):
                for start, data in regions.items():
                    if start <= address and address+size <= start+len(data):
                        return bytes(data[address-start:address-start+size])
                raise AssertionError('Unexpected title read')
        return rom, regions, ReadOnly()

    def test_read_only_observation_binds_complete_loaded_actor_and_assets(self):
        from title_start_smoke import verify
        rom, _, debug = self.fixture()
        result = verify(debug, rom)
        self.assertEqual(result['title_start_memory'], 'passed')
        self.assertTrue(result['read_only'])
        self.assertFalse(result['visual_validation'])

    def test_wrong_game_counts_overlay_and_texture_cannot_pass(self):
        from title_start_smoke import verify
        for region, offset in ((0x80200000, 0x1C9F), (0x80203000, 2),
                               (0x80210000, POSITIONS), (0x80220000, 0x1110)):
            rom, regions, debug = self.fixture()
            regions[region][offset] ^= 1
            with self.subTest(region=region, offset=offset), self.assertRaises(ValueError):
                verify(debug, rom)


if __name__ == '__main__':
    unittest.main()
