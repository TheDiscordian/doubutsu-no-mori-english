"""Full festival/reserve names preserve frames, arguments, and other payloads."""
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
from npc_mail_show import relocate_verified_data
import actor_display_names as a

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PRIOR, BUILD = ROOT/'build/text-choices-pilot', ROOT/'build/actor-names-pilot'


@unittest.skipUnless(ROM.is_file() and (PRIOR/'build.json').is_file(), 'Native ROM and preceding build required')
class ActorNameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((PRIOR/'build.json').read_text())
        cls.module, cls.files = cls.report['runtime_module'], by_vrom(cls.prior)
        cls.original = {v: cls.files[v].extract(cls.prior) for v in (CODE_VROM, a.ACTORS['reserve'].vrom)}
        cls.additions = {v: cls.files[v].extract(cls.prior) for v in (a.MODULE_VROM, a.NAMES_VROM)}

    def test_original_frames_slots_and_guarded_reserve_arguments(self):
        for name, (call, length, offset, frame) in a.CALLS.items():
            data, _ = a.source(self.native, name); spec = a.ACTORS[name]
            start, end, _ = a.FUNCTIONS[name]
            word = lambda address: struct.unpack_from('>I', data, address-spec.ram)[0]
            self.assertEqual(word(start), 0x27BD0000 | ((-frame) & 65535))
            self.assertEqual(word(end-4), 0x27BD0000 | frame)
            self.assertLessEqual(offset+8, frame)
            self.assertGreaterEqual(offset, 0x44)  # All live locals/saved registers end below this.
            self.assertEqual(word(call), a.jump(0x800ACDF8, link=True))
            self.assertEqual(word(length), 0x24070006)
            self.assertEqual(word(length-4), a.jump(a.t.SETTER, link=True))
            self.assertEqual(word(length-12), 0x26050001)  # Slot is participant index + one.
        words = struct.unpack('>11I', a.reserve_body())
        self.assertEqual(words[:4], (0x27A40024, 0x3406D008,
                                    a.jump(a.IMPORTS['af_load_display_name'], link=True), 0x24050008))
        self.assertEqual(words[4], 0x10400006)  # beq v0, zero skips field publication on failure.
        self.assertEqual(a.RESERVE_START+4*4+4+(words[4] & 65535)*4, a.RESERVE_END)
        self.assertEqual(words[5:9], (0x3C048014, 0x24842410, 0x24050001, 0x27A60024))
        self.assertEqual(words[9:], (a.jump(a.t.SETTER, link=True), 0x24070008))
        self.assertEqual(0x24+8, 0x2C)
        data, _ = a.preceding(self.native, 'reserve'); spec = a.ACTORS['reserve']
        self.assertEqual(data[a.RESERVE_START-spec.ram:a.RESERVE_START-spec.ram+4], bytes(4))

    def test_independent_mips_assembly(self):
        with tempfile.TemporaryDirectory(prefix='af-actor-names-') as directory:
            common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/events:/source:ro', '-v', f'{directory}:/out', '-w', '/out', '--entrypoint']
            def run(tool, *args):
                subprocess.run(common+[f'/n64_toolchain/bin/mips64-elf-{tool}', IMAGE, *args], check=True, timeout=60)
            run('as', '-EB', '-mabi=32', '-march=vr4300', '-o', 'names.o', '/source/display_names.s')
            run('ld', '-EB', '-T', '/source/display_names.ld', '-o', 'names.elf', 'names.o')
            expected = {'call': struct.pack('>I', a.jump(a.IMPORTS['af_get_display_name'], link=True)),
                        'length': struct.pack('>I', 0x24070008), 'reserve_name': a.reserve_body()}
            for name, data in expected.items():
                run('objcopy', '-O', 'binary', '-j', '.text.'+name, 'names.elf', name+'.bin')
                self.assertEqual((Path(directory)/(name+'.bin')).read_bytes(), data)

    def test_only_approved_actor_changes_survive_relocation(self):
        replacements = dict(self.original)
        evidence = a.install(self.native, replacements, self.additions, self.module)
        self.assertEqual(evidence['extra_allocation_bytes'], 0)
        self.assertFalse(evidence['saved_layout_changes'])
        for name, spec in a.ACTORS.items():
            before, reloc = a.preceding(self.native, name)
            for base in (0x801A0010, 0x802F8010):
                expected = bytearray(relocate_verified_data(spec, before, reloc, base))
                for address, body in a.patches(name).items():
                    at = address-spec.ram
                    expected[at:at+len(body)] = body
                self.assertEqual(relocate_verified_data(spec, replacements[spec.vrom], reloc, base), expected)
        self.assertEqual(replacements[CODE_VROM], self.original[CODE_VROM])

    def test_failed_guard_does_not_publish_partial_actors(self):
        cases = [(a.ACTORS[name].vrom, 0) for name in a.ACTORS]
        cases += [(CODE_VROM, 0x8009D1F0-CODE_RAM), (a.MODULE_VROM, 60), (a.NAMES_VROM, 33)]
        for vrom, at in cases:
            replacements, additions = dict(self.original), dict(self.additions)
            target = additions if vrom in additions else replacements
            data = bytearray(target.get(vrom, self.files[vrom].extract(self.prior)))
            data[at] ^= 1; target[vrom] = bytes(data)
            before = dict(replacements), dict(additions)
            with self.assertRaises(ValueError): a.install(self.native, replacements, additions, self.module)
            self.assertEqual((replacements, additions), before)

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete actor-name build required')
    def test_complete_cartridge_and_layered_extension_verification(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text()); files = by_vrom(built)
        a.verify_installation(built, self.native, report)
        a.t.verify_installation(built, self.native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        self.assertEqual(set(files), set(self.files))
        replacements = dict(self.original); a.install(self.native, replacements, self.additions, self.module)
        for vrom, file in files.items():
            old = self.files[vrom]
            self.assertEqual((file.index, file.vstart, file.vend), (old.index, old.vstart, old.vend))
            if vrom != 0x19D40:
                self.assertEqual(file.extract(built), replacements.get(vrom, old.extract(self.prior)), f'{vrom:08X}')
        tables = [bytearray(f[0x19D40].extract(rom)) for f, rom in ((files, built), (self.files, self.prior))]
        for file in files.values():
            at = DMA_START-0x19D40+file.index*16+8
            for table in tables: table[at:at+8] = bytes(8)
        self.assertEqual(*tables)
        for key in ('translation_edits', 'runtime_module', 'text_extension', 'display_names',
                    'catchphrases', 'extended_items', 'extended_font', 'npc_mail_loader', 'noticeboard'):
            self.assertEqual(report[key], self.report[key], key)
        with self.assertRaises(ValueError):
            a.t.verify_installation(built, self.native, {**report, 'actor_display_names': {}})

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete actor-name build required')
    def test_combined_accounting_verifies_actors_without_duplicate_source_weight(self):
        from translation_progress import measure, pending_name_consumers
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), report)
        summary = ledger.summary()
        self.assertEqual(summary['total_source_characters'], 751307)
        from item_name_readers import resource_only_weight
        self.assertEqual(summary['replaced_source_characters'], 720661+35+resource_only_weight(ledger))
        self.assertGreater(summary['pending_application_records'], 0)
        self.assertNotIn('Shared choices', str(pending_name_consumers(report)))
        self.assertIn('identity-based', pending_name_consumers(report)['display_names'])


if __name__ == '__main__': unittest.main()
