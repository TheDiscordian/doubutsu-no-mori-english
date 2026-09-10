"""Complete birthday text, fixed allocations/relocations, and cartridge retention."""
import json
from pathlib import Path
import sys
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,apply_ups
from birthday_screen import OWNER,RELOC,ASSET,START,END,PROMPT,MONTHS,compiled,replacements,strings,build,measure_text


@unittest.skipUnless((ROOT/'build/birthday-screen-01/build.json').is_file(),'Local birthday candidate required')
class BirthdayScreenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.native=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        cls.base=(ROOT/'build/service-artwork-01/animal-forest-halfwidth.z64').read_bytes()
        cls.previous=json.loads((ROOT/'build/service-artwork-01/build.json').read_text())
        cls.image=(ROOT/'build/birthday-screen-01/animal-forest-halfwidth.z64').read_bytes()
        cls.report=json.loads((ROOT/'build/birthday-screen-01/build.json').read_text())
        cls.rel=(ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes()
        cls.symbols=(ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes()
        cls.directory=ROOT/'build/birthday-draw-03'

    def test_full_prompt_months_and_only_reviewed_code_assets_relocations(self):
        draw,_=compiled(self.directory);changed=replacements(self.native,draw);files=by_vrom(self.native)
        old=files[OWNER].extract(self.native)
        self.assertEqual(changed[OWNER][:START],old[:START]);self.assertEqual(changed[OWNER][END:],old[END:])
        self.assertEqual(changed[OWNER][START:END],draw+bytes(END-START-len(draw)))
        self.assertEqual(len(changed[RELOC]),192);self.assertEqual(struct.unpack_from('>5I',changed[RELOC]),(2272,64,0,16,35))
        asset=files[ASSET].extract(self.native);allowed=set(range(0x2DB8,0x2FB8))|set(range(0xAB8,0xB00))|set(range(0xB08,0xB50))
        self.assertTrue(all(a==b for i,(a,b) in enumerate(zip(asset,changed[ASSET])) if i not in allowed))
        for load in (0xAB8,0xB08):self.assertEqual(changed[ASSET][load:load+72],bytes.fromhex('E000000000000000')*9)
        payload=strings();self.assertEqual(len(payload),512);self.assertEqual(payload[:22],PROMPT+b'\0')
        self.assertEqual(len(PROMPT),21)
        for i,name in enumerate(MONTHS):self.assertEqual(payload[24+i*10:34+i*10].rstrip(b'\0'),name)
        self.assertEqual(payload[0x90:0x9A],b'?'+bytes(9));self.assertEqual(payload[0x9A:0x9D],b'OK\0')

    def test_independent_compilation_and_wrong_draw_rejection(self):
        from build_birthday_draw import compile_draw
        with tempfile.TemporaryDirectory(prefix='af-birthday-compile-') as directory:
            path=Path(directory)/'draw';compile_draw(path)
            self.assertEqual(compiled(path),compiled(self.directory))
        with self.assertRaises(ValueError):replacements(self.native,bytes(800))

    def test_complete_cartridge_and_installed_text_credit(self):
        image,patch,report=build(self.native,self.base,self.previous,self.rel,self.symbols,self.directory)
        self.assertEqual(image,self.image);self.assertEqual(report,self.report);self.assertEqual(apply_ups(self.native,patch),image)
        old,new=by_vrom(self.base),by_vrom(image);self.assertEqual(set(old),set(new))
        for v,entry in old.items():
            self.assertEqual((entry.index,entry.size),(new[v].index,new[v].size))
            if v not in (OWNER,RELOC,ASSET,0x19D40):self.assertEqual(entry.extract(self.base),new[v].extract(image))
        from textcodec import command_info
        from aflib import CODE_VROM
        from translation_progress import CounterLedger
        ledger=CounterLedger(command_info(by_vrom(self.native)[CODE_VROM].extract(self.native)))
        measure_text(ledger,self.native,image,report)
        self.assertEqual(ledger.summary()['total_source_characters'],13)
        self.assertEqual(ledger.summary()['replaced_source_characters'],13)
        pending=CounterLedger(ledger.info);measure_text(pending,self.native,self.base,self.previous)
        self.assertEqual(pending.summary()['total_source_characters'],13)
        self.assertEqual(pending.summary()['replaced_source_characters'],0)
        with self.assertRaises(ValueError):measure_text(CounterLedger(ledger.info),self.native,self.base,report)


if __name__=='__main__':unittest.main()
