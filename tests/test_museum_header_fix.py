"""Current museum-header cartridge, bounded readers, and source credit."""
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import by_vrom, sha256, apply_ups
import letter_names as names
from npc_mail_show import relocate_verified_data
from catalogue_names import Image
from runtime_layout import MODULE_VROM, MODULE_RAM
import v2_museum_header_fix as fix

OUT = ROOT/'build/v2-museum-header-12-final'


@unittest.skipUnless((OUT/'build.json').is_file(), 'Current museum header build required')
class MuseumHeaderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = (ROOT/'build/v2-keyboard-fit-11/Animal Forest English V2.z64').read_bytes()
        cls.rom = (OUT/'Animal Forest English V2.z64').read_bytes()
        cls.report = json.loads((OUT/'build.json').read_text())
        cls.old, cls.new = by_vrom(cls.base), by_vrom(cls.rom)

    def test_complete_patch_retention_and_no_delivery_changes(self):
        self.assertEqual(sha256(self.base), fix.BASE_SHA)
        self.assertEqual(sha256(self.rom), self.report['output_sha256'])
        native = (ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(native, (OUT/'Animal Forest English V2.ups').read_bytes()), self.rom)
        changed = {int(v, 16) for v in self.report['changed_resources']}
        self.assertEqual(changed, {names.NEW_VROM, names.NEW_RELOC, names.OWNER, MODULE_VROM})
        self.assertEqual(set(self.old), set(self.new))
        for v, entry in self.old.items():
            self.assertEqual(entry.index, self.new[v].index)
            if v not in changed | {0x19D40}:
                self.assertEqual(entry.extract(self.base), self.new[v].extract(self.rom), hex(v))
        self.assertFalse(self.report['save_format_changed'])
        self.assertFalse(self.report['delivery_code_changed'])

    def test_fixed_resident_addresses_and_descriptor_bounds(self):
        old, new = (f[MODULE_VROM].extract(r) for f, r in ((self.old, self.base), (self.new, self.rom)))
        at = fix.NAME_ENTRY-MODULE_RAM
        gate = (OUT/'reader/gate.bin').read_bytes()
        self.assertEqual(fix.patch_module(old, gate), new)
        self.assertEqual(old[:0x90], new[:0x90])
        self.assertEqual(old[0x100:at], new[0x100:at])
        self.assertEqual(old[at+8:], new[at+8:])
        self.assertEqual(struct.unpack_from('>2I', new, at), (fix.jump(fix.GATE), 0))
        for module, adapter in ((bytes([old[0]^1])+old[1:], gate), (old, gate[:80]), (old, gate+bytes(128))):
            with self.assertRaises(ValueError): fix.patch_module(module, adapter)

    def test_board_preserves_defaults_cursor_and_relocates_new_entry(self):
        old, data, rel = (self.old[names.NEW_VROM].extract(self.base), self.new[names.NEW_VROM].extract(self.rom),
                          self.new[names.NEW_RELOC].extract(self.rom))
        at = names.HEADER-names.RAM
        self.assertEqual(old[:at], data[:at])
        self.assertEqual(old[at+4:], data[at+4:len(old)])
        self.assertLessEqual(self.report['board_growth_bytes'], 2560)
        self.assertEqual(self.report['additional_pool_bytes'], 0)
        owner_before, owner_after = (f[names.OWNER].extract(r) for f, r in ((self.old,self.base),(self.new,self.rom)))
        self.assertEqual(owner_before[:names.OWNER_AT], owner_after[:names.OWNER_AT])
        self.assertEqual(owner_before[names.OWNER_AT+16:], owner_after[names.OWNER_AT+16:])
        self.assertEqual(struct.unpack_from('>4I', owner_after, names.OWNER_AT),
            (names.NEW_VROM, names.NEW_VROM+len(data), names.RAM, names.RAM+len(data)))
        for base in (0x80200010, 0x80378010):
            moved = relocate_verified_data(Image(names.RAM, len(data), struct.unpack_from('>5I', rel)), data, rel, base)
            self.assertEqual(struct.unpack_from('>I', moved, at)[0], fix.jump(base+self.report['board']['symbols']['af_letter_header']))
        for path, checksum in self.report['sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()), checksum, path)

    def test_museum_wording_has_one_official_source_record(self):
        from text_provenance import validate
        catalogue = json.loads((ROOT/'translations/provenance.json').read_text())
        validate(catalogue)
        entry = next(row for row in catalogue['entries'] if row['id'] == 'ui/mail/museum-name')['locales']['en']
        self.assertEqual(entry['credit'], 'official')
        self.assertEqual(entry['source']['data_offset'], '0000CD80')
        self.assertEqual(entry['encoded_sha256'], sha256(b'Museum'))
        donor = (ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        self.assertEqual(donor[fix.DATA_BASE+0xCD80:fix.DATA_BASE+0xCD88], b'Museum  ')


if __name__ == '__main__': unittest.main()
