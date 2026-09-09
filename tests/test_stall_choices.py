"""Complete stall labels, bounded four-row stack storage, and cartridge ownership."""
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
from aflib import CODE_RAM, CODE_VROM, DMA_START, by_vrom, sha256, apply_ups
from check_keyboard_assembly import IMAGE
from english_runtime import QUEST_VROM, PLAYER_SELECT_VROM
from extended_items import VROM as ITEMS_VROM
from npc_mail_show import relocate_verified_data
from runtime_module import MODULE_VROM
import stall_choices as s

ROM = ROOT/'local/rom/Doubutsu no Mori (Japan).z64'
PRIOR = ROOT/'build/event-item-names-pilot'
BUILD = ROOT/'build/stall-choices-pilot'


@unittest.skipUnless(ROM.is_file() and (PRIOR/'build.json').is_file(), 'Native ROM and complete event build required')
class StallChoiceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native = ROM.read_bytes()
        cls.prior = (PRIOR/'animal-forest-halfwidth.z64').read_bytes()
        cls.report = json.loads((PRIOR/'build.json').read_text())
        cls.files = by_vrom(cls.prior)
        cls.original = {v: cls.files[v].extract(cls.prior) for v in (CODE_VROM, QUEST_VROM, PLAYER_SELECT_VROM)}
        cls.additions = {v: cls.files[v].extract(cls.prior) for v in (MODULE_VROM, ITEMS_VROM)}
        cls.module = cls.report['runtime_module']

    def test_stack_rows_pointers_and_setter_lengths_change_together(self):
        old, _ = s.source(self.native)
        data, _, changes = s.patch_actor(self.native)
        word = lambda address: struct.unpack_from('>I', data, address-s.SPEC.ram)[0]
        self.assertEqual(word(0x80A72DB8), 0x27BDFF40)  # sp -= 192
        self.assertEqual(word(0x80A72FA0), 0x27BD00C0)  # sp += 192
        self.assertEqual(word(0x80A72E00), 0xAFA200B8)  # choice pointer at array end
        self.assertEqual(word(0x80A72F54), 0x8FA400B8)
        self.assertEqual(word(0x80A72DFC), 0x27B50078)  # array starts in place
        self.assertEqual(word(0x80A72E08), 0x24050040)  # clear all 64 bytes
        for address in (0x80A72E4C, 0x80A72EA0, 0x80A72F3C, 0x80A72F40, 0x80A72F44, 0x80A72F5C):
            self.assertEqual(word(address) & 65535, 16)
        # Four disjoint full rows, unchanged pointer array/saved registers, and
        # a moved live pointer strictly above all possible name/cancel writes.
        spans = [(0x78+i*16, 0x78+(i+1)*16) for i in range(4)]
        self.assertEqual(spans[-1][1], 0xB8)
        self.assertLessEqual(0x68+4*4, spans[0][0])
        self.assertLessEqual(0xB8+4, 192)
        self.assertEqual(data[0x80A72DBC-s.SPEC.ram:0x80A72DEC-s.SPEC.ram],
                         old[0x80A72DBC-s.SPEC.ram:0x80A72DEC-s.SPEC.ram])
        expected = bytearray(old)
        for change in changes:
            at = int(change['ram'], 16)-s.SPEC.ram
            expected[at:at+change['bytes']] = data[at:at+change['bytes']]
        self.assertEqual(data[:len(old)], expected)
        self.assertEqual(data[len(old):], s.references())
        # The only two original call sites still request three and four rows.
        for at, value in ((0x80A7327C, 0x24050003), (0x80A73734, 0x24050004)):
            self.assertEqual(word(at), value)

    def test_full_labels_original_branches_and_relocated_addresses(self):
        old, original_reloc = s.source(self.native)
        data, reloc, _ = s.patch_actor(self.native)
        self.assertEqual(data[-32:], b"I'm not buying! I don't want it!")
        self.assertEqual(reloc[:4]+reloc[8:], original_reloc[:4]+original_reloc[8:])
        self.assertEqual(struct.unpack_from('>5I', reloc), (4528, 192, 0, 0, 77))
        for offset in range(s.SPEC.entry-s.SPEC.ram, s.FUNCTION_END-s.SPEC.ram, 4):
            w = struct.unpack_from('>I', old, offset)[0]
            if w >> 26 in (1, 4, 5, 6, 7, 20, 21, 22, 23):
                self.assertEqual(data[offset:offset+4], old[offset:offset+4])
        for base in (0x801A0010, 0x802F8010):
            moved = relocate_verified_data(s.relocated_spec(), data, reloc, base)
            for high_at, low_at, target in ((0x80A72EAC, 0x80A72EB0, base+4688),
                                             (0x80A72F00, 0x80A72F04, base+4704)):
                high, low = [struct.unpack_from('>I', moved, a-s.SPEC.ram)[0] & 65535 for a in (high_at, low_at)]
                self.assertEqual((high << 16)+low-(65536 if low & 32768 else 0), target)
            self.assertEqual(moved[s.LOAD_START-s.SPEC.ram:s.LOAD_END-s.SPEC.ram], s.loader_body())
            self.assertEqual(moved[-32:], s.references())
        evidence = s.audit_references(self.native)
        self.assertEqual(evidence['external_interior_references'], [])

    def test_independent_mips_loader_assembly(self):
        with tempfile.TemporaryDirectory(prefix='af-stall-asm-') as directory:
            common = ['docker', 'run', '--rm', '--network', 'none', '--user', f'{os.getuid()}:{os.getgid()}',
                      '-v', f'{ROOT}/overlays/events:/source:ro', '-v', f'{directory}:/out', '-w', '/out', '--entrypoint']
            commands = [
                ['/n64_toolchain/bin/mips64-elf-as', IMAGE, '-EB', '-mabi=32', '-march=vr4300',
                 '-o', 'stall.o', '/source/stall_name.s'],
                ['/n64_toolchain/bin/mips64-elf-ld', IMAGE, '-EB', '-Ttext=0x80A72E5C', '-e', 'af_stall_full_name',
                 f'--defsym=af_load_item_name={s.IMPORTS["af_load_item_name"]:#x}', '-o', 'stall.elf', 'stall.o'],
                ['/n64_toolchain/bin/mips64-elf-objcopy', IMAGE, '-O', 'binary', '-j', '.text', 'stall.elf', 'stall.bin'],
            ]
            for command in commands: subprocess.run(common+command, check=True, timeout=60)
            output = (Path(directory)/'stall.bin').read_bytes()
            self.assertEqual(output[:32], s.loader_body())
            self.assertFalse(any(output[32:]))

    def test_installation_guards_are_atomic(self):
        replacements = dict(self.original); moves = {}
        evidence = s.install(self.native, replacements, self.additions, moves, self.module)
        self.assertEqual(evidence['additional_actor_bytes'], 32)
        self.assertEqual(evidence['additional_stack_bytes'], 24)
        self.assertFalse(evidence['saved_layout_changes'])
        self.assertEqual(moves, {s.SPEC.vrom: s.NEW_VROM, s.SPEC.relocation: s.NEW_RELOC})
        for at in (s.METADATA, 0x800A1820, 0x800651C0):
            bad = bytearray(self.original[CODE_VROM]); bad[at-CODE_RAM] ^= 1
            values = {**self.original, CODE_VROM: bytes(bad)}; before = dict(values); moves = {}
            with self.assertRaises(ValueError): s.install(self.native, values, self.additions, moves, self.module)
            self.assertEqual(values, before); self.assertEqual(moves, {})
        old, reloc = s.source(self.native)
        for vrom, value in ((s.SPEC.vrom, old+b'x'), (s.SPEC.relocation, reloc+b'x'), (s.NEW_VROM, b'x')):
            values = {**self.original, vrom: value}; before = dict(values); moves = {}
            with self.assertRaises(ValueError): s.install(self.native, values, self.additions, moves, self.module)
            self.assertEqual(values, before); self.assertEqual(moves, {})

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete stall build required')
    def test_complete_rom_patch_and_retained_payloads(self):
        built = (BUILD/'animal-forest-halfwidth.z64').read_bytes()
        report = json.loads((BUILD/'build.json').read_text())
        files = by_vrom(built)
        s.verify_installation(built, self.native, report)
        self.assertEqual(sha256(built), report['output_sha256'])
        self.assertEqual(apply_ups(self.native, (BUILD/'animal-forest-halfwidth.ups').read_bytes()), built)
        mapping = {s.SPEC.vrom: s.NEW_VROM, s.SPEC.relocation: s.NEW_RELOC}
        self.assertEqual(set(files), {mapping.get(v, v) for v in self.files})
        tables = [bytearray(f[0x19D40].extract(rom)) for f, rom in ((files, built), (self.files, self.prior))]
        for v, old in self.files.items():
            new = files[mapping.get(v, v)]
            self.assertEqual(new.index, old.index)
            a, b = new.extract(built), old.extract(self.prior)
            if v not in (s.SPEC.vrom, s.SPEC.relocation, CODE_VROM, 0x19D40):
                self.assertEqual((new.vstart, new.vend, a), (old.vstart, old.vend, b))
            if v == CODE_VROM:
                offset = s.METADATA-CODE_RAM
                self.assertEqual(a[:offset]+a[offset+32:], b[:offset]+b[offset+32:])
            # Two intentional virtual moves, all other changes only physical addresses.
            at = DMA_START-0x19D40+old.index*16
            for table in tables:
                table[at+8:at+16] = bytes(8)
                if v in mapping: table[at:at+8] = bytes(8)
        self.assertEqual(*tables)
        self.assertEqual(report['translation_edits'], self.report['translation_edits'])
        for key in ('runtime_module', 'extended_font', 'extended_items', 'display_names', 'catchphrases',
                    'npc_mail_loader', 'noticeboard', 'inventory_english', 'catalogue_names',
                    'town_suffix', 'shop_item_names', 'player_item_names', 'event_item_names'):
            self.assertEqual(report[key], self.report[key], key)
        with self.assertRaisesRegex(ValueError, 'application evidence'):
            s.verify_installation(built, self.native, {**report, 'stall_choices': {}})

    @unittest.skipUnless((BUILD/'build.json').is_file(), 'Complete stall build required')
    def test_counter_inventories_both_labels_once_and_requires_application(self):
        from translation_progress import measure
        report = json.loads((BUILD/'build.json').read_text())
        ledger = measure(self.native, (BUILD/'animal-forest-halfwidth.z64').read_bytes(), report)
        for name, _, raw, _, english in s.LABELS:
            row = ledger.rows['ui_stall_choice:'+name]
            self.assertEqual(row['source_characters'], len(raw))
            self.assertEqual(row['replacements'], [{'route': 'stall_choices', 'sha256': sha256(english)}])
        # The prior build has the same two original records, without credit.
        from translation_progress import CounterLedger
        unapplied = CounterLedger(ledger.info)
        s.measure_labels(unapplied, self.native, self.prior, self.report)
        self.assertEqual(unapplied.summary()['total_source_characters'], 12)
        self.assertEqual(unapplied.summary()['replaced_source_characters'], 0)
        self.assertEqual(sum(ledger.rows['ui_stall_choice:'+r[0]]['source_characters'] for r in s.LABELS), 12)
        self.assertTrue(any(row['pending_replacements'] for row in ledger.rows.values()))


if __name__ == '__main__': unittest.main()
