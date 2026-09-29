"""Focused changed quest ownership; no old cartridge or emulator replay."""
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
from aflib import by_vrom,sha256,apply_ups,CODE_VROM,CODE_RAM,u32
from v3_asset_loader import BLOB
from v3_furniture_install import inputs

OUT=ROOT/os.environ.get('V3_CARRIED_QUEST','build/v3-carried-field-work-01/quest-state-02')

class QuestTests(unittest.TestCase):
    def test_complete_dates_and_native_state_lifetime(self):
        with tempfile.TemporaryDirectory(prefix='v3-quest-state-') as temp:
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-ffunction-sections','-fdata-sections','-Wl,--gc-sections',
                '-DAF_V3_EVENT_ITEM_PROFILE=1','-DAF_V3_CARRIED_PROFILE=1','-DAF_V3_CARRIED_QUEST=1',
                'tests/v3_carried_quest_test.c',*(f'overlays/v3/{s}.c' for s in
                    ('carried_quest','holiday_cards','holiday_native','diary_calendar')),
                '-o',str(Path(temp)/'check')]
            for cmd in (command,[str(Path(temp)/'check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_current_cartridge_and_retained_resources(self):
        image,r=inputs(OUT/'build-lock.json');base,prior=inputs(OUT/'base-lock.json')
        e=r['equipment_resources'];d=e['carried_items'];q=d['quest'];p=q['packet']
        raw=image[p['physical']:p['physical']+p['bytes']]
        old=prior['equipment_resources']['carried_items']['spawning']['packet']
        self.assertEqual(raw[:old['bytes']],base[old['physical']:old['physical']+old['bytes']])
        self.assertEqual((p['ram'],p['bytes']),(0x807AC000,0x8000))
        self.assertEqual(raw[-16:],b'AFCQ'*4)
        self.assertEqual(raw[0x7F00:0x7F38],bytes(56))
        self.assertEqual(u32(raw,q['availability_address']-p['ram']),0)
        self.assertEqual(sha256(raw),p['sha256'])
        for code,ram in ((q['code'],q['ram']),(q['storage'],q['storage_ram'])):
            at=ram-p['ram'];self.assertEqual(sha256(raw[at:at+code['bytes']]),code['sha256'])
        self.assertEqual((d['ready_mask'],d['selected_mask']),(0,0))
        self.assertEqual((q['save_format'],q['wire_version']),(17,4))
        prefix=d['packet'];old_prefix=prior['equipment_resources']['carried_items']['packet']
        restored=bytearray(image[prefix['physical']:prefix['physical']+prefix['bytes']])
        self.assertEqual(sha256(restored),prefix['sha256'])
        self.assertEqual(len(q['redirects']),36)
        for h in q['redirects']:
            at=h['address']-prefix['ram'];self.assertEqual(restored[at:at+8].hex(),h['after'])
            self.assertEqual(h['target'],q['storage']['symbols'][h['name']])
            restored[at:at+8]=bytes.fromhex(h['before'])
        self.assertEqual(restored,base[old_prefix['physical']:old_prefix['physical']+old_prefix['bytes']])
        core=bytearray(by_vrom(image)[CODE_VROM].extract(image))
        for h in q['core_patches']:
            at=h['address']-CODE_RAM;n=len(bytes.fromhex(h['after']))
            self.assertEqual(core[at:at+n].hex(),h['after']);core[at:at+n]=bytes.fromhex(h['before'])
        self.assertEqual(core,by_vrom(base)[CODE_VROM].extract(base))
        # Only proven obsolete startup copies are reclaimed. Every other
        # pre-existing physical resource remains unchanged except save redirects.
        records={v['id']:v for v in r['physical_resources']}
        missing={v['id'] for v in prior['physical_resources']}-records.keys()
        self.assertEqual(missing,{'holiday-state-GAFE01-r0','holiday-transition-GAFE01-r0'})
        for v in prior['physical_resources']:
            if v['id'] in missing or v['id']==prefix['id']:continue
            current=records[v['id']]
            self.assertEqual(sha256(image[current['physical']:current['physical']+current['bytes']]),v['sha256'])
        blob=by_vrom(image)[BLOB].extract(image);boot=e['surface_bootstrap']['code']
        at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        self.assertEqual((boot['packet_count'],boot['packet_stride']),(22,16))
        self.assertLessEqual(boot['bytes'],688)
        loaded=[]
        for i in range(22):
            ram,physical,size,crc=struct.unpack_from('>4I',blob,at+16*i);loaded.append((ram,physical,size))
            if physical&0x80000000:data=image[physical&0x7FFFFFFF:(physical&0x7FFFFFFF)+size]
            else:
                entry=next(f for f in by_vrom(image).values() if f.vstart<=physical<f.vend)
                data=entry.extract(image)[physical-entry.vstart:physical-entry.vstart+size]
            self.assertEqual(zlib.crc32(data),u32(blob,e['blob_offset']+crc-e['ram']))
        self.assertIn((p['ram'],p['physical']|0x80000000,p['bytes']),loaded)
        for path,digest in d['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),image)

if __name__=='__main__':unittest.main()
