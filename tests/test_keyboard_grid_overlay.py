"""Compiled grid ownership, relocation, and complete preceding-resource retention."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups,sha256,CODE_VROM,CODE_RAM
import keyboard_grid_overlay as grid
import apology_overlay as previous
import hboard_overlay as editor
from build_keyboard_grid import build as compile_grid


@unittest.skipUnless((ROOT/'build/keyboard-grid-01/build.json').is_file(),'Local compiled keyboard grid required')
class KeyboardGridOverlayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/collection-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.prior=json.loads((ROOT/'build/collection-artwork-01/build.json').read_text())
        cls.directory=ROOT/'build/keyboard-grid-overlay'
        cls.data=(cls.directory/'overlay.bin').read_bytes()
        cls.reloc=(cls.directory/'relocation.bin').read_bytes()
        cls.profile=json.loads((cls.directory/'overlay.json').read_text())
        cls.built=(ROOT/'build/keyboard-grid-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/keyboard-grid-01/build.json').read_text())

    def test_independent_compilation_and_relocations_retain_complete_editor(self):
        with tempfile.TemporaryDirectory(prefix='af-grid-recompile-') as directory:
            profile=compile_grid(self.native,ROOT/'build/apology-input-overlay',Path(directory))
            self.assertEqual(profile,self.profile)
            self.assertEqual((Path(directory)/'overlay.bin').read_bytes(),self.data)
            self.assertEqual((Path(directory)/'relocation.bin').read_bytes(),self.reloc)
        grid.validate(self.native,self.data,self.reloc,self.profile)
        prefix,reloc=grid.preceding(self.data,self.reloc)
        self.assertEqual(sha256(prefix),previous.APPROVED['overlay_sha256'])
        self.assertEqual(sha256(reloc),previous.APPROVED['relocation_sha256'])
        for data,rel in ((self.data[:-1],self.reloc),(self.data,self.reloc[:-1])):
            with self.assertRaises(ValueError):grid.validate(self.native,data,rel)
        profile=copy.deepcopy(self.profile);profile['sources']['overlays/keyboard_grid/core.c']='0'*64
        with self.assertRaises(ValueError):grid.validate(self.native,self.data,self.reloc,profile)

    def test_complete_cartridge_patch_owner_and_allocations(self):
        built,ups,report=grid.build(self.native,self.base,self.prior,self.directory)
        self.assertEqual(built,self.built);self.assertEqual(report,self.report)
        self.assertEqual(apply_ups(self.native,ups),built)
        info=grid.verify_owned_parts(built,self.native,report['keyboard_grid'],report['apology_input'])
        self.assertEqual(info['pool_word'],0x25CE2220)
        self.assertEqual(info['allocation'],{'editor_growth':5504,'extra_pool_bytes':5632,
            'combined_growth_used':17856,'combined_pool_bytes':253056,'conservative_required':252736})
        old,new=by_vrom(self.base),by_vrom(built)
        changed={editor.NEW_VROM,editor.NEW_RELOCATION,editor.OWNER,CODE_VROM,0x19D40}
        self.assertEqual(set(old),set(new));self.assertEqual(len(built),len(self.base))
        for address in old:
            self.assertEqual(old[address].index,new[address].index)
            if address not in changed:self.assertEqual(old[address].extract(self.base),new[address].extract(built))
        old_code=bytearray(old[CODE_VROM].extract(self.base));new_code=new[CODE_VROM].extract(built)
        struct.pack_into('>I',old_code,0x800C4B10-CODE_RAM,grid.POOL_WORD)
        self.assertEqual(bytes(old_code),new_code)
        old_owner=bytearray(old[editor.OWNER].extract(self.base));old_owner[0x2B50:0x2B70]=grid.metadata()
        self.assertEqual(bytes(old_owner),new[editor.OWNER].extract(built))
        with self.assertRaises(ValueError):grid.build(self.native,self.base[:-1],self.prior,self.directory)

    def test_shared_apology_letter_inventory_verifiers_accept_only_installed_grid(self):
        previous.verify_installation(self.built,self.native,self.report)
        from notice_overlay import verify_installation as verify_notice
        verify_notice(self.built,self.native,self.report['runtime_module'],self.report['noticeboard'])
        self.assertEqual(editor.verify_shared_parts(self.built,self.native)['owner_bytes'],grid.metadata())
        report=copy.deepcopy(self.report['apology_input']);report['allocation']['editor_growth']+=1
        with self.assertRaises(ValueError):previous.verify_owned_parts(self.built,self.native,report)
        report=copy.deepcopy(self.report['keyboard_grid']);report['allocation']['extra_pool_bytes']-=64
        with self.assertRaises(ValueError):grid.verify_owned_parts(self.built,self.native,report)


if __name__=='__main__':unittest.main()
