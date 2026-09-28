"""Focused connected carried-category checks; not a native gameplay claim."""
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
from v3_diary_items import RAM,SIZE,TABLE,ICON,ART,records,encode,pocket_icon
from v3_furniture_install import inputs
from v3_furniture_pipeline import Source
from v3_registry import diary_parent_identity
import v3_physical_resources as physical

OUT=ROOT/os.environ.get('V3_DIARY_ITEMS','build/v3-diary-category-work-01/carried-03')


class DiaryItemTests(unittest.TestCase):
    def test_complete_carried_packet_and_retained_native_routes(self):
        image,r=inputs(OUT/'build-lock.json');base,prior=inputs(OUT/'base-lock.json')
        e=r['equipment_resources'];d=e['diary_items'];p=d['packet']
        self.assertEqual(d['selected'],0)
        self.assertFalse(d['native_execution_tested'])
        self.assertEqual((p['ram'],p['bytes']),(RAM,SIZE))
        packet=image[p['physical']:p['physical']+p['bytes']]
        physical.verify(image,r['physical_resources'])
        self.assertEqual(sha256(packet),p['sha256']);self.assertEqual(zlib.crc32(packet),p['crc32'])
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        rows,_=records(source);table=encode(rows);icon,_=pocket_icon(source)
        self.assertEqual(d['rows'],json.loads(json.dumps(rows)))
        self.assertEqual(packet[TABLE:TABLE+len(table)],table)
        self.assertEqual(packet[ICON:ICON+len(icon)],icon)
        self.assertEqual(sha256(packet[ART:ART+d['artwork']['bytes']]),d['artwork']['installed_sha256'])
        self.assertEqual(packet[-16:],bytes.fromhex('41464447')*4)
        files=by_vrom(image);old_files=by_vrom(base)
        blob=files[BLOB].extract(image);core=files[CODE_VROM].extract(image);module=files[MODULE].extract(image)
        for h in d['hooks']:
            owner,origin=(blob,0x80460000) if h['address']>=0x80460000 else (
                (module,MODULE_RAM) if h['address']>=MODULE_RAM else (core,CODE_RAM))
            self.assertEqual(owner[h['address']-origin:h['address']-origin+8].hex(),h['after'])
        h=d['icon_hook'];menu=files[h['vrom']].extract(image);old=old_files[h['vrom']].extract(base)
        expected=bytearray(old);at=h['address']-h['ram'];expected[at:at+8]=bytes.fromhex(h['after'])
        self.assertEqual(menu,bytes(expected))
        native=u32(core,0x8010B334-CODE_RAM+11*4)
        self.assertEqual(core[native-CODE_RAM],21)
        self.assertEqual(r['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        # Same stored menu/core/screen resources, except the relinked room-ID predicate.
        old_ui=prior['equipment_resources']['diaries']['packets']['ui'];ui=e['diaries']['packets']['ui']
        expected=bytearray(base[old_ui['physical']:old_ui['physical']+old_ui['bytes']])
        for h in e['diaries']['carried_identity_patches']:
            at=h['offset'];self.assertEqual(expected[at:at+4].hex(),h['before'])
            expected[at:at+4]=bytes.fromhex(h['after'])
        self.assertEqual(image[ui['physical']:ui['physical']+ui['bytes']],bytes(expected))
        boot=e['surface_bootstrap']['code'];self.assertLessEqual(boot['bytes'],688)
        at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        descriptors=list(struct.iter_unpack('>5I',blob[at:at+16*20]))
        self.assertEqual(descriptors[-1][:3],(RAM,p['physical']|0x80000000,SIZE))
        for dest,source,n,crc,clear in descriptors:
            if source&0x80000000:data=image[source&0x7FFFFFFF:(source&0x7FFFFFFF)+n]
            else:
                owner=next(x for x in files.values() if x.vstart<=source<source+n<=x.vend)
                data=owner.extract(image)[source-owner.vstart:source-owner.vstart+n]
            self.assertEqual(u32(blob,e['blob_offset']+crc-e['ram']),zlib.crc32(data))
            self.assertTrue(0x80400000<=dest<dest+n<=0x807DA800)
        # Existing creature consumers still chain to the same complete readers.
        from v3_creature_items import checked
        self.assertIsNotNone(checked(image,r,Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())))

    def test_ground_bank_appends_without_moving_scenery(self):
        image,r=inputs(OUT/'build-lock.json');base,prior=inputs(OUT/'base-lock.json')
        files=by_vrom(image);old_files=by_vrom(base);e=r['equipment_resources'];old_e=prior['equipment_resources']
        blob=files[BLOB].extract(image);core=files[CODE_VROM].extract(image)
        data=blob[e['blob_offset']:e['blob_offset']+e['bytes']];c=e['item_categories'];ground=e['ground_categories']
        self.assertEqual(data[c['map_offset']+16+17],44)
        self.assertEqual(len(c['objects']),10)
        for t in c['tables']:
            self.assertEqual(u32(data,t['offset']+44*4),(RAM+ART & 0x1FFFFFFF)+e['diary_items']['artwork']['offsets'][t['role']])
        for i,(row,old) in enumerate(zip(ground['owners'],old_e['ground_categories']['owners'])):
            cap=row['capacity'];scenery=old_e['scenery']['owners'][i]
            self.assertGreaterEqual(cap['empty_offset'],scenery['bank_offset']+scenery['bank_bytes'])
            self.assertEqual(cap['parts_offset'],cap['empty_offset']+32)
            self.assertLessEqual(cap['parts_offset']+10*52,cap['resident_bytes'])
            self.assertEqual(u32(data,ground['config_offset']+i*36+24),cap['parts_offset'])
            self.assertEqual(u32(core,row['allocation_descriptor']-CODE_RAM+12),row['ram']+cap['resident_bytes'])
            before=bytearray(old_files[row['reloc']].extract(base));struct.pack_into('>I',before,12,cap['bss_bytes'])
            self.assertEqual(files[row['reloc']].extract(image),bytes(before))
            self.assertEqual(files[row['vrom']].extract(image),old_files[row['vrom']].extract(base))
        self.assertEqual(e['scenery'],old_e['scenery'])

    def test_sanitized_readers_and_registry(self):
        self.assertEqual([diary_parent_identity(0x2B00+i) for i in range(16)],list(range(0x2B10,0x2B20)))
        for invalid in (False,0x2AFF,0x2B10,None):
            with self.assertRaises(ValueError):diary_parent_identity(invalid)
        with tempfile.TemporaryDirectory(prefix='v3-diary-items-') as temp:
            target=Path(temp)/'readers'
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-DAF_V3_CLOTHING_PROFILE=1',
                'tests/v3_diary_items_test.c','overlays/v3/diary_items.c','-o',str(target)]
            result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            result=subprocess.run([str(target)],capture_output=True,text=True,timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            print(result.stdout.strip())

    def test_sanitized_startup_and_relocated_ground_descriptors(self):
        with tempfile.TemporaryDirectory(prefix='v3-diary-art-') as temp:
            for source in ('v3_creature_startup_test.c','v3_ground_categories_test.c'):
                target=Path(temp)/source
                result=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                    '-fno-pie','-no-pie','-fsanitize=address,undefined','-fno-omit-frame-pointer',
                    'tests/'+source,'-o',str(target)],cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                result=subprocess.run([str(target)],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                print(result.stdout.strip())


if __name__=='__main__':unittest.main()
