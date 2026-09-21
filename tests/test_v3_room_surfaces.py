"""Complete bulk surface conversion, identity, metadata, and cache checks."""
import copy
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256
from v3_furniture_install import inputs,provenance_patch
from v3_furniture_pipeline import Source
from v3_registry import SURFACES,surface_identity
from v3_room_surfaces import KINDS,discover,convert_record,source_metadata,checked_prepared,convert
from title_assets import rgb5a3


class RoomSurfacesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(ROOT/'build/v3-start-disabled-imports-01/cartridge/build-lock.json')
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        cls.inventory,cls.assets=discover(cls.source,cls.image)
        cls.output=ROOT/'build/v3-room-surfaces-prepared-02'

    def test_bulk_identity_and_special_bank_preservation(self):
        self.assertEqual(self.inventory['counts'],dict(player_surfaces=134,existing=124,
            ambiguous=0,additive=10,additive_bytes=61760,non_item_shop_surfaces=8))
        self.assertEqual(set(self.assets),{f'{i:04X}' for i in SURFACES})
        self.assertEqual(surface_identity(0x261A),(74,0x264A))
        self.assertEqual(surface_identity(0x271A),(74,0x274A))
        self.assertEqual(self.inventory['floor_sound_inputs']['native_reserved_count'],73)
        self.assertFalse(self.inventory['floor_sound_inputs']['complete_sound_equivalence_verified'])
        for bank in self.inventory['banks']:
            self.assertEqual([r['native_index'] for r in bank['shop_mappings']],[64,65,66,67])
            self.assertEqual([r['source_index'] for r in bank['shop_mappings']],[67,68,69,70])
        for row in self.inventory['rows']:
            if row['source_item_id'] in self.assets:
                self.assertGreaterEqual(row['destination_index'],73)
                self.assertEqual(row['identity_evidence']['native_id'],'-')
                self.assertEqual(row['native_matches'],[])
            else:
                self.assertIsNone(row['destination_index'])
                self.assertEqual(len(row['native_matches']),1)
            self.assertFalse(row['selectable']);self.assertFalse(row['runtime_installed'])
        with self.assertRaises(ValueError):surface_identity(0x2630)

    def test_every_added_palette_and_texel_against_independent_tile_addressing(self):
        rows={r['source_item_id']:r for r in self.inventory['rows']}
        for kind in KINDS:
            bank=(ROOT/f'build/gamecube/files/forest_2nd.arc.unpacked/data/player_room_{kind["kind"]}.bin').read_bytes()
            for key,out in self.assets.items():
                row=rows[key]
                if row['kind']!=kind['kind']:continue
                offset=row['source_index']*kind['stride'];raw=bank[offset:offset+kind['stride']]
                for i in range(16):
                    red,green,blue,alpha=rgb5a3(struct.unpack_from('>H',raw,i*2)[0])
                    expected=((red>>3)<<11)|((green>>3)<<6)|((blue>>3)<<1)|(alpha==255)
                    self.assertEqual(struct.unpack_from('>H',out,i*2)[0],expected)
                for tile in range(kind['tiles']):
                    base=32+tile*0x800
                    for y in range(64):
                        for x in range(64):
                            # GC CI4: 8x8 blocks, 32 bytes each. N64: row-major
                            # nibbles. This does not call the converter's untile.
                            gc=base+((y//8)*8+x//8)*32+(y%8)*4+(x%8)//2
                            n64=base+y*32+x//2;shift=0 if x&1 else 4
                            self.assertEqual((raw[gc]>>shift)&15,(out[n64]>>shift)&15)
                self.assertEqual(sha256(out),row['converted_sha256'])
        with self.assertRaises(ValueError):convert_record(bytes(0x2020-1),4)
        with self.assertRaises(ValueError):convert_record(bytes(0x1820),3)

    def test_source_metadata_and_single_name_catalogue(self):
        rows={r['source_item_id']:r for r in self.inventory['rows']}
        self.assertEqual(rows['261A']['acquisition'],[dict(symbol='carpet_listC',table_index=2)])
        self.assertEqual(rows['271A']['acquisition'],[dict(symbol='wall_listA',table_index=0)])
        self.assertEqual(rows['2641']['acquisition'],[dict(symbol='carpet_listEvent',table_index=3)])
        self.assertEqual(rows['2640']['acquisition'],[dict(symbol='carpet_listHomePage',table_index=16)])
        self.assertEqual(rows['2742']['acquisition'],[dict(symbol='wall_listHarvest',table_index=20)])
        entries={r['id']:r for r in json.loads((ROOT/'translations/provenance.json').read_bytes())['entries']}
        for key in self.assets:
            row=rows[key];credit=entries[row['id']+'/name']['locales']['en']
            self.assertEqual(credit['credit'],'official');self.assertEqual(credit['text'],row['name'])
            self.assertEqual(credit['source']['symbol'],row['name_source_symbol'])
            self.assertEqual(credit['encoded_sha256'],row['name_sha256'])
            self.assertEqual(provenance_patch([row]),'')
        real=self.source.raw
        with patch.object(self.source,'raw',side_effect=lambda name:
                real(name)[:-2]+bytes(2) if name=='carpet_price_table' else real(name)):
            with self.assertRaisesRegex(ValueError,'complete room-surface'):source_metadata(self.source,KINDS[0])

    def test_prepared_cache_and_selection_independent_destinations(self):
        cache=checked_prepared(self.output,self.inventory,self.assets)
        self.assertEqual(set(cache),set(self.assets))
        with tempfile.TemporaryDirectory(prefix='v3-surfaces-',dir=ROOT/'build') as temp:
            directory=Path(temp)/'subset'
            result=convert(self.source,self.image,directory,['2742','261A'],reuse=[self.output])
            self.assertEqual(result['batch'],dict(objects=2,bytes=12352,reused=2,compiler_containers=0))
            self.assertEqual({r['source_item_id']:r['destination_item_id'] for r in result['objects']},
                {'2742':'274D','261A':'264A'})
            self.assertEqual(set(checked_prepared(directory,self.inventory,self.assets)),{'2742','261A'})
            file=directory/'261A.surface.bin';bad=bytearray(file.read_bytes());bad[-1]^=1;file.write_bytes(bad)
            with self.assertRaisesRegex(ValueError,'complete prepared surface'):checked_prepared(directory,self.inventory,self.assets)


if __name__=='__main__':unittest.main()
