"""Current scrolling renderer integration; no replay of unchanged cartridges."""
import copy
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_equipment_runtime import RAM as EQUIPMENT_RAM
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source,prepare,metadata,identity_rows
from v3_import_storage import ROWS,TABLE_END,ITEMS,slot
import v3_furniture_scroll as scroll
import v3_room_rig_runtime as room
import v3_optional_composition as composer

OUT=ROOT/'build/v3-scrolling-materials-runtime-04'
ART=ROOT/'build/v3-scrolling-materials-prepared-03'


class ScrollingLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import os
        cls.out=ROOT/os.environ.get('V3_SCROLL_LIFECYCLE_BUILD','build/v3-scrolling-loop-imports-01/cartridge')
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.equipment=cls.report['equipment_resources']
        cls.runtime=cls.equipment['room_rigs']['scrolling']
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_actual_callbacks_under_memory_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-scroll-lifecycle-') as temporary:
            binary=Path(temporary)/'test';table=Path(temporary)/'table'
            table.write_bytes(scroll.encode_lifecycles(self.runtime['lifecycle_rows']))
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_room_scroll_lifecycle_test.c'),'-o',str(binary)],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary),str(table)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('bounded rejection pass',result.stdout)

    def test_complete_source_and_installed_callback_bindings(self):
        from aflib import CODE_VROM
        from v3_sound_programs import checked_furniture_loops
        contracts,proof=checked_furniture_loops(self.image,by_vrom(self.image)[CODE_VROM].extract(self.image),
                                               self.equipment,self.source)
        self.assertEqual(set(contracts),{'1FE4','1FE8','31A0','3368'})
        self.assertTrue(proof['complete_programs_and_instruments'])
        rows=scroll.checked_runtime(self.equipment,self.blob)
        life=self.runtime['lifecycle_rows'];self.assertEqual(len(life),4)
        for key,contract in contracts.items():
            descriptor=prepare(self.source,int(key,16))[0]
            verified=scroll.checked_lifecycle(self.source,descriptor,rows[key],self.runtime,contracts)
            self.assertEqual(verified,json.loads(json.dumps(contract)))
            self.assertEqual(scroll.profile_lifecycle(descriptor,verified),not contract['start_disabled'])
        self.assertLessEqual(self.runtime['code']['bytes'],4096)
        self.assertLessEqual(self.equipment['room_rigs']['bootstrap']['bytes'],room.TABLE-room.RAM)
        self.assertEqual(scroll.tables(self.runtime),self.blob[self.runtime['packet']['blob_offset']+4096:
                                                             self.runtime['packet']['blob_offset']+8192])
        for field,value in (('mode',3),('sound',96),('flags',2),('on',128),('step',256)):
            bad=copy.deepcopy(life);bad[0][field]=value
            with self.assertRaises(ValueError):scroll.encode_lifecycles(bad)
        bad=copy.deepcopy(self.equipment)
        bad['room_rigs']['scrolling']['rows'][-1]['lifecycle']['constants']['step']['value']+=1
        with self.assertRaisesRegex(ValueError,'lifecycle source binding'):
            scroll.checked_runtime(bad,self.blob)
        for key in contracts:
            descriptor=prepare(self.source,int(key,16))[0]
            forged=copy.deepcopy(contracts[key]);forged['functions']['move']['sha256']='0'*64
            self.assertFalse(scroll.profile_lifecycle(descriptor,forged))
        # Also verifies retained ordinary profiles against the new full vtable.
        room.bind_profiles(self.source,self.image,self.report)

    def test_current_selection_and_translation_only_composition(self):
        import v3_browser_composition as browser
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json')
            catalogue=composer.catalogue(self.image,self.report)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalogue,composer.resolve(catalogue,[]))[0]),
                             self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalogue,composer.resolve(catalogue,list(catalogue)))[0],self.image)
            self.assertEqual(self.report['save_codec']['format_version'],3)
            plan=browser.rules(self.image,self.report);self.assertFalse(plan['web_patcher_enabled'])
            self.assertEqual(len(catalogue),140)
            cases=[]
            for label,requested in (('empty',[]),('all',list(catalogue)),
                    ('legacy-fade',['GAFE01-r0/item/1FE4']),('positioned-loop',['GAFE01-r0/item/31A0'])):
                selection=composer.resolve(catalogue,requested)
                image,_,blob=composer.compose(self.image,self.report,catalogue,selection)
                if requested and label!='all':
                    for item in (0x3C34,0x3C38,0x31A0):
                        enabled=item==(0x3C34 if label=='legacy-fade' else 0x31A0);i=slot(item)
                        self.assertEqual(struct.unpack_from('>I',blob,ROWS+i*80+4)[0],enabled)
                        self.assertEqual(bool(blob[0x40+i//8]&(1<<(i&7))),enabled)
                cases.append(dict(name=label,requested=requested,selection=selection,sha256=sha256(image)))
            with tempfile.TemporaryDirectory(prefix='v3-scroll-loop-composition-') as directory:
                path=Path(directory)/'fixture.json'
                path.write_bytes(composer.canonical(dict(plan=plan,cases=cases,
                    base=str(self.out/'animal-forest-v3-asset-loader.z64'),stable=str(composer.stable_reference(self.report)[0]))))
                result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(path)],
                                      check=True,capture_output=True,text=True,timeout=60)
                self.assertEqual(len(json.loads(result.stdout)['passed']),4)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin

    def test_complete_ordinary_profiles_preserve_donor_destination_and_assets(self):
        rows=self.report['automatic_furniture']['imports']
        self.assertEqual({r['item_id'] for r in rows},{'3C34','3C38','31A0'})
        bindings=room.bind_profiles(self.source,self.image,self.report)
        self.assertEqual(len(bindings),31)
        self.assertEqual(len(self.report['staged_furniture']['rows']),27)
        installed=scroll.checked_runtime(self.equipment,self.blob)
        identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
        assets=json.loads((ART/'art.json').read_bytes())
        from v3_registry import furniture_source
        from v3_furniture_install import profile
        for r in rows:
            donor,index=furniture_source(r);key=f'{donor:04X}'
            original=next(a for a in assets['objects'] if a['item_id']==key)
            binding=installed[key]
            self.assertTrue(binding['parent_selectable']);self.assertTrue(binding['profile_installed'])
            vrom=int(r['object_vrom'],16)
            self.assertEqual(vrom,binding['vrom'])
            self.assertEqual(self.blob[binding['blob_offset']:binding['blob_offset']+binding['bytes']],
                             (ART/original['object_file']).read_bytes())
            self.assertEqual(r['price'],struct.unpack_from('>H',self.source.raw('ftr_price_table'),index*2)[0])
            row=metadata(self.source,donor,prepare(self.source,donor)[0],identities[donor])
            self.assertEqual(row['room_lifecycle'],r['room_lifecycle'])
            self.assertEqual(row['donor_list'],'ftr_listKamakura' if donor==0x31A0 else 'ftr_listJonason')
            self.assertFalse(row['catalogue_orderable'])
            self.assertEqual(profile(r,vrom,limit=0x2800000),bytes.fromhex(bindings[key]['profile_hex']))
        for key in ('3368','33A0'):
            self.assertFalse(installed[key]['profile_installed'])
            with self.assertRaisesRegex(ValueError,'Scrolling artwork'):
                metadata(self.source,int(key,16),prepare(self.source,int(key,16))[0],identities[int(key,16)])
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (self.out/'asset-loader.ups').read_bytes()),self.image)


class ScrollingProfileIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.out=ROOT/'build/v3-draw-only-scrolling-imports-01/cartridge'
        cls.image,cls.report=inputs(cls.out/'build-lock.json')
        cls.stage,cls.staged=inputs(ROOT/'build/v3-draw-only-scrolling-profiles-01/build-lock.json')
        cls.base,cls.prior=inputs(ROOT/'build/v3-draw-only-scrolling-profiles-01/base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image)
        cls.intermediate=by_vrom(cls.stage)[BLOB].extract(cls.stage)
        cls.old=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_profiles_and_promotion_reuse_assets_and_runtime(self):
        rows=[r for r in self.staged['staged_furniture']['rows'] if r['category']==scroll.CATEGORY]
        self.assertEqual({r['item_id'] for r in rows},{'30E4','3258'})
        self.assertEqual(len(self.staged['staged_furniture']['rows']),28)
        self.assertEqual(len(self.report['staged_furniture']['rows']),27)
        self.assertEqual([r['item_id'] for r in self.report['automatic_furniture']['imports']],['3258'])
        art=json.loads((self.out.parent/'assets/art.json').read_bytes())
        self.assertEqual(art['batch'],dict(objects=1,reused=1,compiled=0,compiler_containers=0))
        e=self.report['equipment_resources'];old=self.prior['equipment_resources']
        for key in ('bytes','sha256','furniture_audio','scenery'):self.assertEqual(e[key],old[key])
        self.assertEqual(self.report['furniture']['bank_pool'],self.prior['furniture']['bank_pool'])
        for packet in (e['room_rigs']['packet'],e['room_rigs']['scrolling']['packet']):
            at,n=packet['blob_offset'],packet['bytes']
            self.assertEqual(self.blob[at:at+n],self.old[at:at+n])
        expected=bytearray(self.old[ROWS:TABLE_END])
        for row in rows:
            i=slot(int(row['item_id'],16));at=row['object_vrom']-BLOB;n=row['object_bytes']
            self.assertTrue(row['reused_asset']);self.assertEqual(self.blob[at:at+n],self.old[at:at+n])
            staged=self.intermediate[ROWS+i*80:ROWS+(i+1)*80]
            current=self.blob[ROWS+i*80:ROWS+(i+1)*80]
            enabled=row['item_id']=='3258'
            self.assertEqual(staged[:8],struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),0))
            self.assertEqual(current[:8],struct.pack('>HHI',row['runtime_index'],int(row['item_id'],16),enabled))
            self.assertEqual(current[8:],staged[8:]);self.assertEqual(current[24:56],bytes(32))
            self.assertEqual(struct.unpack_from('>I',current,72)[0],scroll.VTABLE)
            item=self.blob[ITEMS+i*32:ITEMS+(i+1)*32]
            self.assertEqual(item[8:24],row['name'].encode().ljust(16,b' '));self.assertEqual(item[7],enabled)
            expected[i*80:(i+1)*80]=current;expected[ITEMS-ROWS+i*32:ITEMS-ROWS+(i+1)*32]=item
        self.assertEqual(self.blob[ROWS:TABLE_END],expected)
        selected=bytearray.fromhex(self.prior['save_runtime']['profile_hex']);i=slot(0x3258)
        selected[32+i//8]|=1<<(i&7)
        self.assertEqual(self.report['save_runtime']['profile_hex'],selected.hex())
        self.assertEqual(self.report['save_codec']['format_version'],3)

    def test_source_lifecycle_and_acquisition_gates_remain_independent(self):
        bindings=room.bind_profiles(self.source,self.image,self.report)
        self.assertEqual(len(bindings),28)
        identities=identity_rows(ROOT/'build/item-identity-megasheet.xlsx')
        ready=[]
        for row in json.loads((ART/'art.json').read_bytes())['objects']:
            item=int(row['item_id'],16);descriptor=prepare(self.source,item)[0]
            if scroll.draw_only_lifecycle(descriptor,self.source) is not None:ready.append(row['item_id'])
            else:
                with self.assertRaisesRegex(ValueError,'Scrolling artwork'):metadata(self.source,item,descriptor,None)
        self.assertEqual(ready,['30E4','3258'])
        with self.assertRaisesRegex(ValueError,'^acquisition needs an adapter:'):
            metadata(self.source,0x30E4,prepare(self.source,0x30E4)[0],identities[0x30E4])
        pool=metadata(self.source,0x3258,prepare(self.source,0x3258)[0],identities[0x3258])
        self.assertEqual(pool['donor_list'],'ftr_listEvent');self.assertTrue(pool['catalogue_orderable'])
        bad=copy.deepcopy(self.report)
        next(r for r in bad['equipment_resources']['room_rigs']['scrolling']['rows'] if r['source_item_id']=='3258')['lifecycle_installed']=False
        with self.assertRaisesRegex(ValueError,'Incomplete installed scrolling lifecycle'):
            room.bind_profiles(self.source,self.image,bad)
        descriptor=prepare(self.source,0x3258)[0];move=descriptor['callback_adapter']['functions']['move']
        changed=copy.copy(self.source);changed.rel=bytearray(self.source.rel)
        changed.rel[self.source.sections[1][0]+move['offset']+3]^=4
        with self.assertRaisesRegex(ValueError,'Changed source empty furniture lifecycle'):
            scroll.draw_only_lifecycle(descriptor,changed)
        damaged=bytearray(self.blob);packet=self.report['equipment_resources']['room_rigs']['scrolling']['packet']
        damaged[packet['blob_offset']+4096+20]^=1
        with self.assertRaisesRegex(ValueError,'Changed complete scrolling renderer'):
            scroll.checked_runtime(self.report['equipment_resources'],damaged)
        room.bind_profiles(self.source,self.image,self.report)

    def test_optional_browser_composition_and_translation_only_remain_exact(self):
        import v3_browser_composition as browser
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.out/'build-lock.json')
            catalogue=composer.catalogue(self.image,self.report);plan=browser.rules(self.image,self.report)
            self.assertEqual(len(catalogue),137);self.assertFalse(plan['web_patcher_enabled'])
            self.assertNotIn('GAFE01-r0/item/30E4',catalogue)
            cases=[]
            for label,requested in (('empty',[]),('all',list(catalogue)),
                                    ('new-scroll',['GAFE01-r0/item/3258']),('existing-villager',['GAFE01-r0/villager/00EB'])):
                selected=composer.resolve(catalogue,requested)
                image,_,blob=composer.compose(self.image,self.report,catalogue,selected)
                if label=='empty':self.assertEqual(sha256(image),self.report['translation_baseline']['sha256'])
                elif label=='all':self.assertEqual(image,self.image)
                else:
                    i=slot(0x3258);enabled=label=='new-scroll'
                    self.assertEqual(struct.unpack_from('>I',blob,ROWS+i*80+4)[0],enabled)
                    self.assertEqual(bool(blob[0x40+i//8]&(1<<(i&7))),enabled)
                    self.assertFalse(blob[0x40+slot(0x30E4)//8]&(1<<(slot(0x30E4)&7)))
                cases.append(dict(name=label,requested=requested,selection=selected,sha256=sha256(image)))
            with tempfile.TemporaryDirectory(prefix='v3-scroll-composition-') as directory:
                path=Path(directory)/'fixture.json'
                path.write_bytes(composer.canonical(dict(plan=plan,cases=cases,
                    base=str(self.out/'animal-forest-v3-asset-loader.z64'),stable=str(composer.stable_reference(self.report)[0]))))
                result=subprocess.run(['node','--experimental-global-webcrypto',str(ROOT/'tests/v3_browser_equivalence.mjs'),str(path)],
                                      check=True,capture_output=True,text=True,timeout=60)
                self.assertEqual(len(json.loads(result.stdout)['passed']),4)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (self.out/'asset-loader.ups').read_bytes()),self.image)

    def test_subsequent_resource_batches_retain_completed_profiles(self):
        from aflib import CODE_VROM
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        blob=bytearray(self.blob);core=by_vrom(self.image)[CODE_VROM].extract(self.image)
        # Every object is already installed. Reach the empty-new-batch guard
        # after checking both staged and active profiles, without recompiling
        # artwork/runtime or downgrading either lifecycle back to "pending".
        with self.assertRaisesRegex(ValueError,'^Empty scrolling material batch$'):
            scroll.install(self.image,self.report,blob,core,original,self.out,[ART])
        self.assertEqual(blob,self.blob)


class ScrollingRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.report=inputs(OUT/'build-lock.json')
        cls.base,cls.prior=inputs(OUT/'base-lock.json')
        cls.blob=by_vrom(cls.image)[BLOB].extract(cls.image);cls.old=by_vrom(cls.base)[BLOB].extract(cls.base)
        cls.runtime=cls.report['equipment_resources']['room_rigs'];cls.scroll=cls.runtime['scrolling']
        cls.art=json.loads((ART/'art.json').read_bytes())
        cls.source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())

    def test_complete_assets_records_packet_and_additive_destinations(self):
        self.assertEqual(len(self.scroll['rows']),7)
        self.assertEqual(sum(r['bytes'] for r in self.scroll['rows']),38336)
        self.assertEqual(self.scroll['batch'],dict(added=2,retained=5,compiled_artwork=0))
        for row in self.scroll['rows']:
            art=next(r for r in self.art['objects'] if r['item_id']==row['source_item_id'])
            expected=json.loads(json.dumps(scroll.runtime_record(art)))
            self.assertEqual({k:v for k,v in row.items() if k not in ('blob_offset','vrom','source')},
                             {k:v for k,v in expected.items() if k!='source'})
            self.assertEqual({k:v for k,v in row['source'].items() if k!='reused_artwork'},
                             {k:v for k,v in expected['source'].items() if k!='reused_artwork'})
            self.assertEqual(self.blob[row['blob_offset']:row['blob_offset']+row['bytes']],(ART/art['object_file']).read_bytes())
            self.assertTrue(row['renderer_installed'])
            self.assertFalse(any(row[k] for k in ('lifecycle_installed','profile_installed','parent_selectable')))
        mapped={r['source_item_id']:(r['item_id'],r['runtime_index']) for r in self.scroll['rows']}
        self.assertEqual(mapped['1FE4'],('3C34',1805));self.assertEqual(mapped['1FE8'],('3C38',1806))
        sheet=identity_rows(ROOT/'build/item-identity-megasheet.xlsx',include_unmapped_legacy=True)
        for item in (0x1FE4,0x1FE8):
            self.assertTrue(all(sheet[item][1][k]=='-' for k in ('C','H','CG','CJ')))
            key=f'furniture:{(item-0x1000)//4:04x}'
            for path in ('translations/item_reference_matches.json','translations/item_resolved_matches.json'):
                self.assertFalse(any(r.get('reference_id','').lower()==key for r in json.loads((ROOT/path).read_bytes())))
        packet=self.scroll['packet'];raw=self.blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
        code=(OUT/'room_scroll/code.bin').read_bytes();table=scroll.encode(self.scroll['rows'])
        self.assertEqual(raw,code.ljust(4096,b'\0')+table.ljust(4096,b'\0'))
        self.assertEqual(sha256(raw),packet['sha256']);self.assertLessEqual(len(code),4096)
        self.assertEqual(packet['ram'],room.PACKET_RAM+room.PACKET_BYTES)
        self.assertLessEqual(packet['ram']+packet['bytes'],self.report['furniture']['bank_pool']['start'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)
        e=self.report['equipment_resources'];module=self.blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        self.assertEqual(module[scroll.VTABLE-EQUIPMENT_RAM:scroll.VTABLE-EQUIPMENT_RAM+20],
            struct.pack('>5I',0,0,self.runtime['bootstrap']['symbols']['af_v3_room_boot_scroll_dw'],0,0))
        self.assertEqual(module[room.TABLE-EQUIPMENT_RAM:room.TABLE-EQUIPMENT_RAM+8],bytes(8))

    def test_actual_renderer_under_address_and_undefined_sanitizers(self):
        with tempfile.TemporaryDirectory(prefix='v3-room-scroll-') as temporary:
            binary=Path(temporary)/'test';table=Path(temporary)/'table'
            table.write_bytes(scroll.encode(self.scroll['rows']))
            result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',str(ROOT/'tests/v3_room_scroll_test.c'),
                '-o',str(binary)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            result=subprocess.run([str(binary),str(table)],capture_output=True,text=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertIn('bounded rejection pass',result.stdout)

    def test_bad_records_and_incomplete_lifecycles_remain_rejected(self):
        rows=self.scroll['rows']
        for key,value in (('bytes',9217),('segment',7),('colour_mode',5),('model_offsets',[65528]),
                          ('dimensions',[[0,0]]),('rates',[[17,0]]),('state_offset',0x834),
                          ('opaque_models',0),('debug_offset',1),('colour2_a',0xFB000000)):
            bad=copy.deepcopy(rows);bad[0][key]=value
            with self.assertRaises(ValueError):scroll.encode(bad)
        with self.assertRaises(ValueError):scroll.encode(rows+rows)
        with self.assertRaises(ValueError):scroll.encode(list(reversed(rows)))
        for row in rows:
            p=prepare(self.source,int(row['source_item_id'],16))[0];p['callback_adapter']['runtime_installed']=True
            with self.assertRaisesRegex(ValueError,'Scrolling artwork'):metadata(self.source,int(row['source_item_id'],16),p,None)
            i=slot(int(row['item_id'],16))
            self.assertEqual(self.blob[ROWS+i*80:ROWS+(i+1)*80],bytes(80))
            self.assertEqual(self.blob[ITEMS+i*32:ITEMS+(i+1)*32],bytes(32))
        self.assertEqual(len(room.bind_profiles(self.source,self.image,self.report)),26)
        extended={r['source_item_id']:r for r in rows}
        self.assertEqual((extended['3258']['opaque_models'],extended['3258']['colour_mode'],
                          extended['3258']['debug_offset']),(1,4,0x8B2))
        self.assertEqual((extended['33A0']['opaque_models'],extended['33A0']['colour_mode']),(1,3))
        for source in ('3258','33A0'):
            invalid=copy.deepcopy(extended[source]);invalid['debug_offset']=0x1C94
            with self.assertRaises(ValueError):scroll.encode([invalid])

    def test_existing_runtime_saves_and_optional_composition_are_retained(self):
        prior=self.prior['equipment_resources'];current=self.report['equipment_resources']
        for key in ('rows','sound_rows','material_rows','code','packet'):
            self.assertEqual(self.runtime[key],prior['room_rigs'][key])
        packet=self.runtime['packet'];at=packet['blob_offset'];n=packet['bytes']
        self.assertEqual(self.blob[at:at+n],self.old[at:at+n])
        self.assertEqual(self.blob[ROWS:TABLE_END],self.old[ROWS:TABLE_END])
        for old in prior['room_rigs']['scrolling']['rows']:
            new=next(r for r in self.scroll['rows'] if r['source_item_id']==old['source_item_id'])
            for key,value in old.items():self.assertEqual(new[key],value)
            self.assertEqual(self.blob[new['blob_offset']:new['blob_offset']+new['bytes']],
                             self.old[old['blob_offset']:old['blob_offset']+old['bytes']])
        self.assertEqual(self.scroll['packet']['blob_offset'],prior['room_rigs']['scrolling']['packet']['blob_offset'])
        for key in ('furniture_audio','scenery','bytes'):self.assertEqual(current[key],prior[key])
        for key in ('staged_furniture','save_runtime'):self.assertEqual(self.report[key],self.prior[key])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),136)
            self.assertFalse({r['source']['id'] for r in self.scroll['rows']}&set(catalog))
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                             self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
                                  (OUT/'asset-loader.ups').read_bytes()),self.image)
