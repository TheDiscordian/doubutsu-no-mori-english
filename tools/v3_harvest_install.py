"""Connect the complete Harvest owner and retain shared actor/motion consumers.

Linking and static pool construction are not cartridge installation or native
gameplay. Source hiding/manager hooks and selected family admission are required
before an enclosing installer can activate these resources.
"""
import argparse
import copy
import json
import os
from pathlib import Path
import struct
import subprocess
import zlib
from types import SimpleNamespace

from aflib import sha256
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import ROOT

RAM=0x807F0000
CODE_END=0x807FC000
END=0x80800000
SOURCES=('tools/v3_harvest_install.py','overlays/v3/harvest_event.ld',
    'tools/v3_npc_native.py','tools/v3_npc_registry.py','tools/v3_npc_stream_runtime.py',
    'tools/v3_registry.py','overlays/v3/npc_identity.h','overlays/v3/npc_identity.c',
    'overlays/v3/npc_identity_spawn.S','overlays/v3/npc_registry.h','overlays/v3/npc_registry_limits.h',
    'tools/v3_holiday_hiding.py','overlays/v3/holiday_hiding.h','overlays/v3/holiday_hiding.c',
    'overlays/v3/holiday_hiding_native.c','overlays/v3/holiday_placement.c','overlays/v3/holiday_placement.h',
    'overlays/v3/harvest_manager.h','overlays/v3/harvest_manager.c',
    'tools/v3_room_goods.py','overlays/v3/surface_bootstrap.c','tools/v3_furniture_install.py',
    'overlays/v3/asset.c','tools/v3_npc_draw.py')


def franklin(image,prior,report,body,symbols,art_dir):
    """Build the full ninth slot; verify both existing bounded table tails."""
    from v3_npc_registry import TABLE
    from v3_npc_native import IDENTITIES,BRIDGES,identities
    from v3_npc_stream_runtime import native_records
    from v3_furniture_pipeline import Source
    from v3_registry import SPECIAL_NPCS,SPECIAL_NPC_REGISTRY_VERSION
    identity=SPECIAL_NPCS['GAFE01-r0/npc/ev-turkey']
    npc=prior['equipment_resources']['npc_extra'];packet=npc['packet']
    registry=image[packet['physical']:packet['physical']+packet['bytes']]
    if (sha256(registry)!=packet['sha256'] or
            struct.unpack_from('>4I',registry,TABLE)!=(0x41464E58,1,8,44)):
        raise ValueError('Changed complete eight-character native registry')
    row_at=TABLE+16+8*44
    if row_at+44>0xA200 or any(registry[row_at:row_at+44]):
        raise ValueError('Ninth native character overlaps retained descriptor data')
    members={'GAFE01-r0/npc/ev-soncho2':npc['record']['identity']}
    members.update({k:v['identity'] for k,v in npc['prepared_characters'].items() if v['actor_installed']})
    if len(members)!=8:raise ValueError('Incomplete retained native character identities')
    names,retained_rows=identities(image,members)
    if (registry[IDENTITIES:IDENTITIES+144]!=names.ljust(144,b'\0') or
            any(registry[IDENTITIES+144:BRIDGES])):
        raise ValueError('Changed retained NPC names or nonempty ninth identity row')
    members['GAFE01-r0/npc/ev-turkey']=identity
    order=[row['identity'] for row in retained_rows]+['GAFE01-r0/npc/ev-turkey']
    new_names,name_rows=identities(image,members,order=order)
    if len(new_names)!=BRIDGES-IDENTITIES or new_names[16:144]!=names[16:144]:
        raise ValueError('Expanded names alter existing complete character identities')
    compiled=body[symbols['Ev_Turkey_Profile']-RAM:symbols['Ev_Turkey_Profile']-RAM+36]
    actor_bytes=struct.unpack_from('>I',compiled,12)[0]
    if (len(compiled)!=36 or struct.unpack_from('>H',compiled)[0]!=identity['donor_profile'] or
            actor_bytes!=2420 or report['native_layout']['actor_bytes']!=actor_bytes):
        raise ValueError('Changed complete linked Franklin profile')
    art_raw=(art_dir/'art.json').read_bytes();art=json.loads(art_raw)
    if (art['draw_index']!=identity['draw_index'] or art['model_bytes']!=12480 or
            art['texture_bytes']!=4128):
        raise ValueError('Changed complete Franklin art reservation')
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    draw,stream,voice=native_records(source,art,identity['name'],identity['model_bank'],identity['texture_bank'])
    if voice!=233:raise ValueError('Changed complete Franklin voice identity')
    stride=((actor_bytes+15)&~15)+32;pool=bytearray(240+stride)
    callbacks=[symbols['af_hp_'+phase] for phase in ('ctor','dtor','step','draw','save')]
    struct.pack_into('>8I',pool,0,0,0,0,0,0,CODE_END+32,0,0)
    struct.pack_into('>HHIHH6I',pool,32,identity['profile'],3<<8,
        struct.unpack_from('>I',compiled,4)[0],identity['name'],3,actor_bytes,*callbacks)
    pool[80:180]=draw;pool[192:228]=stream
    struct.pack_into('>4I',pool,240,0x41464E53,0,identity['name'],identity['profile'])
    pool[-16:]=b'NPCG'*4
    if len(pool)>END-CODE_END:raise ValueError('Complete Franklin pool exceeds owned tail')
    record=struct.pack('>HH9I2H',identity['name'],identity['profile'],3,actor_bytes,1,stride,
        CODE_END+240,CODE_END,CODE_END+80,CODE_END+192,voice,identity['model_bank'],identity['texture_bank'])
    return bytes(pool),dict(identity=identity,registry_version=SPECIAL_NPC_REGISTRY_VERSION,
        row_offset=row_at,row_hex=record.hex(),names_hex=new_names.hex(),name_rows=name_rows,
        actor_bytes=actor_bytes,slot_stride=stride,pool_ram=CODE_END+240,descriptor=CODE_END,
        profile=CODE_END+32,voice=voice,art=str(art_dir.relative_to(ROOT)),art_sha256=sha256(art_raw),
        retained_registry_sha256=packet['sha256'],installed=False)


