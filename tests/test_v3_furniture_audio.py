"""Shared furniture audio conversion; no historic cartridge or audible replay."""
import copy
import json
from pathlib import Path
import struct
import sys
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_furniture_install import inputs
from v3_villager_audio import instrument
import v3_sound_programs as sound


def font_fixture():
    # Synthetic complete ADPCM instrument with shared low/middle/high samples.
    bank=bytearray(0xD0);struct.pack_into('>I',bank,8,0x10)
    bank[0x11:0x14]=bytes((12,100,240));struct.pack_into('>I',bank,0x14,0x30)
    for field in (8,16,24):struct.pack_into('>2I',bank,0x10+field,0x40,0x3F800000)
    struct.pack_into('>6h',bank,0x30,1,24000,20,12000,-1,0)
    struct.pack_into('>4I',bank,0x40,32,0,0x50,0x60)
    struct.pack_into('>4I',bank,0x50,0,56,0,0)
    struct.pack_into('>2I',bank,0x60,2,2)
    bank[0x68:0xA8]=bytes(range(64))
    return bytes(bank),bytes(range(32))


class SharedFormatTests(unittest.TestCase):
    def test_trigger_keeps_every_timed_note_and_rejects_unaccounted_commands(self):
        raw=bytearray.fromhex('eb0102880007ff671a6e671a6e671a6eff')
        desc=sound.trigger_program(raw,0,len(raw))
        self.assertEqual(desc['duration'],78);self.assertEqual(len(desc['events']),3)
        bound=sound.bind_trigger(raw,desc,0x3201,2,19)
        self.assertEqual(bound[7:],raw[7:]);self.assertEqual(bound[:4],bytes((235,2,19,136)))
        self.assertEqual(struct.unpack_from('>H',bound,4)[0],0x3208)
        for at,value in ((0,0),(1,4),(2,126),(5,8),(6,0),(7,0xC0),(8,0),(9,128),(16,0)):
            bad=raw.copy();bad[at]=value
            with self.subTest(at=at),self.assertRaises(ValueError):sound.trigger_program(bad,0,len(bad))
        with self.assertRaises(ValueError):sound.trigger_program(raw+b'X',0,len(raw)+1)
        for n in range(len(raw)):
            with self.assertRaises(ValueError):sound.trigger_program(raw[:n],0,n)

    def test_font_growth_relocates_all_ranges_and_deduplicates_complete_resources(self):
        bank,wave=font_fixture();old=instrument(bank,wave,0,1,extended=True)
        changed=bytearray(bank);changed[0x13]=220
        donors=[dict(bank_id=5,instrument=0,instrument_count=1,bank=bank,wave=wave),
                dict(bank_id=7,instrument=0,instrument_count=1,bank=bytes(changed),wave=wave),
                dict(bank_id=9,instrument=0,instrument_count=1,bank=bytes(changed),wave=wave)]
        new,waves,receipt=sound.extend_instruments(bank,wave,1,donors)
        self.assertEqual(receipt['instrument_count'],2)
        self.assertEqual([r['native_instrument'] for r in receipt['imports']],[0,1,1])
        self.assertEqual(waves,wave)
        self.assertEqual(instrument(new,waves,0,2,extended=True),old)
        self.assertEqual(instrument(new,waves,1,2,extended=True),instrument(changed,wave,0,1,extended=True))
        self.assertEqual(sound.extend_instruments(bank,wave,1,list(reversed(donors))),(new,waves,receipt))
        # More entries force a table shift; every existing bank pointer follows.
        donors=[]
        for i in range(8):
            data=bytearray(bank);data[0x13]=200+i
            donors.append(dict(bank_id=i,instrument=0,instrument_count=1,bank=data,wave=wave))
        new,waves,receipt=sound.extend_instruments(bank,wave,1,donors)
        self.assertEqual(receipt['original_data_shift'],32)
        self.assertEqual(instrument(new,waves,0,9,extended=True),old)
        self.assertEqual(new[0x10+32:0x14+32],bank[0x10:0x14])
        self.assertEqual(waves,wave)
        for data,count,ds in ((bank,1,[]),(bank,0,donors),(bank,1,donors+[donors[0]])):
            with self.assertRaises(ValueError):sound.extend_instruments(data,wave,count,ds)
        bad=bytearray(bank);struct.pack_into('>I',bad,0x14,8)
        with self.assertRaises(ValueError):sound.extend_instruments(bad,wave,1,donors)


class IncrementalBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=ROOT/'build/v3-material-trigger-runtime-04'
        cls.image,cls.report=inputs(cls.path/'build-lock.json')
        cls.base,cls.prior=inputs(cls.path/'base-lock.json')
        cls.code=by_vrom(cls.image)[CODE_VROM].extract(cls.image)
        cls.old_code=by_vrom(cls.base)[CODE_VROM].extract(cls.base)
        cls.audio=cls.report['equipment_resources']['furniture_audio']
        cls.prepared_path=ROOT/'build/v3-material-trigger-audio-prepared-02'
        cls.prepared=json.loads((cls.prepared_path/'audio.json').read_bytes())

    def test_shared_callback_discovery_is_nonmutating_and_all_dependencies_remain_complete(self):
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        new={r['item_id'] for r in self.prepared['furniture']}
        self.assertEqual(new,{'3314','3318','332C'})
        for row in self.audio['furniture']:
            profile=source.profile(int(row['item_id'],16));before=copy.deepcopy(profile)
            trigger=sound.furniture_trigger(source,profile)
            self.assertEqual(before,profile)
            self.assertEqual(json.loads(json.dumps(profile['callback_adapter'])),row['callback'])
            if row['item_id'] in new:self.assertEqual(json.loads(json.dumps(trigger)),row['trigger'])
        for item in (0x1FD8,0x3298,0x331C):self.assertIsNone(sound.furniture_trigger(source,source.profile(item)))
        profile=source.profile(0x3314);changed=copy.copy(source);changed.rel=bytearray(source.rel)
        changed.rel[source.sections[1][0]+profile['callback_adapter']['functions']['move']['offset']]^=1
        with self.assertRaises(ValueError):sound.furniture_trigger(changed,profile)
        self.assertEqual(self.audio['layout']['native_instrument_count'],79)
        self.assertEqual(self.audio['layout']['instrument_count'],82)
        old_bank,_,_=sound.installed_resource(self.base,self.old_code,'bank',140)
        old_wave,_,_=sound.installed_resource(self.base,self.old_code,'wave',5)
        bank,_,_=sound.installed_resource(self.image,self.code,'bank',140)
        wave,_,_=sound.installed_resource(self.image,self.code,'wave',5)
        self.assertEqual(bank,(self.prepared_path/'font.bin').read_bytes())
        self.assertEqual(wave,(self.prepared_path/'wave.bin').read_bytes())
        self.assertEqual(wave[:len(old_wave)],old_wave)
        for i in range(79):
            self.assertEqual(instrument(old_bank,old_wave,i,79,extended=True),instrument(bank,wave,i,82,extended=True))
        for row in self.audio['layout']['imports']:
            self.assertEqual(instrument(bank,wave,row['native_instrument'],82,extended=True),row['identity'])

    def test_incremental_dispatch_preserves_prior_ids_priorities_and_reuses_existing_programs(self):
        old=self.prior['equipment_resources']['furniture_audio'];a=self.audio
        self.assertEqual(len(a['programs']),8);self.assertEqual(len(a['furniture']),8)
        self.assertEqual(a['tables'],old['tables'])
        rows={r['source_sound_word']:r for r in a['programs']}
        sequence,_,_=sound.installed_resource(self.image,self.code,'seq',199)
        original,_,_=sound.installed_resource(self.base,self.old_code,'seq',199)
        restored=bytearray(sequence[:len(original)])
        priority=self.code[0x80113B84-CODE_RAM:0x80113C04-CODE_RAM]
        self.assertEqual(priority,self.old_code[0x80113B84-CODE_RAM:0x80113C04-CODE_RAM])
        for row in old['programs']:
            self.assertEqual(rows[row['source_sound_word']],row)
            self.assertEqual(sequence[row['offset']:row['offset']+row['bytes']],original[row['offset']:row['offset']+row['bytes']])
        for row in a['programs']:
            word=row['native_sound_word'];group,index=(word&0x7FFF)>>8,word&255
            table=next(t for t in a['tables'] if t['group']==group)
            at=table['offset']+index*2
            self.assertEqual(struct.unpack_from('>H',sequence,at)[0],row['offset'])
            self.assertEqual(priority[index],row['trigger_priority'])
            desc=sound.trigger_program(sequence,row['offset'],row['offset']+row['bytes'])
            for key in ('events','duration','envelope_bytes','decay'):
                self.assertEqual(desc[key],row['source_program'][key])
            if row['source_sound_word'] not in {v['source_sound_word'] for v in old['programs']}:
                restored[at:at+2]=original[at:at+2]
        self.assertEqual(restored,original)
        dol,_=sound.read_audio_donor(ROOT/'local/gamecube/Animal Crossing (USA, Canada).ciso')
        fragments={r['fragment_file']:(self.prepared_path/r['fragment_file']).read_bytes() for r in self.prepared['programs']}
        same,reused,tables=sound.register_triggers(sequence,self.prepared['programs'],fragments,
            {r['group']:r['previous_count'] for r in a['tables']},priority,dol.read(0x800A9A90,128),previous=a)
        self.assertEqual(same,sequence);self.assertEqual(tables,a['tables'])
        self.assertEqual(reused,[rows[r['sound_word']] for r in self.prepared['programs']])
        bad=bytearray(sequence);at=a['tables'][0]['offset'];bad[at+250]^=1
        with self.assertRaisesRegex(ValueError,'dispatch slot'):
            sound.register_triggers(bad,self.prepared['programs'],fragments,
                {r['group']:r['previous_count'] for r in a['tables']},priority,dol.read(0x800A9A90,128),previous=a)
        bad=copy.deepcopy(a);bad['programs'][0]['native_sound_word']^=1
        with self.assertRaises(ValueError):
            sound.register_triggers(sequence,self.prepared['programs'],fragments,
                {r['group']:r['previous_count'] for r in a['tables']},priority,dol.read(0x800A9A90,128),previous=bad)

    def test_whole_wave_relocation_preserves_every_group_and_old_allocation(self):
        from v3_furniture_install import relocate_resource_plan
        files,old=by_vrom(self.image),by_vrom(self.base);growth=self.audio['resource_growth'];v=growth['vrom']
        data=files[v].extract(self.image);before=old[v].extract(self.base)
        self.assertEqual(data[:len(before)],before)
        self.assertNotEqual(files[v].pstart,old[v].pstart)
        self.assertFalse(any(self.base[files[v].pstart:files[v].pstart+len(data)]))
        self.assertEqual(self.image[old[v].pstart:old[v].pstart+old[v].size],before)
        for index in range(6):
            new,header,physical=sound.installed_resource(self.image,self.code,'wave',index)
            prior,old_header,old_physical=sound.installed_resource(self.base,self.old_code,'wave',index)
            self.assertEqual(new[:len(prior)],prior)
            if index!=5:self.assertEqual(new,prior)
            if self.report['fire_sound']['wave_headers'][index]['external_resource_retained']:
                self.assertEqual(physical,old_physical)
            else:self.assertEqual(physical-old_physical,files[v].pstart-old[v].pstart)
            self.assertEqual(header[8:],old_header[8:])
        high,low=struct.unpack_from('>2I',self.code,0x800D28DC-CODE_RAM)
        self.assertEqual(((high&65535)<<16)+(low&65535)-(65536 if low&32768 else 0),files[v].pstart)
        for key in ('daily_growth','field_insects'):
            owner=self.prior['equipment_resources']['scenery'][key]
            for identity in (owner['vrom'],owner['reloc']):
                self.assertEqual(files[identity].extract(self.image),old[identity].extract(self.base))
                self.assertEqual(files[identity].pstart,old[identity].pstart)
        self.assertEqual(self.audio['audio_heap_growth'],0)
        self.assertEqual(sound.permanent_budget(self.code)['conservative_spare'],352)
        with self.assertRaises(ValueError):relocate_resource_plan(self.base,old,v,b'X'+data[1:],minimum_physical=0x3000000)
        with self.assertRaises(ValueError):relocate_resource_plan(self.base,old,v,data,minimum_physical=len(self.base)-16)

    def test_current_callback_bindings_and_optional_composition_remain_inactive(self):
        from aflib import apply_ups
        from v3_asset_loader import BLOB
        from v3_equipment_runtime import RAM as EQUIPMENT_RAM
        from v3_import_storage import ROWS,TABLE_END
        import v3_room_rig_runtime as room
        import v3_optional_composition as composer
        e=self.report['equipment_resources'];r=e['room_rigs'];old=self.prior['equipment_resources']['room_rigs']
        blob=by_vrom(self.image)[BLOB].extract(self.image);prior_blob=by_vrom(self.base)[BLOB].extract(self.base)
        self.assertEqual(r['code']['sha256'],old['code']['sha256'])
        self.assertEqual(r['rows'],old['rows'])
        self.assertEqual(blob[ROWS:TABLE_END],prior_blob[ROWS:TABLE_END])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['staged_furniture'],self.prior['staged_furniture'])
        self.assertEqual(self.report['shared_runtime_refresh']['additional_resident_bytes'],0)
        self.assertEqual(len(r['sound_rows']),8)
        self.assertEqual([v for v in r['sound_rows'] if v['source_item_id'] not in {'3314','3318','332C'}],old['sound_rows'])
        self.assertEqual({v['source_item_id'] for v in r['material_rows'] if v['lifecycle_installed']},{'3314','3318','332C'})
        for row in r['material_rows']:
            a=row['blob_offset'];self.assertEqual(blob[a:a+row['bytes']],prior_blob[a:a+row['bytes']])
            self.assertFalse(row['profile_installed']);self.assertFalse(row['parent_selectable'])
        module=blob[e['blob_offset']:e['blob_offset']+e['bytes']]
        self.assertEqual(struct.unpack_from('>5I',module,room.MATERIAL_VTABLE-EQUIPMENT_RAM),
            (0,r['bootstrap']['symbols']['af_v3_room_boot_sound_mv'],r['bootstrap']['symbols']['af_v3_room_boot_material_dw'],0,0))
        packet=r['packet'];raw=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
        self.assertEqual(raw[4096:],room.encode_packet(r['rows'],r['sound_rows'],r['material_rows']))
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.path/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),136)
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.path/'asset-loader.ups').read_bytes()),self.image)


class PreparedBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image,cls.base=inputs(ROOT/'build/v3-clock-category-runtime-02/build-lock.json')
        cls.words=[0x178,0x44E,0x8179,0x464,0x46A]
        cls.resources,cls.report=sound.prepare_triggers(cls.image,cls.base,cls.words)
        cls.code=by_vrom(cls.image)[CODE_VROM].extract(cls.image)

    def test_complete_five_sound_batch_preserves_existing_font_and_every_source_program(self):
        r=self.report;resources=self.resources
        self.assertEqual(r['layout']['native_instrument_count'],74)
        self.assertEqual(r['layout']['instrument_count'],79)
        self.assertEqual(r['layout']['original_data_shift'],32)
        self.assertEqual(len(r['programs']),5)
        self.assertEqual(sum(p['singleton'] for p in r['programs']),1)
        self.assertFalse(r['runtime_installed']);self.assertFalse(r['allocation_installed'])
        old_bank,_,_=sound.installed_resource(self.image,self.code,'bank',140)
        old_wave,_,_=sound.installed_resource(self.image,self.code,'wave',5)
        self.assertEqual(resources['wave'][:len(old_wave)],old_wave)
        for i in range(74):
            self.assertEqual(instrument(old_bank,old_wave,i,74,extended=True),
                             instrument(resources['font'],resources['wave'],i,79,extended=True))
        for row in r['layout']['imports']:
            self.assertEqual(instrument(resources['font'],resources['wave'],row['native_instrument'],79,extended=True),row['identity'])
        for row in r['programs']:
            desc=row['source_program'];raw=resources['fragments'][row['fragment_file']];at=row['fragment_origin']
            after=sound.trigger_program(bytes(at)+raw,at,at+len(raw))
            for key in ('events','duration','envelope_bytes','decay'):
                self.assertEqual(after[key],desc[key])
            original=bytearray(raw);original[1:3]=bytes((desc['selector'],desc['instrument']))
            for p in desc['pointers']:
                struct.pack_into('>H',original,p,struct.unpack_from('>H',raw,p)[0]-at+desc['origin'])
            self.assertEqual(sha256(original),desc['sha256'])
        self.assertEqual(next(p['source_program']['duration'] for p in r['programs'] if p['sound_word']==0x178),78)
        self.assertEqual(r['permanent_audio_before']['conservative_spare'],192)
        self.assertGreater(r['layout']['font_growth_bytes'],192)
        self.assertEqual(r['additional_font_allocation'],768)
        self.assertEqual(r['additional_capacity_for_font_only'],576)

    def test_prepared_sources_and_bounds_cannot_bypass_runtime_integration(self):
        for words in ([],[0x80000],[True],[0x600],[0x4FF]):
            with self.subTest(words=words),self.assertRaises(ValueError):sound.prepare_triggers(self.image,self.base,words)
        wrong=copy.deepcopy(self.base);wrong['output_sha256']='0'*64
        with self.assertRaises(ValueError):sound.prepare_triggers(self.image,wrong,self.words)
        at=0x800F43D4-CODE_RAM;bad=bytearray(self.image);entry=by_vrom(self.image)[CODE_VROM]
        bad[entry.pstart+at]^=1;wrong['output_sha256']=sha256(bad)
        with self.assertRaisesRegex(ValueError,'interpreter'):sound.prepare_triggers(bad,wrong,self.words)


class InstalledBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=ROOT/'build/v3-furniture-trigger-runtime-03'
        cls.image,cls.report=inputs(cls.path/'build-lock.json')
        cls.base,cls.prior=inputs(cls.path/'base-lock.json')
        cls.files=by_vrom(cls.image);cls.old_files=by_vrom(cls.base)
        cls.code=cls.files[CODE_VROM].extract(cls.image)
        cls.old_code=cls.old_files[CODE_VROM].extract(cls.base)
        cls.audio=cls.report['equipment_resources']['furniture_audio']

    def test_complete_old_resources_and_source_priority_survive_registration(self):
        new,_,_=sound.installed_resource(self.image,self.code,'seq',199)
        old,_,_=sound.installed_resource(self.base,self.old_code,'seq',199)
        restored=bytearray(new[:len(old)])
        for table in self.audio['tables']:
            group=table['group'];pointer=0x188+group*2
            restored[pointer:pointer+2]=old[pointer:pointer+2]
            n=table['previous_count']*2
            self.assertEqual(new[table['offset']:table['offset']+n],old[table['previous_offset']:table['previous_offset']+n])
        self.assertEqual(restored,old)
        self.assertEqual(self.code[0x80113B84-CODE_RAM:0x80113C04-CODE_RAM],
                         self.old_code[0x80113B84-CODE_RAM:0x80113C04-CODE_RAM])
        for row in self.audio['programs']:
            word=row['native_sound_word'];group=word>>8&127;index=word&127
            table=next(r for r in self.audio['tables'] if r['group']==group)
            self.assertEqual(struct.unpack_from('>H',new,table['offset']+index*2)[0],row['offset'])
            self.assertEqual(self.code[0x80113B84-CODE_RAM+index],row['trigger_priority'])
            self.assertEqual(word&0x8000,row['source_sound_word']&0x8000)
            raw=new[row['offset']:row['offset']+row['bytes']]
            desc=sound.trigger_program(bytes(row['offset'])+raw,row['offset'],row['offset']+len(raw))
            for key in ('events','duration','envelope_bytes','decay'):
                self.assertEqual(desc[key],row['source_program'][key])
        self.assertEqual(len(self.audio['programs']),5)

    def test_growth_preserves_complete_dma_owners_and_audio_allocation(self):
        from v3_furniture_install import append_resource_plan
        from aflib import apply_ups,DMA_START,DMA_END
        growth=self.audio['resource_growth'];v=growth['vrom'];data=self.files[v].extract(self.image)
        self.assertEqual(data[:growth['previous_bytes']],self.old_files[v].extract(self.base))
        for owner in growth['relocated_blockers']:
            self.assertEqual(self.files[owner].extract(self.image),self.old_files[owner].extract(self.base))
            self.assertGreaterEqual(self.files[owner].pstart,growth['physical']+growth['bytes'])
        with self.assertRaises(ValueError):append_resource_plan(self.base,self.old_files,v,data,{})
        with self.assertRaises(ValueError):append_resource_plan(self.base,self.old_files,v,b'X'+data[1:],{})
        # Only the import resource, resident module, core, waveform group, and
        # declared complete moved owners may differ in the logical directory.
        from v3_asset_loader import BLOB,MODULE
        allowed={BLOB,MODULE,CODE_VROM,v}
        for owner,entry in self.files.items():
            if owner in allowed:continue
            expected=bytearray(self.old_files[owner].extract(self.base))
            if entry.pstart<=DMA_START and DMA_END<=entry.pstart+entry.size and not entry.pend:
                expected[DMA_START-entry.pstart:DMA_END-entry.pstart]=self.image[DMA_START:DMA_END]
            self.assertEqual(entry.extract(self.image),expected,hex(owner))
        before=struct.unpack_from('>3I',self.old_code,0x80119A44-CODE_RAM)
        after=struct.unpack_from('>3I',self.code,0x80119A44-CODE_RAM)
        self.assertEqual(tuple(b+2048 for b in before),after)
        self.assertEqual(sound.permanent_budget(self.code)['conservative_spare'],864)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(self.path/'asset-loader.ups').read_bytes()),self.image)

    def test_runtime_table_and_composition_preserve_saved_profile_and_choices(self):
        import v3_room_rig_runtime as room
        import v3_optional_composition as composer
        from v3_asset_loader import BLOB
        e=self.report['equipment_resources'];r=e['room_rigs'];blob=self.files[BLOB].extract(self.image)
        packet=blob[r['packet']['blob_offset']:r['packet']['blob_offset']+room.PACKET_BYTES]
        self.assertEqual(packet[room.PACKET_TABLE-room.PACKET_RAM:],room.encode_packet(r['rows'],r['sound_rows']))
        self.assertEqual(r['rows'],self.prior['equipment_resources']['room_rigs']['rows'])
        self.assertEqual(len(r['sound_rows']),5)
        self.assertTrue(all(not row['profile_installed'] and not row['parent_selectable'] for row in r['sound_rows']))
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.path/'build-lock.json');catalog=composer.catalogue(self.image,self.report)
            self.assertEqual(len(catalog),128)
            self.assertEqual(sha256(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,[]))[0]),
                             self.report['translation_baseline']['sha256'])
            self.assertEqual(composer.compose(self.image,self.report,catalog,composer.resolve(catalog,list(catalog)))[0],self.image)
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin

    def test_next_bulk_import_checks_actual_retained_chair_sounds_after_resource_growth(self):
        from v3_furniture_behaviours import audio_contract
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        current=audio_contract(original,self.image,self.report,source)
        self.assertEqual(len(current['sounds']),4)
        self.assertEqual(current['new_audio_bytes'],0)
        # Reject an actual moved-table binding change, not the relocation itself.
        bad=bytearray(self.image);seq=self.audio['sequence'];at=seq['physical']
        table=struct.unpack_from('>H',bad,at+0x190)[0]
        struct.pack_into('>H',bad,at+table+0x1F*2,0)
        wrong=copy.deepcopy(self.report)
        wrong['fire_sound']['resources']['seq']['sha256']=sha256(bad[at:at+seq['bytes']])
        with self.assertRaisesRegex(ValueError,'sound route'):
            audio_contract(original,bytes(bad),wrong,source)


class LoopingFurnitureBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.path=ROOT/'build/v3-scrolling-level-audio-runtime-03'
        cls.image,cls.report=inputs(cls.path/'build-lock.json')
        cls.base,cls.prior=inputs(cls.path/'base-lock.json')
        cls.code=by_vrom(cls.image)[CODE_VROM].extract(cls.image)
        cls.old_code=by_vrom(cls.base)[CODE_VROM].extract(cls.base)
        cls.audio=cls.report['equipment_resources']['furniture_level_audio']
        cls.prepared_path=ROOT/'build/v3-scrolling-level-audio-prepared-01'
        cls.prepared=json.loads((cls.prepared_path/'audio.json').read_bytes())

    def test_shared_lifecycle_discovery_and_complete_source_programs(self):
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        self.assertEqual({r['item_id'] for r in self.audio['furniture']},{'1FE4','1FE8','31A0','3368'})
        self.assertEqual(self.prepared['source_table_entries'],96)
        self.assertEqual(self.prepared['native_table_entries'],128)
        for row in self.audio['furniture']:
            profile=source.profile(int(row['item_id'],16));before=copy.deepcopy(profile)
            contract=sound.furniture_level(source,profile)
            self.assertEqual(profile,before)
            self.assertEqual(json.loads(json.dumps(contract)),row['lifecycle'])
            self.assertFalse(contract['callback_installed'])
            changed=copy.copy(source);changed.rel=bytearray(source.rel)
            changed.rel[source.sections[1][0]+contract['functions']['move']['offset']]^=1
            with self.assertRaises(ValueError):sound.furniture_level(changed,profile)
            if contract['constants']:
                changed.rel=bytearray(source.rel)
                changed.rel[source.sections[4][0]+contract['constants']['zero']['offset']]^=1
                with self.assertRaises(ValueError):sound.furniture_level(changed,profile)
        resources={};sequence,receipt=sound.prepare_levels(self.base,self.prior,self.old_code,
            [0x46,0x4A,0x4B,0x5B],font_resources=resources)
        self.assertEqual(sequence,(self.prepared_path/'sequence.bin').read_bytes())
        for key,value in receipt.items():self.assertEqual(json.loads(json.dumps(value)),self.prepared[key])
        for key,data in resources.items():self.assertEqual(data,(self.prepared_path/(key+'.bin')).read_bytes())
        for ids in ([96],[127],[74,74]):
            with self.assertRaises(ValueError):sound.prepare_levels(self.base,self.prior,self.old_code,ids)

    def test_all_audio_consumers_retain_prior_programs_and_complete_instruments(self):
        sequence,header,physical=sound.installed_resource(self.image,self.code,'seq',199)
        oldseq,_,_=sound.installed_resource(self.base,self.old_code,'seq',199)
        self.assertEqual(sequence,(self.prepared_path/'sequence.bin').read_bytes())
        self.assertEqual(len(sequence)-len(oldseq),128)
        restored=bytearray(sequence[:len(oldseq)])
        for row in self.audio['programs']:
            at=row['native_table']+row['native_sound_id']*2
            self.assertEqual(struct.unpack_from('>H',sequence,at)[0],row['offset'])
            struct.pack_into('>H',restored,at,row['original_table_pointer'])
            raw=sequence[row['offset']:row['offset']+row['bytes']]
            actual=sound.looping_layer(raw,row['offset'],prefix=True)
            for key in ('note','duration','velocity','decay','envelope_bytes'):
                self.assertEqual(actual[key],row['source_program'][key])
            self.assertEqual(actual['loop'],row['source_program']['loop']+4)
            bank,h,_=sound.installed_resource(self.image,self.code,'bank',row['native_bank'])
            wave,_,_=sound.installed_resource(self.image,self.code,'wave',h[10])
            self.assertEqual(instrument(bank,wave,row['native_instrument'],h[12],extended=True),row['instrument_identity'])
        self.assertEqual(restored,oldseq)
        shared=self.report['equipment_resources']['sound_programs'];prior=self.prior['equipment_resources']['sound_programs']
        self.assertEqual(shared['imports'][:-4],prior['imports'])
        self.assertEqual(shared['trigger_batches'],prior['trigger_batches'])
        for record in (shared['sequence'],self.audio['sequence'],
                       self.report['equipment_resources']['furniture_audio']['sequence'],self.report['fire_sound']['resources']['seq']):
            self.assertEqual((record['sha256'],record['header_after'],record['physical']),(sha256(sequence),header.hex(),physical))
        bank,h,_=sound.installed_resource(self.image,self.code,'bank',140)
        oldbank,oldh,_=sound.installed_resource(self.base,self.old_code,'bank',140)
        wave,_,_=sound.installed_resource(self.image,self.code,'wave',5)
        oldwave,_,_=sound.installed_resource(self.base,self.old_code,'wave',5)
        self.assertEqual((oldh[12],h[12]),(82,83))
        self.assertEqual(wave[:len(oldwave)],oldwave)
        for i in range(82):
            self.assertEqual(instrument(bank,wave,i,83,extended=True),instrument(oldbank,oldwave,i,82,extended=True))
        self.assertEqual(self.audio['audio_heap_growth'],0)
        self.assertEqual(sound.permanent_budget(self.code)['conservative_spare'],32)

    def test_archive_relocation_preserves_text_external_waves_and_old_storage(self):
        from v3_furniture_install import relocate_resource_plan
        files,old=by_vrom(self.image),by_vrom(self.base)
        archive=sound.audio_archive(self.image,self.code,'wave');before=sound.audio_archive(self.base,self.old_code,'wave')
        self.assertEqual(archive.vstart,0x04000000);self.assertEqual(before.vstart,0x01A50000)
        self.assertEqual(archive.index,before.index);self.assertNotIn(before.vstart,files)
        self.assertEqual(archive.extract(self.image)[:before.size],before.extract(self.base))
        self.assertEqual(self.image[before.pstart:before.pstart+before.size],before.extract(self.base))
        self.assertEqual(files[0x1FA0000],old[0x1FA0000])
        self.assertEqual(files[0x1FA0000].extract(self.image),old[0x1FA0000].extract(self.base))
        for i in range(6):
            data,_,p=sound.installed_resource(self.image,self.code,'wave',i)
            olddata,_,oldp=sound.installed_resource(self.base,self.old_code,'wave',i)
            self.assertEqual(data[:len(olddata)],olddata)
            if i!=5:self.assertEqual(data,olddata)
            if i==2:self.assertEqual(p,oldp)
        wrong=bytearray(self.code);wrong[0x800D28DC-CODE_RAM]^=1
        with self.assertRaises(ValueError):sound.audio_archive(self.image,wrong,'wave')
        with self.assertRaises(ValueError):
            relocate_resource_plan(self.base,old,before.vstart,archive.extract(self.image),
                minimum_physical=0x3000000,target_vrom=0x1FA0000)
        # The ordinary bulk importer still resolves its actual live audio resources.
        from v3_furniture_pipeline import Source
        from v3_furniture_behaviours import audio_contract
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        audio_contract((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),self.image,self.report,source)

    def test_profiles_and_composition_preserve_the_import_free_cartridge(self):
        from aflib import apply_ups
        from v3_asset_loader import BLOB
        from v3_import_storage import ROWS,TABLE_END
        import v3_optional_composition as composer
        blob=by_vrom(self.image)[BLOB].extract(self.image);old=by_vrom(self.base)[BLOB].extract(self.base)
        self.assertEqual(blob[ROWS:TABLE_END],old[ROWS:TABLE_END])
        self.assertEqual(self.report['save_runtime'],self.prior['save_runtime'])
        self.assertEqual(self.report['staged_furniture'],self.prior['staged_furniture'])
        self.assertEqual(self.report['equipment_resources']['room_rigs'],self.prior['equipment_resources']['room_rigs'])
        pin=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(self.path/'build-lock.json')
            catalogue=composer.catalogue(self.image,self.report);self.assertEqual(len(catalogue),137)
            for selected in ([],list(catalogue)):
                result,_,_=composer.compose(self.image,self.report,catalogue,composer.resolve(catalogue,selected))
                self.assertEqual(sha256(result),sha256(self.image) if selected else self.report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=pin
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (self.path/'asset-loader.ups').read_bytes()),self.image)

    def test_subsequent_trigger_preparation_reuses_the_current_complete_font(self):
        # Exercise the other sound category against the current relocated archive,
        # without rebuilding an old cartridge or playing any audio.
        words=[r['source_sound_word'] for r in self.report['equipment_resources']['furniture_audio']['programs']]
        resources,prepared=sound.prepare_triggers(self.image,self.report,words)
        bank,_,_=sound.installed_resource(self.image,self.code,'bank',140)
        wave,_,_=sound.installed_resource(self.image,self.code,'wave',5)
        self.assertEqual(resources['font'],bank);self.assertEqual(resources['wave'],wave)
        self.assertEqual(prepared['layout']['instrument_count'],83)
        self.assertEqual(prepared['layout']['font_growth_bytes'],0)
        self.assertEqual(prepared['layout']['wave_growth_bytes'],0)


if __name__=='__main__':unittest.main()
