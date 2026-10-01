"""Install full player-note framing and native arrival/return without growing native buffers.

Code uses authenticated unused padding in two already-loaded packets. One new
startup packet owns the complete visiting player's record; resident save formats
and the model pool remain unchanged. All shared item/paper ownership consumers
use the complete visitor record; diary UI and console sessions follow this step.
"""
import copy
import json
import os
import re
import struct
import subprocess
import zlib

from aflib import CODE_RAM, CODE_VROM, by_vrom, sha256, u32
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
       'travel_native','travel_player','travel_context','collection','surface_save',
       'held_collection','carried_collection','diary_items','diary','diary_menu',
       'diary_native','diary_screen','diary_events','holiday_diary')
CONSUMERS=('af_v3_catalogue_record','af_v3_catalogue_owned',
    'af_v3_surface_record','af_v3_surface_owned',
    'af_v3_held_catalogue_record','af_v3_held_catalogue_owned',
    'af_carried_record','af_carried_owned','af_diary_item_record','af_diary_item_owned')
DIARY_CORE=('af_diary_page','af_diary_begin','af_diary_lock')
DIARY_MENU=('af_diary_menu_open','af_diary_menu_input','af_diary_menu_edit','af_diary_menu_grid')
DIARY_UI=('af_diary_native_open','af_diary_screen_open','af_diary_events_draw')
ROOTS=('af_v3_pak_native_read','af_v3_pak_native_write','af_v3_pak_native_status',
       'af_v3_travel_passport_clear','af_v3_travel_passport_save',
       'af_v3_travel_passport_load','af_v3_travel_private_copy',
       'af_v3_travel_visitor_collect','af_v3_travel_visitor_paper',
       'af_v3_travel_creature_collect',*CONSUMERS,*DIARY_CORE,*DIARY_MENU,*DIARY_UI,
       'af_holiday_diary_draw')
SOURCES=tuple(dict.fromkeys((*PLAYER_SOURCES,'tools/v3_player_travel_install.py',
    'tools/v3_room_goods.py','tools/v3_furniture_install.py','overlays/v3/surface_bootstrap.c',
    'overlays/v3/travel_link.ld','overlays/v3/travel_native.c','overlays/v3/travel_native.h',
    'overlays/v3/travel_context.c','tests/v3_travel_native_test.c',
    'overlays/v3/travel_collection.h',*[f'overlays/v3/{p}.c' for p in PARTS],
    'overlays/v3/diary_menu.h','overlays/v3/diary_native.h','overlays/v3/diary_screen.h',
    'overlays/v3/diary_events.h','overlays/v3/diary_draw.h','overlays/v3/holiday_calendar.h',
    'tests/test_v3_diary_native.py','tests/v3_diary_native_test.c')))
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
    owners=(prior['collection']['code'],prior['room_surfaces']['save']['helpers'],
        prior['equipment_resources']['collection']['code'],
        prior['equipment_resources']['diary_items']['code'],
        prior['equipment_resources']['diaries']['compiled'],
        prior['equipment_resources']['diaries']['ui_compiled'],
        prior['equipment_resources']['holiday_state']['code'],
        prior['equipment_resources']['npc_extra']['events']['calendar']['code'])
    for owner in owners:
        providers.update(owner.get('link_symbols',{}));providers.update(owner.get('bindings',{}))
        providers.update(owner['symbols'])
    providers.update(prior['save_codec']['code']['symbols'])
    providers['af_v3_require_save_state']=prior['save_runtime']['diary_runtime_code']['symbols']['af_v3_require_save_state']
    providers['af_v3_save_halt']=prior['save_runtime']['diary_runtime_code']['symbols']['af_v3_save_halt']
    defined=set();undefined=set();compiled={};objects=[]
    storage_flags=prior['save_codec']['active_storage_code']['flags']
    for part in PARTS:
        flags=storage_flags if part in ('console_storage','travel_context') else list(FLAGS)+['-D'+d+'=1' for d in DEFINES]
        flags=[*flags,f'-DAF_TRAVEL_STATE_RAM=0x{STATE:X}u','-DAF_V3_PLAYER_TRAVEL=1']
        if part=='diary_native':flags.append('-DAF_DIARY_HOLIDAYS=1')
        obj=part+'.o';objects.append(obj)
        run('gcc',*flags,'/source/overlays/v3/'+part+'.c','-o',obj)
        # Reuse authenticated unchanged editors and date builders. Localising
        # their duplicate definitions lets other objects bind the existing
        # exports, and section collection discards the uncalled copies. This
        # does not override locally defined changed readers or save ownership.
        reused={'diary':('af_diary_command','af_diary_scroll','af_diary_commit_locked'),
            'diary_events':('af_diary_events_month',),
            'holiday_diary':('af_holiday_diary_month','af_holiday_diary_dates')}.get(part,())
        if reused:run('objcopy',*['--localize-symbol='+n for n in reused],obj)
        defined.update(line.split()[-1] for line in run('nm','--defined-only','--extern-only',obj).splitlines())
        refs={line.split()[-1] for line in run('nm','--undefined-only',obj).splitlines()}
        undefined.update(refs)
        compiled[part]=dict(flags=flags,sha256=sha256((output/obj).read_bytes()),
            stack_usage=(output/(part+'.su')).read_text(),undefined=sorted(refs),
            reused_existing_exports=list(reused))
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


