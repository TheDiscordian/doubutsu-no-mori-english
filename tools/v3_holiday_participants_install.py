"""Install the connected participant family, dialogue, rope, coin, and audio."""
import copy
import json
import os
import struct
import subprocess
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT,BLOB,compile_part

RAM=0x8073C010
SOURCES=('tools/v3_holiday_participants_install.py','overlays/v3/holiday_participants.ld',
    'tools/v3_event_text.py','tools/v3_physical_resources.py','tools/v3_sound_programs.py',
    'tools/v3_room_goods.py','overlays/v3/effect_loader.c','tools/v3_resource_capacity.py',
    'tools/v3_furniture_install.py','tools/v3_holiday_dialogue.py')
SOURCES+=('tools/v3_room_effects.py','tools/v3_holiday_sky.py')
SOURCES+=('tools/v3_holiday_active.py','overlays/v3/holiday_dispatch_native.c')
SOURCES+=('tools/v3_npc_registry.py','overlays/v3/npc_stream_draw.c')


def link(directory,prepared,output):
    """Link the checked prepared object, retaining every function and asset."""
    output.mkdir()
    raw=(directory/'participants.o').read_bytes()
    if prepared['object']['sha256']!=sha256(raw) or prepared['unbound_services']:
        raise ValueError('Incomplete prepared participant module')
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if result.returncode:raise ValueError(result.stderr)
        return result.stdout
    # Restate absolute bindings at final link: partial-link absolute symbols
    # otherwise lose the sign extension needed by MIPS R_MIPS_26 relocations.
    run('ld','-EB','-T','/source/overlays/v3/holiday_participants.ld',
        *(f'--defsym={n}=0x{v:X}' for n,v in prepared['bindings'].items()),
        '/source/'+str(directory.relative_to(ROOT))+'/participants.o',
        '-Map','participants.map','-o','participants.elf')
    if run('nm','--undefined-only','participants.elf').strip():raise ValueError('Unlinked participant service')
    symbols={n:int(a,16) for a,k,n in (s.split() for s in run('nm','--defined-only','participants.elf').splitlines())}
    run('objcopy','-O','binary','participants.elf','participants.bin')
    data=(output/'participants.bin').read_bytes();s=symbols
    if (s['af_hp_packet_start']!=RAM or s['af_hp_packet_end']!=RAM+len(data) or
            not RAM<s['af_hp_code_end']<=s['af_hp_bss_start']<s['af_hp_bss_end'] or
            any(data[s['af_hp_bss_start']-RAM:s['af_hp_bss_end']-RAM]) or
            data[-16:]!=b'AFHP'*4 or u32(data,s['af_hp_available']-RAM)!=0):
        raise ValueError('Changed participant code/state/admission bounds')
    write_new(output/'participants.asm',run('objdump','-d','participants.elf').encode())
    return data,dict(bytes=len(data),sha256=sha256(data),symbols=symbols,toolchain=IMAGE,
        code_bounds=[RAM,s['af_hp_code_end']],bss_bounds=[s['af_hp_bss_start'],s['af_hp_bss_end']])


