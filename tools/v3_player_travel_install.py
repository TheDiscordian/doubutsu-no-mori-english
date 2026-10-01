"""Install full player-note framing and native arrival/return without growing native buffers.

Code uses authenticated unused padding in two already-loaded packets. One new
startup packet owns the complete visiting player's record; resident save formats
and the model pool remain unchanged. Connected item/UI consumers follow this step.
"""
import copy
import json
import os
import re
import struct
import subprocess
import zlib

from aflib import CODE_RAM, sha256, u32
from apply_translation import write_new
from toolchain import IMAGE
from v3_asset_loader import BLOB, ROOT
from v3_console_disk_install import reservations
from v3_furniture_capacity import checked as checked_models
from v3_import_storage import jump
from v3_player_travel import DEFINES, FLAGS, SOURCES as PLAYER_SOURCES
from v3_private_save_bank import refresh_aliases, refresh_code
import v3_physical_resources as physical

BASE_SHA='1e978bc58945b255f601ac0cb0a163e528e3e728c13b50ca065127eca4ce9a60'
STATE, STATE_BYTES, RECORD_BYTES = 0x8062C020, 14240, 14204
IO, IO_END, LIFE, LIFE_END = 0x806A4800, 0x806A7FF0, 0x807F7B50, 0x807FC000
PARTS=('pak_native','pak_codec','pak_workspace','console_storage',
       'travel_native','travel_player','travel_context')
ROOTS=('af_v3_pak_native_read','af_v3_pak_native_write','af_v3_pak_native_status',
       'af_v3_travel_passport_clear','af_v3_travel_passport_save',
       'af_v3_travel_passport_load','af_v3_travel_private_copy',
       'af_v3_travel_visitor_collect','af_v3_travel_visitor_paper',
       'af_v3_travel_creature_collect')
SOURCES=tuple(dict.fromkeys((*PLAYER_SOURCES,'tools/v3_player_travel_install.py',
    'tools/v3_room_goods.py','tools/v3_furniture_install.py','overlays/v3/surface_bootstrap.c',
    'overlays/v3/travel_link.ld','overlays/v3/travel_native.c','overlays/v3/travel_native.h',
    'overlays/v3/travel_context.c','tests/v3_travel_native_test.c')))
NATIVE={
    'af_pi_lock':'padmgr_LockSerialMesgQ','af_pi_unlock':'padmgr_UnlockSerialMesgQ',
    'af_pi_open':'mCPk_NoteOpen','af_pi_make':'mCPk_NoteMake',
    'af_pi_num':'mCPk_NoteNum','af_pi_free':'mCPk_FreeBlockNum',
    'af_pi_file_state':'sCPk_FileState','af_pi_load':'sCPk_Load','af_pi_save':'sCPk_Save',
    'af_pi_delete':'sCPk_DeleteFile','af_pi_null_identity':'mPr_NullCheckPersonalID',
    'af_pak_check_private':'mPr_CheckPrivate','af_pak_set_kind':'mCPk_SetForestPakState',
    'af_pak_clear_private':'mPr_ClearPrivateInfo','af_pak_clear_animal':'mNpc_ClearAnimalInfo',
}


def startup_extents(base, prior, blob):
    e=prior['equipment_resources'];boot=e['surface_bootstrap']['code']
    start=e['blob_offset']+boot['symbols']['packets']-e['ram']
    code=e['blob_offset']+0x804A8D40-e['ram']
    if (boot['packet_stride']!=16 or boot['packet_count']!=23 or boot['bytes']!=676 or
            sha256(blob[code:code+boot['bytes']])!=boot['sha256']):
        raise ValueError('Changed complete current startup reader')
    rows=[]
    for i in range(boot['packet_count']):
        ram,source,n,crcptr=struct.unpack_from('>4I',blob,start+i*16)
        if source&0x80000000:
            at=source&0x7FFFFFFF;raw=base[at:at+n]
        else:
            at=source-BLOB;raw=blob[at:at+n]
        crc_at=e['blob_offset']+crcptr-e['ram']
        if (not 0x80400000<=ram<ram+n<=0x80800000 or len(raw)!=n or
                zlib.crc32(raw)!=u32(blob,crc_at)):
            raise ValueError('Changed actual installed startup descriptor')
        rows.append(dict(ram=ram,end=ram+n,source=source,bytes=n,sha256=sha256(raw)))
    return rows


