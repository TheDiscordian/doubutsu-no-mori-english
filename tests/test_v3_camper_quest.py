"""Complete current-owner preservation and donor-backed summer camper routes."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import DMA_START,by_vrom,sha256,n64_checksum
from gc_names import symbol_data
from v3_asset_loader import BLOB,MODULE,CONFIG
from v3_furniture_art import verify_sources
import v3_camper_quest as runtime
OUTPUT=ROOT/'build/v3-camper-quest-runtime-02'


class CamperQuestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=(runtime.BASE/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.files,cls.old=by_vrom(cls.rom),by_vrom(cls.base)
        cls.quest=cls.report['camper_quest']

    def test_donor_reuses_actual_winter_npc_profile_in_both_controllers(self):
        rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        verify_sources(rel,symbols)
        for name in ('event_npc_profile_table$4912','event_npc_profile_table$3781'):
            table=symbol_data(rel,symbols.decode(),name)
            self.assertEqual(len(table),144*2)
            self.assertEqual(struct.unpack_from('>H',table,0x5E*2),(0x23,))
            self.assertEqual(struct.unpack_from('>H',table,0x8F*2),(0x23,))

    def test_complete_english_owners_rebuild_and_relocate_without_other_changes(self):
        helper=(OUTPUT/'camper_quest/code.bin').read_bytes()
        changes,rebuilt=runtime.install(self.base,helper,self.quest['code'])
        self.assertEqual(json.loads(json.dumps(rebuilt['owners'])),self.quest['owners'])
        self.assertEqual(len(helper),112)
        for row in self.quest['owners']:
            vrom=int(row['vrom'],16);actual=self.files[vrom].extract(self.rom)
            self.assertEqual(actual,changes[vrom]);restored=bytearray(actual)
            at=row['hook']-row['ram'];before=bytes.fromhex(row['before'])
            restored[at:at+len(before)]=before
            self.assertEqual(restored,self.old[vrom].extract(self.base))
            self.assertEqual(sha256(actual),row['patched_sha256'])
        for vrom in (0x878550,0x886FA0):
            self.assertEqual(self.files[vrom].extract(self.rom),self.old[vrom].extract(self.base))
        reloc=self.files[0x84C8A0].extract(self.rom)
        self.assertEqual(reloc,changes[0x84C8A0]);self.assertEqual(len(reloc),800)
        self.assertEqual(struct.unpack_from('>5I',reloc),(9248,2352,0,0,187))
        self.assertEqual(struct.unpack_from('>I',reloc,796),(800,))

    def test_only_declared_files_and_checked_rom_alias_change(self):
        self.assertEqual(set(self.files),set(self.old))
        changed={v for v in self.files if self.files[v].extract(self.rom)!=self.old[v].extract(self.base)}
        self.assertEqual(changed,{BLOB,MODULE,0x19D40,0x8681F0,0x8798C0,0x849B50,0x84C8A0})
        for v in self.files:
            if v not in (BLOB,0x84C8A0): self.assertEqual(self.files[v],self.old[v])
        old=self.old[0x84C8A0]
        self.assertEqual(self.rom[old.pstart:old.pend],self.base[old.pstart:old.pend])
        move=self.quest['resource_moves'][0]
        self.assertEqual(self.files[0x84C8A0].pstart,move['physical'])
        self.assertEqual(self.files[0x84C8A0].pend,0)
        self.assertEqual(self.files[BLOB].size-self.old[BLOB].size,800)
        self.assertEqual(self.quest['additional_resident_bytes'],0)
        self.assertFalse(self.quest['saved_format_changed'])
        self.assertFalse(self.quest['summer_english_message_selection'])

    def test_package_crc_guards_saved_profile_and_complete_previous_blob(self):
        blob=self.files[BLOB].extract(self.rom);old=self.old[BLOB].extract(self.base)
        restored=bytearray(blob[:len(old)]);at=runtime.PACKAGE+runtime.RAM-runtime.PACKAGE_RAM
        self.assertEqual(old[at:at+112],bytes(112));restored[at:at+112]=bytes(112)
        restored[4:8]=old[4:8];restored[0xF8:0xFC]=old[0xF8:0xFC]
        self.assertEqual(restored,old)
        self.assertEqual(struct.unpack_from('>4I',blob,0xF0),
            (BLOB+runtime.PACKAGE,runtime.PACKAGE_SIZE,
             zlib.crc32(blob[runtime.PACKAGE:runtime.PACKAGE+runtime.PACKAGE_SIZE]),runtime.PACKAGE_RAM))
        self.assertEqual(struct.unpack_from('>4I',self.files[MODULE].extract(self.rom),CONFIG),
                         (BLOB,0xC000,zlib.crc32(blob[:0xC000]),78))
        self.assertEqual(struct.unpack_from('>2I',self.rom,0x10),n64_checksum(self.rom))
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])

    def test_changed_helper_binding_or_native_owner_is_rejected(self):
        helper=(OUTPUT/'camper_quest/code.bin').read_bytes();compiled=self.quest['code']
        with self.assertRaises(ValueError): runtime.install(self.base,helper[:-4],compiled)
        bad=copy.deepcopy(compiled);bad['symbols']['camper_greeted']+=4
        with self.assertRaises(ValueError): runtime.install(self.base,helper,bad)
        bad=bytearray(self.base);bad[self.old[0x849B50].pstart+0x358]^=1
        with self.assertRaises(ValueError): runtime.patch_owners(bad,compiled)


if __name__=='__main__': unittest.main()
