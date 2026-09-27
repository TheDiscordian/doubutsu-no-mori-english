"""Focused checks of changed spawning/persistence, not historical game builds."""
from pathlib import Path
import os
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import by_vrom,sha256,u32,apply_ups
from v3_asset_loader import BLOB
from v3_furniture_install import inputs
OUT=ROOT/os.environ.get('V3_CREATURE_CONNECTED_BUILD','build/v3-creature-world-work-01/connected-02')


class ConnectedTests(unittest.TestCase):
    def test_manager_through_source_calendar_and_saved_season(self):
        from v3_creature_spawns import calendars
        from v3_furniture_pipeline import Source
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                      (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        data,_=calendars(source,(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        with tempfile.TemporaryDirectory(prefix='af-creature-manager-') as directory:
            out=Path(directory);(out/'calendar.bin').write_bytes(data)
            p=subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-fno-pie','-no-pie',
                str(ROOT/'tests/v3_creature_manager_test.c'),'-o',str(out/'check')],
                capture_output=True,text=True,timeout=30)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)
            p=subprocess.run([str(out/'check'),str(out/'calendar.bin')],capture_output=True,text=True,timeout=10)
            self.assertEqual(p.returncode,0,p.stdout+p.stderr)

    def test_complete_save_extension_and_forward_migration(self):
        with tempfile.TemporaryDirectory(prefix='af-creature-save-') as directory:
            out=Path(directory)
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-DAF_V3_CLOTHING_PROFILE=1','-DAF_V3_REWARD_PROFILE=1','-DAF_V3_SURFACE_PROFILE=1']
            def run(args):
                p=subprocess.run(args,capture_output=True,text=True,timeout=30)
                self.assertEqual(p.returncode,0,p.stdout+p.stderr)
                return p.stdout
            for label,extra in (('legacy',[]),('console_canonical',['-DAF_V3_CREATURE_PROFILE=1'])):
                run(['cc',*flags,*extra,f'-Daf_v3_save_check=af_{label}_check',
                    f'-Daf_v3_save_pack=af_{label}_pack',f'-Daf_v3_save_collect=af_{label}_collect',
                    '-c',str(ROOT/'overlays/v3/save_codec.c'),'-o',str(out/(label+'.o'))])
            run(['cc',*flags,'-Daf_v3_save_compress=af_legacy_compress','-Daf_v3_save_expand=af_legacy_expand',
                 '-c',str(ROOT/'overlays/v3/save_compressed.c'),'-o',str(out/'legacy-compress.o')])
            run(['cc',*flags,'-DAF_V3_CREATURE_PROFILE=1','-DAF_V3_CONSOLE_STORAGE=1',
                *[str(ROOT/p) for p in ('tests/v3_console_storage_test.c','overlays/v3/save_runtime.c',
                    'overlays/v3/console_storage.c','overlays/v3/save_compressed.c','overlays/v3/creature_spawns.c')],
                *map(str,out.glob('*.o')),'-o',str(out/'check')])
            self.assertIn('native-adapter host assertions',run([str(out/'check')]))

    @unittest.skipUnless((OUT/'build-lock.json').exists(),'Current connected creature build required')
    def test_installed_connected_world_save_and_composition(self):
        image,r=inputs(OUT/'build-lock.json');base,prior=inputs(OUT/'base-lock.json')
        files=by_vrom(image);oldfiles=by_vrom(base);blob=files[BLOB].extract(image)
        e=r['equipment_resources'];world=e['creature_fish']['world'];p=world['packet'];save=world['save']
        raw=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(p['bytes'],0xB000);self.assertEqual(sha256(raw),p['sha256'])
        self.assertEqual(zlib.crc32(raw),p['crc32']);self.assertTrue(world['spawn_manager_installed'])
        for code,offset in ((world['compiled'],0),(save['codec'],0x4000),
                            (save['runtime'],0x6000),(save['helpers'],0xA000)):
            self.assertEqual(sha256(raw[offset:offset+code['bytes']]),code['sha256'])
        self.assertEqual(raw[-16:],bytes.fromhex('AF465748')*4)
        oldworld=prior['equipment_resources']['creature_fish']['world'];oldp=oldworld['packet']
        oldblob=oldfiles[BLOB].extract(base)
        self.assertEqual(raw[0x3000:0x4000],oldblob[oldp['blob_offset']+0x3000:oldp['blob_offset']+0x4000])
        for rows,packet in ((save['stable_console_entries'],e['console_storage']['packet']),
                            (save['stable_canonical_entries'],r['room_surfaces']['items'])):
            data=blob[packet['blob_offset']:packet['blob_offset']+packet['bytes']]
            self.assertEqual(sha256(data),packet['sha256'])
            for row in rows:
                pos=row['address']-packet['ram']
                self.assertEqual(data[pos:pos+8].hex(),row['after'])
                self.assertTrue(0x8064E000<=row['target']<0x80654000)
        stable={p['name'] for p in save['stable_console_entries']}
        self.assertTrue({p['name'] for p in prior['save_runtime']['code']['dispatch']}<=stable)
        for owner in world['manager_owners']:
            data=files[owner['vrom']].extract(image);before=oldfiles[owner['vrom']].extract(base)
            self.assertEqual(sha256(data),owner['sha256']);restored=bytearray(data)
            for patch in owner['patches']:
                pos=patch['address']-owner['ram']
                previous=patch['before'];updated=patch['after']
                previous=struct.pack('>I',previous) if isinstance(previous,int) else bytes.fromhex(previous)
                updated=struct.pack('>I',updated) if isinstance(updated,int) else bytes.fromhex(updated)
                self.assertEqual(data[pos:pos+len(updated)],updated);restored[pos:pos+len(previous)]=previous
            self.assertEqual(restored,before)
            if 'reloc' in owner:self.assertEqual(files[owner['reloc']].extract(image),oldfiles[owner['reloc']].extract(base))
        self.assertEqual(r['save_codec']['format_version'],7);self.assertEqual(r['save_codec']['canonical_format_version'],6)
        self.assertEqual(r['save_runtime']['state_bytes'],1264);self.assertEqual(r['save_runtime']['guard_ram'],0x8046C4E0)
        for name in ('creature_items','creature_field','console_images','room_goods','room_carry'):
            self.assertEqual(e[name]['packet'],prior['equipment_resources'][name]['packet'])
        self.assertEqual(r['physical_resources'],prior['physical_resources'])
        from v3_furniture_pipeline import Source,rig_import_plan
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                      (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        inventory=dict(rows=[dict(item_id=p['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=p['source']['profile'])
            for p in e['creature_items']['profiles']])
        self.assertTrue(rig_import_plan(inventory,prior,{},category='creature-profile-assets',source=source)['creature_fish'])
        self.assertNotIn('creature_fish',rig_import_plan(inventory,r,{},category='creature-profile-assets',source=source))
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        self.assertEqual(apply_ups(original,(OUT/'asset-loader.ups').read_bytes()),image)
        import v3_optional_composition as composer
        saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUT/'build-lock.json');catalogue=composer.catalogue(image,r)
            self.assertEqual(len(catalogue),167)
            self.assertEqual(composer.compose(image,r,catalogue,composer.resolve(catalogue,list(catalogue)))[0],image)
            self.assertEqual(sha256(composer.compose(image,r,catalogue,composer.resolve(catalogue,[]))[0]),
                             r['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=saved


if __name__=='__main__':unittest.main()
