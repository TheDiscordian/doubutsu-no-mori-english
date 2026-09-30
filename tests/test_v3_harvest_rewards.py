"""Focused connected Harvest checks; native services remain recording doubles."""
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from aflib import sha256
OUT=ROOT/os.environ.get('V3_HARVEST_PREPARED','build/v3-harvest-connected-prepared-09')
LINKED=ROOT/os.environ.get('V3_HARVEST_LINKED','build/v3-harvest-connected-linked-18')
INSTALLED=ROOT/os.environ.get('V3_HARVEST_INSTALLED','build/v3-harvest-installed-08')


class HarvestTests(unittest.TestCase):
    def test_complete_native_model_reservations(self):
        from aflib import by_vrom
        from v3_furniture_install import inputs
        from v3_npc_draw import extend_model_reservations,OWNERS
        base,_=inputs(ROOT/'build/v3-password-only-imports-01/password-destinations/build-lock.json')
        files=by_vrom(base);changes={};rows=extend_model_reservations(base,changes,12480)
        self.assertEqual(len(rows),2)
        for row in rows:
            before=files[row['vrom']].extract(base);after=changes[row['vrom']]
            expected=bytearray(before)
            for patch in row['patches']:
                at=patch['address']-row['ram']
                self.assertEqual(before[at:at+4],bytes.fromhex(patch['before']))
                expected[at:at+4]=bytes.fromhex(patch['after'])
            self.assertEqual(after,expected)
            self.assertEqual(row['reserved_model_bytes'],12480)
            self.assertEqual(row['reserved_texture_bytes'],5664)
            self.assertEqual(row['slot_count'],10)
            self.assertEqual(row['additional_scene_bytes'],22400)
            self.assertTrue(row['streaming_clamp_unchanged'])
            self.assertTrue(row['allocation_failure_handling_unchanged'])
        for size in (0,10240,32768,-1):
            with self.assertRaises(ValueError):extend_model_reservations(base,{},size)
        # Refuse a changed second owner's real reservation helper atomically.
        vrom,_,ram,*_=OWNERS[1];changed=bytearray(files[vrom].extract(base))
        changed[0x809A0B34-ram]^=1
        rejected={vrom:bytes(changed)};previous=dict(rejected)
        with self.assertRaises(ValueError):extend_model_reservations(base,rejected,12480)
        self.assertEqual(rejected,previous)

    def test_complete_source_resources_and_native_contract(self):
        report=json.loads((OUT/'prepared.json').read_bytes())
        self.assertEqual(len(report['family'][0]['functions']),39)
        self.assertEqual(len(report['rewards']),12)
        self.assertEqual(len(report['dialogue']['rows']),36)
        self.assertEqual(report['native_layout']['saved_bytes'],22)
        self.assertEqual(report['native_layout']['actor_bytes'],2420)
        self.assertFalse(report['acquisition_installed'])
        self.assertEqual(report['native_contract']['event_areas']['data_bytes'],40)
        self.assertEqual(len(report['native_contract']['native_services']),10)
        self.assertEqual(len(report['native_contract']['player_callbacks']),3)
        for name,digest in report['generated_sha256'].items():
            self.assertEqual(sha256((OUT/name).read_bytes()),digest,name)
        self.assertEqual([row['source_item'] for row in report['rewards'][-2:]],[0x2642,0x2742])
        self.assertEqual([row['item'] for row in report['rewards'][-2:]],[0x264D,0x274D])
        self.assertEqual(report['registry']['owner_count'],28)
        self.assertEqual(report['registry']['rows'][-1]['profile'],0xF5)
        self.assertEqual(report['shared_motions']['added'],[385])
        linked=json.loads((LINKED/'connected.json').read_bytes())
        self.assertEqual(linked['preparation'],report)
        self.assertFalse(linked['installed'])
        for file,key in (('harvest.bin','code'),('franklin-pool.bin','pool')):
            self.assertEqual(sha256((LINKED/file).read_bytes()),linked[key]['sha256'])
        self.assertEqual(linked['pool']['bytes'],2704)
        self.assertEqual(linked['npc']['actor_bytes'],2420)
        self.assertEqual(linked['hiding']['classes'],11)
        self.assertEqual(len(linked['hiding']['functions']),26)
        self.assertEqual(len(linked['hiding']['tables']),9)
        for name,digest in linked['hiding']['generated_sha256'].items():
            self.assertEqual(sha256((LINKED/name).read_bytes()),digest)
        names=bytes.fromhex(linked['npc']['names_hex'])
        self.assertEqual(struct.unpack_from('>4I',names),(0x41464E49,1,9,16))
        self.assertEqual(names[-8:],b'Franklin')
        self.assertEqual(len(linked['npc']['identity_rebindings']),6)
        for row in linked['npc']['render_owners']:
            self.assertEqual(sha256((LINKED/row['file']).read_bytes()),row['sha256'])
        native=(LINKED/'npc-runtime.bin').read_bytes()
        self.assertEqual(sha256(native),linked['npc']['runtime_sha256'])
        at=linked['npc']['runtime']['symbols']['af_npc_identity_spawn']-0x806E4000
        self.assertEqual(struct.unpack_from('>I',native,at+0x4C)[0],0x2D41000A)
        manager=linked['manager']
        self.assertEqual(manager['control_count'],75)
        self.assertEqual(manager['retained_controls'],74)
        self.assertEqual(manager['daily_type_bound'],117)
        self.assertEqual(manager['additional_owner_bytes'],32)
        self.assertTrue(manager['original_controls_and_relocations_retained'])
        self.assertFalse(manager['installed'])
        owner=(LINKED/'harvest-manager.bin').read_bytes()
        relocation=(LINKED/'harvest-manager-reloc.bin').read_bytes()
        core=(LINKED/'harvest-core.bin').read_bytes()
        self.assertEqual(sha256(owner),manager['sha256'])
        self.assertEqual(sha256(relocation),manager['relocation_sha256'])
        self.assertEqual(sha256(core),manager['core_sha256'])
        self.assertEqual(struct.unpack_from('>5I',relocation)[:4],(len(owner),0,0,0))
        self.assertEqual(struct.unpack_from('>8I',owner,len(owner)-32),
            (116,*(manager['callbacks'][name] for name in ('start','stop','in','out','behind')),0,0))
        from aflib import CODE_RAM
        for patch in manager['core_patches']:
            after=bytes.fromhex(patch['after']);at=patch['address']-CODE_RAM
            self.assertEqual(core[at:at+len(after)],after)

    def test_current_cartridge_installs_complete_connected_resources(self):
        from aflib import by_vrom,CODE_RAM,CODE_VROM
        from v3_asset_loader import BLOB,BLOB_RAM
        from v3_furniture_install import inputs
        from v3_npc_registry import TABLE,DMA
        from v3_npc_native import IDENTITIES,BRIDGES
        base,prior=inputs(ROOT/'build/v3-password-only-imports-01/password-destinations/build-lock.json')
        image,report=inputs(INSTALLED/'build-lock.json')
        h=report['equipment_resources']['harvest'];e=report['equipment_resources']
        files=by_vrom(image);old_files=by_vrom(base)
        blob=files[BLOB].extract(image);old_blob=old_files[BLOB].extract(base)
        self.assertTrue(h['installed']);self.assertFalse(h['selectable'])
        self.assertEqual(report['runtime_abi'],379)
        self.assertEqual(report['save_codec']['format_version'],prior['save_codec']['format_version'])
        p=h['packet'];packet=image[p['physical']:p['physical']+p['bytes']]
        self.assertEqual(sha256(packet),p['sha256']);self.assertEqual(packet[-16:],b'AFHV'*4)
        code=(LINKED/'harvest.bin').read_bytes();pool=(LINKED/'franklin-pool.bin').read_bytes()
        self.assertEqual(packet[:len(code)],code)
        at=h['pool']['ram']-p['ram'];self.assertEqual(packet[at:at+len(pool)],pool)
        t=h['object_table'];at=t['ram']-p['ram'];table=packet[at:at+t['bytes']]
        self.assertEqual(sha256(table),t['sha256'])
        self.assertEqual(table[:460*8],old_blob[0x1000:0x1000+460*8])
        self.assertEqual(blob[0x1E60:0x1FF0],old_blob[0x1E60:0x1FF0])
        asset=report['asset'];asset_before=prior['asset'];start=0x100
        expected=bytearray(old_blob[start:start+asset_before['bytes']])
        for row in (asset['object_table_patch'],asset['npc_capacity_patch']):
            offset=row['address']-BLOB_RAM-start;before=bytes.fromhex(row['before']);after=bytes.fromhex(row['after'])
            self.assertEqual(expected[offset:offset+len(before)],before)
            expected[offset:offset+len(after)]=after
        self.assertEqual(blob[start:start+asset['bytes']],expected)
        self.assertEqual(len(t['native_streaming_rebindings']),2)
        for row in t['native_streaming_rebindings']:
            owner=files[row['vrom']].extract(image);at=row['address']-row['ram']
            self.assertEqual(owner[at:at+8],bytes.fromhex(row['after']))
            self.assertTrue(row['relocations_unchanged'])
        self.assertEqual(len(t['native_model_reservations']),2)
        for row in t['native_model_reservations']:
            before=old_files[row['vrom']].extract(base);owner=files[row['vrom']].extract(image)
            for span in row['verified_native_spans']:
                first,last=span['start']-row['ram'],span['end']-row['ram']
                self.assertEqual(sha256(before[first:last]),span['sha256'])
                expected=bytearray(before[first:last])
                for patch in row['patches']:
                    at=patch['address']-row['ram']-first
                    if 0<=at<len(expected):expected[at:at+4]=bytes.fromhex(patch['after'])
                self.assertEqual(owner[first:last],expected)
            self.assertEqual(row['model_bytes'],12480)
            self.assertEqual(row['reserved_model_bytes'],12480)
            self.assertEqual(row['additional_scene_bytes'],22400)
        for b in e['npc_extra']['banks'][-2:]:
            self.assertEqual(struct.unpack_from('>2I',table,b['bank']*8),(b['vrom'],b['vrom']+b['bytes']))
            self.assertEqual(sha256(image[b['physical']:b['physical']+b['bytes']]),b['sha256'])
        npc=e['npc_extra'];p=npc['packet'];registry=image[p['physical']:p['physical']+p['bytes']]
        old=prior['equipment_resources']['npc_extra']['packet'];previous=base[old['physical']:old['physical']+old['bytes']]
        self.assertEqual(struct.unpack_from('>4I',registry,TABLE),(0x41464E58,1,9,44))
        self.assertEqual(registry[TABLE+16:TABLE+16+8*44],previous[TABLE+16:TABLE+16+8*44])
        self.assertEqual(registry[IDENTITIES+16:IDENTITIES+144],previous[IDENTITIES+16:IDENTITIES+144])
        self.assertEqual(registry[IDENTITIES:BRIDGES],bytes.fromhex(h['npc']['names_hex']))
        self.assertEqual(struct.unpack_from('>I',registry,DMA+8)[0],14)
        manager=h['manager'];owner=files[manager['vrom']].extract(image)
        self.assertEqual(sha256(owner),manager['sha256'])
        self.assertEqual(owner,(LINKED/'harvest-manager.bin').read_bytes())
        self.assertEqual(files[manager['reloc']].extract(image),(LINKED/'harvest-manager-reloc.bin').read_bytes())
        core=files[CODE_VROM].extract(image)
        for patch in manager['core_patches']:
            at=patch['address']-CODE_RAM;after=bytes.fromhex(patch['after'])
            self.assertEqual(core[at:at+len(after)],after)
        boot=e['surface_bootstrap']['code']
        self.assertLessEqual(boot['bytes'],0x2B0)
        self.assertIn('harvest_crc',boot['symbols'])
        self.assertEqual(boot['packet_count'],23)
        start=e['blob_offset']+boot['symbols']['packets']-e['ram']
        descriptor=struct.unpack_from('>4I',blob,start+(boot['packet_count']-1)*16)
        harvest_packet=h['packet']
        self.assertEqual(descriptor,(harvest_packet['ram'],harvest_packet['physical']|0x80000000,
            harvest_packet['bytes'],boot['symbols']['harvest_crc']))
        at=e['blob_offset']+boot['symbols']['harvest_crc']-e['ram']
        self.assertEqual(struct.unpack_from('>I',blob,at)[0],harvest_packet['crc32'])
        for row in h['text']['resources']:
            self.assertEqual(sha256(files[row['vrom']].extract(image)),row['sha256'])
        # Only the two declared shared packets change among retained physical
        # resources. No saved file or native historical scenario is replayed.
        changed={old['id'],prior['equipment_resources']['carried_items']['quest']['packet']['id']}
        current={r['id']:r for r in report['physical_resources']}
        for old in prior['physical_resources']:
            if old['id'] in changed:continue
            self.assertEqual(current[old['id']],old)
            self.assertEqual(image[old['physical']:old['physical']+old['bytes']],
                base[old['physical']:old['physical']+old['bytes']])

    def test_complete_actor_and_connected_native_adapters(self):
        with tempfile.TemporaryDirectory(prefix='v3-harvest-') as directory:
            target=Path(directory)/'check'
            flags=['-std=c11','-O1','-g','-Wall','-Wextra','-Werror',
                '-Wno-unused-variable','-Wno-unused-but-set-variable','-Wno-unused-parameter',
                '-Wno-parentheses','-Wno-cast-function-type','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(OUT),'-I'+str(LINKED),'-Ioverlays/v3']
            command=['cc',*flags,'tests/v3_harvest_event_test.c',
                'overlays/v3/harvest_state.c','overlays/v3/harvest_dialogue.c',
                'overlays/v3/harvest_world_native.c','overlays/v3/carried_handover.c',
                'overlays/v3/holiday_hiding.c','overlays/v3/harvest_manager.c',
                str(LINKED/'hiding-source.c'),str(LINKED/'hiding-manager-source.c'),
                str(OUT/'dialogue.c'),str(OUT/'reward-map.c'),'-lm','-o',str(target)]
            for cmd in (command,[str(target)]):
                result=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
