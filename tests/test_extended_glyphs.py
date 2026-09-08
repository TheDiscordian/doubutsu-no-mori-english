"""Exact English glyph resources stay separate from every native font cell."""

import json
import copy
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from aflib import replace_dma, sha256, verified_rom
from build_extended_font_probe import RAM, relocate
from extended_font_test_scenario import HOOKS, native_actions, scenario, texture_commands
from extended_glyphs import (CODEPOINTS, ENCODINGS, GLYPHS, HEADER,
                             RESOURCE_BYTES, resource, source_atlas, untile_i4, validate_resource)
from font import get_glyph, make_halfwidth, pack_pixels, pixels, resize_glyph
from textbanks import banks
from textcodec import tokenize
from runtime_module import add_runtime_module, module_command_info
from test_retail import ROM_PATH

REL = ROOT/'build/gamecube/files/foresta.rel.szs.decoded'
SYMBOLS = ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt'
DECODER = ROOT/'local/ac-decomp/tools/msg_tool.py'
PROBE = ROOT/'build/extended-font-probe'
MODULE = ROOT/'build/runtime-module'


class ExtendedGlyphTests(unittest.TestCase):
    def test_tiled_i4_layout_is_independently_invertible_across_blocks(self):
        width, height = 24, 16
        original = [(x//8+3*(y//8)+x%8+2*(y%8))%16 for y in range(height) for x in range(width)]
        tiled = []
        for y in range(0,height,8):
            for x in range(0,width,8):
                for dy in range(8): tiled.extend(original[(y+dy)*width+x:(y+dy)*width+x+8])
        self.assertEqual(untile_i4(pack_pixels(tiled),width,height),original)
        for args in ((b'',0,0),(b'\0'*32,7,8),(b'\0'*31,8,8),(b'\0'*32,True,8)):
            with self.assertRaises(ValueError): untile_i4(*args)

    def test_resource_boundaries_padding_and_width_contracts(self):
        atlas = [0]*(192*256)
        for _, code, _ in GLYPHS:
            atlas[(code//16*16+4)*192+code%16*12+2] = 15
        data, rows = resource(atlas)
        self.assertEqual(len(data),RESOURCE_BYTES)
        self.assertEqual(data[:32],HEADER)
        self.assertEqual([r['advance'] for r in rows],[2,2,12,12,12])
        for offset,value in ((0,0),(4,1),(31,1),(32,0),(37,1),(48,0),(49,7),(50,6),(63,1),(100,255)):
            damaged=bytearray(data);damaged[offset]=value
            with self.assertRaises(ValueError): validate_resource(bytes(damaged))
        for damaged in (data[:-1],data+b'\0'):
            with self.assertRaises(ValueError): validate_resource(damaged)
        self.assertEqual(set(ENCODINGS),{';','/','☀','☃','💀'})
        self.assertEqual(len(set(ENCODINGS.values())),5)
        self.assertTrue(all(value == bytes((0x80,code)) for code,text in CODEPOINTS.items()
                            for value in [ENCODINGS[text]]))

    def test_portable_native_primitives_with_sanitizers(self):
        with tempfile.TemporaryDirectory() as tmp:
            target=Path(tmp)/'font-test'
            subprocess.run(['gcc','-std=c11','-Wall','-Wextra','-Werror','-O1','-g',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-DAF_GLYPH_HOST_TEST',
                '-I'+str(ROOT/'overlays/extended_font'),str(ROOT/'overlays/extended_font/font.c'),
                str(ROOT/'tests/extended_font_test.c'),'-o',str(target)],check=True,capture_output=True)
            result=subprocess.run([str(target)],check=True,capture_output=True,text=True,timeout=20)
            self.assertIn('extended font primitives passed',result.stdout)


@unittest.skipUnless(REL.is_file() and SYMBOLS.is_file() and DECODER.is_file(), 'English sources remain local')
class ExtendedGlyphRetailTests(unittest.TestCase):
    def test_complete_source_and_each_glyph_are_verified_without_native_atlas_changes(self):
        rel=REL.read_bytes();symbols=SYMBOLS.read_text()
        atlas=source_atlas(rel,symbols,DECODER);data,rows=resource(atlas)
        self.assertEqual([r['advance'] for r in rows],[3,6,12,12,12])
        target=pixels(data[64:])
        for slot,(_,code,halfwidth) in enumerate(GLYPHS):
            original=get_glyph(atlas,code)
            expected=resize_glyph(original)[0] if halfwidth else original
            actual=[target[y*192+slot*12:y*192+slot*12+12] for y in range(16)]
            self.assertEqual(actual,expected)
            self.assertTrue(any(any(row) for row in actual))
            self.assertEqual(rows[slot]['source_glyph_sha256'],sha256(pack_pixels([v for row in original for v in row])))
        with self.assertRaises(ValueError): source_atlas(rel[:-1],symbols,DECODER)
        with self.assertRaises(ValueError): source_atlas(rel,symbols+'\n',DECODER)

    @unittest.skipUnless(ROM_PATH.is_file(),'Native source remains local')
    def test_reserved_two_byte_encodings_are_absent_from_every_native_bank(self):
        rom=verified_rom(ROM_PATH.read_bytes());info=module_command_info(rom)
        hits=[]
        for bank in banks(rom):
            for i,entry in enumerate(bank.entries()):
                hits.extend((bank.name,i,t.data.hex()) for t in tokenize(entry,info,strict=False)
                            if t.kind=='glyph')
        self.assertEqual(hits,[])


@unittest.skipUnless((PROBE/'font.json').is_file() and (PROBE/'font.bin').is_file(),
                     'Native probe is a generated local build')
class ExtendedGlyphProbeTests(unittest.TestCase):
    def setUp(self):
        self.binary = (PROBE/'font.bin').read_bytes()
        self.report = json.loads((PROBE/'font.json').read_text())

    def test_internal_code_and_state_relocate_across_signed_low_address_boundaries(self):
        for base in (0x801A0010,0x802F8010,0x803FD000):
            output = relocate(self.binary,self.report,base)
            self.assertEqual(len(output),len(self.binary))
            pairs = {}
            changed = set()
            for offset,kind in self.report['relocations']:
                old,new = (struct.unpack_from('>I',value,offset)[0] for value in (self.binary,output))
                changed.add(offset)
                if kind=='26':
                    self.assertEqual((new&0x3FFFFFF)*4-(old&0x3FFFFFF)*4,base-RAM)
                    self.assertEqual(new>>26,old>>26)
                elif kind=='HI16': pairs[(old>>16)&31] = offset
                else:
                    high = pairs.pop((old>>21)&31)
                    def pointer(data):
                        lo = struct.unpack_from('>h',data,offset+2)[0]
                        hi = struct.unpack_from('>H',data,high+2)[0]
                        return hi*65536+lo
                    self.assertEqual(pointer(output)-pointer(self.binary),base-RAM)
            self.assertEqual(pairs,{})
            for at in range(0,len(output),4):
                if at not in changed: self.assertEqual(output[at:at+4],self.binary[at:at+4])
            self.assertFalse(any(output[self.report['symbols']['__font_bss_start']-RAM:]))

    def test_relocation_rejects_stale_data_missing_pairs_and_unsafe_destinations(self):
        for base in (0,True,RAM,0x801A0011,0x80400000):
            with self.assertRaises(ValueError): relocate(self.binary,self.report,base)
        for mutation in ('code','source','missing_high','missing_low','missing_jump','duplicate','kind','outside'):
            report = copy.deepcopy(self.report);data = self.binary
            if mutation=='code': data = data[:-4]+b'!!!!'
            elif mutation=='source': report['sources'] = {}
            elif mutation.startswith('missing_'):
                kind = {'high':'HI16','low':'LO16','jump':'26'}[mutation[8:]]
                report['relocations'].remove(next(row for row in report['relocations'] if row[1]==kind))
            elif mutation=='duplicate': report['relocations'].insert(0,report['relocations'][0])
            elif mutation=='kind': report['relocations'][0][1] = '32'
            else: report['relocations'][0][0] = len(data)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                relocate(data,report,0x802F8010)

    @unittest.skipUnless(ROM_PATH.is_file() and (MODULE/'module.json').is_file()
                         and (ROOT/'build/extended-glyphs/glyphs.bin').is_file(),'Pilot and resource stay local')
    def test_native_fixture_owns_code_checks_both_paths_and_restores_all_hooks(self):
        # Build this unhooked fixture in memory from current verified code.
        # Historical checkpoint ROMs must not be overwritten after a module change.
        native = ROM_PATH.read_bytes()
        replacements,_ = make_halfwidth(native)
        additions,module = add_runtime_module(native,replacements,MODULE)
        rom = replace_dma(native,replacements,additions=additions)
        resource = (ROOT/'build/extended-glyphs/glyphs.bin').read_bytes()
        actions = scenario(rom,ROM_PATH.read_bytes(),module,self.binary,self.report,resource)
        self.assertEqual(actions[:3],[{'wait':8},{'save_state':True},{'pause_game_thread':True}])
        self.assertEqual(actions[4:7],[{'load_state':True},{'resume':True},{'wait':2}])
        plan = actions[3]['test_extended_font']
        steps = native_actions(plan,0x802F8010)
        calls = [row['call'] for row in steps if 'call' in row]
        self.assertEqual(sum(row['address']=='80091C98' for row in calls),26)
        self.assertEqual(sum(row['address']=='8009034C' for row in calls),26)
        for hook in HOOKS:
            writes = [row['write'][1] for row in steps if row.get('write',[''])[0]==f'{hook:08X}']
            self.assertEqual(len(writes),2)
            original = next(bytes.fromhex(value)[hook-int(at,16):hook-int(at,16)+8].hex()
                            for at,value in plan['guards'].items()
                            if int(at,16)<=hook<=int(at,16)+len(value)//2-8)
            self.assertEqual(writes[-1],original)
        self.assertEqual(len(texture_commands(0x802F8050,0)),56)
        self.assertEqual(texture_commands(0x802F8050,0)[:8],bytes.fromhex('FD88005F802F8050'))


if __name__ == '__main__':
    unittest.main()
