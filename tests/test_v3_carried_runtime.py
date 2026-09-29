"""Shared carried readers and installed resources, not ordinary gameplay proof."""
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import BLOB,MODULE,MODULE_RAM
from v3_carried_runtime import RAM,TABLE,ICON,ART,PAPER,END,GUARD,native_identities
from v3_furniture_install import inputs
from v3_registry import CARRIED_ITEMS,CARRIED_ITEM_CATEGORIES
import v3_physical_resources as physical

OUT=ROOT/os.environ.get('V3_CARRIED_RUNTIME','build/v3-carried-runtime-work-01/actions-connected-03')

class CarriedRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')

    def test_complete_packet_readers_preserved_native_identities_and_startup(self):
        image,r=self.image,self.report;base,prior=self.base,self.prior
        e=r['equipment_resources'];d=e['carried_items'];p=d['packet'];old=d['previous_packet']
        raw=image[p['physical']:p['physical']+p['bytes']]
        physical.verify(image,r['physical_resources'])
        self.assertEqual((sha256(raw),zlib.crc32(raw)),(p['sha256'],p['crc32']))
        self.assertEqual(sha256(raw[:old['bytes']]),old['sha256'])
        self.assertEqual(p['ram']+len(raw),END);self.assertEqual(raw[-16:],GUARD)
        self.assertEqual(sha256(raw[RAM-p['ram']:]),d['sha256'])
        self.assertEqual(sha256(raw[RAM-p['ram']:RAM-p['ram']+d['code']['bytes']]),d['code']['sha256'])
        self.assertEqual(raw,(OUT/'carried-packet.bin').read_bytes())
        table=raw[TABLE-p['ram']:TABLE-p['ram']+d['table_bytes']]
        self.assertEqual(struct.unpack_from('>8I',table),(0x41464350,1,26,32,0,0,0,0))
        for i,row in enumerate(d['rows']):
            fields=struct.unpack_from('>3H4BHI16s',table,32+i*32)
            self.assertEqual(fields,(CARRIED_ITEMS[int(row['donor_item_id'],16)],int(row['donor_item_id'],16),
                CARRIED_ITEMS[int(row['parent_item_id'],16)],row['family'],row['state_index'],
                CARRIED_ITEM_CATEGORIES[row['source_category']],0,row['price'],row['icon'],row['name'].encode().ljust(16,b' ')))
        for a in d['artwork']:
            at=a['ram']-p['ram'];self.assertEqual(sha256(raw[at:at+a['object_bytes']]),a['installed_sha256'])
        paper=d['paper'];at=PAPER-p['ram']
        self.assertEqual(sha256(raw[at:at+paper['bytes']]),paper['installed_sha256'])
        prepared=bytearray((ROOT/d['prepared']/paper['file']).read_bytes())
        self.assertEqual(sha256(prepared),paper['sha256'])
        for fix in paper['pointer_relocations']:
            self.assertEqual(u32(prepared,fix['offset']),fix['before'])
            struct.pack_into('>I',prepared,fix['offset'],fix['after'])
        self.assertEqual(raw[at:at+paper['bytes']],bytes(prepared))
        files=by_vrom(image);blob=files[BLOB].extract(image);core=files[CODE_VROM].extract(image);module=files[MODULE].extract(image)
        self.assertEqual(native_identities(core),d['native_tables'])
        for h in d['hooks']:
            data,origin=(blob,0x80460000) if h['address']>=0x80460000 else ((module,MODULE_RAM) if h['address']>=MODULE_RAM else (core,CODE_RAM))
            self.assertEqual(data[h['address']-origin:h['address']-origin+8].hex(),h['after'])
        h=d['icon_hook'];menu=files[h['vrom']].extract(image)
        self.assertEqual(menu[h['address']-0x8085BAC0:h['address']-0x8085BAC0+8].hex(),h['after'])
        boot=e['surface_bootstrap']['code'];at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        self.assertEqual(boot['packet_count'],20);self.assertLessEqual(boot['bytes'],688)
        for dest,src,n,crc in struct.iter_unpack('>4I',blob[at:at+20*16]):
            if src&0x80000000:data=image[src&0x7FFFFFFF:(src&0x7FFFFFFF)+n]
            else:
                owner=next(x for x in files.values() if x.vstart<=src<src+n<=x.vend)
                data=owner.extract(image)[src-owner.vstart:src-owner.vstart+n]
            self.assertEqual(u32(blob,e['blob_offset']+crc-e['ram']),zlib.crc32(data))
            self.assertTrue(0x80400000<=dest<dest+n<=0x807DA800)
        self.assertEqual((dest,src,n),(p['ram'],p['physical']|0x80000000,p['bytes']))
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        self.assertFalse(d['saved_format_changed']);self.assertFalse(d['native_execution_verified'])

    def test_retained_reader_chain_and_full_submenu_capacity(self):
        from v3_creature_items import checked
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertIsNotNone(checked(self.image,self.report,source))
        from v3_furniture_capacity import checked as capacity
        broken=copy.deepcopy(self.report)
        broken['equipment_resources']['carried_items']['menu_allocations'][0]['pool_patch']['after']+=64
        with self.assertRaisesRegex(ValueError,'allocation chain'):capacity(self.image,broken)
        broken=copy.deepcopy(self.report)
        broken['equipment_resources']['holiday_items']['controls']['metadata'][0]['additional_pool_bytes']+=64
        with self.assertRaisesRegex(ValueError,'allocation chain'):capacity(self.image,broken)

    def test_complete_letter_tables_and_original_editor_preserved(self):
        d=self.report['equipment_resources']['carried_items'];paper=d['paper'];r=paper['letter_window']
        files=by_vrom(self.image);old=by_vrom(self.base)
        data=files[r['vrom']].extract(self.image);before=old[r['vrom']].extract(self.base)
        current=d.get('actions',{}).get('letter',r)
        self.assertEqual(sha256(data),current['owner_sha256'])
        self.assertEqual(sha256(files[r['reloc']].extract(self.image)),current['relocation_sha256'])
        self.assertEqual(len(r['tables']),3)
        for table in r['tables']:
            at=table['address']-r['ram'];start=table['original']-r['ram']
            self.assertEqual((table['count'],table['original_count'],table['stride']),(65,64,4))
            self.assertEqual(data[at:at+256],before[start:start+256])
        binding=paper['bindings'][0]
        for table,kind in zip(r['tables'][:2],('background','lines')):
            self.assertEqual(u32(data,table['address']-r['ram']+256),
                (PAPER&0x1FFFFFFF)+paper['offsets'][binding[kind]])
        at=r['tables'][2]['address']-r['ram']+256
        self.assertEqual(list(data[at:at+4]),binding['text_rgba'])
        allowed={p['address']-r['ram']+i for p in r['patches']+current['patches'] for i in range(4)}
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,before))))

    def test_shared_stack_actions_have_real_callers_and_preserve_native_owners(self):
        from catalogue_names import Image
        from npc_mail_show import relocate_verified_data
        from v3_import_storage import jump
        d=self.report['equipment_resources']['carried_items'];a=d.get('actions')
        if not a:self.skipTest('Current build predates the shared inventory-action connection')
        files,old=by_vrom(self.image),by_vrom(self.base)
        symbols=d['code']['symbols'];p=d['packet'];raw=self.image[p['physical']:p['physical']+p['bytes']]
        start=RAM-p['ram'];previous=a['code_previous']
        self.assertEqual(sha256(raw[start:start+previous['bytes']]),previous['sha256'])
        self.assertLessEqual(d['code']['bytes'],TABLE-RAM)
        tag=files[0x3950000].extract(self.image);r=a['tag'];ram=0x8086F310
        self.assertEqual(sha256(tag),r['owner_sha256'])
        table=r['tables'][0];self.assertEqual((table['original_count'],table['count']),(47,51))
        self.assertEqual(u32(tag,0x80875834-ram),jump(symbols['af_carried_menu_type'],link=True))
        for i,menu in enumerate(a['menus']):
            self.assertEqual(menu['index'],47+i)
            self.assertEqual(struct.unpack_from('>II',tag,table['address']-ram+8*menu['index']),
                (menu['address'],len(menu['words'])))
            self.assertEqual(menu['words'][-1],0x80879898)
            self.assertEqual(tag[menu['words'][1]-ram:menu['words'][1]-ram+16],b'Grab One        ')
            self.assertEqual(u32(tag,menu['words'][1]-ram+16),symbols['af_carried_grab_one'])
        self.assertEqual([len(m['words']) for m in a['menus']],[5,6,5,4])
        letter=files[0x3B60000].extract(self.image)
        self.assertEqual(u32(letter,0x80889434-0x80888E90),jump(symbols['af_carried_consume_paper'],link=True))
        hand=a['hand'];data=files[hand['vrom']].extract(self.image);before=old[hand['vrom']].extract(self.base)
        reloc=files[hand['reloc']].extract(self.image);old_reloc=old[hand['reloc']].extract(self.base)
        self.assertEqual((sha256(data),sha256(reloc)),(hand['owner_sha256'],hand['relocation_sha256']))
        at=hand['address']-hand['ram']
        self.assertEqual(u32(data,at),jump(symbols['af_carried_drop_stack'],link=True))
        self.assertEqual(data[:at]+data[at+4:],before[:at]+before[at+4:])
        self.assertEqual(reloc[:16],old_reloc[:16]);self.assertEqual(u32(reloc,16),u32(old_reloc,16)-1)
        # The complete native money reader deliberately biases its table base
        # by ITM_MONEY_START*4 before indexing by the full 0x2100..0x2103 ID.
        # This is the sole out-of-owner HI/LO constant, not an escaped pointer.
        from v3_player_actions import native_references
        groups,_,_,_,_=native_references(before,old_reloc,expected_sections=(8864,272,80,768))
        outside=[(hand['ram']+hi,hand['ram']+lo,value) for hi,refs in groups.items() for lo,value in refs
            if not hand['ram']<=value<hand['ram']+len(before)+768]
        self.assertEqual(outside,[(0x8087AE54,0x8087AE80,0x808742A8)])
        self.assertEqual(struct.unpack_from('>4I',before,0x808742A8+0x2100*4-hand['ram']),
            (1000,10000,30000,100))
        for base in (0x80200010,0x80348010):
            b=relocate_verified_data(Image(hand['ram'],len(before)+u32(old_reloc,12),struct.unpack_from('>5I',old_reloc)),before,old_reloc,base,
                address_constants=(0x808742A8,))
            n=relocate_verified_data(Image(hand['ram'],len(data)+u32(reloc,12),struct.unpack_from('>5I',reloc)),data,reloc,base,
                address_constants=(0x808742A8,))
            self.assertEqual(n[:at]+n[at+4:],b[:at]+b[at+4:])
            self.assertEqual(u32(n,at),jump(symbols['af_carried_drop_stack'],link=True))
        # Every actual imported action has its retained complete donor function.
        self.assertEqual({r['symbol'] for r in a['donors']},{'mTG_1catch_proc','mTG_select_tag_decide_item_normal',
            'mHD_prepare_drop_paper','mHD_prepare_drop_wisp','mHD_drop_item2','mBD_move_Obey'})
        self.assertEqual(a['additional_resident_bytes'],0)
        from v3_furniture_capacity import checked
        broken=copy.deepcopy(self.report)
        allocation=broken['equipment_resources']['carried_items']['menu_allocations'][-1]
        # A later resize must start at the exact previous descriptor.
        bad=bytearray.fromhex(allocation['before']);bad[7]^=16;allocation['before']=bad.hex()
        with self.assertRaisesRegex(ValueError,'allocation chain'):checked(self.image,broken)

    def test_shared_rebasing_retains_interior_vertices_and_rejects_overruns(self):
        from v3_category_runtime import rebase_art
        d=self.report['equipment_resources']['carried_items'];p=d['paper']
        raw=(ROOT/d['prepared']/p['file']).read_bytes()
        row=dict(resources=p['resources'],compiled_models=p['models'])
        result,fixes=rebase_art(raw,row,PAPER)
        self.assertEqual(sha256(result),p['installed_sha256'])
        starts={r['native_offset'] for r in p['resources']}
        interior=[f for f in fixes if f['resource_kind']=='vertices' and f['before']&0xFFFFFF not in starts]
        self.assertEqual(len(interior),2)
        broken=bytearray(raw);f=interior[0];offset=f['before']&0xFFFFFF
        owner=next(r for r in p['resources'] if r['kind']=='vertices' and r['native_offset']<=offset<r['native_offset']+r['bytes'])
        struct.pack_into('>I',broken,f['offset'],0x6000000+owner['native_offset']+owner['bytes']-16)
        with self.assertRaisesRegex(ValueError,'vertex slice'):rebase_art(bytes(broken),row,PAPER)

    def test_ground_categories_keep_diary_and_cedar_distinct(self):
        image,r=self.image,self.report;base,prior=self.base,self.prior
        e=r['equipment_resources'];c=e['item_categories'];g=e['ground_categories']
        files=by_vrom(image);old=by_vrom(base);blob=files[BLOB].extract(image);data=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        self.assertEqual(data[c['map_offset']+16+17],44)
        mask=c['ground_bitmap'];self.assertEqual(sha256(data[mask['offset']:mask['offset']+16]),mask['sha256'])
        self.assertTrue({44,48,49,50}<=set(mask['categories']));self.assertNotIn(51,mask['categories'])
        for row in c['objects']:
            for t in c['tables']:
                self.assertEqual(u32(data,t['offset']+row['native_category']*4),(row['ram']&0x1FFFFFFF)+row['model_offsets'][t['role']])
        h=g['carried_prepare'];at=h['address']-e['ram'];self.assertEqual(data[at:at+8].hex(),h['after'])
        for row in g['owners']:
            self.assertEqual(files[row['vrom']].extract(image),old[row['vrom']].extract(base))
            cap=row['capacity'];self.assertLessEqual(cap['parts_offset']+52*len(mask['categories']),cap['resident_bytes'])
            expected=bytearray(old[row['reloc']].extract(base));struct.pack_into('>I',expected,12,cap['bss_bytes'])
            self.assertEqual(files[row['reloc']].extract(image),bytes(expected))
        self.assertEqual(e['scenery'],prior['equipment_resources']['scenery'])

    def test_sanitized_changed_shared_readers_and_ground_bitmap(self):
        d=self.report['equipment_resources']['carried_items']
        with tempfile.TemporaryDirectory(prefix='v3-carried-readers-') as temp:
            for name,flags,args in (
                ('v3_carried_items_test',[],[str(OUT/'carried-packet.bin'),str(TABLE-d['packet']['ram'])]),
                ('v3_ground_categories_test',['-DAF_V3_GROUND_CATEGORY_FLAGS=1'],[])):
                target=Path(temp)/name
                result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                    '-fsanitize=address,undefined','-fno-omit-frame-pointer',*flags,'tests/'+name+'.c','-o',str(target)],
                    cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                result=subprocess.run([str(target),*args],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr);print(result.stdout.strip())

