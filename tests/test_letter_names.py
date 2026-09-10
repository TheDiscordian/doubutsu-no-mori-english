"""Full letter-editor names and header geometry preserve saved fields and reading."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, replace_dma, sha256
from npc_mail_show import relocate_verified_data
import letter_names as n

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
OUT, BUILD, PRIOR = (ROOT/'build'/p for p in ('letter-names-overlay', 'letter-names-pilot', 'house-name-pilot'))


class LetterHostTests(unittest.TestCase):
    def test_name_accounting_requires_every_completed_reader_family(self):
        from display_name_readers import complete, REQUIRED
        report = {key: {'installed': True} for key in REQUIRED}
        report.update({'text_extension': {'choices': {}, 'identities': {}},
                       'mail_view': {'snapshot_reader': True},
                       'inventory_english': {'overlay': {'descriptions': True}},
                       'noticeboard': {'treasure_owner': {'installed': True}}})
        self.assertFalse(complete(report))
        report['text_extension'] = {'choices': {'installed': True}, 'identities': {'installed': True}}
        self.assertTrue(complete(report))
        for key in REQUIRED:
            broken = copy.deepcopy(report); del broken[key]
            self.assertFalse(complete(broken), key)
        for key in ('text_extension', 'mail_view', 'inventory_english', 'noticeboard'):
            broken = copy.deepcopy(report); del broken[key]
            self.assertFalse(complete(broken), key)

    def test_host_names_colours_cursor_fallback_and_unchanged_state(self):
        with tempfile.TemporaryDirectory(prefix='af-letter-names-') as directory:
            target = str(Path(directory)/'check')
            subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-O1', '-g',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer', str(ROOT/'overlays/letter_names/names.c'),
                str(ROOT/'tests/letter_names_check.c'), '-o', target], check=True, capture_output=True, timeout=30)
            subprocess.run([target], check=True, capture_output=True, timeout=10)


@unittest.skipUnless((OUT/'overlay.json').is_file(), 'Compiled letter-name overlay required')
class LetterArtifactTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.module = json.loads((ROOT/'build/notice-seasonal-runtime/module.json').read_text())
        cls.report = json.loads((OUT/'overlay.json').read_text())
        cls.data, cls.reloc = (OUT/'overlay.bin').read_bytes(), (OUT/'relocation.bin').read_bytes()

    def test_source_capacity_and_complete_compiled_profile(self):
        n.validate(self.native, self.data, self.reloc, self.report, self.module)
        self.assertEqual(len(self.data)-n.START, 1504)
        self.assertEqual(self.data[n.PREFIX:n.START], bytes(192))
        self.assertIn('af_letter_header\t112\tstatic', self.report['stack_usage'])
        self.assertIn('af_letter_cursor\t56\tstatic', self.report['stack_usage'])
        self.assertLess(112, 128)  # Header uses less stack than the replaced native function.
        before = n.preceding(self.native)[0]; after = self.data[:n.PREFIX]
        self.assertEqual({i for i in range(0, n.PREFIX, 4) if before[i:i+4] != after[i:i+4]},
                         {n.HEADER-n.RAM, n.HEADER-n.RAM+4, n.CURSOR_CALL-n.RAM})
        original, _, _, _ = n.native_sources(self.native)
        # Both original fallback targets, all acceptance/preference writes, and
        # the complete reader hook calls remain at their previous offsets.
        self.assertEqual(after[0x8088973C-n.RAM:0x808899E4-n.RAM], original[0x8088973C-n.RAM:0x808899E4-n.RAM])
        self.assertEqual(after[0x80889288-n.RAM:0x808894E4-n.RAM], original[0x80889288-n.RAM:0x808894E4-n.RAM])

    def test_relocated_calls_and_pool_arithmetic_are_exact(self):
        spec = n.validate(self.native, self.data, self.reloc, self.report, self.module)
        old, old_reloc = n.preceding(self.native)
        old_spec = n.Image(n.RAM, n.START, struct.unpack_from('>5I', old_reloc))
        for base in (0x801A0010, 0x802F8010):
            moved = relocate_verified_data(spec, self.data, self.reloc, base)
            expected = bytearray(relocate_verified_data(old_spec, old, old_reloc, base))
            struct.pack_into('>2I', expected, n.HEADER-n.RAM, n.jump(base+n.APPROVED['symbols']['af_letter_header']), 0)
            struct.pack_into('>I', expected, n.CURSOR_CALL-n.RAM, n.jump(base+n.APPROVED['symbols']['af_letter_cursor'], link=True))
            self.assertEqual(moved[:n.START], expected)
            for at, kind, target, symbol in self.report['elf_relocations']:
                if kind == 4:
                    actual = (struct.unpack_from('>I', moved, at)[0] & 0x3FFFFFF)*4 | 0x80000000
                    self.assertEqual(actual, target+base-n.RAM if n.RAM <= target < n.RAM+len(self.data) else target, symbol)
        old_endpoint = (0x8089 << 16)+0xFB20-0x10000
        new_endpoint = (0x8089 << 16)+(n.POOL_WORD & 65535)
        self.assertEqual(new_endpoint-old_endpoint, n.POOL_EXTRA)
        self.assertEqual(n.POOL_WORD >> 16, 0x25CE)  # Same addiu registers, no immediate carry into rt.

    def test_rehashed_damage_and_wrong_imports_are_rejected(self):
        for at in (n.HEADER-n.RAM, n.CURSOR_CALL-n.RAM, n.PREFIX, n.START, len(self.data)-1):
            changed = bytearray(self.data); changed[at] ^= 1
            report = {**self.report, 'overlay_sha256': sha256(changed), 'suffix_sha256': sha256(changed[n.START:])}
            with self.assertRaises(ValueError): n.validate(self.native, bytes(changed), self.reloc, report, self.module)
        self.assertNotIn('af_mail_snapshot_header', self.report['imports'])
        self.assertNotIn('af_mail_reader', self.report['imports'])
        module = copy.deepcopy(self.module); module['symbols']['af_mail_draw'] = '80199240'
        with self.assertRaises(ValueError): n.validate(self.native, self.data, self.reloc, self.report, module)

    def test_prospective_shared_installation_before_full_rebuild(self):
        from inventory_english import VROM as TAG_VROM, NEW_VROM as TAG_MOVED
        from notice_overlay import verify_installation as verify_notice
        from text_extension import verify_installation as verify_text
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes(); files = by_vrom(prior)
        report = json.loads((PRIOR/'build.json').read_text())
        replacements = {v:files[v].extract(prior) for v in (CODE_VROM,n.OWNER,n.VROM,n.RELOC)}
        replacements[TAG_VROM] = files[TAG_MOVED].extract(prior)
        relocations = {}
        report['letter_editor_names'] = n.install(self.native,replacements,{},relocations,report['runtime_module'],OUT)
        del replacements[TAG_VROM]
        built = replace_dma(prior,replacements,relocations,{})
        report['vrom_relocations'].update({f'{old:08X}':f'{new:08X}' for old,new in relocations.items()})
        n.verify_installation(built,self.native,report)
        verify_notice(built,self.native,report['runtime_module'],report['noticeboard'])
        verify_text(built,self.native,report)


@unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete letter-name cartridge required')
class LetterCartridgeTests(unittest.TestCase):
    def test_complete_cartridge_retains_previous_resources_and_patch(self):
        native = ROM.read_bytes(); built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes(); report = json.loads((BUILD/'build.json').read_text())
        n.verify_installation(built, native, report)
        from notice_overlay import verify_installation
        verify_installation(built, native, report['runtime_module'], report['noticeboard'])
        from text_extension import verify_installation
        verify_installation(built, native, report)
        self.assertEqual(apply_ups(native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        files, old = by_vrom(built), by_vrom(prior)
        self.assertEqual(set(files), set(old)-{n.VROM, n.RELOC}|{n.NEW_VROM,n.NEW_RELOC})
        for vrom, file in old.items():
            new_vrom = {n.VROM:n.NEW_VROM, n.RELOC:n.NEW_RELOC}.get(vrom,vrom)
            self.assertEqual(file.index, files[new_vrom].index)
            if vrom in (0x19D40, n.VROM, n.RELOC): continue
            before, after = file.extract(prior), bytearray(files[new_vrom].extract(built))
            if vrom == CODE_VROM: after[n.POOL_PATCH-CODE_RAM:n.POOL_PATCH-CODE_RAM+4] = before[n.POOL_PATCH-CODE_RAM:n.POOL_PATCH-CODE_RAM+4]
            if vrom == n.OWNER: after[n.OWNER_AT:n.OWNER_AT+32] = n.OWNER_ROW
            self.assertEqual(after,before,hex(vrom))
        self.assertLessEqual(report['letter_editor_names']['allocation']['conservative_required'],
                             report['letter_editor_names']['allocation']['combined_pool_bytes'])

    def test_combined_counter_requires_complete_editor_and_reader(self):
        from translation_progress import measure
        native = ROM.read_bytes(); built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(native,built,report); summary = ledger.summary()
        self.assertEqual(summary['total_source_characters'],751284)
        new_weight = sum(row['source_characters'] for row in ledger.rows.values()
                         if row['replacements'] and all(r['route'] == 'display_names' for r in row['replacements']))
        self.assertGreater(new_weight,0)
        from item_name_readers import resource_only_weight
        self.assertEqual(summary['replaced_source_characters'],720689+35+new_weight+resource_only_weight(ledger))
        from translation_progress import pending_name_consumers
        self.assertNotIn('display_names',pending_name_consumers(report))
        broken = copy.deepcopy(report); broken['letter_editor_names']['name_bytes'] = 6
        with self.assertRaises(ValueError): measure(native,built,broken)
        from display_name_readers import verify_main_routes
        broken = copy.deepcopy(report); broken['runtime_module']['symbols']['af_get_display_name'] = '80195D24'
        with self.assertRaises(ValueError): verify_main_routes(built,broken)


if __name__ == '__main__': unittest.main()