def manager_owner(image,prior,symbols,output):
    """Prepare the complete five-callback row and native daily cleanup caller.

    Preserve every existing relocated control and the installed birthday hook.
    Nothing is written to the cartridge by this preparation.
    """
    from aflib import CODE_RAM,CODE_VROM,by_vrom,u32
    from v3_campsite_manager import RAM as owner_ram,VROM,RELOC,METADATA,CONTROL_COUNT
    from npc_mail_show import relocate_verified_data
    from v3_import_storage import jump
    files=by_vrom(image);old=files[VROM].extract(image);oldrel=files[RELOC].extract(image)
    previous=prior['campsite_manager'];table=previous['table'];count=previous['control_count']
    head=struct.unpack_from('>5I',oldrel)
    if (count!=74 or table-owner_ram+count*32!=len(old) or
            u32(old,CONTROL_COUNT-owner_ram)!=count or head[:4]!=(len(old),0,0,0) or
            sha256(oldrel)!=previous['relocation_sha256'] or previous['today_pointer_capacity']<count+1):
        raise ValueError('Changed complete native Harvest manager capacity')
    phases=('start','stop','in','out','behind')
    callbacks=[symbols['af_hr_manager_'+phase] for phase in phases]
    if any(not RAM<=address<CODE_END for address in callbacks):
        raise ValueError('Unowned complete Harvest manager callback')
    data=bytearray(old);struct.pack_into('>I',data,CONTROL_COUNT-owner_ram,count+1)
    data.extend(struct.pack('>8I',116,*callbacks,0,0))
    reloc=bytearray(oldrel);struct.pack_into('>I',reloc,0,len(data))
    if len(data)+len(reloc)>0xC000 or VROM+len(data)>RELOC or owner_ram+len(data)>0x809670B0:
        raise ValueError('Harvest control exceeds the existing native manager allocation')
    for address in (0x801A0010,0x802F8010):
        before=relocate_verified_data(SimpleNamespace(ram=owner_ram,resident_bytes=len(old),sections=head),old,oldrel,address)
        after=relocate_verified_data(SimpleNamespace(ram=owner_ram,resident_bytes=len(data),
            sections=(len(data),0,0,0,head[4])),bytes(data),bytes(reloc),address)
        allowed=range(CONTROL_COUNT-owner_ram,CONTROL_COUNT-owner_ram+4)
        if (any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))) or
                after[len(old):]!=data[len(old):] or
                before[table-owner_ram:len(old)]!=after[table-owner_ram:len(old)]):
            raise ValueError('Harvest changes existing relocated native controls')
    core=bytearray(files[CODE_VROM].extract(image));patches=[]
    def patch(address,before,after):
        at=address-CODE_RAM
        if core[at:at+len(before)]!=before:raise ValueError('Changed complete Harvest daily caller')
        core[at:at+len(after)]=after
        patches.append(dict(address=address,before=before.hex(),after=after.hex()))
    calendar=prior['equipment_resources']['carried_items']['quest']['code']['symbols']['af_cw_calendar_before_cleanup']
    patch(0x8007F630,struct.pack('>2I',jump(calendar,link=True),0),
        struct.pack('>2I',jump(symbols['af_hr_calendar_before_cleanup'],link=True),0))
    for address in (0x8007F640,0x8007F660):
        patch(address,struct.pack('>I',0x24110074),struct.pack('>I',0x24110075))
    patch(METADATA,struct.pack('>4I',VROM,VROM+len(old),owner_ram,owner_ram+len(old)),
        struct.pack('>4I',VROM,VROM+len(data),owner_ram,owner_ram+len(data)))
    for name,value in (('harvest-manager.bin',data),('harvest-manager-reloc.bin',reloc),('harvest-core.bin',core)):
        write_new(output/name,bytes(value))
    return dict(vrom=VROM,reloc=RELOC,ram=owner_ram,table=table,control_count=count+1,
        retained_controls=count,callbacks=dict(zip(phases,callbacks)),
        bytes=len(data),sha256=sha256(data),previous_sha256=sha256(old),
        relocation_sha256=sha256(reloc),relocation_bytes=len(reloc),
        core_sha256=sha256(core),core_patches=patches,daily_type_bound=117,
        original_controls_and_relocations_retained=True,additional_owner_bytes=32,
        additional_resident_bytes=0,installed=False,native_execution_verified=False)


