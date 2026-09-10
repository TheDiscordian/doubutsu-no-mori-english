"""House-sign names retain position lookup, stack bounds, and prior translations."""
import copy
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom
from check_keyboard_assembly import IMAGE
from npc_mail_show import relocate_verified_data
import house_name as h

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PRIOR, BUILD = ROOT/'build/conversation-names-pilot', ROOT/'build/house-name-pilot'


@unittest.skipUnless(ROM.is_file() and (PRIOR/'build.json').is_file(), 'Native ROM and prior build required')
class HouseNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes(); cls.prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((PRIOR/'build.json').read_text()); cls.files = by_vrom(cls.prior)
        cls.original = {v: cls.files[v].extract(cls.prior) for v in (CODE_VROM, h.VROM, h.RELOC)}
        cls.additions = {h.TEXT_VROM: cls.files[h.TEXT_VROM].extract(cls.prior)}

    def test_eight_byte_initialization_and_position_abi_fit_original_frame(self):
        data, _, code = h.source(self.native)
        word = lambda at: struct.unpack_from('>I', data, at-h.RAM)[0]
        self.assertEqual(word(0x80A963E0), 0x27BDFFD8)
        self.assertEqual(word(0x80A963E4), 0xAFBF0014)
        self.assertEqual(word(0x80A96480), 0x27BD0028)
        self.assertEqual(word(0x80A96434), 0x24041369)  # Same message.
        self.assertEqual(word(0x80A96420), 0x00002825)  # Same field zero.
        self.assertEqual(0x1C+8, 0x24)  # Immediately before later colour, below frame end.
        self.assertEqual(0x24+4, 0x28)
        # Independently specify the setup register/dataflow and both blank words.
        self.assertEqual(struct.unpack('>11I', h.preparation()), (
            0x00807025, 0x3C082020, 0x35082020, 0xAFA8001C, 0xAFA80020,
            0x8DC50028, 0x8DC6002C, 0x8DC70030, 0x27A4001C,
            h.jump(h.HELPER, link=True), 0))
        # The actual callee spills all four arguments into the outgoing homes;
        # no removed caller store was an independent parameter.
        self.assertEqual(struct.unpack_from('>4I', code, 0x800ACF98-CODE_RAM),
                         (0xAFA40060, 0xAFA50064, 0xAFA60068, 0xAFA7006C))
        new = h.patch_code(code)
        self.assertEqual(h.patch_code(new, reverse=True), code)
        self.assertEqual({i for i in range(0, len(code), 4) if code[i:i+4] != new[i:i+4]},
                         {h.IDENTITY_CALL-CODE_RAM})

    def test_independent_mips_preparation_and_call_assembly(self):
        with tempfile.TemporaryDirectory(prefix='af-house-name-') as directory:
            common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/house_name:/source:ro', '-v', f'{directory}:/out',
                      '-w', '/out', '--entrypoint']
            def run(tool, *args):
                subprocess.run(common+[f'/n64_toolchain/bin/mips64-elf-{tool}', IMAGE, *args],
                               check=True, capture_output=True, timeout=60)
            run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'name.o', '/source/name.s')
            run('ld', '-EB', '-T', '/source/name.ld', '-o', 'name.elf', 'name.o')
            for name, expected in (('preparation', h.preparation()), ('length', bytes.fromhex('24070008')),
                                   ('identity', struct.pack('>I', h.jump(h.BRIDGE, link=True)))):
                run('objcopy', '-O', 'binary', '-j', '.text.'+name, 'name.elf', name+'.bin')
                self.assertEqual((Path(directory)/(name+'.bin')).read_bytes(), expected)

    def test_exclusive_caller_and_unchanged_actor_relocation(self):
        before, reloc, _ = h.source(self.native); after = h.patch_actor(self.native)
        evidence = h.audit_references(self.native)
        self.assertEqual(evidence['callers'], ['80A9640C'])
        self.assertEqual(evidence['literal_pointers'], [])
        for base in (0x801A0010, 0x802F8010):
            expected = bytearray(relocate_verified_data(h.image_spec(), before, reloc, base))
            expected[h.START-h.RAM:h.END-h.RAM] = h.preparation()
            struct.pack_into('>I', expected, h.LENGTH-h.RAM, 0x24070008)
            self.assertEqual(relocate_verified_data(h.image_spec(), after, reloc, base), expected)
        masked = bytearray(after)
        for start, end in ((h.START, h.END), (h.LENGTH, h.LENGTH+4)):
            masked[start-h.RAM:end-h.RAM] = before[start-h.RAM:end-h.RAM]
        self.assertEqual(masked, before)

    def test_failed_dependencies_do_not_publish_partial_changes(self):
        cases = ((h.VROM, 0), (h.RELOC, 0), (CODE_VROM, h.HELPER-CODE_RAM),
                 (CODE_VROM, h.METADATA-CODE_RAM), (CODE_VROM, h.SETTER-CODE_RAM), (h.TEXT_VROM, 0))
        for vrom, at in cases:
            replacements, additions = dict(self.original), dict(self.additions)
            target = additions if vrom in additions else replacements
            data = bytearray(target[vrom]); data[at] ^= 1; target[vrom] = bytes(data)
            saved = dict(replacements), dict(additions)
            with self.assertRaises(ValueError): h.install(self.native, replacements, additions, self.report)
            self.assertEqual((replacements, additions), saved)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete house-sign cartridge required')
    def test_cartridge_retains_every_prior_payload_and_reconstructs_patch(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text()); files = by_vrom(built)
        h.verify_installation(built, self.native, report)
        from text_extension import verify_installation
        verify_installation(built, self.native, report)
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(set(files), set(self.files))
        changes = dict(self.original); h.install(self.native, changes, self.additions, self.report)
        for vrom, file in files.items():
            old = self.files[vrom]
            self.assertEqual((file.index, file.vstart, file.vend), (old.index, old.vstart, old.vend))
            if vrom != 0x19D40:
                self.assertEqual(file.extract(built), changes.get(vrom, old.extract(self.prior)), hex(vrom))
        for key in ('translation_edits', 'runtime_module', 'text_extension', 'display_names', 'catchphrases',
                    'extended_items', 'extended_font', 'noticeboard', 'secret_actor', 'conversation_names'):
            self.assertEqual(report[key], self.report[key], key)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete house-sign cartridge required')
    def test_combined_accounting_requires_complete_house_reader(self):
        from translation_progress import measure
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes(); report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, built, report)
        self.assertEqual(ledger.summary()['total_source_characters'], 751284)
        from item_name_readers import resource_only_weight
        self.assertEqual(ledger.summary()['replaced_source_characters'], 720689+35+resource_only_weight(ledger))
        broken = copy.deepcopy(report); broken['house_name']['name_bytes'] = 6
        with self.assertRaises(ValueError): measure(self.native, built, broken)


if __name__ == '__main__': unittest.main()