def authenticate(base, prior, blob):
    e=prior['equipment_resources']
    if (sha256(base)!=BASE_SHA or prior['runtime_abi']!=391 or e.get('player_travel') or
            prior['save_codec']['format_version']!=21 or
            prior['save_runtime']['state_bytes']!=1264):
        raise ValueError('Player travel requires the pinned current full-storage base')
    checked_models(base,prior)
    pool=prior['furniture']['bank_pool'];disk=e['console_disk']['packet']
    rows=startup_extents(base,prior,blob)
    if (pool['end']!=STATE or pool['guard']+16!=STATE or
            disk['ram']!=0x80630000 or STATE+STATE_BYTES>disk['ram'] or
            any(a<STATE+STATE_BYTES and STATE<b for a,b in reservations(prior)) or
            any(r['ram']<STATE+STATE_BYTES and STATE<r['end'] for r in rows)):
        raise ValueError('Visitor record overlaps a live model/startup/mutable reservation')
    ui=e['diaries']['packets']['ui'];uc=e['diaries']['ui_compiled']
    harvest=e['harvest'];hp=harvest['packet'];hc=harvest['code']
    for p,c,first,last,prefix in ((ui,uc,IO,IO_END,0x47F0),(hp,hc,LIFE,LIFE_END,0x7B50)):
        raw=base[p['physical']:p['physical']+p['bytes']]
        if (sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                c['ram']!=p['ram'] or c['bytes']!=prefix or
                sha256(raw[:prefix])!=c['sha256'] or
                not p['ram']+prefix<=first<last<=p['ram']+p['bytes'] or
                any(raw[first-p['ram']:last-p['ram']]) or
                not any(r['ram']==p['ram'] and r['bytes']==p['bytes'] and
                        r['source']==p['physical']|0x80000000 for r in rows)):
            raise ValueError('Changed authenticated unused loaded code padding')
    # Diary UI's checked linker forbids BSS/data and uses an explicit separate
    # state bank. Harvest includes all BSS and its guard before packet_end.
    if (ui['ram']!=0x806A0000 or ui['bytes']!=0x9000 or
            bytes.fromhex(ui['guard'])!=base[ui['physical']+0x7FF0:ui['physical']+0x8000] or
            e['diaries']['memory']['ui_state']!=dict(ram=0x806A8000,bytes=0x1000) or
            hc['symbols']['af_hr_packet_end']!=LIFE or
            hc['symbols']['af_hr_bss_end']+16!=LIFE or LIFE_END!=0x807FC000):
        raise ValueError('Changed code padding/mutable-state boundary')
    return rows


