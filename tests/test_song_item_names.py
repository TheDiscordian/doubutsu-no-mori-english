"""Guarded song-title caller and unchanged credits/overlay ownership."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256
import credits_strings as c
import song_item_names as s
from npc_mail_show import relocate_verified_data
from dataclasses import replace
from runtime_layout import MODULE_VROM
from extended_items import VROM as ITEMS_VROM

PREVIOUS = ROOT/'build/ordinary-items-pilot'
BUILD = ROOT/'build/song-names-pilot'
ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'


@unittest.skipUnless(ROM.is_file() and (PREVIOUS/'build.json').is_file(), 'Local ROM and current complete build required')
class SongItemNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.built = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        cls.files = by_vrom(cls.built)
        cls.report = json.loads((PREVIOUS/'build.json').read_text())
        cls.data = cls.files[c.VROM].extract(cls.built)
        cls.relocation = cls.files[c.RELOCATION].extract(cls.built)

    def test_only_original_setter_changes_and_relocation_preserves_tail_jump(self):
        output = s.patch(self.data, self.relocation)
        a, b = s.START-c.RAM, s.END-c.RAM
        self.assertEqual(output[:a], self.data[:a])
        self.assertEqual(output[b:], self.data[b:])
        self.assertEqual(output[a:b], s.PATCH)
        self.assertEqual(sha256(self.data[a:b]), s.SOURCE_HASH)
        spec = replace(c.CreditsOverlay(), sections=(*c.SECTIONS[:3], c.OLD_BSS+c.EXTRA_BSS, c.SECTIONS[4]))
        for base in (0x801A0000, 0x802F8000, 0x802A0B28):
            old = relocate_verified_data(spec, self.data, self.relocation, base, base_alignment=8)
            new = relocate_verified_data(spec, output, self.relocation, base, base_alignment=8)
            self.assertEqual(new[:a]+new[b:], old[:a]+old[b:])
            self.assertEqual(new[a:b], s.PATCH)
            self.assertEqual(len(new), c.RESIDENT_BYTES)
            high = struct.unpack_from('>I', new, 0x80AA3C00-c.RAM)[0] & 65535
            low = struct.unpack_from('>h', new, 0x80AA3C28-c.RAM+2)[0]
            self.assertEqual((high << 16)+low, base+a)
        with self.assertRaisesRegex(ValueError, 'base'):
            relocate_verified_data(spec, output, self.relocation, 0x802A0B28)
        for alignment, base in ((4,0x802A0B28),(8,0x802A0B2C),(8,0x80400000),
                                (True,0x802A0B28),(8,0x801948E0)):
            with self.assertRaisesRegex(ValueError, 'base'):
                relocate_verified_data(spec, output, self.relocation, base, base_alignment=alignment)
        for offset in range(a, b, 4):
            changed = bytearray(self.data)
            changed[offset] ^= 1
            with self.assertRaisesRegex(ValueError, 'Changed native song'):
                s.patch(changed, self.relocation)
        changed = bytearray(self.relocation)
        struct.pack_into('>I', changed, 20, 0x42000000 | a)
        with self.assertRaisesRegex(ValueError, 'relocation inside'):
            s.patch(self.data, changed)

    def test_four_instructions_preserve_slot_low_byte_and_tail_return(self):
        # Independently decoded instructions; Docker assembly also verifies the
        # corresponding source. Preserve the full int slot, not its low byte.
        self.assertEqual(s.WORDS, (0x30A800FF, 0x00802825, 0x0802EDA8, 0x25042A00))
        for song in (*range(256), 0x100, 0x12A, 0xFFFFFF00, 0xFFFFFFFF):
            for slot in (*range(6), 0x100, 0xFFFFFFFF):
                regs = {0:0, 4:slot, 5:song, 31:0x8019A8E0}
                for word in s.WORDS:
                    op, rs, rt, rd = word >> 26, (word >> 21)&31, (word >> 16)&31, (word >> 11)&31
                    if op == 12:
                        regs[rt] = regs[rs] & (word & 65535)
                    elif op == 0 and word & 63 == 37:
                        regs[rd] = regs[rs] | regs[rt]
                    elif op == 9:
                        regs[rt] = (regs[rs]+(word & 65535)) & 0xFFFFFFFF
                    elif op == 2:
                        self.assertEqual(0x80000000 | ((word & 0x03FFFFFF)<<2), s.WRAPPER)
                    else:
                        self.fail('Unexpected song wrapper instruction')
                self.assertEqual(regs[4], 0x2A00+(song & 255))
                self.assertEqual(regs[5], slot)
                self.assertEqual(regs[31], 0x8019A8E0)

    def test_live_actor_metadata_keeps_all_static_fields_guarded(self):
        from song_item_names_smoke import owner_metadata
        expected = bytearray(c.METADATA_BYTES)
        struct.pack_into('>I', expected, 12, c.RAM+c.RESIDENT_BYTES)
        self.assertEqual(owner_metadata(expected, expected), (0,0))
        actual = bytearray(expected)
        struct.pack_into('>I', actual, 16, 0x802A0B28)
        actual[30] = 1
        self.assertEqual(owner_metadata(actual, expected), (0x802A0B28,1))
        for at in [*range(16), *range(20,30), 31]:
            changed = bytearray(actual)
            changed[at] ^= 1
            with self.assertRaisesRegex(ValueError, 'identity or invalid'):
                owner_metadata(changed, expected)
        for pointer,count in ((0,1),(0x802A0B28,0),(0x801948E0,1),
                              (0x802A0B29,1),(0x803FFFFC,1),(0x802A0B28,128)):
            changed = bytearray(actual)
            struct.pack_into('>I', changed, 16, pointer)
            changed[30] = count
            with self.assertRaises(ValueError):
                owner_metadata(changed, expected)

    def test_installer_requires_all_real_dependencies_without_partial_writes(self):
        original = {v:self.files[v].extract(self.built) for v in (CODE_VROM, c.VROM, c.RELOCATION)}
        additions = {v:self.files[v].extract(self.built) for v in (MODULE_VROM, ITEMS_VROM)}
        replacements = dict(original)
        result = s.install(self.native, replacements, additions, self.report['runtime_module'])
        self.assertEqual(replacements[c.VROM], s.patch(self.data, self.relocation))
        self.assertEqual(replacements[CODE_VROM], original[CODE_VROM])
        self.assertEqual(replacements[c.RELOCATION], original[c.RELOCATION])
        self.assertEqual(result['new_resident_bytes'], 0)
        self.assertEqual(result['new_saved_bytes'], 0)
        self.assertFalse(result['song_request_input_expanded'])
        for target in (c.VROM, c.RELOCATION, CODE_VROM):
            bad = dict(original)
            altered = bytearray(bad[target])
            at = s.WRAPPER-CODE_RAM if target == CODE_VROM else 0
            altered[at] ^= 1
            bad[target] = bytes(altered)
            before = dict(bad)
            with self.assertRaises(ValueError):
                s.install(self.native, bad, additions, self.report['runtime_module'])
            self.assertEqual(bad, before)
        for missing in (MODULE_VROM, ITEMS_VROM):
            with self.assertRaises(ValueError):
                s.install(self.native, dict(original), {k:v for k,v in additions.items() if k != missing}, self.report['runtime_module'])
        with self.assertRaises(ValueError):
            s.install(self.native, dict(original), additions, None)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Local complete song-title ROM required')
class SongItemNameArtifactTests(unittest.TestCase):
    def test_native_scenario_binds_every_installed_song_and_current_actor(self):
        from song_item_names_scenario import scenario
        native = ROM.read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        actions = scenario(native, built, report)
        self.assertEqual(actions, json.loads((ROOT/'build/song-item-names-scenario.json').read_text()))
        request = actions[3]['test_song_item_names']
        self.assertEqual(len(request['names']), 55)
        self.assertTrue(all(len(bytes.fromhex(name)) == 16 for name in request['names']))
        self.assertEqual(len(bytes.fromhex(request['short_names'])), 550)
        self.assertEqual(bytes.fromhex(request['names'][0]), b'K.K. Chorale    ')
        self.assertEqual(bytes.fromhex(request['names'][1]), b'K.K. March      ')
        damaged = bytearray(built)
        damaged[-1] ^= 1
        with self.assertRaisesRegex(ValueError, 'Changed complete'):
            scenario(native, damaged, report)

    def test_only_song_overlay_changes_and_complete_patch_reconstructs(self):
        from aflib import apply_ups
        native = ROM.read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        previous = (PREVIOUS/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        s.verify_installation(native, built, report)
        old, new = by_vrom(previous), by_vrom(built)
        self.assertEqual(old.keys(), new.keys())
        self.assertEqual({v for v in old if old[v].extract(previous) != new[v].extract(built)}, {c.VROM})
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(sha256(built), report['output_sha256'])


@unittest.skipUnless((ROOT/'build/smoke-song-item-names-03/results.json').is_file(),
                     'Local complete native song-title evidence required')
class SongItemNameResultsTests(unittest.TestCase):
    def test_all_titles_real_insertions_bounds_restoration_and_blank_saves(self):
        from collections import Counter
        run = ROOT/'build/smoke-song-item-names-03'
        raw = (run/'results.json').read_bytes()
        self.assertEqual(sha256(raw), '958609e5839f4fcb1beffa363e2f24c1e79dc133ecbdf0e8df2bd2a211fee3b4')
        rows = json.loads(raw)
        info = json.loads((run/'run.json').read_text())
        plan = json.loads((ROOT/'build/song-item-names-resume.json').read_text())
        request = next(a['test_song_item_names'] for a in plan if 'test_song_item_names' in a)
        self.assertEqual(len(rows), 516)
        self.assertFalse(any('error' in r or r.get('assertion') == 'failed' for r in rows))
        checks = [r for r in rows if 'song_item_check' in r]
        self.assertEqual(len(checks), 325)
        self.assertTrue(all(r['assertion'] == 'passed' and r['expected_sha256'] == r['observed_sha256'] for r in checks))
        calls = [r for r in rows if 'test_only_function_call' in r]
        self.assertEqual(len(calls), 125)
        self.assertTrue(all(r['stack_restored'] for r in calls))
        self.assertEqual(calls[1]['test_only_function_call'], '800262D0')
        self.assertEqual(calls[1]['return_value'], c.RESIDENT_BYTES)
        entry = f"{calls[1]['arguments'][4]+s.START-c.RAM:08X}"
        setters = [r for r in calls if r['test_only_function_call'] == entry]
        self.assertEqual([r['arguments'] for r in setters],
                         [[i%5,i] for i in range(55)]+[[0,55],[0,255],[5,0],[0xFFFFFFFF,1],[256,2]]+
                         [[4,0x100],[4,0x101],[4,0xFFFFFF00],[0,0],[0,0]])
        insertions = [r for r in calls if r['test_only_function_call'] == '800A17FC']
        self.assertEqual(len(insertions), 55)
        self.assertTrue(all(r['return_value'] == 0 for r in insertions))
        self.assertEqual([r['arguments'] for r in insertions], [[0x80142410,0,i%5] for i in range(55)])
        self.assertEqual([r['native_song_item'] for r in rows if 'native_song_item' in r], list(range(55)))
        messages = [r for r in checks if r['song_item_check'] == 'complete native song-title insertion']
        self.assertEqual([r['observed_sha256'] for r in messages],
                         [sha256(bytes.fromhex(n).rstrip(b' ')+b'!') for n in request['names']])
        labels = Counter(r['song_item_check'] for r in checks)
        for label,count in (('song global restored',6),('song fixture and stack guard',7),
                            ('saved state unchanged',1),('song setter heap retained',1),
                            ('native live actor code and credits state retained',1),
                            ('invalid song or slot retains full fields',5)):
            self.assertEqual(labels[label], count)
        saved = next(r for r in checks if r['song_item_check'] == 'saved state unchanged')
        self.assertEqual(saved['bytes'], 63872)
        summary = next(r for r in rows if 'complete_song_fields' in r)
        self.assertTrue(summary['resource_fallback_and_retry'])
        for key in ('normal_performance','song_request_input_tested','game_save_validation','hardware_verified'):
            self.assertFalse(summary[key])
        self.assertEqual(summary['debugger_uploaded_production_bytes'], 0)
        self.assertEqual(info['rom_sha256'], sha256((BUILD/'animal-forest-halfwidth.z64').read_bytes()))
        self.assertEqual(info['scenario_sha256'], sha256((ROOT/'build/song-item-names-resume.json').read_bytes()))
        self.assertEqual(info['audio'], 'disabled')
        for key in ('initial_screenshot','expansion_pak','allow_test_flash_write','allow_test_pak_write'):
            self.assertFalse(info[key])
        seed = next(r for r in info['seed_files'] if r['file'] == 'test.bs1')
        self.assertEqual(seed['sha256'], '2d451168de28ce62cc58017ed3441cb41eb17fb4fa10d38a6b0f480a9e6dee91')
        restored = max(i for i,r in enumerate(rows) if r.get('loaded_state') == 'test.bs1')
        self.assertTrue(any(r.get('read') == ['8019B000',4] and r.get('data') == '00000000'
                            and r.get('assertion') == 'passed' for r in rows[restored+1:]))
        self.assertTrue(rows[-1]['graceful_shutdown'])
        for name,digest in (('test.bs1','8e9ece8f9fd078d7168684bcfc441471ef69e6f2842378c2522d455f61620cc2'),
                            ('test.flash','b5a41c3758763bbec72769fab4a2533bf2db0b6312d93d25a695f9e4b9e02260'),
                            ('test.pak','ab2a6e04fd3ceb36594f1216c888a1b8bd0a3ba0a94f715a7c7601e98c49ec51')):
            self.assertEqual(sha256((run/name).read_bytes()), digest)


if __name__ == '__main__':
    unittest.main()
