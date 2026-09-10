"""Persistent upper-RAM font and retained RC3 resources."""
import struct
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import apply_ups, by_vrom, sha256
from font_expansion_memory import MODULE, FONT, MODULE_RAM, START, END, BASE, build, expected_font
from name_space_markers import VROM as NAME, BRANCH, RAM as NAME_RAM, NEW


class LoaderHostTests(unittest.TestCase):
    def test_sanitized_ownership_configuration_failure_and_absent_memory_paths(self):
        with tempfile.TemporaryDirectory(prefix='af-font-memory-host-') as temp:
            binary=Path(temp)/'loader-test'
            subprocess.run(['gcc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'overlays/font_memory/loader.c'),str(ROOT/'tests/font_expansion_loader_test.c'),
                str(ROOT/'runtime/crc32.c'),'-o',str(binary)],check=True,capture_output=True)
            result=subprocess.run([str(binary)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('absent RAM, bounds, failures, and re-entry passed',result.stdout)


@unittest.skipUnless((ROOT/'build/v1rc3/Animal Forest English V1RC3.z64').is_file(),'Local RC3 required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/v1rc3/Animal Forest English V1RC3.z64').read_bytes()
        with tempfile.TemporaryDirectory(prefix='af-font-memory-test-') as temp:
            cls.image,cls.patch,cls.report=build(cls.native,cls.base,Path(temp))
        cls.old,cls.new=by_vrom(cls.base),by_vrom(cls.image)

    def test_only_font_loader_function_and_name_space_branch_change(self):
        self.assertEqual(set(self.old),set(self.new))
        for v,entry in self.old.items():
            before,after=entry.extract(self.base),self.new[v].extract(self.image)
            self.assertEqual(entry.index,self.new[v].index)
            if v==MODULE:
                allowed=set(range(START-MODULE_RAM,END-MODULE_RAM))
            elif v==NAME:
                allowed=set(range(BRANCH-NAME_RAM,BRANCH-NAME_RAM+4))
                self.assertEqual(struct.unpack_from('>I',after,BRANCH-NAME_RAM)[0],NEW)
            else:
                allowed=set()
            self.assertEqual(len(before),len(after))
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(before,after))),hex(v))
        self.assertFalse(self.report['save_format_changed'])

    def test_complete_font_relocation_in_the_owned_expansion_region(self):
        blob=self.new[FONT].extract(self.image)
        module=self.new[MODULE].extract(self.image)
        relocated=expected_font(blob,module)
        self.assertEqual(sha256(relocated),self.report['relocated_font_sha256'])
        target=0x80000000|((struct.unpack_from('>I',relocated)[0]&0x3FFFFFF)<<2)
        self.assertTrue(BASE<=target<BASE+len(relocated))
        self.assertLessEqual(BASE+len(blob),0x80457FF0)
        for offset in (0,12000,len(blob)-1):
            bad=bytearray(blob);bad[offset]^=1
            with self.assertRaises(ValueError): expected_font(bad,module)

    def test_full_patch_reconstruction_and_source_rejection(self):
        self.assertEqual(apply_ups(self.native,self.patch),self.image)
        self.assertEqual(sha256(self.image),self.report['output_sha256'])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError): build(self.native,self.native,Path(temp))


if __name__=='__main__': unittest.main()
