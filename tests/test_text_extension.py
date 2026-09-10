"""Focused artifact, actor, startup, and cartridge checks for complete free fields."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import CODE_RAM, CODE_VROM, DMA_START, apply_ups, by_vrom, sha256
from check_keyboard_assembly import IMAGE
from runtime_module import MODULE_VROM
from extended_items import VROM as ITEMS_VROM
import text_extension as t

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PRIOR, BUILD, ARTIFACT = (ROOT/'build'/name for name in
                         ('stall-choices-pilot', 'text-extension-pilot', 'text-extension'))


@unittest.skipUnless(ROM.is_file() and (PRIOR/'build.json').is_file(), 'Native ROM and preceding build required')
class TextExtensionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((PRIOR/'build.json').read_text())
        cls.files = by_vrom(cls.prior)
        cls.module = cls.report['runtime_module']
        cls.original = {CODE_VROM: cls.files[CODE_VROM].extract(cls.prior)}
        cls.additions = {v: cls.files[v].extract(cls.prior) for v in (MODULE_VROM, ITEMS_VROM, 0x03400000)}

    def test_complete_artifacts_and_independent_rebuild(self):
        artifact = json.loads((ARTIFACT/'extension.json').read_text())
        blob, loader = ((ARTIFACT/name).read_bytes() for name in ('blob.bin', 'loader.bin'))
        t.validate(blob, loader, artifact)
        for name in ('extension.json', 'extension.bin', 'relocation.bin', 'blob.bin', 'loader.bin'):
            self.assertEqual((ARTIFACT/name).read_bytes(), (ROOT/'build/text-extension-rebuild'/name).read_bytes())
        for part in (0, 1616, len(blob)-1):
            altered = bytearray(blob); altered[part] ^= 1
            with self.assertRaises(ValueError): t.validate(altered, loader, artifact)
        with self.assertRaises(ValueError): t.validate(blob, loader, {**artifact, 'imports': {}})

    def test_sanitized_general_fields_and_native_formatting(self):
        with tempfile.TemporaryDirectory(prefix='af-free-fields-') as directory:
            binary = str(Path(directory)/'fields')
            subprocess.run(['gcc', '-std=c11', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                '-I', str(ROOT/'overlays/text_extension'), str(ROOT/'overlays/text_extension/fields.c'),
                str(ROOT/'tests/text_extension_fields_harness.c'), '-o', binary], check=True, timeout=30)
            subprocess.run([binary], check=True, timeout=30)

    def test_independent_assembly_for_bootstrap_and_three_adapters(self):
        with tempfile.TemporaryDirectory(prefix='af-free-item-asm-') as directory:
            common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/events:/source:ro', '-v', f'{directory}:/out', '-w', '/out', '--entrypoint']
            def run(tool, *args):
                subprocess.run(common+[f'/n64_toolchain/bin/mips64-elf-{tool}', IMAGE, *args], check=True, timeout=60)
            run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'hooks.o', '/source/free_item.s')
            run('ld', '-EB', '-T', '/source/free_item.ld', '-o', 'hooks.elf', 'hooks.o')
            for name in ('tail', *t.ACTORS):
                run('objcopy', '-O', 'binary', '-j', '.text.'+name, 'hooks.elf', name+'.bin')
                self.assertEqual((Path(directory)/(name+'.bin')).read_bytes(),
                                 t.tail_body() if name == 'tail' else t.call_body(name))

    def test_source_guards_relocation_and_atomic_failure(self):
        replacements, additions = dict(self.original), dict(self.additions)
        evidence = t.install(self.native, replacements, additions, {}, self.module, ARTIFACT)
        self.assertEqual(evidence['additional_system_allocation_bytes'], 2159)
        self.assertFalse(evidence['saved_layout_changes'])
        self.assertEqual(set(replacements), {CODE_VROM, *(s.vrom for s in t.ACTORS.values())})
        for address in (t.SETTER, t.TAIL, t.EPILOGUE, 0x800A1370, 0x800BB6F8):
            code = bytearray(self.original[CODE_VROM]); code[address-CODE_RAM] ^= 1
            values, extra = {CODE_VROM: bytes(code)}, dict(self.additions)
            before, extra_before = dict(values), dict(extra)
            with self.assertRaises(ValueError): t.install(self.native, values, extra, {}, self.module, ARTIFACT)
            self.assertEqual(values, before); self.assertEqual(extra, extra_before)
        # Shrine's original window is the singleton, not an arbitrary argument.
        data, _ = t.source(self.native, 'shrine'); spec = t.ACTORS['shrine']
        self.assertEqual(data[0x80A0A938-spec.ram:0x80A0A93C-spec.ram], bytes.fromhex('0c02747c'))
        self.assertEqual(data[0x80A0A948-spec.ram:0x80A0A94C-spec.ram], bytes.fromhex('afa20034'))
        self.assertEqual(evidence['reference_audit']['external_interior_references'], [])

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete extension build required')
    def test_complete_rom_patch_and_all_preceding_payloads(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        files = by_vrom(built)
        t.verify_installation(built, self.native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(set(files), set(self.files) | {t.VROM})
        replacements, additions = dict(self.original), dict(self.additions)
        t.install(self.native, replacements, additions, {}, self.module, ARTIFACT)
        for vrom, old in self.files.items():
            new = files[vrom]
            self.assertEqual((new.index, new.vstart, new.vend), (old.index, old.vstart, old.vend))
            if vrom == 0x19D40: continue
            self.assertEqual(new.extract(built), replacements.get(vrom, old.extract(self.prior)))
        # Existing DMA identities stay fixed. The sole new row is the extension.
        tables = [bytearray(f[0x19D40].extract(rom)) for f, rom in ((files, built), (self.files, self.prior))]
        for file in files.values():
            at = DMA_START-0x19D40+file.index*16
            for table in tables:
                table[at+8:at+16] = bytes(8)
                if file.vstart == t.VROM: table[at:at+8] = bytes(8)
        self.assertEqual(*tables)
        self.assertEqual(report['translation_edits'], self.report['translation_edits'])
        for key in ('runtime_module', 'extended_font', 'extended_items', 'display_names', 'catchphrases',
                    'npc_mail_loader', 'noticeboard', 'inventory_english', 'catalogue_names',
                    'town_suffix', 'shop_item_names', 'player_item_names', 'event_item_names', 'stall_choices'):
            self.assertEqual(report[key], self.report[key], key)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete extension build required')
    def test_combined_counter_requires_extension_and_retains_unfinished_reader_status(self):
        from translation_progress import measure
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, built, report)
        result = ledger.summary()
        self.assertEqual(result['replaced_source_characters'], 720661+35)
        self.assertEqual(result['total_source_characters'], 751307)
        self.assertGreater(result['pending_application_records'], 0)
        # No invented source records or duplicate weight for field connections.
        self.assertFalse(any(key.startswith('text_extension:') for key in ledger.rows))


if __name__ == '__main__': unittest.main()
