"""Native cursor ABI, preserved live layout, and complete corrected cartridge."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from keyboard_grid_cursor import build,GRID,RELOC
from keyboard_grid_overlay import validate,verify_owned_parts,APPROVED,CURSOR_APPROVED,RAM
from keyboard_grid_labels import install,CURSOR_CORRECTED_SHA,compiled_form
from hboard_overlay import EDITOR


@unittest.skipUnless((ROOT/'build/keyboard-grid-cursor-01/build.json').is_file(),'Local cursor candidate required')
class KeyboardGridCursorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/redd-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.previous=json.loads((ROOT/'build/redd-artwork-01/build.json').read_text())
        cls.image=(ROOT/'build/keyboard-grid-cursor-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/keyboard-grid-cursor-01/build.json').read_text())
        cls.directory=ROOT/'build/keyboard-grid-cursor-aligned'

    def test_numeric_cursor_commands_bind_to_the_original_game_not_our_enum(self):
        # Original command selector: actual controller masks, returned commands.
        native=by_vrom(self.native)[EDITOR].extract(self.native)
        for address,word in ((0x8088547C,0x11200003),(0x80885480,0x306A0004),
            (0x80885488,0x24020002),(0x80885490,0x306B0008),(0x80885498,0x24020004),
            (0x808854A0,0x306C0001),(0x808854A8,0x24020003),(0x808854B8,0x24020001)):
            self.assertEqual(struct.unpack_from('>I',native,address-RAM)[0],word)
        old=(ROOT/'build/keyboard-grid-overlay/overlay.bin').read_bytes()
        current=(self.directory/'overlay.bin').read_bytes()
        self.assertEqual(old[:0x5A80],current[:0x5A80])
        self.assertEqual(old[0x5FD8:],current[0x5FD8:])
        for key in ('bytes','code_end','bss_start','symbols'):
            self.assertEqual(APPROVED[key],CURSOR_APPROVED[key])
        self.assertEqual(sha256(install(current)),CURSOR_CORRECTED_SHA)
        self.assertEqual(compiled_form(install(current)),current)

    def test_complete_resource_retention_current_ownership_and_patch_recovery(self):
        image,patch,report=build(self.native,self.base,self.previous,self.directory)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,patch),image)
        before,after=by_vrom(self.base),by_vrom(image)
        for vrom,entry in before.items():
            self.assertEqual(after[vrom].index,entry.index)
            self.assertEqual(after[vrom].size,entry.size)
            if vrom not in (GRID,RELOC,0x19D40):
                self.assertEqual(after[vrom].extract(image),entry.extract(self.base),f'{vrom:08X}')
        verify_owned_parts(image,self.native,report['keyboard_grid'],report['apology_input'])
        from apology_overlay import verify_installation
        verify_installation(image,self.native,report)
        from notice_overlay import verify_installation as verify_notice
        verify_notice(image,self.native,report['runtime_module'],report['noticeboard'])

    def test_profiles_do_not_accept_mixed_relocations_or_unreviewed_code(self):
        data=(self.directory/'overlay.bin').read_bytes()
        reloc=(self.directory/'relocation.bin').read_bytes()
        report=json.loads((self.directory/'overlay.json').read_text())
        validate(self.native,data,reloc,report)
        wrong=copy.deepcopy(report);wrong['version']=1
        with self.assertRaises(ValueError):validate(self.native,data,reloc,wrong)
        wrong=copy.deepcopy(report);wrong['sources']['overlays/keyboard_grid/core.h']='0'*64
        with self.assertRaises(ValueError):validate(self.native,data,reloc,wrong)
        old_rel=(ROOT/'build/keyboard-grid-overlay/relocation.bin').read_bytes()
        with self.assertRaises(ValueError):validate(self.native,data,old_rel)
        bad=bytearray(data);bad[0x5C40]^=1
        with self.assertRaises(ValueError):validate(self.native,bytes(bad),reloc)


if __name__=='__main__':unittest.main()
