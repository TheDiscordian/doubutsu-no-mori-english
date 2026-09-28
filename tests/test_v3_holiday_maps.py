"""Complete layout/category check; no emulator fixture or old-build execution."""
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from v3_furniture_pipeline import Source
from v3_holiday_maps import discover,encode,owner_source
from apply_translation import write_new


class HolidayMapsTests(unittest.TestCase):
    def test_connected_decoration_lifecycles_and_native_owners(self):
        import json
        import struct
        import zlib
        from aflib import by_vrom,CODE_RAM,CODE_VROM,sha256,u32
        from v3_asset_loader import BLOB
        from v3_furniture_install import inputs
        from v3_decoration_actor import RAM,END,CONTEXT,DATA_END,SERVICES,DESCRIPTORS,PROFILES
        from v3_registry import DECORATION_NAMES,DECORATION_PROFILES,DECORATION_DUMMIES
        from v3_holiday_structures import source_bundle
        from v3_password_policy import function
        current=ROOT/'build/v3-diary-category-work-01/decoration-services-installed-02'
        image,report=inputs(current/'build-lock.json')
        base,prior=inputs(current/'base-lock.json')
        e=report['equipment_resources'];d=e['npc_extra']['events']['decorations'];c=d['controllers']
        p=e['holiday_state']['packet'];raw=image[p['physical']:p['physical']+p['bytes']]
        original=c['input_packet'];old=base[original['physical']:original['physical']+original['bytes']]
        self.assertTrue(c['refresh'])
        self.assertEqual((p['physical'],p['bytes']),(original['physical'],original['bytes']))
        self.assertEqual(len(report['physical_resources']),len(prior['physical_resources']))
        self.assertEqual(p['ram']+len(raw),END)
        self.assertEqual(zlib.crc32(raw),p['crc32'])
        self.assertEqual(sha256(raw),p['sha256'])
        self.assertEqual(raw[-16:],b'AFHS'*4)
        for preserved in c['preserved']:
            at=preserved['ram']-p['ram'];n=preserved['bytes']
            self.assertEqual(raw[at:at+n],old[at:at+n])
        self.assertEqual(raw[:CONTEXT-p['ram']],old[:CONTEXT-p['ram']])
        self.assertEqual(raw[DATA_END-p['ram']:RAM-p['ram']],old[DATA_END-p['ram']:RAM-p['ram']])
        for part in ('loaded_code','data'):
            a=c[part];offset=a['ram']-p['ram']
            self.assertEqual(sha256(raw[offset:offset+a['bytes']]),a['sha256'])
        self.assertLessEqual(c['loaded_code']['bytes'],END-RAM-16)
        s=c['code']['symbols'];at=s['af_decor_actor_records']-p['ram']
        self.assertEqual(len(c['profiles']),11)
        rows=list(struct.iter_unpack('>6H5I',raw[at:at+18*32]))
        self.assertEqual({r[0]:r[1] for r in rows},DECORATION_NAMES)
        for r in rows:
            owner=c['owners'][r[3]]
            self.assertEqual(r[2],DECORATION_PROFILES[owner['owner']])
            self.assertEqual(r[6],owner['dependencies'])
            self.assertTrue(r[6]&2)
            self.assertEqual(r[5],DECORATION_DUMMIES.get(r[4],0))
            self.assertEqual(r[5],owner['native_dummy'])
            self.assertEqual(r[7:],tuple(s[owner['entries'][phase]] for phase in ('ctor','dtor','init','move')))
        for i,row in enumerate(c['profiles']):
            descriptor=struct.unpack_from('>8I',raw,DESCRIPTORS+i*32-p['ram'])
            self.assertEqual(descriptor,(0,0,0,0,0,PROFILES+i*36,0,0))
            profile=struct.unpack_from('>HHIHH6I',raw,PROFILES+i*36-p['ram'])
            self.assertEqual(profile,(row['profile'],0,row['native_flags'],row['name'],3,0x2D8,
                *(s['af_decor_actor_'+phase] for phase in ('ctor','dtor','init','draw')),0))
        self.assertEqual(struct.unpack_from('>4I',raw,SERVICES-p['ram']),
            (7,*(s['af_decor_actor_'+n] for n in ('demo','resolve','effect'))))
        self.assertFalse(any(raw[SERVICES+16-p['ram']:SERVICES+0xF0-p['ram']]))
        self.assertEqual(c['timing'],dict(source_hz=60,native_hz=30,movement_substeps=2,
            draw_substeps=2,geometry_submissions=1))
        # All marker mappings are bound; the remaining fishing/Harvest services
        # are not represented as successful providers.
        self.assertEqual(sum(bool(r[5]) for r in rows),18)
        # Inspect the changed cartridge and restore only declared patches for
        # comparison with its input. This never executes an older cartridge.
        files=by_vrom(image);basefiles=by_vrom(base)
        for marker in c['native_markers']:
            body=files[marker['vrom']].extract(image)
            self.assertEqual(sha256(body),marker['sha256'])
            self.assertEqual(u32(body,marker['address']-marker['ram']),0x34040000|marker['native'])
        for row in c['marker_consumers']:
            body=files[row['vrom']].extract(image)[row['start']-row['ram']:row['end']-row['ram']]
            self.assertEqual(sha256(body),row['sha256'])
        self.assertEqual(c['additive_markers'],dict(Ghog_Profile=dict(source=0xF125,native=0xF300),
            Htable_Profile=dict(source=0xF126,native=0xF301)))
        for vrom in {h['vrom'] for h in c['hooks']}:
            changed=bytearray(files[vrom].extract(image))
            for h in c['hooks']:
                if h['vrom']!=vrom:continue
                off=h['address']-h['ram'];after=bytes.fromhex(h['after'])
                self.assertEqual(changed[off:off+len(after)],after)
                changed[off:off+len(after)]=bytes.fromhex(h['before'])
            self.assertEqual(changed,basefiles[vrom].extract(base))
        self.assertEqual(files[0x008CD350].extract(image),basefiles[0x008CD350].extract(base))
        core=files[CODE_VROM].extract(image)
        for row in c['native_functions']:
            # Actor_info_make_actor contains the intentional descriptor hook.
            if row['symbol']=='Actor_info_make_actor':continue
            self.assertEqual(sha256(core[row['start']-CODE_RAM:row['end']-CODE_RAM]),row['sha256'])
        for i,owner in enumerate(c['owners']):
            root=next(n for n in owner['references'] if n.endswith('.c'))
            text,refs=source_bundle(ROOT/'local/ac-decomp'/root)
            self.assertEqual(refs,owner['references'])
            for name,digest in owner['source_functions'].items():
                self.assertEqual(sha256(function(text,name).encode()),digest)
            generated=(current/'decoration-actors'/f'owner-{i:02}.c').read_bytes()
            self.assertEqual(sha256(generated),owner['generated_sha256'])
            self.assertIn(b'af_decor_source_move_install',generated)
            self.assertNotIn(b'mv_proc =',generated)
            if owner['owner']=='Count02_Profile':
                draw=function(text,'aCOU_actor_draw')
                self.assertEqual(sha256(draw.encode()),owner['draw_tick_source_sha256'])
                import re
                tail=re.search(r'(\n    if \(actor->arg0 != actor->arg1\) \{.*\n    \})\n\}$',draw,re.S)[1]
                self.assertEqual(sha256(tail.encode()),owner['draw_tick_tail_sha256'])
                self.assertIn(tail.encode(),(current/'decoration-actors/registry.c').read_bytes())
        # Refreshes retain the original fallback chain, rather than linking
        # the new descriptor/setup back to the previous module at the same RAM.
        self.assertEqual(s['af_decor_previous_descriptor'],
            prior['equipment_resources']['npc_extra']['code']['symbols']['af_v3_npc_extra_descriptor'])
        self.assertEqual(s['af_decor_previous_setup'],
            prior['campsite_exterior']['code']['symbols']['af_v3_campsite_structure_setup'])
        self.assertEqual(report['save_codec'],prior['save_codec'])
        self.assertEqual(report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        boot=e['surface_bootstrap']['code'];blob=files[BLOB].extract(image)
        boot_ram=e['surface_bootstrap']['ram'];offset=e['blob_offset']+boot_ram-e['ram']
        code=blob[offset:offset+boot['bytes']];s=boot['symbols']
        self.assertEqual(sha256(code),boot['sha256'])
        self.assertEqual(u32(code,s['holiday_state_crc']-boot_ram),p['crc32'])
        self.assertEqual(struct.unpack_from('>5I',code,s['packets']-boot_ram+17*20),
            (p['ram'],p['physical']|0x80000000,p['bytes'],s['holiday_state_crc'],0))
        self.assertFalse(c['actors_active']);self.assertFalse(d['selectable'])
        self.assertFalse(c['native_execution_verified']);self.assertFalse(c['services_bound'])
        self.assertEqual(json.loads((current/'decoration-actors/installed.json').read_bytes()),c)

    def test_connected_decoration_render_collision_and_startup(self):
        import json
        import struct
        from aflib import by_vrom,CODE_RAM,CODE_VROM,sha256,u32
        from v3_asset_loader import BLOB
        from v3_furniture_install import inputs
        from v3_holiday_structures import PREPARED,prepared_packet
        from v3_decoration_draw import RAM,TABLE,ART,END,resources,BOUNDS
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        current=ROOT/'build/v3-diary-category-work-01/decoration-draw-installed-04'
        image,report=inputs(current/'build-lock.json')
        # Read the unchanged input for preservation; never run an old build.
        base,prior=inputs(current/'base-lock.json')
        e=report['equipment_resources'];d=e['npc_extra']['events']['decorations'];r=d['renderer']
        p=e['holiday_state']['packet'];raw=image[p['physical']:p['physical']+p['bytes']]
        old=r['original_packet'];prefix=base[old['physical']:old['physical']+old['bytes']]
        self.assertEqual(raw[:len(prefix)],prefix)
        self.assertEqual(p['ram']+len(raw),END)
        self.assertEqual(raw[-16:],bytes.fromhex('41464853')*4)
        art,metadata=prepared_packet(source,PREPARED)
        self.assertEqual(raw[ART-p['ram']:ART-p['ram']+len(art)],art)
        table,symbols,rigs,palettes,shadows=resources(source,metadata)
        self.assertEqual(set(BOUNDS),set(metadata['owners']))
        self.assertEqual(len(rigs),2)
        self.assertEqual(shadows,r['shadows'])
        self.assertEqual(len(r['bindings']),18)
        self.assertEqual(sum(bool(b['collision']) for b in r['bindings']),15)
        for i,b in enumerate(r['bindings']):
            o=next(o for o in r['owners'] if o['owner']==b['owner']);rig=rigs.get(b['owner'],{})
            self.assertEqual(b['draw'],r['code']['symbols'][o['entry']])
            self.assertEqual(b['collision'],r['code']['symbols'][o['collision_entry']] if o['collision_entry'] else 0)
            struct.pack_into('>HH5I',table,i*24,b['source_name'],list(metadata['owners']).index(b['owner']),
                rig.get('base',0),rig.get('skeleton',0),rig.get('animation',0),b['draw'],b['collision'])
        self.assertEqual(raw[TABLE-p['ram']:TABLE-p['ram']+len(table)],table)
        for part in ('loaded_code','tables','artwork'):
            block=r[part];at=block['ram']-p['ram']
            self.assertEqual(sha256(raw[at:at+block['bytes']]),block['sha256'])
        for name,address in symbols.items():
            if not name.startswith('af_decor_list_'):continue
            words=struct.unpack_from('>6I',table,address-TABLE)
            self.assertEqual(words[::2],(0xDB060018,0xDE000000,0xDF000000))
            self.assertTrue((ART&0x1FFFFFFF)<=words[1]<((ART+len(art))&0x1FFFFFFF))
            self.assertTrue(ART<=words[3]<ART+len(art))
        corrected=next(s for s in shadows if s['symbol']=='aYAT_shadow_data_r')
        self.assertEqual(corrected['count'],7)
        # Native functions and the old actor-hook chain are untouched.
        core=by_vrom(image)[CODE_VROM].extract(image)
        self.assertEqual(core,by_vrom(base)[CODE_VROM].extract(base))
        for row in r['native_functions']:
            self.assertEqual(sha256(core[row['start']-CODE_RAM:row['end']-CODE_RAM]),row['sha256'])
        self.assertEqual(report['save_codec'],prior['save_codec'])
        self.assertEqual(report['save_runtime']['profile_hex'],prior['save_runtime']['profile_hex'])
        boot=e['surface_bootstrap']['code'];blob=by_vrom(image)[BLOB].extract(image)
        boot_ram=e['surface_bootstrap']['ram'];offset=e['blob_offset']+boot_ram-e['ram']
        code=blob[offset:offset+boot['bytes']];s=boot['symbols']
        self.assertEqual(sha256(code),boot['sha256'])
        self.assertEqual(u32(code,s['holiday_state_crc']-boot_ram),p['crc32'])
        self.assertEqual(struct.unpack_from('>5I',code,s['packets']-boot_ram+17*20),
            (p['ram'],p['physical']|0x80000000,p['bytes'],s['holiday_state_crc'],0))
        self.assertFalse(d['actors_installed']);self.assertFalse(d['selectable'])
        self.assertFalse(r['native_execution_verified'])
        self.assertEqual(json.loads((current/'decoration-draw/installed.json').read_bytes()),r)

    def test_complete_decoration_batch_and_current_cartridge(self):
        import json
        import struct
        from aflib import by_vrom, CODE_VROM, sha256
        from v3_furniture_install import inputs
        from v3_holiday_structures import Source, PREPARED, prepared_packet, plans, discover
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        data,art=prepared_packet(source,PREPARED)
        current=ROOT/'build/v3-diary-category-work-01/decorations-installed-01'
        image,report=inputs(current/'build-lock.json')
        installed=report['equipment_resources']['npc_extra']['events']['decorations']
        resource=installed['packet'];at=resource['physical']
        self.assertEqual(image[at:at+resource['bytes']],data)
        self.assertEqual(sha256(data),resource['sha256'])
        self.assertEqual((len(art['bindings']),len(art['owners']),len(art['objects'])),(18,11,32))
        self.assertFalse(installed['actors_installed']);self.assertFalse(installed['selectable'])
        # Check newly emitted native commands against the complete parsed
        # source, not merely a checksum produced by the same emitter.
        batch,_=plans(source,discover(source))
        for plan,obj in zip(batch,art['objects'],strict=True):
            asset=data[obj['packet_offset']:obj['packet_offset']+obj['object_bytes']]
            for model in obj['models']:
                first=model['native_offset'];last=first+model['bytes']
                words=list(struct.iter_unpack('>II',asset[first:last]))
                parsed=plan['prepared'][4][model['layer']]['rows']
                for op in (0xFC,0xE2):
                    self.assertEqual([r for r in words if r[0]>>24==op],
                        [tuple(r['words']) for r in parsed if r['opcode']==op])
                dynamic=[r['dynamic_vertices'] for r in parsed if 'dynamic_vertices' in r]
                self.assertEqual([b for a,b in words if a>>24==1 and b>>24==8],dynamic)
                self.assertEqual(sum(2 if a>>24==6 else 1 if a>>24==5 else 0 for a,b in words),
                    sum(len(r.get('triangles',[])) for r in parsed))
                self.assertEqual(words[-1],(0xDF000000,0))
        rigs=[r for r in art['objects'] if r['rig']]
        self.assertEqual(len(rigs),2)
        for row in rigs:
            self.assertIn('animations',row['rig'])
        digit=next(r for r in rigs if r['draw_context']['callback_adapter'].get('material_frames'))
        frames=digit['draw_context']['callback_adapter']['material_frames']
        self.assertEqual([r['segment_address'] for r in frames],[0x08000000,0x09000000])
        self.assertEqual([len(r['frames']) for r in frames],[10,10])
        self.assertEqual(len([r for r in digit['resources'] if r['kind']=='texture']),10)
        corrected=[s for o in art['owners'].values() for s in o['shadows'] if s['source_count_exceeds_arrays']]
        self.assertEqual([(s['source_count'],s['projection_count']) for s in corrected],[(10,7)])
        # A resource-only stage changes no native owner, resident packet,
        # saved field, or profile. Reading the predecessor is not executing it.
        previous=ROOT/'build/v3-diary-category-work-01/state-transition-connected-01'
        base,old=inputs(previous/'build-lock.json')
        self.assertEqual(report['save_codec'],old['save_codec'])
        self.assertEqual(by_vrom(image)[CODE_VROM].extract(image),by_vrom(base)[CODE_VROM].extract(base))
        for key in ('npc_extra','holiday_state'):
            p=old['equipment_resources'][key]['packet'];first=p['physical'];last=first+p['bytes']
            self.assertEqual(image[first:last],base[first:last])

    def test_native_binding_contract(self):
        from v3_holiday_maps import native_contract
        from v3_furniture_install import inputs
        from v3_holiday_placement import BINDINGS
        image,_=inputs(ROOT/'build/v3-diary-category-work-01/tortimer-state-05/build-lock.json')
        contract=native_contract(image)
        self.assertEqual(contract['game_context'],0x8010EF90)
        self.assertEqual(BINDINGS['af_holiday_native_game'],contract['game_context'])

    def test_connected_layout_and_source_owners(self):
        source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
            (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
        report=discover(source);packet=encode(report);generated,owners=owner_source(source)
        self.assertEqual(len(report['maps']),17)
        self.assertEqual(sum(r.get('variants',0) for r in report['maps']),52)
        self.assertEqual(len(owners['owners']),14)
        expected=[]
        for row in report['maps']:
            for v,actors in enumerate(row.get('layouts',[])):
                for i,a in enumerate(actors):expected.append((row['event'],v,i,a['source_name'],a['x'],a['z']))
        with tempfile.TemporaryDirectory(prefix='v3-holiday-maps-') as temp:
            out=Path(temp)
            write_new(out/'owners.c',generated.encode())
            text='static const unsigned char maps[]={'+','.join(map(str,packet))+'};\n'
            text+='static const unsigned int expected[][6]={'+','.join('{'+','.join(map(str,r))+'}' for r in expected)+'};\n'
            write_new(out/'holiday-maps-data.h',text.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer',
                '-I'+str(ROOT/'overlays/v3'),'-I'+str(out),'tests/v3_holiday_maps_test.c',
                'overlays/v3/holiday_reserved.c',str(out/'owners.c'),'-o',str(out/'check')]
            for cmd in (command,[str(out/'check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())
            # Same generated source and data; exercise the complete new native
            # adapter in this batch, without replaying a cartridge fixture.
            from v3_holiday_native import identities
            from v3_holiday_events import discover as event_discover,encode as event_encode
            ids,_=identities()
            arrays=(('af_holiday_native_ids',ids[:128]),('af_holiday_source_ids',ids[128:]),
                ('af_holiday_event_data',event_encode(event_discover(source))))
            native_data='#include "holiday-maps-data.h"\n'+'\n'.join('const unsigned char '+name+'[]={'+
                ','.join(map(str,data))+'};' for name,data in arrays)+'\n'
            write_new(out/'holiday-native-data.h',native_data.encode())
            command=['cc','-std=c11','-O1','-g','-Wall','-Wextra','-Werror','-fno-pie','-no-pie',
                '-fsanitize=address,undefined','-fno-omit-frame-pointer','-ffunction-sections',
                '-fdata-sections','-Wl,--gc-sections','-I'+str(ROOT/'overlays/v3'),'-I'+str(out),
                'tests/v3_holiday_dedicated_native_test.c',
                *(f'overlays/v3/{s}.c' for s in ('holiday_reserved','holiday_native','holiday_events')),
                str(out/'owners.c'),'-o',str(out/'native-check')]
            for cmd in (command,[str(out/'native-check')]):
                result=subprocess.run(cmd,cwd=ROOT,capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)
                if result.stdout:print(result.stdout.strip())


if __name__=='__main__':unittest.main()
