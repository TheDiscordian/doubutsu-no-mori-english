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
SOURCES+=('overlays/v3/surface_bootstrap.c',)


def link(directory,prepared,output,*,object_name='participants',ram=RAM):
    """Link the checked prepared object, retaining every function and asset."""
    output.mkdir()
    if object_name not in ('participants','exercise','festivals') or ram&15 or not RAM<=ram<0x807DA800:
        raise ValueError('Invalid shared participant object/address')
    raw=(directory/(object_name+'.o')).read_bytes()
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
    run('ld','-EB',f'--defsym=AF_HP_LINK_RAM=0x{ram:X}',
        '-T','/source/overlays/v3/holiday_participants.ld',
        *(f'--defsym={n}=0x{v:X}' for n,v in prepared['bindings'].items()),
        '/source/'+str(directory.relative_to(ROOT))+'/'+object_name+'.o',
        '-Map','participants.map','-o','participants.elf')
    if run('nm','--undefined-only','participants.elf').strip():raise ValueError('Unlinked participant service')
    defined=[s.split() for s in run('nm','--defined-only','participants.elf').splitlines()]
    symbols={n:int(a,16) for a,k,n in defined}
    run('objcopy','-O','binary','participants.elf','participants.bin')
    data=(output/'participants.bin').read_bytes();s=symbols
    if (s['af_hp_packet_start']!=ram or s['af_hp_packet_end']!=ram+len(data) or
            not ram<s['af_hp_code_end']<=s['af_hp_bss_start']<s['af_hp_bss_end'] or
            any(data[s['af_hp_bss_start']-ram:s['af_hp_bss_end']-ram]) or
            data[-16:]!=b'AFHP'*4 or
            (object_name=='participants' and u32(data,s['af_hp_available']-ram)!=0)):
        raise ValueError('Changed participant code/state/admission bounds')
    write_new(output/'participants.asm',run('objdump','-d','participants.elf').encode())
    return data,dict(bytes=len(data),sha256=sha256(data),symbols=symbols,toolchain=IMAGE,
        functions=[n for a,k,n in defined if k=='T' and ram<=int(a,16)<s['af_hp_code_end']],
        code_bounds=[ram,s['af_hp_code_end']],bss_bounds=[s['af_hp_bss_start'],s['af_hp_bss_end']])


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
    if prepared.get('category')=='complete-exercise-card':
        return install_exercise(base,prior,blob,core,output,directory,prepared)
    if prepared.get('category')=='complete-festival-participants':
        return install_festivals(base,prior,blob,core,output,directory,prepared)
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


