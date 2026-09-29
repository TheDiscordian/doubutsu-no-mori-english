"""Connect complete golden reward actors, effects, and native consumers.

Preparation retains every donor callback and reuses the checked complete art.
Only the enclosing installer can make these services available in a cartridge.
"""
import copy
import json
import os
import struct
import subprocess
import zlib
from pathlib import Path

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT
from v3_reward_bindings import LAYOUT


def connect(base,prior,actors,effects,output):
    """Resolve both whole objects together in their separate owned arenas."""
    actors,effects,output=(Path(p).resolve() for p in (actors,effects,output))
    if output.exists() or not all(p.is_relative_to(ROOT/'build') for p in (actors,effects,output)):
        raise ValueError('Use checked ignored preparations and a fresh output')
    a=json.loads((actors/'prepared.json').read_bytes())
    e=json.loads((effects/'prepared.json').read_bytes())
    for directory,report,name in ((actors,a,'reward-events'),(effects,e,'reward-effects')):
        if report['base_sha256']!=sha256(base) or report['base_abi']!=prior['runtime_abi']:
            raise ValueError('Golden rewards require their current locked input')
        if sha256((directory/(name+'.o')).read_bytes())!=report['object']['sha256']:
            raise ValueError('Changed complete golden reward object')
        for file,digest in report['sources'].items():
            if sha256((ROOT/file).read_bytes())==digest:continue
            # This policy extension only admits Farley's complete ground-light
            # profile; it does not change any prepared effect function or art.
            if report is e and file=='tools/v3_holiday_sky.py':
                from v3_holiday_sky import native_bindings
                from v3_reward_effects import NATIVE_SERVICES
                links,receipts=native_bindings(base,{n:n for n in NATIVE_SERVICES})
                current=(ROOT/file).read_bytes();extension=b",'00c300ffc47a0cff'"
                if (current.count(extension)==1 and sha256(current.replace(extension,b''))==digest and
                        links==e['native_service_candidates'] and receipts==e['native_service_evidence']):
                    continue
            raise ValueError('Changed golden reward source: '+file)
        for file,digest in report['generated_sha256'].items():
            if sha256((directory/file).read_bytes())!=digest:
                raise ValueError('Changed generated golden reward source: '+file)
    output.mkdir(parents=True)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        return subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            check=True,text=True,capture_output=True,timeout=60).stdout
    objects=['/source/'+str(d.relative_to(ROOT))+'/'+n+'.o'
        for d,n in ((actors,'reward-events'),(effects,'reward-effects'))]
    defined=set();undefined=set()
    for obj in objects:
        defined.update(line.split()[-1] for line in run('nm','--defined-only','--extern-only',obj).splitlines())
        undefined.update(line.split()[-1] for line in run('nm','--undefined-only',obj).splitlines())
    sky=prior['equipment_resources']['npc_extra']['events']['sky']
    candidates=dict(e['native_service_candidates'])
    candidates.update(sky['code']['symbols']);candidates.update(a['bindings'])
    from v3_holiday_participants import bindings
    sound,sound_evidence=bindings(base,prior,extra={'af_hp_native_sound':0x800D1D58})
    candidates['af_hp_native_sound']=sound['af_hp_native_sound']
    missing=undefined-defined-candidates.keys()
    if missing:raise ValueError('Unbound golden reward services: '+', '.join(sorted(missing)))
    # Restate only actual absolute imports for MIPS jump sign extension. Do not
    # replace newly compiled owners with an older symbol of the same name.
    links={n:candidates[n] for n in sorted(undefined-defined)}
    # Partial-link absolute imports also need their definitions restated.
    links.update(a['bindings'])
    run('ld','-EB',*(f'--defsym={n}=0x{v:X}' for n,v in links.items()),
        '-T','/source/overlays/v3/reward_events.ld',*objects,
        '-Map','reward.map','-o','reward.elf')
    if run('nm','--undefined-only','reward.elf').strip():
        raise ValueError('Golden reward link retains undefined services')
    symbols={name:int(address,16) for address,kind,name in
        (line.split() for line in run('nm','--defined-only','reward.elf').splitlines())}
    run('objcopy','-O','binary','reward.elf','reward.bin')
    body=(output/'reward.bin').read_bytes();start=LAYOUT['actors']['ram']
    if (symbols['af_hp_packet_start']!=start or
            symbols['af_rw_effect_packet_end']!=start+len(body)):
        raise ValueError('Unexpected connected golden reward packet extent')
    for low,high in (('af_hp_bss_start','af_hp_bss_end'),
                     ('af_rw_effect_bss_start','af_rw_effect_bss_end')):
        if any(body[symbols[low]-start:symbols[high]-start]):
            raise ValueError('Golden reward state is not initialised in its packet')
    regions={}
    for kind,low,code,high,guard in (
            ('actors','af_hp_packet_start','af_hp_code_end','af_hp_packet_end',b'AFHP'*4),
            ('effects','af_rw_effect_packet_start','af_rw_effect_code_end','af_rw_effect_packet_end',b'AFRW'*4)):
        payload=body[symbols[low]-start:symbols[high]-start]
        if payload[-16:]!=guard:raise ValueError('Golden reward packet guard differs')
        write_new(output/(kind+'.bin'),payload)
        regions[kind]=dict(ram=symbols[low],bytes=len(payload),sha256=sha256(payload),
            code_bounds=[symbols[low],symbols[code]])
    write_new(output/'reward.asm',run('objdump','-d','reward.elf').encode())
    result=dict(format='AFV3-CONNECTED-REWARDS-1',base_abi=prior['runtime_abi'],
        base_sha256=sha256(base),bindings=links,symbols=symbols,regions=regions,
        actor_preparation=str(actors.relative_to(ROOT)),effect_preparation=str(effects.relative_to(ROOT)),
        object_sha256=[a['object']['sha256'],e['object']['sha256']],
        actor_report=copy.deepcopy(a),effect_report=copy.deepcopy(e),
        sha256=sha256(body),bytes=len(body),native_services_bound=True,
        native_sound_evidence=[r for r in sound_evidence if r['name']=='af_hp_native_sound'],
        installed=False,native_execution_verified=False)
    write_new(output/'connected.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


def native_consumers(base,symbols):
    """Patch only verified callers/tables; original callable bodies remain.

    Overlay fixups for replaced local references are removed. Check the full
    relocated images at two different live addresses, including every unchanged
    instruction, resource, and BSS byte.
    """
    from v3_import_storage import jump
    from catalogue_names import Image
    from npc_mail_show import relocate_verified_data
    files=by_vrom(base);changes={};hooks=[]
    owners={0x741FB0:(0x80802AE0,0x743950),
            0x8D8EC0:(0x80A0A1F0,0x8D9FA0),
            0x3E90000:(0x809BE720,0x3EA0000),
            0x3800000:(0x8095B8B0,0x3810000)}
    def patch(vrom,address,before,helper,kind):
        ram=CODE_RAM if vrom==CODE_VROM else owners[vrom][0]
        body=changes.setdefault(vrom,bytearray(files[vrom].extract(base)))
        at=address-ram
        if u32(body,at)!=before:raise ValueError('Changed golden reward caller: '+hex(address))
        dest=symbols[helper]
        if dest&3 or not LAYOUT['actors']['ram']<=dest<LAYOUT['effects']['ram']:
            raise ValueError('Golden reward hook has no owned actor entry')
        after=dest if kind=='pointer' else jump(dest,link=True)
        struct.pack_into('>I',body,at,after)
        hooks.append(dict(vrom=vrom,ram=ram,address=address,before=before,after=after,
            helper=helper,kind=kind,delay_slot_preserved=kind=='call'))
    for vrom,address,before,helper,kind in (
        (CODE_VROM,0x8007E968,0x0C021369,'af_rw_field_rank','call'),
        (CODE_VROM,0x800C3C28,0x0C021369,'af_rw_field_rank','call'),
        (CODE_VROM,0x800D1FF8,0x0C03EA4B,'af_rw_voice_spec','call'),
        (CODE_VROM,0x800D1C08,0x0C03E47F,'af_rw_voice_emit','call'),
        (0x741FB0,0x80803288,0x0C015C9D,'af_rw_actors_destroy','call'),
        (0x741FB0,0x808034DC,0x0C015BA2,'af_rw_actors_init','call'),
        (0x741FB0,0x8080362C,0x0C015CC1,'af_rw_actors_move','call'),
        (0x3E90000,0x809BF6AC,0x0C26FD61,'af_rw_house_door','call'),
        (0x8D8EC0,0x80A0B1C0,0x80A0A240,'af_rw_shrine_ctor','pointer'),
        (0x8D8EC0,0x80A0B1C4,0x80A0A358,'af_rw_shrine_dtor','pointer'),
        (0x8D8EC0,0x80A0B264,0x80A0A7A4,'af_rw_shrine_talk','pointer'),
        (0x8D8EC0,0x80A0A808,0x0C021342,'af_rw_field_condition','call'),
        (0x3800000,0x809614C4,0x0C02A6F5,'af_rw_birthday_mail','call')):
        patch(vrom,address,before,helper,kind)
    relocation_evidence=[]
    for vrom,(ram,reloc) in owners.items():
        original=files[vrom].extract(base);raw=files[reloc].extract(base)
        sections=struct.unpack_from('>5I',raw)
        if len(original)!=sum(sections[:3]) or len(raw)<24+sections[4]*4:
            raise ValueError('Changed complete golden reward overlay dimensions')
        selected={h['address']-ram:h for h in hooks if h['vrom']==vrom}
        keep=[];removed=[]
        for word, in struct.iter_unpack('>I',raw[20:20+sections[4]*4]):
            section,kind,offset=word>>30,word>>24&63,word&0xFFFFFF
            if section not in (1,2,3) or kind not in (2,4,5,6):
                raise ValueError('Unreviewed native reward relocation')
            at=sum(sections[:section-1])+offset
            if at in selected:
                want=2 if selected[at]['kind']=='pointer' else 4
                if kind!=want:raise ValueError('Golden reward hook changes a paired address fixup')
                removed.append(word)
            else:keep.append(word)
        required={at for at,h in selected.items() if h['kind']=='pointer' or
            (h['kind']=='call' and h['before']&0x03FFFFFF==(0x809BF584>>2&0x03FFFFFF))}
        removed_offsets={sum(sections[:(word>>30)-1])+(word&0xFFFFFF) for word in removed}
        if removed_offsets!=required:raise ValueError('Golden reward fixup removal differs from local references')
        fixed=struct.pack('>5I',*sections[:4],len(keep))+struct.pack('>'+str(len(keep))+'I',*keep)
        fixed+=bytes(len(raw)-len(fixed)-4)+struct.pack('>I',len(raw))
        allowed={at+i for at in selected for i in range(4)}
        for load in (0x80200010,0x80348010):
            before=relocate_verified_data(Image(ram,sum(sections[:4]),sections),original,raw,load)
            after=relocate_verified_data(Image(ram,sum(sections[:4]),(*sections[:4],len(keep))),
                changes[vrom],fixed,load)
            if len(before)!=len(after) or any(x!=y and i not in allowed for i,(x,y) in enumerate(zip(before,after))):
                raise ValueError('Golden reward hooks change unrelated loaded bytes')
        if removed:changes[reloc]=bytearray(fixed)
        relocation_evidence.append(dict(vrom=vrom,relocation=reloc,sections=sections,
            retained_fixups=len(keep),removed=removed,whole_loaded_images_checked=True))
    return {v:bytes(body) for v,body in changes.items()},hooks,relocation_evidence


def redirect_module(body,packet,previous,origin,target,target_origin,prefixes):
    """Replace checked public entries, leaving state and fallback bodies intact."""
    from v3_import_storage import jump
    start=origin-packet['ram'];end=origin+previous['bytes']
    if sha256(body[start:start+previous['bytes']])!=previous['sha256']:
        raise ValueError('Changed retained public module')
    code_end=previous.get('code_bounds',(origin,end))[1]
    target_end=target.get('code_bounds',(target_origin,target_origin+target['bytes']))[1]
    markers={'af_hp_packet_start','af_hp_code_end','af_hp_bss_start','af_hp_bss_end','af_hp_packet_end'}
    entries=sorted(set(a for a in previous['symbols'].values() if origin<=a<code_end))
    redirects=[]
    for name,address in previous['symbols'].items():
        if not origin<=address<code_end or name in markers or not name.startswith(prefixes):continue
        dest=target['symbols'].get(name)
        if dest is None or not target_origin<=dest<target_end:continue
        following=next((a for a in entries if a>address),code_end)
        if following-address<8:raise ValueError('Short retained public entry: '+name)
        pos=address-packet['ram'];before=bytes(body[pos:pos+8]);after=struct.pack('>2I',jump(dest),0)
        body[pos:pos+8]=after
        redirects.append(dict(name=name,address=address,target=dest,before=before.hex(),after=after.hex()))
    previous['sha256']=sha256(body[start:start+previous['bytes']])
    return redirects


def reward_npcs(base,e,actor_data,symbols):
    """Append both complete static actors to the existing eight-slot registry."""
    from v3_npc_registry import TABLE,DMA
    from v3_npc_native import identities,IDENTITIES
    from v3_npc_stream_runtime import native_records
    from v3_registry import SPECIAL_NPCS,SPECIAL_NPC_REGISTRY_VERSION
    from v3_furniture_pipeline import Source
    npc=e['npc_extra'];packet=npc['packet']
    registry=bytearray(base[packet['physical']:packet['physical']+packet['bytes']])
    if sha256(registry)!=packet['sha256'] or struct.unpack_from('>4I',registry,TABLE)!=(0x41464E58,1,6,44):
        raise ValueError('Changed six-character native registry')
    members={'GAFE01-r0/npc/ev-soncho2':npc['record']['identity']}
    members.update({k:v['identity'] for k,v in npc['prepared_characters'].items() if v['actor_installed']})
    names,_=identities(base,members)
    if registry[IDENTITIES:IDENTITIES+144]!=names.ljust(144,b'\0'):
        raise ValueError('Changed retained official NPC identities')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    pools=bytearray(LAYOUT['pools']['bytes']);used=0
    olddraw=bytes(registry[0xA250:0xA250+100]);oldstream=bytes(registry[0xA2C0:0xA2C0+36])
    donor_table=source.raw('npc_draw_data_tbl')
    if donor_table[348*108:349*108]!=donor_table[354*108:355*108]:
        raise ValueError('Gift Tortimer does not share the complete existing draw record')
    for index,(identity,label,profile_name) in enumerate((
            ('GAFE01-r0/npc/hem','Npc_Hem','Npc_Hem_Profile'),
            ('GAFE01-r0/npc/present-tortimer','Present_Npc','Present_Npc_Profile')),6):
        r=SPECIAL_NPCS[identity]
        if identity in members:raise ValueError('Golden reward character is already installed')
        profile_at=symbols[profile_name]-LAYOUT['actors']['ram']
        profile=actor_data[profile_at:profile_at+36]
        if len(profile)!=36 or struct.unpack_from('>HH',profile)!=(r['donor_profile'],4<<8):
            raise ValueError('Changed complete compiled reward NPC profile')
        actor_bytes=u32(profile,12)
        if not 2300<=actor_bytes<=2800:raise ValueError('Unreviewed complete reward actor extent')
        stride=((actor_bytes+15)&~15)+32;chunk=bytearray(240+stride)
        if used+len(chunk)>len(pools)-16:raise ValueError('Complete reward actors exceed their owned pools')
        address=LAYOUT['pools']['ram']+used
        callbacks=[symbols['af_hp_'+phase] for phase in ('ctor','dtor','step','draw','save')]
        struct.pack_into('>8I',chunk,0,0,0,0,0,0,address+32,0,0)
        struct.pack_into('>HHIHH6I',chunk,32,r['profile'],3<<8,u32(profile,4),r['name'],3,actor_bytes,*callbacks)
        if index==6:
            art_dir=ROOT/'build/v3-reward-farley-art-01';art_raw=(art_dir/'art.json').read_bytes();art=json.loads(art_raw)
            if art['draw_index']!=r['draw_index']:raise ValueError('Changed complete Farley artwork')
            draw,stream,voice=native_records(source,art,r['name'],r['model_bank'],r['texture_bank'])
            art_fields=dict(art=str(art_dir.relative_to(ROOT)),art_sha256=sha256(art_raw),
                model_bytes=art['model_bytes'],texture_bytes=art['texture_bytes'])
        else:
            draw=olddraw;stream=struct.pack('>H',r['name'])+oldstream[2:];voice=npc['record']['voice']
            if struct.unpack_from('>2H',draw)!=(r['model_bank'],r['texture_bank']) or voice!=281:
                raise ValueError('Changed complete retained Tortimer artwork')
            art_fields=dict(reused_artwork='GAFE01-r0/npc/ev-soncho2',
                model_bytes=npc['record']['model_bytes'],texture_bytes=npc['record']['texture_bytes'])
        chunk[80:180]=draw;chunk[192:228]=stream
        struct.pack_into('>4I',chunk,240,0x41464E53,0,r['name'],r['profile']);chunk[-16:]=b'NPCG'*4
        pools[used:used+len(chunk)]=chunk;used+=len(chunk)
        at=TABLE+16+index*44
        if any(registry[at:at+44]):raise ValueError('Reward NPC overwrites an existing registry row')
        struct.pack_into('>HH9I2H',registry,at,r['name'],r['profile'],3,actor_bytes,1,stride,
            address+240,address,address+80,address+192,voice,r['model_bank'],r['texture_bank'])
        members[identity]=r
        npc['prepared_characters'][identity]=dict(identity=r,registry_version=SPECIAL_NPC_REGISTRY_VERSION,
            draw_hex=draw.hex(),stream_hex=stream.hex(),voice=voice,banks_installed=True,actor_installed=True,
            active=True,selectable=False,native_execution_verified=False,actor_bytes=actor_bytes,
            descriptor=address,profile=address+32,slots=1,slot_stride=stride,pool_ram=address+240,
            flags_offset=at+4,callback_family=label,selection_gate='selected golden tool and real reward scene',**art_fields)
    struct.pack_into('>I',registry,TABLE+8,8)
    names,name_rows=identities(base,members);registry[IDENTITIES:IDENTITIES+144]=names.ljust(144,b'\0')
    old_banks=npc['banks'];dma=struct.pack('>4I',0x41464E44,1,len(old_banks),12)+b''.join(
        struct.pack('>3I',b['vrom'],b['vrom']+b['bytes'],b['physical']) for b in old_banks)
    if registry[DMA:DMA+len(dma)]!=dma:raise ValueError('Changed retained character DMA directory')
    pools[-16:]=b'AFRP'*4
    return registry,bytes(pools),name_rows


def install(base,prior,blob,core,output,directory):
    """Install one connected reward batch through the shared cartridge writer."""
    from v3_asset_loader import BLOB,compile_part
    from v3_npc_registry import append_banks,DMA
    from v3_registry import SPECIAL_NPCS
    from v3_holiday_selection import refresh_receipts
    from v3_holiday_dialogue import check_provenance
    from v3_event_text import patch_bounds
    from v3_holiday_sky import profile_packet
    from v3_resource_capacity import checked_limit
    from v3_room_effects import restore_controller,extend_controller,RAM as OWNER_RAM
    from v3_furniture_install import relocate_resource_plan
    from v3_sound_programs import install_audio_resources,permanent_budget,audio_archive,installed_resource
    from v3_tree_effects_runtime import relocate_art_pages
    import v3_physical_resources as physical
    directory=directory.resolve();connected=json.loads((directory/'connected.json').read_bytes())
    if (not directory.is_relative_to(ROOT/'build') or connected['format']!='AFV3-CONNECTED-REWARDS-1' or
            connected['base_sha256']!=sha256(base) or connected['base_abi']!=prior['runtime_abi'] or
            not connected['native_services_bound']):raise ValueError('Rewards need their current connected preparation')
    a=connected['actor_report'];fx=connected['effect_report'];symbols=connected['symbols']
    actor_dir=ROOT/connected['actor_preparation'];effect_dir=ROOT/connected['effect_preparation']
    for report,parent in ((a,actor_dir),(fx,effect_dir)):
        for file,digest in report['sources'].items():
            current=(ROOT/file).read_bytes()
            if sha256(current)==digest:continue
            extension=b",'00c300ffc47a0cff'"
            if (report is fx and file=='tools/v3_holiday_sky.py' and current.count(extension)==1 and
                    sha256(current.replace(extension,b''))==digest):
                from v3_holiday_sky import native_bindings
                from v3_reward_effects import NATIVE_SERVICES
                links,evidence=native_bindings(base,{n:n for n in NATIVE_SERVICES})
                if links==fx['native_service_candidates'] and evidence==fx['native_service_evidence']:continue
            raise ValueError('Changed connected reward source: '+file)
        for file,digest in report['generated_sha256'].items():
            if sha256((parent/file).read_bytes())!=digest:raise ValueError('Changed generated reward source')
    from v3_reward_bindings import layout
    if a['memory']!=layout(prior):raise ValueError('Changed reward memory ownership')
    pieces={}
    for kind in ('actors','effects'):
        data=(directory/(kind+'.bin')).read_bytes();row=connected['regions'][kind]
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:raise ValueError('Changed connected reward region')
        pieces[kind]=data
    e=copy.deepcopy(prior['equipment_resources']);d=e['carried_items'];q=d['quest'];npc=e['npc_extra']
    old=copy.deepcopy(q['packet']);files=by_vrom(base);state=a['native_state']
    if (q.get('rewards') or prior['save_codec']['format_version']!=19 or
            old!=q['npc']['packet'] or old!=d['spawning']['packet'] or old!=d['paper']['quantities']['packet'] or
            q['npc']['end']!=old['ram']+old['bytes'] or state['state_ram']!=LAYOUT['state']['ram']):
        raise ValueError('Rewards require the complete installed carried baseline')
    work=output/'golden-rewards';work.mkdir()
    raw=bytearray(base[old['physical']:old['physical']+old['bytes']])
    if sha256(raw)!=old['sha256']:raise ValueError('Changed retained carried startup packet')
    raw.extend(bytes(LAYOUT['pools']['ram']+LAYOUT['pools']['bytes']-old['ram']-len(raw)))
    storage=copy.deepcopy(state['storage']);storage_data=(actor_dir/'storage/code.bin').read_bytes()
    if len(storage_data)!=storage['bytes'] or sha256(storage_data)!=storage['sha256']:
        raise ValueError('Changed complete format-20 storage')
    for address,data in ((LAYOUT['storage']['ram'],storage_data),
            (LAYOUT['actors']['ram'],pieces['actors']),(LAYOUT['effects']['ram'],pieces['effects'])):
        at=address-old['ram'];raw[at:at+len(data)]=data
    actor_code=dict(connected['regions']['actors'],symbols=symbols,toolchain=IMAGE)
    redirects=redirect_module(raw,old,q['storage'],q['storage_ram'],storage,LAYOUT['storage']['ram'],
        ('af_v3_','af_holiday_cards_','af_carried_','af_reward_'))
    for row in redirects:row['owner']='storage'
    required={'af_v3_save_check','af_v3_save_pack','af_v3_console_storage_reset',
        'af_v3_console_storage_commit','af_v3_console_storage_valid','af_v3_console_player_clear',
        'af_holiday_cards_valid','af_carried_quest_set_day'}
    if not required<={r['name'] for r in redirects}:raise ValueError('Incomplete format-20 save redirects')
    rr=redirect_module(raw,old,q['npc']['code'],q['npc']['ram'],actor_code,LAYOUT['actors']['ram'],('af_hp_',))
    for row in rr:row['owner']='registry'
    redirects.extend(rr)
    required=set(a['registry']['redirects'])|{'af_hp_spawn_profile'}
    if not required<={r['name'] for r in rr}:raise ValueError('Incomplete 27-owner registry redirects')
    # All fallback imports belong to earlier native trampolines/controllers,
    # not to the public entries being redirected into this new owner.
    if {r['address'] for r in redirects}&{v for n,v in connected['bindings'].items() if 'previous' in n}:
        raise ValueError('Golden registry would recurse through a fallback import')
    q['npc']['loaded_code']['sha256']=q['npc']['code']['sha256']
    q['npc']['sha256']=sha256(raw[q['npc']['ram']-old['ram']:q['npc']['end']-old['ram']])
    registry,pools,name_rows=reward_npcs(base,e,pieces['actors'],symbols)
    at=LAYOUT['pools']['ram']-old['ram'];raw[at:at+len(pools)]=pools
    art_dir=ROOT/'build/v3-reward-farley-art-01';identity='GAFE01-r0/npc/hem'
    waves=(effect_dir/'reward-wave.bin').read_bytes();wave_owner=audio_archive(base,core,'wave')
    old_wave,_,_=installed_resource(base,core,'wave',fx['audio']['wave_index'])
    wave_end=wave_owner.pstart+wave_owner.size;wave_after=wave_end+len(waves)-len(old_wave)
    if wave_after<=wave_end:raise ValueError('Unexpected golden reward sample-bank growth')
    banks,asset,records,writes,staged=append_banks(base,prior,blob,
        [dict(SPECIAL_NPCS[identity],identity=identity,directory=art_dir)],excluded_spans=((wave_end,wave_after),))
    old_count=len(npc['banks']);npc['banks']+=banks
    if any(registry[DMA+16+old_count*12:DMA+16+(old_count+len(banks))*12]):
        raise ValueError('Expanded reward DMA directory overwrites data')
    struct.pack_into('>I',registry,DMA+8,len(npc['banks']))
    for i,b in enumerate(banks,old_count):struct.pack_into('>3I',registry,DMA+16+i*12,b['vrom'],b['vrom']+b['bytes'],b['physical'])
    changes,hooks,relocation_evidence=native_consumers(base,symbols)
    patched=changes.pop(CODE_VROM)
    if bytes(core)!=files[CODE_VROM].extract(base):raise ValueError('Reward callers overlap another core update')
    core[:]=patched
    text=copy.deepcopy(a['dialogue']);check_provenance(text)
    text.update(choice_vrom=prior['import_storage']['choice_vrom'],
        hooks=patch_bounds(core,text['first_id'],text['count']),installed=True)
    if text['choice_count']:raise ValueError('Unreviewed extra reward choice directory')
    for row in text['resources']:
        data=(actor_dir/row['file']).read_bytes()
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:raise ValueError('Changed reward dialogue')
        row['original_sha256']=row.pop('previous_sha256');name='golden-rewards/'+row['file']
        write_new(output/name,data);row['file']=name
    effects=e['room_rigs']['effects'];controller=effects['controller']
    if controller['count']!=122 or [r['id'] for r in effects['profiles']]!=list(range(111,122)):
        raise ValueError('Changed complete native/additive effect identities')
    native,rel=restore_controller(files[controller['vrom']].extract(base),files[controller['reloc']].extract(base),controller)
    start=(len(blob)+15)&~15;count=14
    if BLOB+start+64*count>checked_limit(base,prior):raise ValueError('Reward profiles exceed shared storage')
    blob.extend(bytes(start+64*count-len(blob)));rows=[];additions=[]
    for i in range(count):
        at=start+64*i
        if i<11:
            row=copy.deepcopy(effects['profiles'][i]);payload=bytes(blob[row['blob_offset']:row['blob_offset']+64])
            if sha256(payload)!=row['sha256']:raise ValueError('Changed retained complete effect profile')
            addition=copy.deepcopy(controller['additions'][i])
        else:
            family=fx['family'][i-11];kind=family['kind']
            callbacks=[symbols['af_rw_effect_'+kind+'_'+phase] for phase in ('init','ct','mv','dw')]
            payload=profile_packet(callbacks,family['policy_hex'],code_bounds=connected['regions']['effects']['code_bounds'])
            row=dict(id=family['native_id'],kind='reward-'+kind,callbacks=callbacks,
                callback_owner='golden-rewards',policy_hex=family['policy_hex'],
                source_symbol=family['source_symbol'],source_id=family['source_id'],source_sha256=family['sha256'])
            addition=dict(id=family['native_id'],graphics=fx['artwork'][kind]['graphics'],unique=family['unique'])
        row.update(blob_offset=at,vrom=BLOB+at,bytes=64,sha256=sha256(payload));rows.append(row);blob[at:at+64]=payload
        logical=0x80700000+i*0x100
        addition['overlay']=[BLOB+at,BLOB+at+32,logical,logical+32,logical];additions.append(addition)
    defines=[f[2:] for f in controller['loader']['flags'] if f.startswith('-D') and
        not f.startswith(('-DAF_EFFECT_PROFILES=','-DAF_EFFECT_COUNT=','-DAF_EFFECT_REWARD_','-DAF_EFFECT_TREE_COUNT='))]
    defines.extend((f'AF_EFFECT_PROFILES=0x{BLOB+start:X}u',f'AF_EFFECT_COUNT={count}u',
        'AF_EFFECT_TREE_COUNT=2u','AF_EFFECT_REWARD_COUNT=3u',f'AF_EFFECT_REWARD_START=0x{LAYOUT["effects"]["ram"]:X}u',
        f'AF_EFFECT_REWARD_END=0x{connected["regions"]["effects"]["code_bounds"][1]:X}u'))
    loader=compile_part('effect_loader',work/'effect-loader',defines=tuple(defines))
    owner,newrel,new_controller=extend_controller(native,rel,additions,loader=loader,graphics_vrom=effects['bank']['vrom'])
    offset=0x801010B0-CODE_RAM;before=bytes.fromhex(controller['descriptor']['after'])
    if core[offset:offset+32]!=before:raise ValueError('Changed effect controller descriptor')
    after=struct.pack('>8I',controller['vrom'],controller['vrom']+len(owner),OWNER_RAM,OWNER_RAM+len(owner),0,OWNER_RAM+0x36A0,0,0)
    core[offset:offset+32]=after
    new_controller.update(installed=True,vrom=controller['vrom'],reloc=controller['reloc'],ram=OWNER_RAM,
        descriptor=dict(address=0x801010B0,before=before.hex(),after=after.hex()))
    bank=(effect_dir/'effect-art-bank.bin').read_bytes();previous=effects['bank']
    if (len(bank)!=fx['bank']['bytes'] or sha256(bank)!=fx['bank']['sha256'] or
            bank[:previous['bytes']]!=files[previous['vrom']].extract(base)):
        raise ValueError('Changed complete reward effect artwork bank')
    changes.update({controller['vrom']:owner,controller['reloc']:newrel,previous['vrom']:bank})
    effects.update(profiles=rows,controller=new_controller,additional_scene_bytes=new_controller['additional_scene_bytes'])
    effects['bank'].update(bytes=len(bank),sha256=sha256(bank))
    audio=copy.deepcopy(fx['audio'])
    for name,row in audio['files'].items():
        data=(effect_dir/name).read_bytes()
        if len(data)!=row['bytes'] or sha256(data)!=row['sha256']:raise ValueError('Changed reward audio resource')
    staged,records,page_writes,page_moves=relocate_art_pages(staged,records,e,wave_end,
        wave_after,excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),))
    writes.extend(page_writes);audio_prior=copy.deepcopy(prior);audio_prior['physical_resources']=records
    seq,font,wave,audio_changes,audio_growth,heap_growth,heap_patches,budget,fire=install_audio_resources(
        staged,audio_prior,blob,core,(effect_dir/'reward-sequence.bin').read_bytes(),
        dict(font=(effect_dir/'reward-font.bin').read_bytes(),wave=waves),audio)
    if set(changes)&set(audio_changes):raise ValueError('Reward owner and audio changes overlap')
    changes.update(audio_changes);moves=[audio_growth] if audio_growth else []
    for v,value in changes.items():
        if any(r['vrom']==v for r in moves):continue
        if len(value)==files[v].size and not files[v].pend:continue
        _,row=relocate_resource_plan(staged,files,v,value,minimum_physical=0x100000,
            reservations=records+moves,append_only=False,allow_compressed=True,
            excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),))
        moves.append(row)
    # Reserve every changed DMA owner before allocating the larger startup
    # packet, including compressed owners whose complete expanded image grows.
    pending=tuple((r['physical'],r['physical']+r['bytes']) for r in moves)
    replacement=physical.allocate(staged,records,bytes(raw),'golden-rewards-GAFE01-r0',best_fit=True,
        excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),*pending))
    records.append(replacement);packet=dict(replacement,ram=old['ram'],crc32=zlib.crc32(raw),storage='physical-ROM')
    writes.append((replacement,bytes(raw)))
    payloads={npc['packet']['id']:registry};refresh_receipts(e,records,payloads)
    row=next(r for r in records if r['id']==npc['packet']['id']);previous_row=next(r for r in prior['physical_resources'] if r['id']==row['id'])
    writes.append((dict(row,previous_sha256=previous_row['sha256']),bytes(registry)))
    for parent in (q,q['npc'],d['spawning'],d['paper']['quantities']):parent['packet']=copy.deepcopy(packet)
    q['storage_previous']=q['storage'];q.update(storage=storage,storage_ram=LAYOUT['storage']['ram'],save_format=20,wire_version=7)
    for saved in (d['storage'],e['holiday_items']['controls']['storage']):
        saved.update(active_code=copy.deepcopy(storage),save_format=20,wire_version=7)
    e['console_storage'].update(save_format=20,card_runtime=copy.deepcopy(storage))
    if e['diaries']['memory']['scratch']['bytes']!=state['retained_scratch_bytes']:
        raise ValueError('Changed active save scratch owner')
    e['diaries']['memory']['scratch']['bytes']=state['scratch_bytes']
    shared=e['sound_programs'];shared.update(previous_sequence=copy.deepcopy(shared['sequence']),sequence=seq,
        before_budget=budget,after_budget=permanent_budget(core),native_synthesis_tested=False)
    shared.setdefault('trigger_batches',[]).append(dict(programs=audio['registered_programs'],tables=audio['registered_tables']))
    for key in ('furniture_audio','furniture_level_audio'):
        if key in e:e[key].update(sequence=copy.deepcopy(seq),font=copy.deepcopy(font),wave=copy.deepcopy(wave),after_budget=copy.deepcopy(shared['after_budget']))
    trigger=e['furniture_audio'];trigger.update(programs=sorted(trigger['programs']+audio['registered_programs'],key=lambda r:r['source_sound_word']),
        tables=audio['registered_tables'],layout=audio['layout'],priority_table_sha256=sha256(core[0x80113B84-CODE_RAM:0x80113B84-CODE_RAM+128]))
    audio.update(installed=True,sequence=seq,font=font,wave=wave,heap_growth=heap_growth,heap_patches=heap_patches)
    report=dict(format='AFV3-GOLDEN-REWARDS-INSTALLED-1',installed=True,prepared=str(directory.relative_to(ROOT)),
        packet=copy.deepcopy(packet),preserved_packet=old,ram=LAYOUT['state']['ram'],end=LAYOUT['pools']['ram']+LAYOUT['pools']['bytes'],
        memory=a['memory'],storage=storage,save_format=20,wire_version=7,registry=a['registry'],code=actor_code,
        effects=dict(fx,code=connected['regions']['effects'],profiles=rows[11:]),identities=name_rows,
        redirects=redirects,installed_hooks=hooks,relocation_evidence=relocation_evidence,text=text,audio=audio,
        speech=dict(a['speech'],native_hooks_installed=True),native_execution_verified=False,selectable=False,
        pending=['independent golden tool selection','native golden reward and shovel acquisition checks'])
    if 'af_rw_birthday_mode' in symbols:
        from v3_creature_choices import BIRTHDAY_CHOICE
        mode=symbols['af_rw_birthday_mode'];at=mode-packet['ram']
        if not actor_code['ram']<=mode<actor_code['ram']+actor_code['bytes'] or raw[at:at+4]!=bytes(4):
            raise ValueError('Missing owned N64-default birthday presentation setting')
        report['birthday_choice']=dict(BIRTHDAY_CHOICE,ram=mode,default='N64',values=dict(N64=0,GameCube=1))
    q['rewards']=report;effects['golden_rewards']=dict(profiles=[122,123,124],code=connected['regions']['effects'])
    report['sources']={p:sha256((ROOT/p).read_bytes()) for p in
        (*a['sources'],*fx['sources'],'tools/v3_reward_install.py','overlays/v3/reward_events.ld',
         'tools/v3_holiday_participants_install.py','tools/v3_holiday_dialogue.py',
         'tools/v3_room_goods.py','tools/v3_furniture_install.py','tools/v3_npc_native.py','tools/v3_npc_registry.py')}
    report['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in
        ('tools/v3_creature_choices.py','tools/v3_holiday_selection.py')})
    npc['sources'].update(report['sources']);d['sources'].update(report['sources'])
    updates={k:copy.deepcopy(prior[k]) for k in ('save_codec','clothing','room_surfaces')}
    updates['save_codec'].update(format_version=20,active_storage_code=copy.deepcopy(storage),card_storage_code=copy.deepcopy(storage))
    ext=updates['clothing']['save_extension'];ext.update(format_version=20,active_storage_code=copy.deepcopy(storage))
    ext['legacy_formats_read']=list(dict.fromkeys([*ext['legacy_formats_read'],'AFS3-v19']))
    updates['room_surfaces']['save']['disk_format_version']=20
    updates.update(asset=asset,object_capacity=460,physical_resources=records,resource_growth=moves,
        relocated_physical_resources=page_moves,fire_sound=fire,
        save_warning='Format-20 experimental saves require this or a newer compatible build. Compatible older saves migrate forward. '
            'Four-sheet saves still require four-sheet mode. V2 and format-19-or-earlier V3 cannot read these saves. Keep backups.')
    write_new(work/'installed.json',(json.dumps(report,indent=2)+'\n').encode());write_new(work/'packet.bin',raw)
    return e,changes,updates,writes
