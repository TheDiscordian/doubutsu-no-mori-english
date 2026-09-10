"""Exact extra accent cells and complete compatibility with preceding fonts."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))


class AccentFontTests(unittest.TestCase):
    @unittest.skipUnless((ROOT/'build/accent-font/font.json').is_file(),'Compiled accent font required')
    def test_compiled_profile_and_relocation_retain_old_capabilities(self):
        import copy,json
        from extended_font_cartridge import validate,relocate,mail_capability
        directory=ROOT/'build/accent-font'
        data=(directory/'font.bin').read_bytes();rel=(directory/'relocation.bin').read_bytes()
        report=json.loads((directory/'font.json').read_text());validate(data,rel,report)
        self.assertTrue(report['mail_glyphs'] and report['world_names'] and report['accent_glyphs'])
        for base in (0x801A0010,0x802F8010,0x803FD000):self.assertEqual(len(relocate(data,rel,base)),4576)
        self.assertTrue(mail_capability(directory))
        for key,value in (('accent_glyphs',False),('world_names',False),('sources',{}),('unapproved_candidate',True)):
            changed=copy.deepcopy(report);changed[key]=value
            with self.assertRaises(ValueError):validate(data,rel,changed)
        for at in (0,report['symbols']['af_glyph_bind'],report['symbols']['af_font_resource']+46,len(data)-1):
            changed=bytearray(data);changed[at]^=1
            with self.assertRaises(ValueError):validate(changed,rel,report)
        old=ROOT/'build/world-names-font'
        validate((old/'font.bin').read_bytes(),(old/'relocation.bin').read_bytes(),json.loads((old/'font.json').read_text()))

    def test_exact_source_cells_previous_resource_retention_and_rejection(self):
        from extended_glyphs import source_atlas,resource,validate_resource,ACCENT_GLYPHS
        from aflib import sha256
        from font import get_glyph,resize_glyph,pixels
        rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
        atlas=source_atlas(rel,symbols,ROOT/'local/ac-decomp/tools/msg_tool.py',mail=True,accents=True)
        data,rows=resource(atlas,mail=True,accents=True)
        old,_=resource(atlas,mail=True)
        self.assertEqual(sha256(data),'24ae623d2917a2370ec70504daf372be327c830d24fb37bacc68ad84f0bbe90e')
        self.assertEqual(sha256(old),'12a90673f21a6c0bfa3fc05039279b1efc65d96319460ae36993eafa0822c105')
        self.assertEqual(len(data),1600);self.assertEqual(len(rows),16)
        self.assertEqual(data[32:46],old[32:46]);self.assertEqual(data[48:62],old[48:62])
        current,prior=pixels(data[64:]),pixels(old[64:])
        for y in range(16):self.assertEqual(current[y*192:y*192+168],prior[y*192:y*192+168])
        for slot,(_,code,_) in enumerate(ACCENT_GLYPHS[-2:],14):
            expected,advance=resize_glyph(get_glyph(atlas,code))
            self.assertEqual(advance,6)
            self.assertEqual([current[y*192+slot*12:y*192+slot*12+12] for y in range(16)],expected)
        self.assertEqual(validate_resource(data,mail=True,accents=True),data)
        for value,mail,accents in ((data,True,False),(data,False,True),(old,True,True)):
            with self.assertRaises(ValueError):validate_resource(value,mail=mail,accents=accents)
        for at in (19,46,47,62,63):
            changed=bytearray(data);changed[at]=0
            with self.assertRaises(ValueError):validate_resource(changed,mail=True,accents=True)

    def test_portable_native_font_and_prior_profiles_under_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='af-accent-font-') as directory:
            target=str(Path(directory)/'check')
            subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O1','-g',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-DAF_GLYPH_HOST_TEST',
                '-I'+str(ROOT/'overlays/extended_font'),str(ROOT/'overlays/accent_font/font.c'),
                str(ROOT/'tests/accent_font_test.c'),'-o',target],check=True,capture_output=True,timeout=30)
            subprocess.run([target],check=True,capture_output=True,timeout=15)


if __name__=='__main__':unittest.main()
