"""Complete guide name preserves its neighbouring pointer and coloured field."""
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
from aflib import CODE_RAM, CODE_VROM, apply_ups, by_vrom, sha256
from check_keyboard_assembly import IMAGE
from npc_mail_show import relocate_verified_data
import guide_name as g

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PRIOR, BUILD = ROOT/'build/map-names-pilot', ROOT/'build/guide-name-pilot'


@unittest.skipUnless(ROM.is_file(), 'Native ROM required')
class GuideNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()

    def test_original_frame_numeric_fields_and_colour_are_preserved(self):
        original, _ = g.source(self.native); data, _ = g.patched(self.native)
        changes = {g.RAM+i for i in range(0, g.PREFIX, 4) if data[i:i+4] != original[i:i+4]}
        self.assertEqual(changes, {g.CALL, g.LENGTH})
        word = lambda address: struct.unpack_from('>I', data, address-g.RAM)[0]
        self.assertEqual(word(0x809C8248), 0x27BDFFC0)
        self.assertEqual(word(0x809C8314), 0x27A4002C)
        self.assertEqual(word(0x809C831C), 0x8FA50034)
        self.assertEqual(0x2C+8, 0x34)
        self.assertEqual(word(0x809C8320), 0x24080001)
        self.assertEqual(word(0x809C8324), 0xAFA80010)
        self.assertEqual(word(0x809C832C), 0x24050005)
        self.assertEqual(word(0x809C8334), g.jump(0x8009D820, link=True))
        self.assertEqual(word(0x809C8338), 0x24070008)
        for at in (0x809C82DC, 0x809C8310): self.assertEqual(word(at), 0x24070006)
        words = struct.unpack('>28I', g.body())
        self.assertEqual(words[10], 0x12200009)
        self.assertEqual(10+1+(words[10] & 65535), 20)
        self.assertEqual(16+1+(words[16] & 65535), 20)
        self.assertEqual(words[12:16], (0x96260000, 0x24C82000, 0x3108FFFF, 0x2D0800D8))
        self.assertEqual([i for i in range(65536) if ((i+0x2000) & 65535) < 216], list(range(0xE000, 0xE0D8)))
        self.assertEqual(words[:4], (0x27BDFFE0, 0xAFBF001C, 0xAFB00018, 0xAFB10014))
        self.assertEqual(words[20:25], (0x8FBF001C, 0x8FB10014, 0x8FB00018, 0x03E00008, 0x27BD0020))

    def test_independent_mips_assembly(self):
        with tempfile.TemporaryDirectory(prefix='af-guide-name-') as directory:
            common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/events:/source:ro', '-v', f'{directory}:/out', '-w', '/out', '--entrypoint']
            def run(tool, *args):
                subprocess.run(common+[f'/n64_toolchain/bin/mips64-elf-{tool}', IMAGE, *args], check=True, timeout=60)
            run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'name.o', '/source/guide_name.s')
            run('ld', '-EB', '-T', '/source/guide_name.ld', '-o', 'name.elf', 'name.o')
            run('objcopy', '-O', 'binary', '-j', '.text', 'name.elf', 'name.bin')
            self.assertEqual((Path(directory)/'name.bin').read_bytes(), g.body())

    def test_original_relocation_and_fixed_calls_at_two_bases(self):
        original, original_reloc = g.source(self.native); data, reloc = g.patched(self.native)
        for base in (0x801A0010, 0x802F8010):
            old = relocate_verified_data(g.Image(g.RAM, g.PREFIX, g.SECTIONS), original, original_reloc, base)
            new = relocate_verified_data(g.relocated_spec(), data, reloc, base)
            for at in range(0, g.PREFIX, 4):
                if g.RAM+at not in (g.CALL, g.LENGTH): self.assertEqual(new[at:at+4], old[at:at+4])
            self.assertEqual(new[g.PREFIX:], g.body())
            self.assertEqual(struct.unpack_from('>I', new, g.CALL-g.RAM)[0], g.jump(base+g.PREFIX, link=True))

    @unittest.skipUnless((PRIOR/'build.json').is_file(), 'Preceding map build required')
    def test_failed_guard_is_atomic(self):
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes(); files = by_vrom(prior)
        module = json.loads((PRIOR/'build.json').read_text())['runtime_module']
        for vrom, at in ((g.VROM, 0), (CODE_VROM, g.METADATA-CODE_RAM), (g.NAMES_VROM, 35),
                         (g.MODULE_VROM, 60), (CODE_VROM, 0x800ACD18-CODE_RAM)):
            changes = {CODE_VROM: files[CODE_VROM].extract(prior)}
            additions = {v: files[v].extract(prior) for v in (g.MODULE_VROM, g.NAMES_VROM)}
            target = additions if vrom in additions else changes
            data = bytearray(target.get(vrom, files[vrom].extract(prior))); data[at] ^= 1
            target[vrom] = bytes(data); before = copy.deepcopy((changes, additions))
            with self.assertRaises(ValueError): g.install(self.native, changes, additions, {}, module)
            self.assertEqual((changes, additions), before)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete guide build required')
    def test_complete_patch_retains_map_and_every_prior_translation(self):
        prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text()); files, old = by_vrom(built), by_vrom(prior)
        g.verify_installation(built, self.native, report)
        from text_extension import verify_installation
        verify_installation(built, self.native, report)
        from notice_overlay import verify_installation
        verify_installation(built, self.native, report['runtime_module'], report['noticeboard'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(set(old)-set(files), {g.VROM, g.RELOC})
        self.assertEqual(set(files)-set(old), {g.NEW_VROM, g.NEW_RELOC})
        for v in files.keys() & old.keys():
            if v not in (0x19D40, CODE_VROM): self.assertEqual(files[v].extract(built), old[v].extract(prior), hex(v))
        code = bytearray(old[CODE_VROM].extract(prior))
        code[g.METADATA-CODE_RAM:g.METADATA-CODE_RAM+32] = g.metadata()
        self.assertEqual(files[CODE_VROM].extract(built), code)
        self.assertEqual(sha256(built), report['output_sha256'])

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete guide build required')
    def test_combined_accounting_verifies_the_reader(self):
        from translation_progress import measure, pending_name_consumers
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), report)
        self.assertEqual(ledger.summary()['total_source_characters'], 751307)
        # This one reader does not finish the entire pending name family.
        previous = measure(self.native, (PRIOR/'animal-forest-halfwidth.z64').read_bytes(),
                           json.loads((PRIOR/'build.json').read_text()))
        self.assertEqual(ledger.summary()['replaced_source_characters'],
                         previous.summary()['replaced_source_characters'])
        self.assertIn('opening-guide name is connected', pending_name_consumers(report)['display_names'])
        broken = copy.deepcopy(report); broken['guide_name']['field_slot'] = 4
        with self.assertRaises(ValueError):
            measure(self.native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), broken)


if __name__ == '__main__': unittest.main()