def connect_consumers(base,prior,live,blob,rows,writes,compiled,hooks,records):
    """Replace public ownership entries, retaining callers and native aliases.

    Authenticate each complete current owner before patching. Physical changes
    merge with staged creature redirects; blob owners retain their load mapping.
    """
    e=live['equipment_resources'];old_e=prior['equipment_resources']
    owners=(('collection/code',0x804699C0,CONSUMERS[0:2]),
        ('room_surfaces/save/helpers',0x804BC900,CONSUMERS[2:4]),
        ('equipment_resources/collection/code',0x804AFA00,CONSUMERS[4:6]),
        ('save_codec/active_storage_code',prior['save_codec']['active_storage_code']['ram'],CONSUMERS[6:8]),
        ('equipment_resources/diary_items/code',0x806E0000,CONSUMERS[8:10]),
        ('equipment_resources/holiday_state/code',0x806F4000,DIARY_CORE),
        ('equipment_resources/diaries/compiled',prior['equipment_resources']['diaries']['compiled']['ram'],(*DIARY_CORE,*DIARY_MENU)),
        ('equipment_resources/diaries/ui_compiled',0x806A0000,DIARY_UI),
        ('equipment_resources/npc_extra/events/calendar/code',
            prior['equipment_resources']['npc_extra']['events']['calendar']['ram'],
            ('af_holiday_diary_draw','af_diary_native_open')))
    def node(report,path):
        for key in path.split('/'):report=report[key]
        return report
    staged={p['physical']:(p,bytearray(raw)) for p,raw in writes}
    initial=((0x80460000,0xC000,0),(old_e['ram'],old_e['bytes'],old_e['blob_offset']))
    for path,ram,names in owners:
        old=node(prior,path);owner=node(live,path);n=old['bytes']
        packet=next((r for r in rows if r['ram']<=ram and ram+n<=r['end']),None)
        if packet and packet['source']&0x80000000:
            physical_at=packet['source']&0x7FFFFFFF;offset=ram-packet['ram']
            before=base[physical_at:physical_at+packet['bytes']]
            if physical_at in staged:p,raw=staged[physical_at]
            else:
                row=next(r for r in records if r['physical']==physical_at)
                p=dict(row,previous_sha256=row['sha256'])
                raw=bytearray(before)
        else:
            if packet:
                start=packet['source']-BLOB;packet_ram=packet['ram'];size=packet['bytes']
            else:
                packet_ram,size,start=next((a,n,b) for a,n,b in initial if a<=ram<ram+old['bytes']<=a+n)
            offset=ram-packet_ram;before=bytes(blob[start:start+size]);raw=bytearray(before)
        preceding=bytes(raw)
        authenticated=bytearray(before[offset:offset+n])
        bridges={}
        if path=='collection/code':
            # Public native entries now dispatch through paper/diary/surface/
            # display handlers. Replace only the retained innermost bridges,
            # never bypass that chain. Reconstruct their copied prologues to
            # authenticate the original complete inner collection body.
            for name,h in zip(names,prior['clothing']['display']['readers']['collection_hooks']):
                entry=old['symbols'][name];at=entry-ram
                bridge=h['bridge']-packet_ram
                if (h['entry']!=entry or raw[offset+at:offset+at+8].hex()!=h['after'] or
                        raw[bridge:bridge+16].hex()!=h['bridge_bytes']):
                    raise ValueError('Changed retained inner collection bridge')
                authenticated[at:at+8]=bytes.fromhex(h['before'])
                bridges[name]=h['bridge']
        if sha256(authenticated)!=old['sha256']:
            raise ValueError('Changed complete collection owner: '+path)
        for name in names:
            address=bridges.get(name,old['symbols'][name]);at=offset+address-ram
            if not 0<=at<at+8<=len(raw):raise ValueError('Collection entry outside loaded packet')
            previous=bytes(raw[at:at+8]);after=struct.pack('>2I',jump(compiled['symbols'][name]),0)
            raw[at:at+8]=after
            def refresh_redirect(value):
                if isinstance(value,dict):
                    if value.get('address')==address and value.get('after')==previous.hex():
                        value.update(previous_after=value['after'],after=after.hex(),
                            target=compiled['symbols'][name],current_visitor_reader=name)
                    for child in value.values():refresh_redirect(child)
                elif isinstance(value,list):
                    for child in value:refresh_redirect(child)
            refresh_redirect(live)
            hooks.append(dict(address=address,symbol=name,target=compiled['symbols'][name],
                before=previous.hex(),after=after.hex(),owner=path,
                storage='physical-ROM' if packet and packet['source']&0x80000000 else 'blob',
                packet_ram=packet['ram'] if packet else packet_ram,
                packet_source=packet['source'] if packet else BLOB+start))
        if packet and packet['source']&0x80000000:
            refresh_code(live,preceding,raw,packet['ram'])
            previous=dict(p);replacement=dict(p,sha256=sha256(raw),crc32=zlib.crc32(raw))
            refresh_aliases(live,previous,replacement);p.update(replacement)
            next(r for r in records if r['physical']==physical_at)['sha256']=replacement['sha256']
            staged[physical_at]=(p,raw)
        else:
            refresh_code(live,before,raw,packet_ram)
            blob[start:start+len(raw)]=raw
            if packet:
                def refresh_packet(value):
                    if isinstance(value,dict):
                        if value.get('ram')==packet_ram and value.get('blob_offset')==start and value.get('bytes')==len(raw):
                            value.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
                        for child in value.values():refresh_packet(child)
                    elif isinstance(value,list):
                        for child in value:refresh_packet(child)
                refresh_packet(live)
        # Older compile receipts omit RAM. Refresh their complete authenticated
        # code digest explicitly without changing public symbols or providers.
        if path!='collection/code':
            owner.setdefault('compiled_sha256',old['sha256'])
            owner['sha256']=sha256(raw[offset:offset+n])
    live['collection']['foreign_import_collection']='complete identity-bound visitor ownership'
    writes[:]=[(p,bytes(raw)) for p,raw in staged.values()]


