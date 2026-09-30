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
    'overlays/v3/npc_identity_spawn.S','overlays/v3/npc_registry.h','overlays/v3/npc_registry_limits.h')


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
    undefined={row.split()[-1] for row in report['unbound_services']}
    missing=undefined-candidates.keys()
    if missing:raise ValueError('Unbound complete Harvest services: '+', '.join(sorted(missing)))
    links={name:candidates[name] for name in sorted(undefined)}
    # Whole registry redirects must not chain a rebuilt owner to its own old
    # public entry. Retain only the original explicit fallback providers.
    redirected=set(report['registry']['redirects'].values())|{report['shared_motions']['redirect']}
    if any(address in redirected for name,address in links.items()):
        raise ValueError('Harvest would recurse through a replaced shared entry')
    output.mkdir(parents=True)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        result=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            text=True,capture_output=True,timeout=60)
        if result.returncode:raise ValueError(result.stdout+result.stderr)
        return result.stdout
    obj='/source/'+str(prepared.relative_to(ROOT))+'/harvest-unbound.o'
    run('ld','-EB',*(f'--defsym={n}=0x{v:X}' for n,v in links.items()),
        '-T','/source/overlays/v3/harvest_event.ld',obj,'-Map','harvest.map','-o','harvest.elf')
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
    write_new(output/'harvest.asm',run('objdump','-d','harvest.elf').encode())
    result=dict(format='AFV3-CONNECTED-HARVEST-1',base_sha256=sha256(image),base_abi=prior['runtime_abi'],
        prepared=str(prepared.relative_to(ROOT)),preparation=report,bindings=links,symbols=symbols,
        memory=dict(ram=RAM,end=END,code_end=CODE_END),
        code=dict(ram=RAM,bytes=len(body),sha256=sha256(body),code_bounds=[RAM,symbols['af_hr_code_end']],symbols=symbols),
        pool=dict(ram=CODE_END,bytes=len(pool),sha256=sha256(pool)),npc=npc,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES},
        installed=False,native_execution_verified=False)
    write_new(output/'connected.json',(json.dumps(result,indent=2)+'\n').encode())
    return result


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
