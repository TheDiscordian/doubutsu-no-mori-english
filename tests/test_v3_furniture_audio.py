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


if __name__=='__main__':unittest.main()
