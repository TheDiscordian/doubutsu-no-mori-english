"""Reference-key mapping and memory-safe shared grid input before native installation."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from check_keyboard_assembly import IMAGE
from gc_text import decoder_tables
from keyboard_grid import extract, keycap, DISABLED
from textcodec import ENCODE


@unittest.skipUnless((ROOT/'build/keyboard-grid-layout/keys.bin').is_file(),'Local supplied keyboard layout required')
class KeyboardGridTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.glyphs=decoder_tables(ROOT/'local/ac-decomp/tools/msg_tool.py')['CHAR_MAP']

    def test_source_bound_key_layouts_and_no_unmapped_raw_gc_codes(self):
        data,report=extract(self.rel,self.symbols,self.glyphs)
        self.assertEqual(sha256(data),'de0934289f9ee4f86cdadd87df63fe2eba0ab0b7d5cdb76949bd98ab7c54c0a7')
        self.assertEqual(data,(ROOT/'build/keyboard-grid-layout/keys.bin').read_bytes())
        words=struct.unpack('>240H',data)
        for table,text in ((2,'1234567890QWERTYUIOPASDFGHJKL\nZXCVBNM,. '),
                           (3,'1234567890ABCDEFGHIJKLMNOPQRS\nTUVWXYZ,. ')):
            self.assertEqual(words[table*40:(table+1)*40],tuple(ENCODE[c] for c in text))
        self.assertEqual(words[9],DISABLED)
        self.assertEqual(words[7],DISABLED)  # Semicolon lacks general saved-input support.
        self.assertEqual(words[160+28],ENCODE['+'])
        self.assertEqual(words[200+14],0x80BA)
        self.assertEqual(words[200+20],0x80A7)
        self.assertFalse(set(words)&{0x7F,0x80})
        self.assertTrue(all(v<=255 or v in (DISABLED,0x80A7,0x80BA) for v in words))
        for rel,symbols in ((self.rel[:-1],self.symbols),(self.rel,self.symbols+b'\n')):
            with self.assertRaises(ValueError):extract(rel,symbols,self.glyphs)
        glyphs=list(self.glyphs);glyphs[ord('A')]='B'
        with self.assertRaises(ValueError):extract(self.rel,self.symbols,glyphs)

    def test_controller_with_address_and_undefined_behaviour_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-keyboard-grid-host-') as directory:
            target=str(Path(directory)/'check')
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I',str(ROOT/'overlays/keyboard_grid'),str(ROOT/'overlays/keyboard_grid/core.c'),
                str(ROOT/'tests/keyboard_grid_check.c'),'-o',target],check=True,capture_output=True,timeout=30)
            subprocess.run([target,str(ROOT/'build/keyboard-grid-layout/keys.bin')],
                           check=True,capture_output=True,timeout=10)

    def test_native_compiler_needs_no_external_runtime_support(self):
        with tempfile.TemporaryDirectory(prefix='af-keyboard-grid-mips-') as directory:
            docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
                '-v',f'{ROOT}/overlays/keyboard_grid:/source:ro','-v',f'{directory}:/out','-w','/out','--entrypoint']
            def run(tool,*args):
                return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
                                      check=True,capture_output=True,text=True,timeout=60).stdout
            run('gcc','-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
                '-fno-pic','-ffreestanding','-fno-builtin','-Wall','-Wextra','-Werror','/source/core.c','-o','core.o')
            self.assertEqual(run('nm','--undefined-only','core.o').strip(),'')

    def test_native_bridge_preserves_drafts_and_editor_capacities(self):
        with tempfile.TemporaryDirectory(prefix='af-grid-editor-host-') as directory:
            target=str(Path(directory)/'check')
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I',str(ROOT/'overlays/keyboard_grid'),
                str(ROOT/'overlays/keyboard_grid/core.c'),str(ROOT/'overlays/keyboard_grid/editor.c'),
                str(ROOT/'tests/keyboard_grid_editor_check.c'),'-o',target],
                check=True,capture_output=True,timeout=30)
            subprocess.run([target],check=True,capture_output=True,timeout=10)

    def test_keycap_preserves_donor_pixels_and_all_cell_positions(self):
        from title_assets import DATA_BASE,untile
        from font import pixels
        data=keycap(self.rel,self.symbols)
        self.assertEqual(len(data),128)
        self.assertEqual(bytes(pixels(data)),untile(self.rel[DATA_BASE+0x420AA0:DATA_BASE+0x420B20],16,16,4))
        with self.assertRaises(ValueError):keycap(self.rel[:-1],self.symbols)


if __name__=='__main__':unittest.main()
