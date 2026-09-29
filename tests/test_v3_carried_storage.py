"""Changed save/collection path; reuse native I/O doubles, no emulator replay."""
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
from aflib import by_vrom,sha256,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
from v3_carried_runtime import END,GUARD
OUT=ROOT/os.environ.get('V3_CARRIED_RUNTIME','build/v3-carried-runtime-work-01/storage-connected-06')

class CarriedStorageTests(unittest.TestCase):
    def test_save_transaction_and_native_collection(self):
        with tempfile.TemporaryDirectory(prefix='v3-carried-storage-') as temp:
            out=Path(temp)
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections','-fdata-sections',
                *('-D'+name+'=1' for name in ('AF_V3_CLOTHING_PROFILE','AF_V3_REWARD_PROFILE',
                    'AF_V3_SURFACE_PROFILE','AF_V3_CREATURE_PROFILE','AF_V3_INSECT_SEASONS',
                    'AF_V3_DIARY_STORAGE','AF_V3_HOLIDAY_STORAGE','AF_V3_FISHING_STORAGE','AF_V3_CARD_STORAGE'))]
            commands=[['cc',*flags,'-Daf_v3_save_check=af_console_canonical_check',
                '-Daf_v3_save_pack=af_console_canonical_pack','-Daf_v3_save_collect=af_console_canonical_collect',
                '-c','overlays/v3/save_codec.c','-o',str(out/'codec.o')]]
            entries=('compress','expand','compress_diary','measure_diary','expand_diary',
                'compress_fishing','measure_fishing','expand_fishing','compress_cards','measure_cards','expand_cards')
            for name,extra in (('old',['-DAF_V3_EVENT_ITEM_PROFILE=1']),('v14',[])):
                commands.append(['cc',*flags,*extra,*(f'-Daf_v3_save_{s}=af_{name}_{s}' for s in entries),
                    '-c','overlays/v3/save_compressed.c','-o',str(out/(name+'.o'))])
            commands.extend([['cc',*flags,'-DAF_V3_EVENT_ITEM_PROFILE=1','-DAF_V3_CARRIED_PROFILE=1',
                '-DAF_V3_CONSOLE_STORAGE=1','-Wl,--gc-sections','tests/v3_carried_storage_test.c',
                *(f'overlays/v3/{s}.c' for s in ('save_runtime','console_storage','save_compressed',
                    'diary','diary_calendar','holiday_fishing','holiday_cards','carried_items','carried_collection')),
                str(out/'codec.o'),str(out/'old.o'),str(out/'v14.o'),'-o',str(out/'check')],
                [str(out/'check')]])
            for command in commands:
                result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())

    def test_installed_storage_dispatch_and_unchanged_carried_art(self):
        image,r=inputs(OUT/'build-lock.json');base,prior=inputs(OUT/'base-lock.json')
        e=r['equipment_resources'];d=e['carried_items'];s=d['storage'];p=d['packet']
        old=prior['equipment_resources']['carried_items']['packet']
        raw=image[p['physical']:p['physical']+p['bytes']]
        cat=d['paper']['catalogue'];c=cat['code'];ca=c['link_symbols']['AF_CARRIED_CATALOGUE_RAM']-p['ram']
        self.assertEqual(sha256(raw[ca:ca+c['bytes']]),c['sha256'])
        retained=bytearray(raw[:old['bytes']]);retained[ca:ca+c['bytes']]=bytes(c['bytes'])
        self.assertEqual(retained,base[old['physical']:old['physical']+old['bytes']])
        self.assertEqual(raw[-16:],GUARD)
        self.assertEqual(sha256(raw),(p['sha256']))
        self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(s['ram'],END);self.assertEqual(p['ram']+p['bytes'],s['end'])
        self.assertEqual(sha256(raw[END-p['ram']:-16]),s['code']['sha256'])
        self.assertEqual((s['save_format'],s['wire_version'],s['retained_card_state']['bytes']), (16,3,48))
        self.assertEqual(s['retained_scratch']['bytes'],120352)
        self.assertEqual(e['console_storage']['save_format'],16)
        self.assertEqual(r['save_codec']['active_storage_code'],s['code'])
        prefix=e['npc_extra']['events']['sky']['packet'];start=prefix['physical'];ram=prefix['ram']
        predecessor=prior['equipment_resources']['npc_extra']['events']['sky']['packet']
        before=base[predecessor['physical']:predecessor['physical']+predecessor['bytes']]
        restored=bytearray(image[start:start+prefix['bytes']])
        self.assertEqual(sha256(restored),prefix['sha256'])
        self.assertEqual(len(s['redirects']),30)
        for h in s['redirects']:
            at=h['address']-ram
            self.assertEqual(restored[at:at+8].hex(),h['after'])
            self.assertEqual(h['target'],s['code']['symbols'][h['name']])
            restored[at:at+8]=bytes.fromhex(h['before'])
        self.assertEqual(restored,before)
        blob=by_vrom(image)[BLOB].extract(image)
        for h,record in zip(s['collection_hooks'],r['clothing']['display']['readers']['collection_hooks']):
            at=h['address']-0x80460000
            self.assertEqual(blob[at:at+8].hex(),h['after']);self.assertEqual(record['after'],h['after'])
        boot=e['surface_bootstrap']['code'];at=e['blob_offset']+boot['symbols']['packets']-e['ram']
        packets=[struct.unpack_from('>4I',blob,at+i*boot.get('packet_stride',16))
                 for i in range(boot.get('packet_count',20))]
        self.assertIn((p['ram'],p['physical']|0x80000000,p['bytes']),[row[:3] for row in packets])
        for ram,physical,size,crc in packets:
            if physical&0x80000000:data=image[physical&0x7FFFFFFF:(physical&0x7FFFFFFF)+size]
            else:
                entry=next(f for f in by_vrom(image).values() if f.vstart<=physical<f.vend)
                data=entry.extract(image)[physical-entry.vstart:physical-entry.vstart+size]
            self.assertEqual(zlib.crc32(data),struct.unpack_from('>I',blob,e['blob_offset']+crc-e['ram'])[0])
        for path,digest in d['sources'].items():self.assertEqual(sha256((ROOT/path).read_bytes()),digest,path)
        self.assertEqual(apply_ups((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes(),
            (OUT/'asset-loader.ups').read_bytes()),image)

    def test_connected_paper_catalogue_preserves_original_styles(self):
        image,r=inputs(OUT/'build-lock.json');base,prior=inputs(OUT/'base-lock.json')
        d=r['equipment_resources']['carried_items'];cat=d['paper']['catalogue']
        files,before=by_vrom(image),by_vrom(base)
        data,old=files[cat['vrom']].extract(image),before[cat['vrom']].extract(base)
        ram=cat['ram'];at=cat['list_address']-ram
        self.assertEqual(struct.unpack_from('>65H',data,at),(*range(64),67))
        self.assertEqual(struct.unpack_from('>2I',data,cat['descriptor']-ram),(cat['list_address'],65))
        self.assertEqual(sha256(data),cat['owner_sha256'])
        self.assertEqual(sha256(files[cat['reloc']].extract(image)),cat['relocation_sha256'])
        for table,kind in zip(cat['tables'],('background','lines')):
            self.assertEqual(table['count'],65);self.assertEqual(table['original_count'],64)
            a,b=table['address']-ram,table['original']-ram
            self.assertEqual(data[a:a+256],old[b:b+256])
            paper=d['paper'];binding=paper['bindings'][0]
            expected=(paper['ram']&0x1FFFFFFF)+paper['offsets'][binding[kind]]
            self.assertEqual(struct.unpack_from('>I',data,a+256)[0],expected)
        from v3_import_storage import jump
        self.assertEqual(struct.unpack_from('>I',data,0x808A6B80-ram)[0],
            jump(cat['code']['symbols']['af_carried_paper_init'],link=True))
        entry=r['catalogue']['code']['symbols']['af_v3_catalogue_bit']
        self.assertEqual(struct.unpack_from('>I',data,entry+8-ram)[0],
            jump(cat['code']['symbols']['af_carried_catalogue_bit']))
        allowed={p['address']-ram+i for p in cat['patches'] for i in range(4)}
        self.assertTrue(all(a==b or i in allowed for i,(a,b) in enumerate(zip(data,old))))

if __name__=='__main__':unittest.main()