def install(base, prior, blob, core, module, output):
    del module
    rows=authenticate(base,prior,blob)
    directory=output/'player_travel'
    compiled=compile_connected(prior,directory)
    live=copy.deepcopy(prior);e=live['equipment_resources'];updates={};records=copy.deepcopy(prior['physical_resources'])
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
    connect_consumers(base,prior,live,blob,rows,writes,compiled,hooks,records)
    menu_changes,virtual_moves=connect_native_dma(base,live,core)
    updates['native_dma_virtual_moves']=virtual_moves
    # Code entry uses the same installed keyboard. Its current resource aliases
    # must follow the move; recipe verification must not look up retired VROMs.
    editor=copy.deepcopy(prior['password_editor'])
    destinations={r['old_vrom']:r['vrom'] for r in virtual_moves}
    for key in ('vrom','reloc'):editor[key]=destinations[editor[key]]
    for owner in editor['owner_resizes']:owner['vrom']=destinations[owner['vrom']]
    updates['password_editor']=editor
    for key in ('collection','room_surfaces','save_codec','clothing','catalogue','shop_floor','shop_actors'):
        if live[key]!=prior[key]:updates[key]=live[key]
    report=dict(format='AFV3-PLAYER-TRAVEL-INSTALLED-1',installed=True,
        state_packet=packet,record_bytes=RECORD_BYTES,compiled=compiled,hooks=hooks,
        checked_previous_startup=rows,shared_workspace_bytes=119932,
        source_rom_sha256=BASE_SHA,source_ram_requirement=0x800000,
        native_private_bytes=0xBD0,native_passport_bytes=0x1200,native_backup_bytes=0x6700,
        passport_binding='AFV3-PASSPORT-PLAYER-1',journal_version=1,player_record_version=1,
        saved_format_changed=False,original_pak_notes_retained=True,
        startup_descriptor_growth=1,native_execution_verified=False,ordinary_visiting_verified=False,
        collection_consumers_connected=True,
        visitor_diary_reading_connected=True,
        diary_menu_virtual_moves=virtual_moves[:4],
        native_dma_virtual_moves=virtual_moves,
        pending=['visitor console sessions',
            'native execution and actual card path verification'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    e['player_travel']=report;updates['physical_resources']=records
    write_new(directory/'state.bin',state)
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    return e,menu_changes,updates,writes


def connect_native_dma(base,live,core):
    """Keep installed menu/actor loads inside the original DMA request limit.

    The existing relocated menu/relocation pairs occupy synthetic addresses
    beyond that limit. Move their directory identities and owner descriptors
    into a checked empty virtual gap; retain every physical byte and the native
    loader's validation. These are code addresses, not item/player identities.
    """
    e=live['equipment_resources'];files=by_vrom(base);parent=0x7749C0
    owner=bytearray(files[parent].extract(base));moves=[]
    def move_pair(originals,targets):
        if files[originals[1]].index!=files[originals[0]].index+1:
            raise ValueError('Native relocation loses adjacent directory index')
        for original,target in zip(originals,targets,strict=True):
            entry=files[original]
            if (entry.pend or target&15 or target+entry.size>0x03000000 or
                    any(f.vstart<target+entry.size and target<f.vend for f in files.values()) or
                    any(r['vrom']<target+entry.size and target<r['vrom']+r['bytes'] for r in moves)):
                raise ValueError('Native virtual destination overlaps a live resource')
            moves.append(dict(old_vrom=original,vrom=target,bytes=entry.size,
                previous_bytes=entry.size,directory_index=entry.index,
                physical=entry.pstart,physical_end=entry.pend,
                sha256=sha256(entry.extract(base))))
    def descriptor(data,at,original,target,ram):
        before=list(struct.unpack_from('>4I',data,at))
        if before!=(expected:=[original,original+files[original].size,ram,ram+files[original].size]):
            raise ValueError('Changed complete native DMA descriptor: '+str(expected))
        after=[target,target+files[original].size,*before[2:]]
        struct.pack_into('>4I',data,at,*after)
        return before,after
    for index,name in enumerate(('hboard','keyboard')):
        receipt=e['diaries']['hooks']['menus'][name]
        before=receipt['owner_after'];at=receipt['owner_at']
        if list(struct.unpack_from('>7I',owner,at))!=before:
            raise ValueError('Changed native diary menu descriptor')
        new_pair=(0x02E10000+index*0x20000,0x02E20000+index*0x20000)
        old_pair=(receipt['target_vrom'],receipt['target_reloc'])
        move_pair(old_pair,new_pair)
        after=[*before];after[:2]=[new_pair[0],new_pair[0]+files[old_pair[0]].size]
        struct.pack_into('>7I',owner,at,*after)
        receipt.update(previous_target_vrom=old_pair[0],previous_target_reloc=old_pair[1],
            target_vrom=new_pair[0],target_reloc=new_pair[1],owner_after=after)
    # These retained native shop consumers were appended for item imports.
    # Only their DMA identities/descriptors change; their code and behaviour do
    # not. Use current owner hashes, including subsequent Nook-code repairs.
    shop_rows=e['carried_items']['paper']['quantities']['native_consumers']
    for row in shop_rows:
        if not row['name'].startswith('shop-'):continue
        old_pair=(row['installed_vrom'],row['installed_reloc'])
        new_pair=tuple(0x02E50000+v-0x04640000 for v in old_pair)
        alias=live['shop_floor'] if row['name']=='shop-floor' else live['shop_actors']['owners'][row['name'][5:]]
        if (alias['vrom']!=old_pair[0] or alias['reloc']!=old_pair[1] or
                sha256(files[old_pair[0]].extract(base))!=alias['output_sha256'] or
                sha256(files[old_pair[1]].extract(base))!=alias['relocation_sha256']):
            raise ValueError('Changed current native shop resource')
        move_pair(old_pair,new_pair)
        descriptor(core,row['descriptor']-CODE_RAM,old_pair[0],new_pair[0],row['ram'])
        row.update(installed_vrom=new_pair[0],installed_reloc=new_pair[1])
        alias.update(vrom=new_pair[0],reloc=new_pair[1])
        if 'nook_code_entry' in alias:alias['nook_code_entry']['installed_reloc_vrom']=new_pair[1]
    # Preserve the already-installed native menu/actor adapters without adding
    # or finishing their unrelated features. They use the same bounded loader.
    bank=e['bank'];plan=bank['resources']
    for index,pair in enumerate(plan['pairs']):
        old_pair=(pair['target_vrom'],pair['target_relocation_vrom'])
        new_pair=tuple(0x02E50000+v-0x04640000 for v in old_pair)
        if (sha256(files[old_pair[0]].extract(base))!=pair['sha256'] or
                sha256(files[old_pair[1]].extract(base))!=pair['relocation_sha256']):
            raise ValueError('Changed retained native menu/actor resource')
        move_pair(old_pair,new_pair)
        receipt=plan['submenu_descriptor'] if index==0 else plan['pelly_descriptor']
        data,at=(owner,receipt['offset']) if index==0 else (core,receipt['address']-CODE_RAM)
        if data[at:at+32].hex()!=receipt['after']:
            raise ValueError('Changed retained native menu/actor descriptor')
        descriptor(data,at,old_pair[0],new_pair[0],pair['ram'])
        receipt['after']=data[at:at+32].hex()
        pair.update(target_vrom=new_pair[0],target_relocation_vrom=new_pair[1])
        if index==0:bank['menu_allocation']['after']=receipt['after']
    # Current Nook descriptors and relocation readers follow their actual
    # resources. Keep historical before/previous receipts untouched.
    destinations={r['old_vrom']:r['vrom'] for r in moves}
    nook=e['passwords']['nook']['native']
    for row in nook['descriptors']:
        old=row['after'][0];target=destinations[old]
        row['after'][:2]=[target,target+row['after'][1]-old]
    for row in nook['owners'].values():
        row['installed_reloc_vrom']=destinations[row['installed_reloc_vrom']]
    known={r['old_vrom'] for r in moves}
    if any(0x04600000<=v<0x04800000 and v not in known for v in files):
        raise ValueError('Unmapped native resource beyond original DMA limit')
    # The icon receipt retains its own installation generation. Record this
    # current complete parent separately rather than rewriting that history.
    e['diaries']['native_menu_owner_sha256']=sha256(owner)
    plan['submenu_descriptor']['owner_sha256']=sha256(owner)
    return {parent:bytes(owner)},moves