def install_exercise(base,prior,blob,core,output,directory,prepared):
    """Install the whole exercise family, shared registry, art, text, and saves."""
    from v3_console_disk_install import reservations
    from v3_event_text import patch_bounds
    from v3_holiday_dialogue import check_provenance
    from v3_npc_registry import RAM as NPC_RAM,TABLE,DMA,DRAW,STREAM,append_banks
    from v3_npc_native import identities,IDENTITIES
    from v3_npc_stream_runtime import native_records
    from v3_registry import SPECIAL_NPCS,SPECIAL_NPC_REGISTRY_VERSION
    from v3_furniture_pipeline import Source
    from v3_villager_art import DRAW_BASE,DRAW_STRIDE
    from v3_import_storage import jump
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];events=npc['events']
    if events.get('exercise') or prior['save_codec']['format_version']!=13:
        raise ValueError('Exercise needs the current complete format-thirteen proposal')
    work=output/'holiday-exercise';work.mkdir()
    old_packet=copy.deepcopy(events['sky']['packet']);start=old_packet['ram']+old_packet['bytes']
    prefix=bytearray(base[old_packet['physical']:old_packet['physical']+old_packet['bytes']])
    if sha256(prefix)!=old_packet['sha256'] or events['participants']['packet']!=old_packet:
        raise ValueError('Changed retained complete participant packet')
    code,compiled=link(directory,prepared,work/'linked',object_name='exercise',ram=start)
    symbols=compiled['symbols'];appended=bytearray(code)
    actor_bytes=u32(code,symbols['af_he_actor_bytes']-start)
    if actor_bytes!=2400:raise ValueError('Changed complete exercise native actor size')
    gate=symbols['af_hp_available']-old_packet['ram']
    if not 0<=gate<len(prefix)-4 or u32(prefix,gate):raise ValueError('Cannot replace an active participant registry')
    memory=e['diaries']['memory']['scratch'];scratch_end=memory['ram']+memory['bytes']
    if memory!={'ram':0x80682000,'bytes':120304} or any(
            a<scratch_end+48 and scratch_end<b for a,b in reservations(prior)):
        raise ValueError('Card scratch extension overlaps existing memory')

    # Both obsolete packets are documented predecessors with live, larger
    # replacements. Reclaim only those checked copies in the output cartridge.
    staged,records,retired=physical.retire_packet_copies(base,prior,(
        (events['participants']['preserved_sky_packet'],old_packet),
        (events['decorations']['controllers']['original_packet'],e['holiday_state']['packet'])))
    art_manifest=(directory/'art-batch.json').read_bytes();art_rows=json.loads(art_manifest)
    expected={'GAFE01-r0/npc/exercise-copper','GAFE01-r0/npc/exercise-tortimer'}
    if len(art_rows)!=2 or {r['identity'] for r in art_rows}!=expected:
        raise ValueError('Exercise requires both complete special-character resources')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    members={'GAFE01-r0/npc/ev-soncho2':npc['record']['identity']}
    members.update({k:v['identity'] for k,v in npc['prepared_characters'].items() if v['actor_installed']})
    new_banks=[];characters=[]
    for row in art_rows:
        identity=row['identity'];reservation=SPECIAL_NPCS[identity];art_dir=(ROOT/row['art']).resolve()
        if not art_dir.is_relative_to(ROOT/'build') or identity in members:raise ValueError('Invalid new exercise character')
        art_raw=(art_dir/'art.json').read_bytes();art=json.loads(art_raw)
        index=reservation['draw_index'];canonical=art['draw_index'];table=source.raw('npc_draw_data_tbl')
        if (index not in art.get('source_aliases',[canonical]) or
                table[index*DRAW_STRIDE:(index+1)*DRAW_STRIDE]!=table[canonical*DRAW_STRIDE:(canonical+1)*DRAW_STRIDE] or
                {p-(DRAW_BASE+index*DRAW_STRIDE):v for p,v in source.pointers(DRAW_BASE+index*DRAW_STRIDE,DRAW_STRIDE).items()}!=
                {p-(DRAW_BASE+canonical*DRAW_STRIDE):v for p,v in source.pointers(DRAW_BASE+canonical*DRAW_STRIDE,DRAW_STRIDE).items()}):
            raise ValueError('Wrong complete exercise artwork identity')
        for kind in ('model','texture'):
            data=(art_dir/(kind+'.bin')).read_bytes()
            if len(data)!=art[kind+'_bytes'] or sha256(data)!=art[kind+'_sha256']:
                raise ValueError('Changed complete exercise artwork')
            bank=reservation[kind+'_bank']
            if bank<prior['object_capacity']:
                found=[b for b in npc['banks'] if b['bank']==bank]
                if len(found)!=1 or found[0]['sha256']!=sha256(data) or found[0]['bytes']!=len(data):
                    raise ValueError('Reused character bank differs from complete source artwork')
        if reservation['model_bank']>=prior['object_capacity']:
            new_banks.append(dict(identity=identity,directory=art_dir,**reservation))
        if reservation['model_bank']<prior['object_capacity']:
            # Reuse the already-installed complete draw record too. Its
            # converter revision need not match later unrelated converter work.
            original=npc['record'];packet=npc['packet'];at=packet['physical']
            draw=base[at+DRAW:at+DRAW+100];stream=base[at+STREAM:at+STREAM+36]
            if (reservation['model_bank']!=original['identity']['model_bank'] or
                    reservation['texture_bank']!=original['identity']['texture_bank'] or
                    sha256(draw)!=original['draw_sha256'] or sha256(stream)!=original['stream_sha256'] or
                    sha256(table[index*DRAW_STRIDE:(index+1)*DRAW_STRIDE])!=art['donor_draw_sha256']):
                raise ValueError('Changed reused complete character drawing record')
            stream=struct.pack('>H',reservation['name'])+stream[2:];voice=original['voice']
        else:
            draw,stream,voice=native_records(source,art,reservation['name'],reservation['model_bank'],reservation['texture_bank'])
        characters.append((identity,reservation,draw,stream,voice,art_dir,art_raw,art))
        members[identity]=reservation
    staged_prior=copy.deepcopy(prior);staged_prior['physical_resources']=records
    banks,asset,records,writes,staged=append_banks(staged,staged_prior,blob,new_banks)
    packet=npc['packet'];original=base[packet['physical']:packet['physical']+packet['bytes']]
    registry=bytearray(original)
    if sha256(registry)!=packet['sha256'] or struct.unpack_from('>4I',registry,TABLE)!=(0x41464E58,1,3,44):
        raise ValueError('Changed complete special-character registry')
    if any(u32(registry,TABLE+20+i*44) for i in range(3)):raise ValueError('Cannot extend active special characters')
    for index,(identity,r,draw,stream,voice,art_dir,art_raw,art) in enumerate(characters,3):
        at=len(appended);descriptor=start+at;profile=descriptor+32
        draw_at=descriptor+80;stream_at=descriptor+192;area=descriptor+240
        stride=((actor_bytes+15)&~15)+32;chunk=bytearray(240+stride)
        struct.pack_into('>8I',chunk,0,0,0,0,0,0,profile,0,0)
        callbacks=[symbols['af_hp_'+name] for name in ('ctor','dtor','step','draw','save')]
        struct.pack_into('>HHIHH6I',chunk,32,r['profile'],3<<8,prepared['registry']['native_flags'],
            r['name'],3,actor_bytes,*callbacks)
        chunk[80:180]=draw;chunk[192:228]=stream
        struct.pack_into('>4I',chunk,240,0x41464E53,0,r['name'],r['profile'])
        struct.pack_into('>4I',chunk,len(chunk)-16,*([0x4E504347]*4))
        offset=TABLE+16+index*44
        if any(registry[offset:offset+44]):raise ValueError('Exercise overwrites an existing special row')
        struct.pack_into('>HH9I2H',registry,offset,r['name'],r['profile'],0,actor_bytes,1,stride,
            area,descriptor,draw_at,stream_at,voice,r['model_bank'],r['texture_bank'])
        appended.extend(chunk)
        npc['prepared_characters'][identity]=dict(identity=r,registry_version=SPECIAL_NPC_REGISTRY_VERSION,
            art=str(art_dir.relative_to(ROOT)),art_sha256=sha256(art_raw),draw_hex=draw.hex(),stream_hex=stream.hex(),
            voice=voice,model_bytes=art['model_bytes'],texture_bytes=art['texture_bytes'],banks_installed=True,
            actor_installed=True,active=False,selectable=False,native_execution_verified=False,actor_bytes=actor_bytes,
            descriptor=descriptor,profile=profile,slots=1,slot_stride=stride,pool_ram=area,flags_offset=offset+4,
            callback_family='Taisou_Npc0')
    struct.pack_into('>I',registry,TABLE+8,5)
    identity_data,identity_rows=identities(base,members)
    old_members={k:v for k,v in members.items() if k not in expected};old_identities,_=identities(base,old_members)
    if registry[IDENTITIES:IDENTITIES+len(old_identities)]!=old_identities or any(
            registry[IDENTITIES+len(old_identities):IDENTITIES+144]):
        raise ValueError('Changed complete installed identity directory')
    registry[IDENTITIES:IDENTITIES+144]=identity_data.ljust(144,b'\0')
    old_banks=npc['banks'];old_dma=struct.pack('>4I',0x41464E44,1,len(old_banks),12)+b''.join(
        struct.pack('>3I',b['vrom'],b['vrom']+b['bytes'],b['physical']) for b in old_banks)
    if registry[DMA:DMA+len(old_dma)]!=old_dma or any(registry[DMA+len(old_dma):DMA+len(old_dma)+len(banks)*12]):
        raise ValueError('Changed complete character transfer table')
    struct.pack_into('>I',registry,DMA+8,len(old_banks)+len(banks))
    for i,b in enumerate(banks,len(old_banks)):
        struct.pack_into('>3I',registry,DMA+16+i*12,b['vrom'],b['vrom']+b['bytes'],b['physical'])
    npc['banks']+=banks

    # Every existing public registry and save entry keeps its address. Never
    # redirect data symbols or the exercise-specific dialogue/death adapters.
    functions=set(compiled['functions']);redirects=[]
    buffers={old_packet['id']:prefix,npc['packet']['id']:registry}
    def redirect(label,owner,old,wanted):
        data=buffers.setdefault(owner['id'],bytearray(base[owner['physical']:owner['physical']+owner['bytes']]))
        origin=owner['ram'];addresses=sorted(set(v for v in old['symbols'].values()
            if origin<=v<origin+owner['bytes']))
        for name,address in old['symbols'].items():
            target=symbols.get(name)
            if name not in functions or not wanted(name) or not origin<=address<origin+owner['bytes']:continue
            end=next((v for v in addresses if v>address),origin+owner['bytes'])
            if end-address<8:raise ValueError('Public entry is too short for a checked redirect: '+name)
            offset=address-origin;before=bytes(data[offset:offset+8]);after=struct.pack('>2I',jump(target),0)
            data[offset:offset+8]=after
            redirects.append(dict(owner=label,name=name,address=address,target=target,before=before.hex(),after=after.hex()))
    participants=events['participants']
    redirect('participants',old_packet,participants['code'],lambda n:n.startswith('af_hp_') or n in ('mEv_get_save_area','mEv_reserve_save_area'))
    for label,owner,old in (('diary',e['diaries']['packets']['storage'],e['diaries']['compiled']),
            ('holiday',e['holiday_state']['packet'],e['holiday_state']['code']),
            ('fishing',e['holiday_fishing']['packet'],e['holiday_fishing']['code'])):
        redirect(label,owner,old,lambda n:n.startswith('af_v3_'))
    needed={'af_v3_save_check','af_v3_save_pack','af_v3_console_storage_reset','af_v3_console_storage_commit',
        'af_v3_console_storage_valid','af_v3_console_player_clear','af_v3_diary_measure'}
    for label in ('diary','holiday','fishing'):
        if not needed<={r['name'] for r in redirects if r['owner']==label}:raise ValueError('Incomplete format-14 save callers')
    for label,owner,old in (('diary',e['diaries']['packets']['storage'],e['diaries']['compiled']),
            ('holiday',e['holiday_state']['packet'],e['holiday_state']['code']),
            ('fishing',e['holiday_fishing']['packet'],e['holiday_fishing']['code']),
            ('participants',old_packet,participants['code'])):
        data=buffers[owner['id']]
        origin=old['code_bounds'][0] if 'code_bounds' in old else (
            0x80730000 if label=='fishing' else owner['ram'])
        pos=origin-owner['ram']
        old.update(sha256=sha256(data[pos:pos+old['bytes']]),exercise_redirects=[r for r in redirects if r['owner']==label])
    appended.extend(b'AFHX'*4);end=start+len(appended)
    if end>0x807DA800 or any(a<end and start<b for a,b in reservations(prior)):
        raise ValueError('Complete exercise packet overlaps retained native memory')
    combined=bytes(prefix+appended)
    allocation=physical.allocate(staged,records,combined,'holiday-exercise-GAFE01-r0',best_fit=True)
    records.append(allocation);writes.append((allocation,combined))
    fresh=dict(allocation,ram=old_packet['ram'],crc32=zlib.crc32(combined),storage='physical-ROM')
    events['sky']['packet']=copy.deepcopy(fresh);participants['packet']=copy.deepcopy(fresh)
    participants['loaded_code']['sha256']=participants['code']['sha256']
    for owner in (npc['packet'],e['diaries']['packets']['storage'],e['holiday_state']['packet']):
        data=bytes(buffers[owner['id']]);previous=owner['sha256'];owner.update(sha256=sha256(data),crc32=zlib.crc32(data))
        row=next(r for r in records if r['id']==owner['id']);row['sha256']=owner['sha256']
        writes.append((dict(row,previous_sha256=previous),data))
    e['holiday_fishing']['packet']=copy.deepcopy(e['holiday_state']['packet'])
    e['holiday_fishing']['loaded_code']['sha256']=e['holiday_fishing']['code']['sha256']
    npc['lifecycle']['code']=copy.deepcopy(e['holiday_state']['code'])
    # Keep the complete installed player controller and all callback addresses.
    # Only its two existing calendar calls gain the imported RUN condition.
    player=e['player_motion']['exercise']['native'];pp=player['packet'];pc=player['code']
    begin=pp['blob_offset'];player_code=bytearray(blob[begin:begin+pp['bytes']])
    if sha256(player_code)!=pp['sha256'] or sha256(player_code[:pc['bytes']])!=pc['sha256']:
        raise ValueError('Changed complete player exercise controller')
    entry=pc['symbols']['af_v3_exercise_native_able']
    end_entry=min(v for v in pc['symbols'].values() if v>entry)
    # The compiler shares $s0 between two jalr calls, loading the callee with
    # lui/ori. Keep both complete calls and their event arguments unchanged.
    callee=symbols['af_he_player_status']
    edits=((0x1F8,0x3C108007,0x3C100000|(callee>>16)),
           (0x208,0x3610FF08,0x36100000|(callee&65535)))
    if (entry!=pp['ram']+0x1DC or end_entry!=pp['ram']+0x2D4 or
            sha256(player_code[0x1DC:0x2D4])!='620af9596ac9ca9a9a23bd0ef95b0b605a0c76f5bd01add1eb90506bb030d35d' or
            any(u32(player_code,i)!=word for i,word in
                ((0x20C,0x0200F809),(0x210,0x24040010),(0x288,0x0200F809),(0x28C,0x24040008))) or
            any(u32(player_code,i)!=before for i,before,after in edits)):
        raise ValueError('Changed complete player exercise event checks')
    player_hooks=[]
    for i,before,after in edits:
        struct.pack_into('>I',player_code,i,after)
        player_hooks.append(dict(address=pp['ram']+i,before=before,after=after,delay_slot_preserved=True))
    blob[begin:begin+pp['bytes']]=player_code
    pp.update(sha256=sha256(player_code),crc32=zlib.crc32(player_code))
    pc['sha256']=sha256(player_code[:pc['bytes']])
    player['imported_event_hooks']=player_hooks
    memory['bytes']+=48
    text=copy.deepcopy(prepared['dialogue']);check_provenance(text)
    text.update(choice_vrom=prior['import_storage']['choice_vrom'],hooks=patch_bounds(core,text['first_id'],text['count']),installed=True)
    for row in text['resources']:
        data=(directory/row['file']).read_bytes()
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:raise ValueError('Changed complete exercise text')
        row['original_sha256']=row.pop('previous_sha256')
        name='holiday-exercise/'+row['file'];write_new(output/name,data);row['file']=name
    report=dict(format='AFV3-EXERCISE-CARD-1',installed=True,code=compiled,bindings=prepared['bindings'],
        ram=start,bytes=len(appended),sha256=sha256(appended),loaded_code=dict(ram=start,bytes=len(code),sha256=sha256(code)),
        prepared=str(directory.relative_to(ROOT)),prepared_sha256=sha256((directory/'prepared.json').read_bytes()),
        art_manifest_sha256=sha256(art_manifest),registry=prepared['registry'],identities=identity_rows,
        characters=sorted(expected),redirects=redirects,text=text,packet=copy.deepcopy(fresh),
        saved_format_changed=True,save_format=14,card_state=dict(ram=symbols['af_v3_card_state'],bytes=48),
        scratch=copy.deepcopy(memory),additional_resident_bytes=len(appended)+48,
        actor_admission_changed=False,native_execution_verified=False,sources=copy.deepcopy(prepared['sources']))
    report['player_event_hooks']=player_hooks
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    npc['sources'].update(report['sources'])
    npc.setdefault('source_batches',[]).append(dict(installed=True,ram=start,bytes=len(appended),sha256=sha256(appended),category='exercise-card'))
    events['exercise']=report
    e['console_storage'].update(save_format=14,diary_runtime=copy.deepcopy(e['diaries']['compiled']),
        fishing_runtime=copy.deepcopy(e['holiday_fishing']['code']),card_runtime=copy.deepcopy(compiled))
    updates={k:copy.deepcopy(prior[k]) for k in ('save_runtime','save_codec','clothing','room_surfaces')}
    updates['save_runtime']['diary_runtime_code']=copy.deepcopy(e['diaries']['compiled'])
    updates['save_codec'].update(format_version=14,active_storage_code=copy.deepcopy(compiled),card_storage_code=copy.deepcopy(compiled),
        holiday_state_code=copy.deepcopy(e['holiday_state']['code']),fishing_storage_code=copy.deepcopy(e['holiday_fishing']['code']))
    updates['clothing']['save_extension'].update(format_version=14,active_storage_code=copy.deepcopy(compiled))
    updates['clothing']['save_extension']['legacy_formats_read']=list(dict.fromkeys(
        [*updates['clothing']['save_extension']['legacy_formats_read'],'AFS3-v13']))
    updates['room_surfaces']['save']['disk_format_version']=14
    updates.update(physical_resources=records,retired_physical_resources=retired,asset=asset,
        object_capacity=prior['object_capacity']+len(banks),saved_format_changed=True,
        save_warning='Format-14 experimental saves require this or a newer compatible build. Compatible older saves migrate forward; exercise-card records start empty. V2 and format-13-or-earlier V3 cannot load new saves. Preserve backups. Native diary/exercise gameplay and save/reload remain unverified.')
    write_new(work/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(work/'packet.bin',combined);write_new(work/'registry.bin',registry)
    return e,{},updates,writes


def install_festivals(base,prior,blob,core,output,directory,prepared):
    """Extend the one resident registry with all five complete festival families."""
    del blob
    from v3_console_disk_install import reservations
    from v3_event_text import patch_bounds
    from v3_holiday_dialogue import check_provenance
    from v3_import_storage import jump
    from v3_npc_draw import relocation_offsets
    import v3_physical_resources as physical
    e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra'];events=npc['events']
    if events.get('festivals') or not events.get('calendar') or prior['save_codec']['format_version']!=15:
        raise ValueError('Festival participants need the current complete calendar proposal')
    work=output/'holiday-festivals';work.mkdir()
    old=copy.deepcopy(events['sky']['packet']);start=old['ram']+old['bytes']
    prefix=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if sha256(prefix)!=old['sha256'] or any(events[k]['packet']!=old for k in ('participants','exercise','calendar')):
        raise ValueError('Changed shared calendar/participant packet')
    data,compiled=link(directory,prepared,work/'linked',object_name='festivals',ram=start)
    symbols=compiled['symbols'];functions=set(compiled['functions'])-{'af_hp_packet_start'}
    sizes={r['stem']:u32(data,symbols['af_hg_bytes_'+r['stem']]-start)
        for r in prepared['registry']['records']}
    if len(sizes)!=10 or any(not 0x93C<=n<=2400 for n in sizes.values()):
        raise ValueError('Complete festival actor exceeds the shared native allocation')
    gate=symbols['af_hp_available']-old['ram']
    if not 0<=gate<=len(prefix)-4 or u32(prefix,gate):
        raise ValueError('Cannot replace an active participant registry')
    # All existing callbacks must reach this same registry/state. Retain entry
    # addresses used by native hooks, imported profiles, and special actors.
    # The previous animation function is deliberately not redirected: it is
    # the fallback for native motions and the previously imported prayer.
    redirects=[]
    for family in ('participants','exercise'):
        previous=events[family]['code'];lo,hi=previous['code_bounds']
        offset=lo-old['ram']
        if sha256(prefix[offset:offset+previous['bytes']])!=previous['sha256']:
            raise ValueError('Changed retained registry module: '+family)
        addresses=sorted(set(v for v in previous['symbols'].values() if lo<=v<hi))
        for name,address in previous['symbols'].items():
            if (name not in functions or not lo<=address<hi or
                    not (name.startswith('af_hp_') or name in ('mEv_get_save_area','mEv_reserve_save_area'))):continue
            end=next((v for v in addresses if v>address),hi)
            if end-address<8:raise ValueError('Registry entry is too short for a redirect: '+name)
            at=address-old['ram'];before=bytes(prefix[at:at+8]);target=symbols[name]
            after=struct.pack('>2I',jump(target),0);prefix[at:at+8]=after
            redirects.append(dict(owner=family,name=name,address=address,target=target,
                before=before.hex(),after=after.hex()))
        required={'af_hp_owned','af_hp_identity','af_hp_event_lookup','af_hp_resident_bind',
            'af_hp_descriptor','af_hp_spawn_profile','af_hp_world_name','af_hp_events_clear','af_hp_free'}
        if not required<={r['name'] for r in redirects if r['owner']==family}:
            raise ValueError('Incomplete shared registry redirect: '+family)
        previous.update(sha256=sha256(prefix[offset:offset+previous['bytes']]),
            festival_redirects=[r for r in redirects if r['owner']==family])
        events[family]['loaded_code']['sha256']=previous['sha256']
        if 'ram' in events[family] and 'bytes' in events[family]:
            at=events[family]['ram']-old['ram']
            events[family]['sha256']=sha256(prefix[at:at+events[family]['bytes']])
    extra=data+b'AFHF'*4;end=start+len(extra)
    if end>0x807DA800 or any(a<end and start<b for a,b in reservations(prior)):
        raise ValueError('Complete festival packet overlaps retained resident memory')
    # Fragmented ROM space cannot hold another full combined copy. Reclaim
    # the verified obsolete prefix and load the appended code separately at
    # its contiguous RAM address through the shared startup descriptor loop.
    obsolete=next(r for r in prior['physical_resources'] if r['id']=='holiday-sky-participants-GAFE01-r0')
    staged,records,retired=physical.retire_packet_copies(base,prior,((dict(obsolete,ram=old['ram']),old),))
    retained=next(r for r in records if r['id']==old['id'])
    if any(retained[k]!=old[k] for k in ('physical','bytes','sha256')):
        raise ValueError('Changed complete festival packet predecessor')
    allocation=physical.allocate(staged,records,extra,'holiday-festivals-GAFE01-r0',best_fit=True)
    fresh=copy.deepcopy(allocation);records.append(fresh)
    packet=dict(fresh,ram=start,crc32=zlib.crc32(extra),storage='physical-ROM')
    prefix_record=dict(retained,sha256=sha256(prefix))
    records=[prefix_record if r['id']==old['id'] else r for r in records]
    prefix_packet=dict(old,sha256=sha256(prefix),crc32=zlib.crc32(prefix))
    for family in ('sky','participants','exercise','calendar'):events[family]['packet']=copy.deepcopy(prefix_packet)
    # Complete motion/expression handling belongs at the shared native NPC
    # initializer, before its ordinary 234-entry bank directory is consulted.
    files=by_vrom(base);vrom,reloc,ram=0x8681F0,0x878550,0x809735B0
    native=bytearray(files[vrom].extract(base));fixups=files[reloc].extract(base)
    at=0x809749D0;before=jump(events['participants']['code']['symbols']['af_hp_animation'])
    if (u32(native,at-ram)!=before or u32(native,at+4-ram)!=0 or
            {at-ram,at+4-ram}&relocation_offsets(fixups,len(native))):
        raise ValueError('Changed native animation redirect/relocations')
    if prepared['bindings']['af_hg_previous_animation']!=events['participants']['code']['symbols']['af_hp_animation']:
        raise ValueError('Festival motion fallback would not retain existing motions')
    original_sha=sha256(native);after=jump(symbols['af_hg_animation'])
    struct.pack_into('>I',native,at-ram,after)
    native_report=dict(vrom=vrom,reloc=reloc,ram=ram,original_sha256=original_sha,
        owner_sha256=sha256(native),relocation_sha256=sha256(fixups),bytes=len(native),
        patches=[dict(address=at,before=before,after=after)],relocations_unchanged=True)
    text=copy.deepcopy(prepared['dialogue']);check_provenance(text)
    if text['choice_count']:raise ValueError('Festival choice expansion requires an explicit native bound')
    text.update(choice_vrom=prior['import_storage']['choice_vrom'],
        hooks=patch_bounds(core,text['first_id'],text['count']),installed=True)
    for row in text['resources']:
        payload=(directory/row['file']).read_bytes()
        if len(payload)!=row['bytes'] or sha256(payload)!=row['sha256']:
            raise ValueError('Changed complete festival dialogue')
        row['original_sha256']=row.pop('previous_sha256')
        name='holiday-festivals/'+row['file'];write_new(output/name,payload);row['file']=name
    report=dict(format='AFV3-FESTIVAL-PARTICIPANTS-1',installed=True,code=compiled,
        bindings=prepared['bindings'],registry=prepared['registry'],actor_bytes=sizes,
        ram=start,bytes=len(extra),sha256=sha256(extra),
        loaded_code=dict(ram=start,bytes=len(data),sha256=sha256(data)),
        prepared=str(directory.relative_to(ROOT)),prepared_sha256=sha256((directory/'prepared.json').read_bytes()),
        redirects=redirects,text=text,motions=prepared['motions'],native_animation=native_report,
        packet=packet,previous_packet=old,additional_resident_bytes=len(extra),
        native_services_bound=True,actor_admission_changed=False,saved_format_changed=False,
        native_execution_verified=False,sources=copy.deepcopy(prepared['sources']))
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    npc['sources'].update(report['sources']);events['festivals']=report
    for batch in npc.get('source_batches',[]):
        pos=batch['ram']-old['ram']
        if 0<=pos and pos+batch['bytes']<=len(prefix):batch['sha256']=sha256(prefix[pos:pos+batch['bytes']])
    npc.setdefault('source_batches',[]).append(dict(installed=True,ram=start,bytes=len(extra),
        sha256=sha256(extra),category='festival-participants',packet_id=packet['id']))
    write_new(work/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(work/'packet.bin',extra)
    write_new(work/'retained-prefix.bin',prefix)
    return e,{vrom:native,reloc:fixups},dict(physical_resources=records,
        retired_physical_resources=retired),[(dict(prefix_record,previous_sha256=old['sha256']),bytes(prefix)),(allocation,extra)]


def finish(image,base,prior,output,equipment):
    from v3_event_text import install as install_text
    npc=equipment['npc_extra'];report=npc['events']['participants']
    records=prior['physical_resources']+[dict((k,v) for k,v in report['packet'].items()
        if k in ('id','physical','bytes','sha256'))]
    image=install_text(image,base,output,report['dialogue'],relocate=True,physical_resources=records,
        reserved_end=prior['resource_capacity']['reserved_physical_end'])
    write_new(output/'holiday-participants/installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return image