class FoodTests(unittest.TestCase):
    """Current food consumer changes; do not replay the earlier menu fixture."""
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/os.environ.get('V3_CARRIED_FOOD','build/v3-carried-runtime-work-01/field-actions-01')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.base,cls.prior=inputs(cls.out/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.image),by_vrom(cls.base)

    def test_complete_food_tables_native_indices_and_unchanged_animation(self):
        from types import SimpleNamespace
        from npc_mail_show import relocate_verified_data
        e=self.report['equipment_resources'];d=e['carried_items'];food=d['eating'];p=d['packet']
        raw=self.image[p['physical']:p['physical']+p['bytes']]
        inventory=self.files[food['inventory_vrom']].extract(self.image)
        old=self.before[food['inventory_vrom']].extract(self.base)
        rel=self.files[food['inventory_reloc']].extract(self.image)
        old_rel=self.before[food['inventory_reloc']].extract(self.base)
        restored=bytearray(inventory);origin=food['inventory_ram']
        for patch in food['patches']:
            at=patch['address']-origin;self.assertEqual(u32(restored,at),patch['after'])
            struct.pack_into('>I',restored,at,patch['before'])
        self.assertEqual(restored,old)
        self.assertEqual(sha256(inventory),e['inventory_preview']['owner_sha256'])
        self.assertEqual(sha256(rel),e['inventory_preview']['relocation_sha256'])
        count=u32(old_rel,16);records=struct.unpack_from('>'+str(count)+'I',old_rel,20)
        self.assertEqual(struct.unpack_from('>'+str(count-4)+'I',rel,20),
            tuple(r for r in records if r not in food['removed_relocations']))
        self.assertEqual(rel[:16],old_rel[:16])
        for table in food['tables']:
            at=table['ram']-p['ram'];native=table['native']-origin
            values=struct.unpack_from('>9I',raw,at);original=struct.unpack_from('>8I',old,native)
            self.assertEqual(values[:7],original[:7]);self.assertEqual(values[8],original[7])
            self.assertEqual(values[7],table['model']);self.assertLess(values[7],0x800000)
            self.assertEqual(sha256(raw[at:at+36]),table['sha256'])
        self.assertEqual((food['coconut_index'],food['turnip_index']),(7,8))
        for address in (0x80200010,0x80348010):
            def relocated(data,reloc):
                sections=struct.unpack_from('>5I',reloc)
                return relocate_verified_data(SimpleNamespace(ram=origin,resident_bytes=sum(sections[:4]),
                    sections=sections),data,reloc,address)
            current,previous=relocated(inventory,rel),relocated(old,old_rel)
            allowed={r['address']-origin+i for r in food['patches'] for i in range(4)}
            self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(current,previous))))
            for table,pair in zip(food['tables'],((0x8087E918,0x8087E91C),(0x8087E954,0x8087E968))):
                hi,lo=(u32(current,p-origin) for p in pair);low=struct.unpack('>h',struct.pack('>H',lo&65535))[0]
                self.assertEqual(((hi&65535)<<16)+low,table['ram'])
        hand=d['actions']['hand'];data=bytearray(self.files[hand['vrom']].extract(self.image))
        patch=food['hand_patch'];at=patch['address']-hand['ram']
        self.assertEqual(u32(data,at),0x24190008);struct.pack_into('>I',data,at,patch['before'])
        self.assertEqual(data,self.before[hand['vrom']].extract(self.base))
        self.assertEqual(self.files[hand['reloc']].extract(self.image),self.before[hand['reloc']].extract(self.base))

    def test_packet_bounds_artwork_save_retention_and_startup(self):
        from aflib import apply_ups
        e=self.report['equipment_resources'];d=e['carried_items'];p=d['packet'];food=d['eating']
        old=self.prior['equipment_resources']['carried_items'];op=old['packet']
        raw=self.image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual((p['physical'],p['bytes'],p['ram']),(op['physical'],op['bytes'],op['ram']))
        restored=bytearray(raw);at=food['ram']-p['ram'];restored[at:at+food['bytes']]=bytes(food['bytes'])
        self.assertEqual(restored,self.base[op['physical']:op['physical']+op['bytes']])
        self.assertEqual(sha256(raw),p['sha256']);self.assertEqual(sha256(raw[RAM-p['ram']:]),d['sha256'])
        self.assertEqual(raw[-16:],GUARD);self.assertLessEqual(food['ram']+food['bytes'],TABLE)
        for key in ('artwork','paper','storage','rows','ready_mask','selected_mask'):
            self.assertEqual(d[key],old[key])
        self.assertEqual(e['scenery'],self.prior['equipment_resources']['scenery'])
        self.assertEqual(self.report['save_codec'],self.prior['save_codec'])
        refresh=self.report['shared_runtime_refresh']
        self.assertFalse(refresh['saved_format_changed']);self.assertFalse(refresh['saved_profile_changed'])
        self.assertEqual(refresh['additional_resident_bytes'],0);self.assertEqual(refresh['additional_menu_bytes'],0)
        blob=self.files[BLOB].extract(self.image);boot=e['surface_bootstrap']['code']
        at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        for i in range(boot['packet_count']):
            ram,vrom,n,crc=struct.unpack_from('>4I',blob,at+i*boot['packet_stride'])
            if vrom&0x80000000:data=self.image[vrom&0x7FFFFFFF:(vrom&0x7FFFFFFF)+n]
            else:
                f=next(f for f in self.files.values() if f.vstart<=vrom<vrom+n<=f.vend)
                data=f.extract(self.image)[vrom-f.vstart:vrom-f.vstart+n]
            self.assertEqual(zlib.crc32(data),u32(blob,e['blob_offset']+crc-e['ram']))
        physical.verify(self.image,self.report['physical_resources'])
        for path,digest in d['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_complete_source_bindings_and_changed_consumer_rejection(self):
        from v3_carried_runtime import food_tables
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        d=self.report['equipment_resources']['carried_items'];food=d['eating']
        art=next(r for r in d['artwork'] if r['source_category']==28)
        owner=self.before[food['inventory_vrom']].extract(self.base)
        rel=self.before[food['inventory_reloc']].extract(self.base)
        data,new_rel,tables,receipt=food_tables(source,owner,rel,art,food['ram'])
        self.assertEqual(data,self.files[food['inventory_vrom']].extract(self.image))
        self.assertEqual(new_rel,self.files[food['inventory_reloc']].extract(self.image))
        for key,value in receipt.items():self.assertEqual(json.loads(json.dumps(value)),food[key])
        self.assertEqual(sha256(tables),food['sha256'])
        damaged=copy.copy(source);damaged.rel=bytearray(source.rel)
        damaged.rel[source.sections[1][0]+0x2725C0]^=1
        with self.assertRaisesRegex(ValueError,'source eating'):food_tables(damaged,owner,rel,art,food['ram'])
        damaged=bytearray(owner);damaged[0x8087E628-food['inventory_ram']]^=1
        with self.assertRaisesRegex(ValueError,'native food'):food_tables(source,damaged,rel,art,food['ram'])
        damaged=copy.copy(source);damaged.relocations=dict(source.relocations)
        damaged.relocations[0x80118+28]=(1,True,5,8989856)
        with self.assertRaisesRegex(ValueError,'donor food'):food_tables(damaged,owner,rel,art,food['ram'])


if __name__=='__main__':unittest.main()
