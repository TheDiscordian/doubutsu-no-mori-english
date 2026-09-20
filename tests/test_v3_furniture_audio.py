"""Shared furniture audio conversion; no historic cartridge or audible replay."""
import copy
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


if __name__=='__main__':unittest.main()
