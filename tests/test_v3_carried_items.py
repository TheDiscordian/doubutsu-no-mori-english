"""Complete carried families/resources; preparation is not gameplay admission."""
import copy
import json
import os
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
import v3_carried_items as carried
from v3_furniture_pipeline import Source
from v3_item_categories import discover as categories,checked_art
from v3_ui_art import Packet,validate_state

OUTPUT=ROOT/os.environ.get('V3_CARRIED_ART','build/v3-carried-batch-prepared-05')


class CarriedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import v3_optional_composition as composition
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        composition.use_build_lock(ROOT/'build/v3-diary-category-work-01/admission-connected-04/build-lock.json')
        image,report=composition.inputs()
        cls.installed=composition.catalogue(image,report)
        cls.rows,cls.receipt=carried.records(cls.source,ROOT/'build/item-identity-megasheet.xlsx',cls.installed)

    def test_complete_state_families_names_and_source_prices(self):
        self.assertEqual((self.receipt['parent_count'],self.receipt['state_count']),(7,26))
        parents={r['parent_item_id'] for r in self.rows}
        self.assertEqual(parents,{'2003','251E','2523','2530','2807','2901','2D28'})
        by_item={r['item_id']:r for r in self.rows}
        for row in self.rows:
            family=carried.states(int(row['donor_item_id'],16))
            self.assertEqual(row['state_count'],len(family))
            self.assertEqual(row['item_id'],f'{family[row["state_index"]]:04X}')
            name=self.source.raw(row['name_source_symbol'])[row['name_source_index']*16:][:16]
            self.assertEqual(sha256(name),row['name_sha256'])
            self.assertEqual(name.decode('ascii').rstrip(),row['name'])
            self.assertIsNone(row['native_item_id'])
            self.assertFalse(row['ready']);self.assertFalse(row['selected'])
        self.assertEqual([by_item[f'{i:04X}']['price'] for i in carried.states(0x2003)],[40,80,120,160])
        self.assertEqual([by_item[i]['price'] for i in ('251E','2807','2901')],[500,600,60])
        self.assertTrue(all(r['price']==0 for r in self.rows if r['parent_item_id'] in ('2523','2530','2D28')))

    def test_all_icons_use_actual_group_and_quantity_bindings(self):
        data,report=carried.pocket_icons(self.source,self.rows)
        self.assertEqual((report['unique_icons'],len(data)),(14,8064))
        by_item={r['item_id']:r for r in report['bindings']}
        for parent,count in ((0x2003,4),(0x2523,1),(0x2D28,5)):
            self.assertEqual(len({by_item[f'{i:04X}']['address'] for i in carried.states(parent)}),count)
        for row in report['bindings']:
            at=row['offset']
            self.assertEqual(struct.unpack_from('>2I',data,at),(report['ram']+at+32,report['ram']+at+64))
            self.assertEqual(data[at+8:at+32],bytes(24))
            for resource in row['resources']:
                start,n=resource['offset'],resource['bytes']
                self.assertEqual(sha256(data[start:start+n]),resource['sha256'])
                self.assertEqual(sha256(self.source.raw(resource['symbol'])),resource['source_sha256'])
        from v3_holiday_items import records,pocket_icons,PREPARED
        rows,_=records(self.source);old,receipt=pocket_icons(self.source,rows)
        prior=json.loads((PREPARED/'items.json').read_bytes())
        self.assertEqual(old,(PREPARED/'icons.bin').read_bytes())
        self.assertEqual(json.loads(json.dumps(receipt)),prior['icons'])

    def test_handover_cage_does_not_fabricate_a_ground_descriptor(self):
        report=categories(self.source,self.rows,require_ground=False)
        self.assertEqual(len(report['rows']),7)
        for row in report['rows']:
            self.assertEqual(len(row['ground_descriptors']),0 if row['source_category']==18 else 4)
        with self.assertRaisesRegex(ValueError,'seasonal category descriptor'):
            categories(self.source,self.rows)

    def test_complete_nested_paper_art_and_rejection_guards(self):
        prepared,report=carried.paper_art(self.source,self.rows)
        self.assertEqual(report['bindings'][0]['text_rgba'],[75,115,215,255])
        self.assertEqual(len(prepared[2]),12)
        self.assertEqual(sum(len(r.get('triangles',[])) for m in prepared[4].values() for r in m['rows']),20)
        bg=prepared[4]['paper_03_background']
        self.assertTrue(any('calls' in p for p in bg['source_parts']))
        self.assertFalse(any(r['opcode']==0xDE for m in prepared[4].values() for r in m['rows']))
        for a,b in ((0xE3001001,1),(0xE200001C,0),(0xEF08AC10,0)):
            with self.assertRaisesRegex(ValueError,'Unsupported UI state'):validate_state(a,b)
        source=copy.copy(self.source);source.relocations=dict(self.source.relocations)
        at,_=source.symbol('lat_letter04_model');source.relocations[at+4]=(1,True,5,at)
        with self.assertRaisesRegex(ValueError,'recursive model graph'):
            Packet(source).model('bad',['lat_letter_mode','lat_letter04_model'])
        source=copy.copy(self.source);source.rel=bytearray(self.source.rel)
        source.rel[source.sections[1][0]+0x784E0+0x98]^=1
        with self.assertRaisesRegex(ValueError,'price function'):
            carried.price_records(source,copy.deepcopy(self.rows))

    @unittest.skipUnless((OUTPUT/'items.json').is_file(),'Current prepared carried batch required')
    def test_complete_prepared_objects_and_paper_preserve_every_resource(self):
        report=json.loads((OUTPUT/'items.json').read_bytes())
        self.assertEqual(report['rows'],self.rows)
        for path,digest in report['sources'].items():
            self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertFalse(report['runtime_installed']);self.assertFalse(report['selectable'])
        for row in report['categories']['objects']:
            data,_=checked_art(self.source,OUTPUT/'categories',row)
            self.assertEqual(len(data),816)
            self.assertIn('reused_from',row)
            changed=copy.deepcopy(row);changed['model_offsets']['geometry']+=8
            with self.assertRaisesRegex(ValueError,'split category display lists'):
                checked_art(self.source,OUTPUT/'categories',changed)
            changed=copy.deepcopy(row)
            changed['profile']['models']['material']=report['categories']['objects'][-1]['models'][0]
            if changed['profile']!=row['profile']:
                with self.assertRaisesRegex(ValueError,'prepared category artwork'):
                    checked_art(self.source,OUTPUT/'categories',changed)
        prepared,_=carried.paper_art(self.source,self.rows);p=report['stationery']
        raw=(OUTPUT/p['file']).read_bytes()
        self.assertEqual(len(raw),3088);self.assertEqual(sha256(raw),p['sha256'])
        self.assertEqual(prepared[5],(OUTPUT/'stationery/commands.c').read_text())
        self.assertEqual(prepared[2],p['resources'])
        for resource in p['resources']:
            at,n=resource['native_offset'],resource['bytes']
            self.assertEqual(sha256(raw[at:at+n]),resource['output_sha256'])
        for model in p['models']:
            at,n=model['native_offset'],model['bytes'];data=raw[at:at+n]
            self.assertEqual(sha256(data),model['output_sha256'])
            self.assertEqual(data[-8:],struct.pack('>2I',0xDF000000,0))
            self.assertFalse({0x0A,0xD2,0xDE}&{a>>24 for a,b in struct.iter_unpack('>2I',data)})


if __name__=='__main__':unittest.main()