def compile_connected(prior, output):
    output.mkdir(parents=True,exist_ok=False)
    docker=['docker','run','--rm','--network','none','--user',f'{os.getuid()}:{os.getgid()}',
        '-v',f'{ROOT}:/source:ro','-v',f'{output.resolve()}:/out','-w','/out','--entrypoint']
    def run(tool,*args):
        p=subprocess.run(docker+['/n64_toolchain/bin/mips64-elf-'+tool,IMAGE,*args],
            capture_output=True,text=True,timeout=60)
        if p.returncode:raise ValueError(p.stdout+p.stderr)
        return p.stdout
    inventory=dict((name,int(value,16)) for name,value in re.findall(
        r'^(\w+) = (0x[0-9A-Fa-f]+);',
        (ROOT/'upstream/af/linker_scripts/jp/symbol_addrs_code.txt').read_text(),re.MULTILINE))
    providers=dict(prior['save_codec']['active_storage_code']['symbols'])
    for name,native in NATIVE.items():
        if native not in inventory:raise ValueError('Unmapped native provider: '+native)
        providers[name]=inventory[native]
    quest=prior['equipment_resources']['carried_items']['quest']['npc']['code']['symbols']
    providers.update({n:quest[n] for n in ('af_cw_passport_stage','af_cw_passport_complete')})
    providers['af_diary_native_selected']=prior['equipment_resources']['diaries']['ui_compiled']['symbols']['af_diary_native_selected']
    defined=set();undefined=set();compiled={};objects=[]
    storage_flags=prior['save_codec']['active_storage_code']['flags']
    for part in PARTS:
        flags=storage_flags if part in ('console_storage','travel_context') else list(FLAGS)+['-D'+d+'=1' for d in DEFINES]
        flags=[*flags,f'-DAF_TRAVEL_STATE_RAM=0x{STATE:X}u']
        obj=part+'.o';objects.append(obj)
        run('gcc',*flags,'/source/overlays/v3/'+part+'.c','-o',obj)
        defined.update(line.split()[-1] for line in run('nm','--defined-only','--extern-only',obj).splitlines())
        refs={line.split()[-1] for line in run('nm','--undefined-only',obj).splitlines()}
        undefined.update(refs)
        compiled[part]=dict(flags=flags,sha256=sha256((output/obj).read_bytes()),
            stack_usage=(output/(part+'.su')).read_text(),undefined=sorted(refs))
    external=undefined-defined
    if external-providers.keys():raise ValueError('Unbound connected dependencies: '+str(sorted(external-providers.keys())))
    bindings={n:providers[n] for n in sorted(external)}
    run('ld','-EB','--gc-sections',*[f'--defsym={n}=0x{v:X}' for n,v in bindings.items()],
        *['-u'+n for n in ROOTS],'-T','/source/overlays/v3/travel_link.ld',
        '-Map=travel.map','-o','travel.elf',*objects)
    if run('nm','--undefined-only','travel.elf').strip():raise ValueError('Unresolved connected travel code')
    symbols={f[2]:int(f[0],16) for line in run('nm','--defined-only','travel.elf').splitlines()
        if len(f:=line.split())==3}
    fragments={}
    for name,ram,end in (('io',IO,IO_END),('life',LIFE,LIFE_END)):
        run('objcopy','-O','binary','-j','.'+name,'travel.elf',name+'.bin')
        raw=(output/(name+'.bin')).read_bytes()
        if not raw or len(raw)&15 or ram+len(raw)>end:raise ValueError('Invalid bounded code fragment')
        fragments[name]=dict(ram=ram,bytes=len(raw),capacity=end-ram,sha256=sha256(raw))
    write_new(output/'travel.asm',run('objdump','-d','travel.elf').encode())
    return dict(toolchain=IMAGE,objects=compiled,symbols=symbols,bindings=bindings,fragments=fragments)


