"""Shared vendor transaction, owner relocation, and complete text-bank retention."""
import json
import os
from pathlib import Path
import struct
import sys
from types import SimpleNamespace
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,apply_ups,n64_checksum,u32
from v3_asset_loader import BLOB,MODULE,STARTUP,CONFIG
from v3_furniture_install import inputs
from npc_mail_show import relocate_verified_data
from textbanks import Bank
from runtime_module import module_command_info
from textcodec import tokenize
from textvalidate import expanded_bound
from v3_camper_text import donor
from gc_text import decode_gc
from textcodec import encode
import v3_event_acquisition as event
import v3_event_text as text
import tests.test_v3_equipment_runtime as shared

OUTPUT=ROOT/os.environ.get('V3_EVENT_MENU_BUILD','build/v3-event-menu-06')

class HostTests(unittest.TestCase):
    sanitized=shared.HostTests.sanitized
    def test_shared_menu_with_actual_stock_module(self):
        self.sanitized('v3_event_menu_test.c',('overlays/v3/event_acquisition.c',))

@unittest.skipUnless((OUTPUT/'build.json').is_file(),'Current event-menu cartridge required')
class CartridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rom=(OUTPUT/'animal-forest-v3-asset-loader.z64').read_bytes()
        cls.report=json.loads((OUTPUT/'build.json').read_bytes())
        cls.base,cls.prior=inputs(OUTPUT/'base-lock.json')
        cls.files,cls.before=by_vrom(cls.rom),by_vrom(cls.base)
        cls.blob=cls.files[BLOB].extract(cls.rom);cls.e=cls.report['equipment_resources']
        cls.r=cls.e['event_acquisition']['menu'];at=cls.e['blob_offset']
        cls.module=cls.blob[at:at+cls.e['bytes']]

    def test_complete_loaded_owner_and_retained_original_wares(self):
        old=self.before[event.OWNER].extract(self.base);new=self.files[event.OWNER].extract(self.rom)
        oldrel=self.before[event.RELOC].extract(self.base);rel=self.files[event.RELOC].extract(self.rom)
        restored=bytearray(new)
        for p in self.r['patches']:
            at=p['offset'];self.assertEqual(u32(old,at),p['before']);self.assertEqual(u32(new,at),p['after'])
            restored[at:at+4]=old[at:at+4]
        self.assertEqual(new[0x1220:0x1226],struct.pack('>3H',text.FIRST,text.FIRST+1,text.FIRST+2))
        restored[0x1220:0x1226]=old[0x1220:0x1226];self.assertEqual(restored,old)
        self.assertEqual(new[0x1228:0x122E],struct.pack('>3H',980,1000,1280))
        self.assertEqual(u32(new,0x11BC),0x958)
        self.assertEqual(sha256(new),self.r['owner_sha256']);self.assertEqual(sha256(rel),self.r['reloc_sha256'])
        oldrows=list(struct.unpack_from('>'+str(u32(oldrel,16))+'I',oldrel,20))
        for row in self.r['removed_relocations']:oldrows.remove(row)
        self.assertEqual(list(struct.unpack_from('>'+str(u32(rel,16))+'I',rel,20)),oldrows)
        sections=struct.unpack_from('>5I',rel)
        for base in (0x80200010,0x80350010):
            moved=relocate_verified_data(SimpleNamespace(ram=event.OWNER_RAM,resident_bytes=len(new),sections=sections),new,rel,base)
            self.assertEqual(u32(moved,0x1158),event.jump(self.r['code']['symbols']['af_v3_event_menu_setup']))
            self.assertEqual(moved[0x1038:0x1044],new[0x1038:0x1044])
            for at in (0x1230,0x1234,0x1238,0x123C,0x1240,0x1244):
                pointer=u32(new,at)
                expected=pointer-event.OWNER_RAM+base if event.OWNER_RAM<=pointer<event.OWNER_RAM+len(new) else pointer
                self.assertEqual(u32(moved,at),expected)
        core=bytearray(self.files[CODE_VROM].extract(self.rom));prior=self.before[CODE_VROM].extract(self.base)
        for p in self.r['message_bounds']:
            at=p['address']-CODE_RAM;self.assertEqual(u32(prior,at),p['before']);self.assertEqual(u32(core,at),p['after'])
            struct.pack_into('>I',core,at,p['before'])
        self.assertEqual(core,prior)

    def test_complete_text_and_provenance(self):
        def messages(image,files):
            return Bank('message',text.MESSAGE,text.TABLE,files[text.MESSAGE].extract(image),
                        files[text.TABLE].extract(image)).entries()
        old=messages(self.base,self.before);new=messages(self.rom,self.files)
        self.assertEqual(len(old),text.FIRST);self.assertEqual(len(new),text.FIRST+4)
        self.assertEqual(new[:len(old)],old)
        catalogue=json.loads((ROOT/'translations/provenance.json').read_bytes())
        indexed={r['id']:r for r in catalogue['entries']};info=module_command_info(self.rom)
        for row in self.r['text']['provenance_entries']:
            self.assertEqual(indexed[row['id']],row)
        for i,data in enumerate(new[text.FIRST:]):
            record=indexed[f'message:{text.FIRST+i:04X}']['locales']['en']
            self.assertEqual(sha256(data),record['encoded_sha256']);self.assertLessEqual(expanded_bound(data,info),1024)
            self.assertEqual(list(tokenize(data,info))[-1].data,b'\x7f\x01')
        source,_,decoder=donor()
        for i in range(3):
            parts=decode_gc(source[0x1758+i],decoder).split('{cmd:7F02}')
            self.assertTrue(new[text.FIRST+i].startswith(encode(parts[0],info)+b'\x7f\x02'))
            self.assertTrue(new[text.FIRST+i].endswith(encode(parts[-1],info)))
            self.assertIn(str((980,1000,1280)[i]).encode() if i==0 else (b'1,000',b'1,280')[i-1],new[text.FIRST+i])
        for v in (text.CHOICES,text.CHOICE_TABLE):
            self.assertEqual(self.files[v].extract(self.rom),self.before[v].extract(self.base))
        for p in self.r['text']['placements']:
            e=self.files[p['vrom']];self.assertEqual((e.pstart,e.size),(p['physical'],p['bytes']))
            self.assertEqual(sha256(e.extract(self.rom)),p['sha256'])
        self.assertFalse(self.r['text']['provenance_missing'])

    def test_complete_module_patch_and_unchanged_profiles(self):
        old=self.prior['equipment_resources'];blob=self.before[BLOB].extract(self.base)
        self.assertEqual(self.module[:old['bytes']],blob[old['blob_offset']:old['blob_offset']+old['bytes']])
        self.assertEqual(len(self.module),0xD000);self.assertEqual(sha256(self.module),self.e['sha256'])
        self.assertEqual(zlib.crc32(self.module),self.e['crc32']);self.assertEqual(self.module[-16:],bytes.fromhex('AF48C0DE')*4)
        code=self.r['code'];self.assertLessEqual(code['bytes'],0xFF0)
        self.assertEqual(sha256(self.module[0xC000:0xC000+code['bytes']]),code['sha256'])
        self.assertEqual(self.blob[0x20:0xE0],blob[0x20:0xE0])
        self.assertIn('-DAF_V3_EQUIPMENT_BYTES=0xD000u',self.report['startup']['flags'])
        self.assertLessEqual(self.report['startup']['bytes'],CONFIG-STARTUP)
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),self.rom)
        self.assertEqual(struct.unpack_from('>2I',self.rom,16),n64_checksum(self.rom))
        self.assertEqual(sha256(self.rom),self.report['output_sha256'])
        changed={BLOB,MODULE,CODE_VROM,0x19D40,event.OWNER,event.RELOC,text.MESSAGE,text.TABLE,text.CHOICES,text.CHOICE_TABLE}
        self.assertEqual(self.before.keys(),self.files.keys())
        for v,e in self.before.items():
            self.assertEqual(e.index,self.files[v].index)
            if v not in changed:self.assertEqual(e.extract(self.base),self.files[v].extract(self.rom),hex(v))
        for p in event.SOURCES:self.assertEqual(sha256((ROOT/p).read_bytes()),self.report['sources'][p])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_format_changed'])
        self.assertFalse(self.report['shared_runtime_refresh']['saved_profile_changed'])
        self.assertEqual(self.e['event_acquisition']['profile_bits_enabled'],0)

if __name__=='__main__':unittest.main()
