"""Complete compiler, donor-article, and prior-profile identities stay enforced."""
import json
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
from extended_font_cartridge import validate,relocate
from accent_item_articles import build


class AccentMailProfileTests(unittest.TestCase):
    def test_independent_compilers_exact_imports_and_existing_font_profiles(self):
        directory=ROOT/'build/accent-mail-font'
        image=(directory/'font.bin').read_bytes();reloc=(directory/'relocation.bin').read_bytes()
        report=json.loads((directory/'font.json').read_text());validate(image,reloc,report)
        for name in ('accent-mail-font-candidate','accent-mail-font-rebuild'):
            self.assertEqual((ROOT/'build'/name/'font.bin').read_bytes(),image)
            self.assertEqual((ROOT/'build'/name/'relocation.bin').read_bytes(),reloc)
            with self.assertRaises(ValueError):
                validate(image,reloc,json.loads((ROOT/'build'/name/'font.json').read_text()))
        for name in ('world-names-font','accent-font'):
            path=ROOT/'build'/name
            validate((path/'font.bin').read_bytes(),(path/'relocation.bin').read_bytes(),json.loads((path/'font.json').read_text()))
        for base in (0x8019C8E0,0x801A0010,0x80300000):
            self.assertEqual(len(relocate(image,reloc,base,mail_literals=True)),len(image))
        for key in ('mail_literals','accent_glyphs','world_names'):
            bad={**report,key:False}
            with self.assertRaises(ValueError):validate(image,reloc,bad)
        at=report['symbols']['mail_hooks'];bad=bytearray(image);bad[at]^=1
        with self.assertRaises(ValueError):validate(bytes(bad),reloc,{**report,'sha256':sha256(bad)})

    def test_complete_articles_change_only_five_names_and_the_bound_header(self):
        native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_text()
        names=(ROOT/'build/accent-items-candidate/names.bin').read_bytes()
        before=(ROOT/'build/design-items-articles/articles.bin').read_bytes()
        data,report=build(native,rel,symbols,names,before)
        self.assertEqual(data,(ROOT/'build/accent-item-articles/articles.bin').read_bytes())
        self.assertEqual(sha256(data),'b218119460fdbb472e641cbbc6d77ff809d489bda8b8622f0157562294d575ff')
        restored=bytearray(data);restored[16:48]=before[16:48]
        for row in report['changed_rows']:restored[48+5*row:53+5*row]=before[48+5*row:53+5*row]
        self.assertEqual(bytes(restored),before)
        bad=bytearray(names);bad[32]^=1
        with self.assertRaises(ValueError):build(native,rel,symbols,bytes(bad),before)


if __name__=='__main__':unittest.main()
