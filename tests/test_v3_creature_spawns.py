"""Whole-calendar conversion and the shared native-bound spawn algorithm."""
from pathlib import Path
import json
import os
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_creature_spawns import calendars,HEADER,CALENDARS
from v3_furniture_pipeline import Source
from v3_furniture_install import inputs
from v3_asset_loader import BLOB
from aflib import by_vrom,sha256,u32,apply_ups
from v3_player_actions import native_references

OUTPUT=ROOT/os.environ.get('V3_CREATURE_WORLD_BUILD','build/v3-creature-world-work-01/runtime')


class SpawnTests(unittest.TestCase):
    @unittest.skipUnless((OUTPUT/'build-lock.json').exists(),'Current fish world build required')
    def test_current_world_installation_and_optional_composition(self):
        import v3_creature_fish as fish
        image,report=inputs(OUTPUT/'build-lock.json');base,prior=inputs(OUTPUT/'base-lock.json')
        files=by_vrom(image);old=by_vrom(base);blob=files[BLOB].extract(image)
        world=report['equipment_resources']['creature_fish']['world'];p=world['packet']
        packet=blob[p['blob_offset']:p['blob_offset']+p['bytes']]
        self.assertEqual(len(packet),fish.WORLD_SIZE);self.assertEqual(sha256(packet),p['sha256'])
        self.assertEqual(sha256(packet[:world['compiled']['bytes']]),world['compiled']['sha256'])
        self.assertEqual(packet[-16:],struct.pack('>4I',*([0xAF465748]*4)))
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                      (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        original=(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()
        data,receipt=calendars(source,original)
        self.assertEqual(world['calendar'],json.loads(json.dumps(receipt)))
        self.assertEqual(packet[fish.WORLD_TABLE:fish.WORLD_TABLE+len(data)],data)
        self.assertEqual(u32(packet,world['patrol_mode']['ram']-fish.WORLD_RAM),0)
        self.assertFalse(world['spawn_manager_installed'])
        self.assertFalse(world['patrol_mode']['browser_selection_installed'])
        for r in world['owners']:
            owner=files[r['vrom']].extract(image);reloc=files[r['reloc']].extract(image)
            previous=old[r['vrom']].extract(base);prevrel=old[r['reloc']].extract(base)
            self.assertEqual(sha256(owner),r['sha256']);self.assertEqual(sha256(reloc),r['reloc_sha256'])
            self.assertEqual(reloc[:16],prevrel[:16]);self.assertEqual(len(owner),len(previous))
            restored=bytearray(owner)
            self.assertEqual(len(r['patches']),6)
            for patch in r['patches']:
                at=patch['address']-r['ram'];self.assertEqual(u32(owner,at),patch['after'])
                self.assertTrue(fish.WORLD_RAM<=patch['after']<fish.WORLD_RAM+world['compiled']['bytes'])
                struct.pack_into('>I',restored,at,patch['before'])
            self.assertEqual(restored,previous) # Includes all original functions and rod hooks.
            before=native_references(previous,prevrel,expected_sections=tuple(r['sections']))
            after=native_references(owner,reloc,expected_sections=tuple(r['sections']))
            self.assertEqual(set(before[2])-set(after[2]),set(r['removed_relocations']))
            self.assertFalse(set(after[2])-set(before[2]))
        startup=report['room_surfaces']['items']['bootstrap']['code']
        self.assertIn(f'-DAF_FISH_WORLD_VROM=0x{p["vrom"]:X}u',startup['flags'])
        self.assertIn(f'-DAF_FISH_WORLD_CRC=0x{p["crc32"]:X}u',startup['flags'])
        self.assertLessEqual(startup['bytes'],688)
        for key in ('save_runtime','save_codec','translation_baseline','physical_resources'):
            self.assertEqual(report[key],prior[key])
        self.assertEqual(apply_ups(original,(OUTPUT/'asset-loader.ups').read_bytes()),image)
        from v3_furniture_pipeline import rig_import_plan
        inventory=dict(rows=[dict(item_id=r['source_item_id'],asset_ready=True,installed=False,
            categories=['creature-profile-assets'],profile=r['source']['profile'])
            for r in report['equipment_resources']['creature_items']['profiles']])
        self.assertTrue(rig_import_plan(inventory,prior,{},category='creature-profile-assets',source=source)['creature_fish'])
        self.assertNotIn('creature_fish',rig_import_plan(inventory,report,{},category='creature-profile-assets',source=source))
        import v3_optional_composition as composer
        saved=composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI
        try:
            composer.use_build_lock(OUTPUT/'build-lock.json');catalogue=composer.catalogue(image,report)
            self.assertEqual(len(catalogue),167)
            self.assertEqual(composer.compose(image,report,catalogue,composer.resolve(catalogue,list(catalogue)))[0],image)
            empty=composer.compose(image,report,catalogue,composer.resolve(catalogue,[]))[0]
            self.assertEqual(sha256(empty),report['translation_baseline']['sha256'])
        finally:composer.BASE,composer.BASE_SHA,composer.REPORT_SHA,composer.ABI=saved

    def test_terrain_and_patrol_alternatives(self):
        with tempfile.TemporaryDirectory(prefix='af-world-') as directory:
            exe=Path(directory)/'check'
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_creature_world_test.c'),'-o',str(exe)],check=True)
            result=subprocess.run([str(exe)],capture_output=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            self.assertIn(b'pass',result.stdout)

    def test_source_calendars_and_connected_runtime(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
                      (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        data,report=calendars(source,(ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
        self.assertEqual(len(report['calendars']),CALENDARS)
        self.assertEqual({s for rows in report['calendars'] for s,_,_ in rows if s>=36},set(range(36,45)))
        cases=[]
        def expected(water,time,mask,rain,term,next_term,rate):
            rows=[]
            if water>=3:rate=1
            for p,(t,factor) in enumerate(((term,rate),(next_term,1-rate))):
                if p and not factor:break
                at=water*96+t*4+time if water<3 else 288+(water-3)*4+time
                for actor,area,weight in report['calendars'][at]:
                    if actor>=36 and not mask&(1<<(actor-36)):continue
                    if weight*factor:rows.append((actor,area,weight*factor))
                if water==0 and factor:
                    rows.append((1,0,report['native_herabuna_weights'][t*4+time]*factor))
                if not p and water in (1,4) and rain and time!=2:rows.append((31,4,2))
            return rows
        # Calendar/state boundaries, not a native scenario for each species.
        for water in range(5):
            for term in range(24 if water<3 else 1):
                for time in range(4):
                    at=water*96+term*4+time if water<3 else 288+(water-3)*4+time
                    offset,count=struct.unpack_from('>HH',data,HEADER+at*4)
                    self.assertEqual(list(struct.iter_unpack('>HBB',data[offset:offset+count*4])),
                                     report['calendars'][at])
                    for mask,rate,rain in ((511,1,0),(511,0.5,1),(0,1,1)):
                        next_term=(term+1)%24
                        rows=expected(water,time,mask,rain,term,next_term,rate)
                        case=struct.pack('>6IfI',water,time,mask,rain,term,next_term,rate,len(rows))
                        case+=b''.join(struct.pack('>IIf',*row) for row in rows)
                        cases.append(case)
        with tempfile.TemporaryDirectory(prefix='af-spawns-') as tmp:
            tmp=Path(tmp);fixture=tmp/'calendar.bin';exe=tmp/'check'
            fixture.write_bytes(struct.pack('>I',len(data))+data+struct.pack('>I',len(cases))+b''.join(cases))
            subprocess.run(['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                str(ROOT/'tests/v3_creature_spawns_test.c'),'-o',str(exe)],check=True)
            result=subprocess.run([str(exe),str(fixture)],capture_output=True,timeout=20)
            self.assertEqual(result.returncode,0,result.stderr.decode())
            self.assertIn(b'pass',result.stdout)


if __name__=='__main__':unittest.main()