def install(base,prior,blob,core,output,directory):
    from v3_console_disk_install import reservations
    from v3_holiday_participants import patch
    from v3_holiday_dialogue import check_provenance
    from v3_holiday_sky import profile_packet
    from v3_event_text import patch_bounds
    from v3_furniture_install import relocate_resource_plan
    from v3_furniture_pipeline import Source
    from v3_resource_capacity import checked_limit
    from v3_room_effects import restore_controller,extend_controller,RAM as OWNER_RAM
    from v3_room_rig_runtime import packet_layout
    from v3_sound_programs import install_audio_resources,permanent_budget
    import v3_physical_resources as physical
    directory=directory.resolve();raw=(directory/'prepared.json').read_bytes();prepared=json.loads(raw)
    if not directory.is_relative_to(ROOT/'build') or prepared['base_sha256']!=sha256(base):
        raise ValueError('Participants need their checked current preparation')
    for path,digest in prepared['sources'].items():
        if sha256((ROOT/path).read_bytes())!=digest:raise ValueError('Changed participant preparation source: '+path)
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra'];events=npc['events']
    if not events.get('sky') or events.get('participants'):raise ValueError('Participants need the complete sky baseline')
    work=output/'holiday-participants';work.mkdir();data,code=link(directory,prepared,work/'linked')
    end=RAM+len(data)
    if any(a<end and RAM<b for a,b in reservations(prior)):raise ValueError('Participants overlap resident memory')
    files=by_vrom(base);report=copy.deepcopy(prepared)
    report.update(code=code,prepared=str(directory.relative_to(ROOT)),prepared_sha256=sha256(raw),
        loaded_code=dict(ram=RAM,bytes=len(data),sha256=sha256(data)),
        additional_resident_bytes=len(data),installed=True,events_active=False,saved_format_changed=False)
    # Share the existing nineteenth startup entry; its sky prefix and guard
    # remain intact. All participant BSS is explicitly zero in this packet.
    sky=events['sky'];old=copy.deepcopy(sky['packet']);prefix=base[old['physical']:old['physical']+old['bytes']]
    if old['ram']+old['bytes']!=RAM or sha256(prefix)!=old['sha256']:
        raise ValueError('Changed complete retained sky packet')
    combined=prefix+data;records=copy.deepcopy(prior['physical_resources'])
    fresh=physical.allocate(base,records,combined,'holiday-sky-participants-GAFE01-r0',best_fit=True)
    records.append(fresh);packet=dict(fresh,ram=old['ram'],crc32=zlib.crc32(combined),storage='physical-ROM')
    report.update(packet=packet,preserved_sky_packet=old,preserved_prefix_bytes=len(prefix))
    sky['packet']=packet
    changes,hooks=patch(base,prepared,code['symbols'])
    patched=changes.pop(CODE_VROM);previous=files[CODE_VROM].extract(base)
    if bytes(core)!=previous:raise ValueError('Participant hooks overlap another core adapter')
    core[:]=patched;report['installed_hooks']=hooks
    text=report['dialogue'];check_provenance(text)
    text['choice_vrom']=prior['import_storage']['choice_vrom']
    text['hooks']=patch_bounds(core,text['first_id'],text['count'])
    at=0x80065544-CODE_RAM;before=0x2A010000|text['first_choice']
    after=0x2A010000|(text['first_choice']+text['choice_count'])
    if u32(core,at)!=before:raise ValueError('Changed complete participant choice bound')
    struct.pack_into('>I',core,at,after);text['hooks'].append(dict(address=at+CODE_RAM,before=before,after=after))
    for row in text['resources']:
        payload=(directory/row['file']).read_bytes()
        if len(payload)!=row['bytes'] or sha256(payload)!=row['sha256']:raise ValueError('Changed complete participant text')
        row['original_sha256']=row.pop('previous_sha256')
        name='holiday-participants/'+row['file'];write_new(output/name,payload);row['file']=name
    text['installed']=True
    audio=report['coin']['audio']
    for name,row in audio['files'].items():
        payload=(directory/name).read_bytes()
        if len(payload)!=row['bytes'] or sha256(payload)!=row['sha256']:raise ValueError('Changed participant sound')
    seq,bank,wave,audio_changes,audio_growth,heap_growth,heap_patches,budget,fire=install_audio_resources(
        base,prior,blob,core,(directory/'coin-sequence.bin').read_bytes(),
        {k:(directory/f'coin-{k}.bin').read_bytes() for k in ('font','wave')},audio)
    if set(changes)&set(audio_changes):raise ValueError('Participant owner changes overlap sound owners')
    changes.update(audio_changes);growth=[audio_growth] if audio_growth else []
    for v,payload in changes.items():
        if files[v].pend:
            _,row=relocate_resource_plan(base,files,v,payload,
                minimum_physical=files[BLOB].pstart+len(blob),reservations=records+growth,
                append_only=False,allow_compressed=True)
            growth.append(row)
    shared=equipment['sound_programs'];programs=audio['registered_programs'];tables=audio['registered_tables']
    shared.update(previous_sequence=copy.deepcopy(shared['sequence']),sequence=seq,
        before_budget=budget,after_budget=permanent_budget(core),native_synthesis_tested=False)
    shared.setdefault('trigger_batches',[]).append(dict(programs=programs,tables=tables))
    for key in ('furniture_audio','furniture_level_audio'):
        if key in equipment:equipment[key].update(sequence=copy.deepcopy(seq),font=copy.deepcopy(bank),
            wave=copy.deepcopy(wave),after_budget=copy.deepcopy(shared['after_budget']))
    trigger=equipment['furniture_audio'];trigger.update(
        programs=sorted(trigger['programs']+programs,key=lambda r:r['source_sound_word']),tables=tables,layout=audio['layout'])
    audio.update(installed=True,sequence=seq,font=bank,wave=wave,heap_growth=heap_growth,heap_patches=heap_patches)
    room=equipment['room_rigs'];effects=room['effects'];old_controller=effects['controller']
    if old_controller['count']!=119 or [r['id'] for r in effects['profiles']]!=list(range(111,119)):
        raise ValueError('Changed complete room/sky effect directory')
    native,reloc=restore_controller(files[old_controller['vrom']].extract(base),
        files[old_controller['reloc']].extract(base),old_controller)
    start=(len(blob)+15)&~15
    if BLOB+start+9*64>checked_limit(base,prior):raise ValueError('Effect profiles exceed shared import storage')
    blob.extend(bytes(start+9*64-len(blob)));profiles=[];additions=[]
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    unique=source.raw('eEC_effect_feature')
    if len(unique)!=126 or unique[118]!=0:raise ValueError('Changed complete coin duplicate policy')
    for i in range(9):
        at=start+64*i
        if i<8:
            row=copy.deepcopy(effects['profiles'][i]);p=row['blob_offset'];payload=bytes(blob[p:p+64])
            if sha256(payload)!=row['sha256']:raise ValueError('Changed retained effect profile')
            graphics=old_controller['additions'][i]['graphics'];policy=old_controller['additions'][i]['unique']
        else:
            callbacks=[code['symbols']['af_coin_'+role] for role in ('init','ct','mv','dw')]
            if any(p&3 or not RAM<=p<code['code_bounds'][1] for p in callbacks):raise ValueError('Coin callback outside code')
            tail=report['coin']['policy_hex']
            if tail!='fffe00ffc47a0cff':raise ValueError('Changed complete offering coin policy')
            payload=profile_packet(callbacks,tail,code_bounds=code['code_bounds'])
            row=dict(id=119,kind='coin',callbacks=callbacks,callback_owner='holiday-participants',policy_hex=tail)
            graphics=[0,0];policy=unique[118]
        blob[at:at+64]=payload
        row.update(blob_offset=at,vrom=BLOB+at,bytes=64,sha256=sha256(payload));profiles.append(row)
        r=0x80700000+i*0x100
        additions.append(dict(id=111+i,overlay=[BLOB+at,BLOB+at+32,r,r+32,r],graphics=graphics,unique=policy))
    lo,hi,_=packet_layout(room);sky_code=sky['loaded_code']
    loader=compile_part('effect_loader',work/'effect-loader',defines=(
        f'AF_EFFECT_PROFILES=0x{BLOB+start:X}u','AF_EFFECT_COUNT=9u','AF_EFFECT_ROOM_COUNT=4u','AF_EFFECT_SKY_COUNT=4u',
        f'AF_EFFECT_CODE_START=0x{lo:X}u',f'AF_EFFECT_CODE_END=0x{hi:X}u',
        f'AF_EFFECT_SKY_START=0x{sky_code["ram"]:X}u',f'AF_EFFECT_SKY_END=0x{sky_code["ram"]+sky_code["bytes"]:X}u',
        f'AF_EFFECT_PARTICIPANT_START=0x{RAM:X}u',f'AF_EFFECT_PARTICIPANT_END=0x{code["code_bounds"][1]:X}u'))
    owner,fixed,controller=extend_controller(native,reloc,additions,loader=loader,graphics_vrom=effects['bank']['vrom'])
    at=0x801010B0-CODE_RAM;before=bytes.fromhex(old_controller['descriptor']['after'])
    if core[at:at+32]!=before:raise ValueError('Changed complete native effect descriptor')
    after=struct.pack('>8I',old_controller['vrom'],old_controller['vrom']+len(owner),OWNER_RAM,OWNER_RAM+len(owner),0,OWNER_RAM+0x36A0,0,0)
    core[at:at+32]=after;controller.update(installed=True,vrom=old_controller['vrom'],reloc=old_controller['reloc'],ram=OWNER_RAM,
        descriptor=dict(address=0x801010B0,before=before.hex(),after=after.hex()))
    for v,payload in ((old_controller['vrom'],owner),(old_controller['reloc'],fixed)):
        changes[v]=payload
        _,row=relocate_resource_plan(base,files,v,payload,minimum_physical=files[BLOB].pstart+len(blob),
            reservations=records+growth,append_only=False)
        growth.append(row)
    effects.update(profiles=profiles,controller=controller,additional_scene_bytes=controller['additional_scene_bytes'],
        participants=dict(installed=True,profiles=[119],code=code))
    report['coin'].update(installed=True,profile=profiles[-1],unique=unique[118])
    from v3_holiday_active import refresh_dispatch
    dispatch_write=refresh_dispatch(base,npc,records,work/'owner-dispatch',
        dict(af_hp_identity=code['symbols']['af_hp_identity']),
        ('AF_HOLIDAY_SKY','AF_HOLIDAY_PARTICIPANTS'))
    from v3_npc_registry import refresh_renderer
    npc_data=refresh_renderer(npc,dispatch_write[1],work/'npc-renderer',base,changes)
    dispatch_write[0]['sha256']=npc['packet']['sha256']
    next(r for r in records if r['id']==npc['packet']['id'])['sha256']=npc['packet']['sha256']
    dispatch_write=(dispatch_write[0],npc_data)
    events['dispatch']['participants_bound']=True
    report['dispatcher_bound']=True
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    npc['sources'].update(report['sources']);effects['sources'].update(report['sources'])
    events['participants']=report
    return equipment,changes,dict(physical_resources=records,resource_growth=growth,fire_sound=fire),[(fresh,combined),dispatch_write]


def finish(image,base,prior,output,equipment):
    from v3_event_text import install as install_text
    npc=equipment['npc_extra'];report=npc['events']['participants']
    records=prior['physical_resources']+[dict((k,v) for k,v in report['packet'].items()
        if k in ('id','physical','bytes','sha256'))]
    image=install_text(image,base,output,report['dialogue'],relocate=True,physical_resources=records,
        reserved_end=prior['resource_capacity']['reserved_physical_end'])
    write_new(output/'holiday-participants/installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return image