def install(base, prior, blob, core, module, output):
    del module
    rows=authenticate(base,prior,blob)
    directory=output/'player_travel'
    compiled=compile_connected(prior,directory)
    e=copy.deepcopy(prior['equipment_resources']);updates={};records=copy.deepcopy(prior['physical_resources'])
    state=bytearray(STATE_BYTES);struct.pack_into('>I',state,0,0x41465431)
    struct.pack_into('>4I',state,16+RECORD_BYTES,*([0xAF54524C]*4))
    row=physical.allocate(base,records,state,'v3-travelling-player',best_fit=True)
    records.append(row)
    packet=dict(row,ram=STATE,crc32=zlib.crc32(state),storage='physical-ROM')
    writes=[];s=compiled['symbols'];hooks=[]
    pairs=((0x8007920C,'af_v3_pak_native_write'),(0x800792FC,'af_v3_pak_native_read'),
        (0x800794E4,'af_v3_pak_native_status'),(0x80079080,'af_v3_travel_passport_clear'),
        (0x800793B8,'af_v3_travel_passport_save'),(0x8007942C,'af_v3_travel_passport_load'),
        (0x800B7F48,'af_v3_travel_private_copy'))
    # The whole source ROM is pinned, including the existing creature adapters.
    for address,name in pairs:
        at=address-CODE_RAM;before=bytes(core[at:at+8]);after=struct.pack('>2I',jump(s[name]),0)
        core[at:at+8]=after;hooks.append(dict(address=address,symbol=name,target=s[name],before=before.hex(),after=after.hex()))
        for retained in e['carried_items']['quest']['npc']['installed_hooks']:
            if retained['address']==address and retained['ram']==CODE_RAM:
                if retained['after']!=before.hex():raise ValueError('Changed retained passport hook receipt')
                retained.update(previous_after=retained['after'],after=after.hex(),target=s[name],
                    current_player_transport=name)
    for name,p in (('life',e['harvest']['packet']),('io',e['diaries']['packets']['ui'])):
        previous=copy.deepcopy(p);before=base[p['physical']:p['physical']+p['bytes']];raw=bytearray(before)
        fragment=compiled['fragments'][name];at=fragment['ram']-p['ram']
        data=bytearray((directory/(name+'.bin')).read_bytes())
        if name=='io':
            for symbol,crc in (('af_travel_harvest_crc',e['harvest']['packet']['crc32']),
                    ('af_travel_record_crc',packet['crc32'])):
                struct.pack_into('>I',data,s[symbol]-fragment['ram'],crc)
            fragment['compiled_sha256']=fragment['sha256'];fragment['sha256']=sha256(data)
            write_new(directory/'io-installed.bin',data)
        raw[at:at+len(data)]=data
        replacement=dict(p,sha256=sha256(raw),crc32=zlib.crc32(raw))
        refresh_aliases(e,previous,replacement);refresh_code(e,before,raw,p['ram'])
        row=next(r for r in records if r['id']==p['id']);row['sha256']=replacement['sha256']
        writes.append((dict(row,previous_sha256=previous['sha256']),bytes(raw)))
    # Existing creature acquisition already calls these exports. Preserve both
    # compiled generations' ABI while moving the state to the complete record.
    source=e['carried_items']['quest']['packet'];previous=copy.deepcopy(source)
    before=base[source['physical']:source['physical']+source['bytes']];raw=bytearray(before)
    target=s['af_v3_travel_creature_collect']
    address=e['carried_items']['quest']['npc']['code']['symbols']['af_v3_creature_visitor_collect']
    at=address-source['ram'];old=bytes(raw[at:at+8]);after=struct.pack('>2I',jump(target),0)
    raw[at:at+8]=after;hooks.append(dict(address=address,symbol='af_v3_creature_visitor_collect',target=target,before=old.hex(),after=after.hex()))
    replacement=dict(source,sha256=sha256(raw),crc32=zlib.crc32(raw))
    refresh_aliases(e,previous,replacement);refresh_code(e,before,raw,source['ram'])
    row=next(r for r in records if r['id']==source['id']);row['sha256']=replacement['sha256']
    writes.append((dict(row,previous_sha256=previous['sha256']),bytes(raw)))
    # The older fish-world ABI also remains addressable by retained callers.
    fish=e['creature_fish']['world']['packet'];at=fish['blob_offset']+0x806558DC-fish['ram']
    raw_before=bytes(blob[fish['blob_offset']:fish['blob_offset']+fish['bytes']])
    old=bytes(blob[at:at+8]);blob[at:at+8]=after
    raw_after=bytes(blob[fish['blob_offset']:fish['blob_offset']+fish['bytes']])
    if sha256(raw_before)!=fish['sha256']:raise ValueError('Changed retained fish-world provider')
    refresh_code(e,raw_before,raw_after,fish['ram'])
    fish.update(sha256=sha256(raw_after),crc32=zlib.crc32(raw_after))
    hooks.append(dict(address=0x806558DC,symbol='retained_creature_visitor_collect',target=target,before=old.hex(),after=after.hex()))
    writes.append((next(r for r in records if r['id']==packet['id']),bytes(state)))
    report=dict(format='AFV3-PLAYER-TRAVEL-INSTALLED-1',installed=True,
        state_packet=packet,record_bytes=RECORD_BYTES,compiled=compiled,hooks=hooks,
        checked_previous_startup=rows,shared_workspace_bytes=119932,
        source_rom_sha256=BASE_SHA,source_ram_requirement=0x800000,
        native_private_bytes=0xBD0,native_passport_bytes=0x1200,native_backup_bytes=0x6700,
        passport_binding='AFV3-PASSPORT-PLAYER-1',journal_version=1,player_record_version=1,
        saved_format_changed=False,original_pak_notes_retained=True,
        startup_descriptor_growth=1,native_execution_verified=False,ordinary_visiting_verified=False,
        pending=['visitor item/paper consumers','visitor diary interaction','visitor console sessions',
            'native execution and actual card path verification'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    e['player_travel']=report;updates['physical_resources']=records
    write_new(directory/'state.bin',state)
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return e,{},updates,writes