def connect(lock,prepared,output,art):
    from v3_furniture_install import inputs
    from v3_console_disk_install import reservations
    from v3_holiday_participants import bindings
    prepared,output,art=(Path(p).resolve() for p in (prepared,output,art))
    if output.exists() or not all(p.is_relative_to(ROOT/'build') for p in (prepared,output,art)):
        raise ValueError('Use checked ignored preparations and a fresh output')
    image,prior=inputs(lock);report=json.loads((prepared/'prepared.json').read_bytes())
    if report['base_sha256']!=sha256(image) or report['base_abi']!=prior['runtime_abi']:
        raise ValueError('Harvest preparation is not based on the current input')
    for file,digest in report['sources'].items():
        if sha256((ROOT/file).read_bytes())!=digest:raise ValueError('Changed prepared source: '+file)
    for file,digest in report['generated_sha256'].items():
        if sha256((prepared/file).read_bytes())!=digest:raise ValueError('Changed generated source: '+file)
    if sha256((prepared/'harvest-unbound.o').read_bytes())!=report['object']['sha256']:
        raise ValueError('Changed complete Harvest object')
    if any(a<END and RAM<b for a,b in reservations(prior)):
        raise ValueError('Complete Harvest reservation overlaps a retained owner')
    equipment=prior['equipment_resources'];quest=equipment['carried_items']['quest']
    native=equipment['npc_extra']['events']['native_directory']
    candidates,_=bindings(image,prior)
    candidates.update(quest['npc']['bindings'])
    for owner in (equipment['carried_items']['code'],quest['code'],quest['npc']['code'],
            quest['rewards']['code'],native['code'],quest['rewards']['storage']):
        candidates.update(owner['symbols'])
    candidates.update(report['native_contract']['bindings'])
    shared=equipment['npc_extra']['events']['participants']['code']['symbols']
    for name in ('af_hp_continue','af_hp_frame'):
        candidates[name]=shared[name]
    candidates['af_hr_prior_calendar_before_cleanup']=quest['code']['symbols']['af_cw_calendar_before_cleanup']
    from v3_holiday_hiding import generate as hiding_generate
    from v3_furniture_pipeline import Source
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,hiding=hiding_generate(source,image,prior)
    candidates.update(equipment['npc_extra']['events']['placement']['bindings'])
    candidates.update(hiding['bindings'])
    candidates['af_holiday_hide_native_ball']=hiding['native_ball_position']
    candidates.update(af_hr_manager_native_set_status=0x8007FDA8,
        af_hr_manager_native_clear_status=0x8007FE74,af_hr_manager_native_check_status=0x8007FF08)
    output.mkdir(parents=True)
    for name,value in generated.items():write_new(output/name,value.encode())
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            text=True,capture_output=True,timeout=60)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        return result.stdout
    obj='/source/'+str(prepared.relative_to(ROOT))+'/harvest-unbound.o'
    flags=['-c','-Os','-EB','-mabi=32','-march=vr4300','-mfix4300','-G0','-mno-abicalls',
        '-fno-pic','-ffreestanding','-fno-builtin','-fno-common','-fno-stack-protector',
        '-ffunction-sections','-fdata-sections','-fstack-usage','-Wall','-Wextra','-Werror',
        '-I/source/overlays/v3','-I/out']
    units=['hiding-source.c','hiding-manager-source.c','/source/overlays/v3/harvest_manager.c',
        '/source/overlays/v3/holiday_hiding.c','/source/overlays/v3/holiday_hiding_native.c',
        '/source/overlays/v3/holiday_placement.c']
    run('gcc',*flags,*units)
    run('ld','-EB','-r',obj,*(Path(n).stem+'.o' for n in units),'-o','connected-unbound.o')
    undefined={row.split()[-1] for row in run('nm','--undefined-only','connected-unbound.o').splitlines()}
    missing=undefined-candidates.keys()
    if missing:raise ValueError('Unbound complete Harvest services: '+', '.join(sorted(missing)))
    links={name:candidates[name] for name in sorted(undefined)}
    redirected=set(report['registry']['redirects'].values())|{report['shared_motions']['redirect']}
    if any(address in redirected for name,address in links.items()):
        raise ValueError('Harvest would recurse through a replaced shared entry')
    run('ld','-EB',*(f'--defsym={n}=0x{v:X}' for n,v in links.items()),
        '-T','/source/overlays/v3/harvest_event.ld','connected-unbound.o','-Map','harvest.map','-o','harvest.elf')
    if run('nm','--undefined-only','harvest.elf').strip():raise ValueError('Harvest retains unresolved services')
    symbols={name:int(at,16) for at,kind,name in
        (line.split() for line in run('nm','--defined-only','harvest.elf').splitlines())}
    run('objcopy','-O','binary','harvest.elf','harvest.bin');body=(output/'harvest.bin').read_bytes()
    if (symbols['af_hr_packet_start']!=RAM or symbols['af_hr_packet_end']!=RAM+len(body) or
            len(body)>CODE_END-RAM or body[-16:]!=b'AFHR'*4 or
            any(body[symbols['af_hr_bss_start']-RAM:symbols['af_hr_bss_end']-RAM])):
        raise ValueError('Incomplete Harvest packet/state/guard')
    pool,npc=franklin(image,prior,report,body,symbols,art)
    # Compile both nine-row readers in the existing native reservation. This
    # verifies preserved public entry addresses before eventual installation.
    from v3_npc_registry import refresh_renderer
    native_npc=copy.deepcopy(equipment['npc_extra']);pk=native_npc['packet']
    original=image[pk['physical']:pk['physical']+pk['bytes']];render_changes={}
    native_data=refresh_renderer(native_npc,original,output/'npc-code',image,render_changes,
        extra_sources=('overlays/v3/npc_identity.c','overlays/v3/npc_identity_spawn.S'),rebind_identities=True)
    write_new(output/'npc-runtime.bin',native_data)
    npc['runtime']=native_npc['code']
    npc['runtime_sha256']=sha256(native_data)
    npc['render_hooks']=native_npc['render_hooks']
    npc['identity_rebindings']=native_npc.get('identity_rebindings',[])
    npc['native_registry_public_addresses_retained']=True
    spawn_at=native_npc['code']['symbols']['af_npc_identity_spawn']-pk['ram']
    if struct.unpack_from('>I',native_data,spawn_at+0x4C)[0]!=0x2D41000A:
        raise ValueError('Native spawn assembly does not admit the complete nine-row registry')
    render_reports=[]
    for vrom,data in sorted(render_changes.items()):
        name=f'npc-render-{vrom:08X}.bin';write_new(output/name,data)
        render_reports.append(dict(vrom=vrom,file=name,bytes=len(data),sha256=sha256(data)))
    npc['render_owners']=render_reports
    write_new(output/'franklin-pool.bin',pool)
    manager=manager_owner(image,prior,symbols,output)
    write_new(output/'harvest.asm',run('objdump','-d','harvest.elf').encode())
    result=dict(format='AFV3-CONNECTED-HARVEST-1',base_sha256=sha256(image),base_abi=prior['runtime_abi'],
        prepared=str(prepared.relative_to(ROOT)),preparation=report,hiding=hiding,manager=manager,
        bindings=links,symbols=symbols,
        memory=dict(ram=RAM,end=END,code_end=CODE_END),
        code=dict(ram=RAM,bytes=len(body),sha256=sha256(body),code_bounds=[RAM,symbols['af_hr_code_end']],symbols=symbols),
        pool=dict(ram=CODE_END,bytes=len(pool),sha256=sha256(pool)),npc=npc,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        installed=False,native_execution_verified=False)
    write_new(output/'connected.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


def install(base,prior,blob,core,module,output,directory):
    """Publish the complete connected owner through the ordinary cartridge writer.

    Family admission remains a separate shared-category consumer. Disabled
    reward profiles cannot activate Franklin merely because his resources exist.
    """
    from aflib import CODE_RAM,CODE_VROM,by_vrom
    from v3_asset_loader import BLOB,MODULE
    from v3_npc_registry import append_banks,TABLE,DMA
    from v3_npc_native import IDENTITIES,BRIDGES
    from v3_reward_install import redirect_module
    from v3_holiday_selection import refresh_receipts
    from v3_holiday_dialogue import check_provenance
    from v3_event_text import patch_bounds
    from v3_furniture_install import relocate_resource_plan
    from v3_console_disk_install import reservations
    import v3_physical_resources as physical
    directory=directory.resolve();connected=json.loads((directory/'connected.json').read_bytes())
    if (not directory.is_relative_to(ROOT/'build') or connected['format']!='AFV3-CONNECTED-HARVEST-1' or
            connected['base_sha256']!=sha256(base) or connected['base_abi']!=prior['runtime_abi'] or
            prior['equipment_resources'].get('harvest')):
        raise ValueError('Harvest requires its complete current connected preparation')
    for file,digest in connected['sources'].items():
        if sha256((ROOT/file).read_bytes())!=digest:raise ValueError('Changed connected Harvest source: '+file)
    prepared=ROOT/connected['prepared'];a=connected['preparation']
    for file,digest in a['sources'].items():
        if sha256((ROOT/file).read_bytes())!=digest:raise ValueError('Changed Harvest actor source: '+file)
    for file,digest in a['generated_sha256'].items():
        if sha256((prepared/file).read_bytes())!=digest:raise ValueError('Changed complete prepared Harvest data')
    if any(first<END and RAM<last for first,last in reservations(prior)):
        raise ValueError('Connected Harvest overlaps a retained resident owner')
    def checked(file,row,key='sha256'):
        data=(directory/file).read_bytes()
        if sha256(data)!=row[key] or 'bytes' in row and len(data)!=row['bytes']:
            raise ValueError('Changed connected Harvest resource: '+file)
        return data
    files=by_vrom(base);e=copy.deepcopy(prior['equipment_resources']);npc=e['npc_extra']
    work=output/'harvest';work.mkdir()
    data=bytearray(END-RAM);code=checked('harvest.bin',connected['code'])
    pool=checked('franklin-pool.bin',connected['pool'])
    data[:len(code)]=code;data[CODE_END-RAM:CODE_END-RAM+len(pool)]=pool
    data[-16:]=b'AFHV'*4
    art=ROOT/connected['npc']['art'];identity=connected['npc']['identity']
    table_ram=CODE_END+0x1000;table=bytearray(462*8)
    table[:460*8]=blob[0x1000:0x1000+460*8]
    if CODE_END+len(pool)>table_ram or table_ram+len(table)>END-16:
        raise ValueError('Complete NPC object table overlaps Franklin or packet guards')
    banks,asset,records,writes,staged=append_banks(base,prior,blob,[dict(
        identity='GAFE01-r0/npc/ev-turkey',directory=art,
        model_bank=identity['model_bank'],texture_bank=identity['texture_bank'])],
        excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),),
        object_table=table,object_table_ram=table_ram)
    data[table_ram-RAM:table_ram-RAM+len(table)]=table
    allocation=physical.allocate(staged,records,bytes(data),'harvest-connected',best_fit=True,
        excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),))
    records.append(allocation);writes.append((allocation,bytes(data)))
    staged[allocation['physical']:allocation['physical']+len(data)]=data
    packet=dict(allocation,ram=RAM,crc32=zlib.crc32(data),storage='physical-ROM')
    native=bytearray(checked('npc-runtime.bin',dict(sha256=connected['npc']['runtime_sha256'])))
    old=npc['packet'];original=base[old['physical']:old['physical']+old['bytes']]
    if len(native)!=len(original) or native[0x2000:]!=original[0x2000:]:
        raise ValueError('Nine-row reader preparation changes retained actor data')
    row=connected['npc']['row_offset'];names=bytes.fromhex(connected['npc']['names_hex'])
    if row!=TABLE+16+8*44 or any(native[row:row+44]) or len(names)!=BRIDGES-IDENTITIES:
        raise ValueError('Changed ninth complete native identity reservation')
    native[row:row+44]=bytes.fromhex(connected['npc']['row_hex'])
    struct.pack_into('>I',native,TABLE+8,9);native[IDENTITIES:BRIDGES]=names
    old_banks=npc['banks'];all_banks=old_banks+banks
    expected=struct.pack('>4I',0x41464E44,1,len(old_banks),12)+b''.join(
        struct.pack('>3I',b['vrom'],b['vrom']+b['bytes'],b['physical']) for b in old_banks)
    if (native[DMA:DMA+len(expected)]!=expected or
            any(native[DMA+len(expected):DMA+16+len(all_banks)*12])):
        raise ValueError('Changed complete native NPC transfer directory')
    struct.pack_into('>I',native,DMA+8,len(all_banks))
    for i,b in enumerate(banks,len(old_banks)):
        struct.pack_into('>3I',native,DMA+16+i*12,b['vrom'],b['vrom']+b['bytes'],b['physical'])
    npc.update(code=connected['npc']['runtime'],banks=all_banks,
        render_hooks=connected['npc']['render_hooks'],identity_rebindings=connected['npc']['identity_rebindings'])
    changes={}
    # Merge the disjoint identity and calendar edits, never overwrite a changed
    # core with an independently prepared whole-file copy.
    before=files[CODE_VROM].extract(base)
    manager_core=checked('harvest-core.bin',dict(sha256=connected['manager']['core_sha256']))
    for i,(old_byte,new_byte) in enumerate(zip(before,manager_core)):
        if old_byte!=new_byte:
            if core[i]!=old_byte:raise ValueError('Harvest manager overlaps a changed core byte')
            core[i]=new_byte
    for owner in connected['npc']['render_owners']:
        changed=checked(owner['file'],owner);vrom=owner['vrom']
        if vrom==CODE_VROM or vrom==MODULE:
            target=core if vrom==CODE_VROM else module;baseline=files[vrom].extract(base)
            if len(changed)!=len(baseline):raise ValueError('Changed native identity owner extent')
            for i,(old_byte,new_byte) in enumerate(zip(baseline,changed)):
                if old_byte!=new_byte:
                    if target[i]!=old_byte:raise ValueError('Harvest identity overlaps a changed owner byte')
                    target[i]=new_byte
        else:changes[vrom]=changed
    manager=copy.deepcopy(connected['manager'])
    from v3_npc_draw import rebind_streaming_tables,extend_model_reservations
    streaming=rebind_streaming_tables(base,changes,table_ram)
    model_reservations=extend_model_reservations(base,changes,
        json.loads((art/'art.json').read_bytes())['model_bytes'])
    changes[manager['vrom']]=checked('harvest-manager.bin',manager)
    changes[manager['reloc']]=checked('harvest-manager-reloc.bin',
        dict(sha256=manager['relocation_sha256'],bytes=manager['relocation_bytes']))
    quest=e['carried_items']['quest'];old_packet=quest['packet']
    carried=bytearray(base[old_packet['physical']:old_packet['physical']+old_packet['bytes']])
    rewards=quest['rewards'];previous=copy.deepcopy(rewards['code'])
    redirects=redirect_module(carried,old_packet,rewards['code'],previous['ram'],
        connected['code'],RAM,('af_hp_',))
    earlier=quest['npc'];loaded=earlier['code']
    redirects.extend(redirect_module(carried,old_packet,loaded,earlier['ram'],
        connected['code'],RAM,('mEv_get_save_area','mEv_reserve_save_area','af_hg_animation')))
    earlier['loaded_code']['sha256']=loaded['sha256']
    earlier['sha256']=sha256(carried[earlier['ram']-old_packet['ram']:earlier['end']-old_packet['ram']])
    required=set(a['registry']['redirects'])|{'af_hp_spawn_profile'}
    if not required<={r['name'] for r in redirects}:
        raise ValueError('Incomplete connected Harvest shared owner redirects')
    motion=[r for r in redirects if r['name']=='af_hg_animation']
    if len(motion)!=1 or motion[0]['address']!=a['shared_motions']['redirect']:
        raise ValueError('Incomplete shared Harvest motion redirect')
    if {r['address'] for r in redirects}&set(connected['bindings'].values()):
        raise ValueError('Connected Harvest recurses through a retained service')
    payloads={npc['packet']['id']:native,old_packet['id']:carried}
    refresh_receipts(e,records,payloads)
    for old_row,value in ((prior['equipment_resources']['npc_extra']['packet'],native),
            (prior['equipment_resources']['carried_items']['quest']['packet'],carried)):
        record=next(r for r in records if r['id']==old_row['id'])
        writes.append((dict(record,previous_sha256=old_row['sha256']),bytes(value)))
    npc['prepared_characters']['GAFE01-r0/npc/ev-turkey']=dict(connected['npc'],
        banks_installed=True,actor_installed=True,selectable=False,native_execution_verified=False)
    text=copy.deepcopy(a['dialogue']);check_provenance(text)
    text['choice_vrom']=prior['import_storage']['choice_vrom']
    text['hooks']=patch_bounds(core,text['first_id'],text['count'])
    for resource in text['resources']:
        raw=(prepared/resource['file']).read_bytes()
        if (sha256(raw)!=resource['sha256'] or len(raw)!=resource['bytes'] or
                sha256(files[resource['vrom']].extract(base))!=resource['previous_sha256']):
            raise ValueError('Changed complete prepared Harvest dialogue bank')
        target='harvest/'+resource['file'];write_new(output/target,raw)
        resource.update(file=target,original_sha256=resource.pop('previous_sha256'))
    growth=[]
    for vrom,value in changes.items():
        if len(value)==files[vrom].size and not files[vrom].pend:continue
        _,move=relocate_resource_plan(staged,files,vrom,value,minimum_physical=0x100000,
            reservations=records+growth,append_only=False,allow_compressed=True,
            excluded_spans=((files[BLOB].pstart,files[BLOB].pstart+len(blob)),))
        growth.append(move)
    manager.update(installed=True,core_sha256=sha256(core))
    text['installed']=True
    report=dict(format='AFV3-HARVEST-INSTALLED-1',installed=True,packet=packet,
        preparation=str(directory.relative_to(ROOT)),code=connected['code'],pool=connected['pool'],
        npc=dict(connected['npc'],installed=True),registry=dict(a['registry'],installed=True),
        shared_motions=dict(a['shared_motions'],installed=True),
        manager=manager,hiding=dict(connected['hiding'],installed=True),text=text,redirects=redirects,
        rewards=a['rewards'],sources=connected['sources'],saved_format_changed=False,
        object_table=dict(ram=table_ram,bytes=len(table),sha256=sha256(table),count=462,
            retained_count=460,retained_prefix_sha256=sha256(table[:460*8]),
            native_streaming_rebindings=streaming,native_model_reservations=model_reservations),
        native_execution_verified=False,ordinary_gameplay_verified=False,selectable=False,
        pending=['independent Harvest furniture/surface admission with cutlery dependency',
            'ordinary conversation, hiding/arrival, reward delivery, and save/restart'])
    e['harvest']=report
    updates=dict(asset=asset,object_capacity=462,physical_resources=records,resource_growth=growth)
    campsite=copy.deepcopy(prior['campsite_manager'])
    campsite.update(control_count=75,output_sha256=manager['sha256'],
        relocation_sha256=manager['relocation_sha256'],bytes=manager['bytes'],harvest=manager)
    updates['campsite_manager']=campsite
    write_new(work/'packet.bin',data);write_new(work/'npc-registry.bin',native)
    write_new(work/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return e,changes,updates,writes


def finish(image,base,output,equipment,records):
    from v3_event_text import install as install_text
    text=equipment['harvest']['text']
    image=install_text(image,base,output,text,relocate=True,physical_resources=records)
    # Nook checks the current whole banks while its per-message identities stay
    # unchanged. An appended official conversation is not a Nook text defect.
    extensions={r['vrom']:r for r in text['resources']}
    for row in equipment['passwords']['nook']['dialogue']['resources']:
        extension=extensions.get(row['vrom'])
        if extension is None or row['sha256']!=extension['original_sha256']:
            raise ValueError('Harvest bank append does not preserve the current Nook text owner')
        row.update(sha256=extension['sha256'],bytes=extension['bytes'])
    return image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True)
    parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--art',type=Path,default=ROOT/'build/v3-harvest-franklin-art-02')
    args=parser.parse_args();report=connect(args.base_lock,args.prepared,args.output,args.art)
    print(json.dumps(dict(code_bytes=report['code']['bytes'],pool_bytes=report['pool']['bytes'],
        services=len(report['bindings']),installed=False)))


if __name__=='__main__':main()
