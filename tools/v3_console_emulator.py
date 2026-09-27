"""Bind shared full-image iNES lifecycle to the checked native emulator."""
import copy
import struct
import zlib
from types import SimpleNamespace
from aflib import by_vrom,sha256,u32,CODE_VROM,CODE_RAM
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT,compile_part
from v3_console_games import NATIVE_VROM as VROM,NATIVE_RAM as RAM,NATIVE_SHA
from v3_console_image_native import RAM as CODE,SIZE,METADATA
from v3_import_storage import jump

RELOC=0x771900
RELOC_SHA='cea080ec680a8d63793812acae8c6c620a0c007828914e363b27296a0f1c3659'
CODE_BYTES=0x804FB000-CODE
ARENA_HOOK=(0x8082A88C,'af_v3_console_arena_allocate','0c0345f5afa60020')
HOOKS=(
    (0x8082E0D8,'af_v3_console_graphics','0c20aa0534845008'),
    (0x8082E0F4,'af_v3_console_setup','0c20b4a7ac224a14'),
    (0x8082E338,'af_v3_console_initialize','0c20a9bb8c844a08'),
    (0x8082DC68,'af_v3_console_frame_native','0c20a91b27a400ec'),
    (0x8082DF04,'af_v3_console_reset_native','0c20a99200000000'),
    (0x8082E490,'af_v3_console_close_native','0c20a84300000000'))
CPU_FRAME_HOOK=(0x8082A554,'af_v3_console_cpu_frame','0c20bc27ae1942d8')
SOURCES=('tools/v3_console_emulator.py','overlays/v3/console_emulator.c','overlays/v3/console_emulator.ld',
    'tools/v3_furniture_install.py','tools/v3_asset_loader.py','tools/v3_room_goods.py',
    'overlays/v3/console_image_native.c','overlays/v3/console_image.c','overlays/v3/console_image.h',
    'overlays/v3/console_save.c','overlays/v3/console_save.h')


def patch(native,relocation,symbols,*,disk_symbols=None):
    if sha256(native)!=NATIVE_SHA or sha256(relocation)!=RELOC_SHA:
        raise ValueError('Changed complete native console emulator or relocations')
    sections=struct.unpack_from('>5I',relocation)
    if sections!=(0xBD30,0x1C4F0,0x400,0x6370,2853):raise ValueError('Changed native emulator dimensions')
    data=bytearray(native);changed=set();hooks=[]
    # Earlier immutable builds have the six lifecycle symbols only. Recreate
    # their exact patch before accepting a refresh; never unpatch guessed bytes.
    session_hooks=disk_symbols is not None and 'af_v3_console_extent' in disk_symbols
    calls=HOOKS+((ARENA_HOOK,) if ARENA_HOOK[1] in symbols else ())
    if session_hooks:calls+=(CPU_FRAME_HOOK,)
    for address,name,expected in calls:
        at=address-RAM;before=bytes.fromhex(expected)
        target=(disk_symbols if session_hooks else symbols)[name]
        low,high=(0x80630000,0x80636000) if session_hooks else (CODE,CODE+METADATA)
        if data[at:at+8]!=before or not low<=target<high or target&3:
            raise ValueError('Changed complete console call: '+name)
        data[at:at+4]=struct.pack('>I',jump(target,link=True));changed.add(at)
        hooks.append(dict(address=address,symbol=name,target=target,before=expected,after=data[at:at+8].hex()))
    # The disk audio module replaces only the DPCM byte fetch, preserving the
    # existing synthesizer and all other live audio registers. This is optional
    # so installed cartridge-only revisions can still be reproduced exactly.
    dpcm_relocs={}
    if session_hooks:
        address=0x8082E194;at=address-RAM;name='af_v3_console_extent';target=disk_symbols[name]
        expected='904e0005905800043c038085000e7b400018cb8001f94821252a001024634b74ac6a0000004a60213c018085ac2c4b7c'
        if data[at:at+48]!=bytes.fromhex(expected) or not 0x80630000<=target<0x80636000 or target&3:
            raise ValueError('Changed complete native image extent reader')
        data[at:at+48]=struct.pack('>II',0x00402025,jump(target,link=True))+bytes(40)
        changed.update(range(at,at+48,4))
        dpcm_relocs.update({at+8:5,at+28:6,at+40:5,at+44:6})
        hooks.append(dict(address=address+4,range_address=address,symbol=name,target=target,
            before=expected,after=data[at:at+48].hex()))
    if disk_symbols is not None:
        name='af_v3_qd_dpcm_bridge';target=disk_symbols[name];address=0x80833DBC
        at=address-RAM
        expected='3c0a80838d4a7bc094c90018012a582101646021918d0000a0cd001c'
        if data[at:at+28]!=bytes.fromhex(expected) or not 0x80630000<=target<0x80636000 or target&3:
            raise ValueError('Changed native DPCM fetch or disk bridge')
        data[at:at+28]=struct.pack('>I',jump(target))+bytes(24)
        changed.update(range(at,at+28,4));dpcm_relocs.update({at:5,at+4:6})
        hooks.append(dict(address=address,symbol=name,target=target,before=expected,
            after=data[at:at+28].hex(),link=False))
    retained=[];removed=[]
    for word in struct.unpack_from('>'+str(sections[4])+'I',relocation,20):
        section,kind,offset=word>>30,word>>24&63,word&0xFFFFFF
        at=sum(sections[:section-1])+offset
        if at in changed:
            if section!=1 or kind!=dpcm_relocs.get(at,4):raise ValueError('Unexpected replaced console relocation')
            removed.append(word)
        else:retained.append(word)
    expected_removed=[a-RAM for a,_,_ in HOOKS]+list(dpcm_relocs)
    if session_hooks:expected_removed.append(CPU_FRAME_HOOK[0]-RAM)
    if sorted(w&0xFFFFFF for w in removed)!=sorted(expected_removed):
        raise ValueError('Missing console call relocations or unexpected core-call relocation')
    reloc=bytearray(relocation);struct.pack_into('>I',reloc,16,len(retained))
    reloc[20:-4]=struct.pack('>'+str(len(retained))+'I',*retained)+bytes(len(reloc)-24-len(retained)*4)
    spec=SimpleNamespace(ram=RAM,resident_bytes=len(native)+sections[3],sections=sections)
    new_spec=SimpleNamespace(ram=RAM,resident_bytes=spec.resident_bytes,sections=(*sections[:4],len(retained)))
    for base in (0x801A0010,0x802F0010):
        before=relocate_verified_data(spec,native,relocation,base)
        after=relocate_verified_data(new_spec,data,reloc,base)
        if any(a!=b and at//4*4 not in changed for at,(a,b) in enumerate(zip(before,after,strict=True))):
            raise ValueError('Console hooks change unrelated relocated code/data')
        for h in hooks:
            if u32(after,h['address']-RAM)!=jump(h['target'],link=h.get('link',True)):
                raise ValueError('Console hook incorrectly receives native relocation')
    return bytes(data),bytes(reloc),dict(hooks=hooks,removed_relocations=removed,
        sha256=sha256(data),relocation_sha256=sha256(reloc),caller_delay_slots_retained=True)


def install(base,prior,blob,output,original):
    equipment=copy.deepcopy(prior['equipment_resources']);images=equipment['console_images']
    disk=equipment.get('console_disk')
    packet=images['packet'];at=packet['blob_offset'];old=bytes(blob[at:at+SIZE])
    if packet['ram']!=CODE or packet['bytes']!=SIZE or sha256(old)!=packet['sha256']:
        raise ValueError('Changed complete console reader packet')
    previous=images.get('emulator');files=by_vrom(base);original_files=by_vrom(original)
    native=original_files[VROM].extract(original);relocation=original_files[RELOC].extract(original)
    if previous:
        previous_disk=(disk['compiled']['symbols'] if disk and disk.get('session_hooks_installed') else None)
        expected_owner,expected_reloc,expected_binding=patch(native,relocation,images['compiled']['symbols'],
            disk_symbols=previous_disk)
        if (files[VROM].extract(base)!=expected_owner or files[RELOC].extract(base)!=expected_reloc or
                previous['native']!=expected_binding or
                sha256(old[:images['compiled']['bytes']])!=images['compiled']['sha256']):
            raise ValueError('Changed installed console lifecycle before refresh')
    elif files[VROM].extract(base)!=native or files[RELOC].extract(base)!=relocation:
        raise ValueError('Changed original console lifecycle before installation')
    from v3_console_room import checked_runtime
    checked_runtime(equipment,blob,base)
    core=files[CODE_VROM].extract(base);original_core=original_files[CODE_VROM].extract(original)
    arena_at=0x800D17D4-CODE_RAM
    if core[arena_at:arena_at+32]!=original_core[arena_at:arena_at+32]:
        raise ValueError('Changed complete native arena allocator')
    session_ram=CODE+SIZE
    if session_ram+0x800>prior['furniture']['bank_pool']['start']:
        raise ValueError('Console session overlaps complete model banks')
    storage=equipment['console_storage']['compiled']['symbols']
    symbols=images['compiled'];flags=[x[2:] for x in symbols['flags'] if x.startswith('-D') and
        not x.startswith(('-DAF_CONSOLE_SAVED_PLAYERS=','-DAF_CONSOLE_STORAGE_VALID='))]
    flags.extend((f'AF_CONSOLE_SAVED_PLAYERS=0x{storage["af_v3_console_player_data"]:X}u',
                  f'AF_CONSOLE_STORAGE_VALID=0x{storage["af_v3_console_storage_valid"]:X}u'))
    if disk:
        from v3_console_disk_install import RAM as DISK_RAM,END,LAYOUT
        from v3_console_disk import BIOS_SHA,BOOT_STATE_SHA,NATIVE_SOURCES
        p=disk['packet'];start=p['blob_offset'];raw=bytes(blob[start:start+p['bytes']])
        if (p['ram']!=DISK_RAM or p['bytes']!=END-DISK_RAM or disk['layout']!=LAYOUT or
                sha256(raw)!=p['sha256'] or zlib.crc32(raw)!=p['crc32'] or
                sha256(raw[0x6000:0x8000])!=BIOS_SHA or sha256(raw[0x14000:0x16000])!=BIOS_SHA or
                sha256(raw[0x8200:0x8304])!=BOOT_STATE_SHA or any(raw[0x8000:0x8200]) or
                any(raw[0xA000:0x14000]) or raw[-16:]!=bytes.fromhex('51444721')*4):
            raise ValueError('Changed complete installed disk packet before session integration')
        shared={'VALIDATE':'af_v3_console_validate','LOAD':'af_v3_console_image_native_load',
            'OPEN':'af_v3_console_open_loaded','FRAME':'af_v3_console_frame','CLOSE':'af_v3_console_close'}
        flags+=['AF_CONSOLE_DISK=1']+[f'AF_SHARED_{key}=0x{symbols["symbols"][name]:X}u' for key,name in shared.items()]
        code,compiled=compile_part('console_disk_native',output/'console_disk_session',defines=tuple(flags),
            extra_sources=('overlays/v3/console_disk.c','overlays/v3/console_disk_bridge.S','overlays/v3/console_emulator.c'))
        if len(code)>0x6000:raise ValueError('Complete disk session exceeds its code reservation')
        updated=code.ljust(0x6000,b'\0')+raw[0x6000:];blob[start:start+len(updated)]=updated
        p.update(sha256=sha256(updated),crc32=zlib.crc32(updated))
        owner,reloc,binding=patch(native,relocation,symbols['symbols'],disk_symbols=compiled['symbols'])
        disk.update(compiled=compiled,session_hooks_installed=True,choice_eligible=False,
            shared_calls={name:symbols['symbols'][name] for name in shared.values()},
            pending=['native disk gameplay and return verification','complete furniture profile and acquisition'],
            sources={s:sha256((ROOT/s).read_bytes()) for s in dict.fromkeys((*disk['sources'],*NATIVE_SOURCES,*SOURCES))})
        images['emulator'].update(native=binding,qd_engine_installed=True,native_gameplay_tested=False,
            disk_lifecycle_ram=DISK_RAM,sources={s:sha256((ROOT/s).read_bytes()) for s in SOURCES})
        # The caller installs these newly generated owners after this returns.
        # The old owners were verified above; validate the updated packet here.
        checked_runtime(equipment,blob)
        return equipment,{VROM:owner,RELOC:reloc}
    code,compiled=compile_part('console_emulator',output/'console_emulator',
        primary_source='overlays/v3/console_image_native.c',defines=tuple(flags),
        extra_sources=('overlays/v3/console_image.c','overlays/v3/console_save.c','overlays/v3/console_emulator.c'))
    if len(code)>CODE_BYTES:raise ValueError('Console lifecycle exceeds code reservation')
    new=code.ljust(CODE_BYTES,b'\0')+old[CODE_BYTES:];blob[at:at+SIZE]=new
    owner,reloc,binding=patch(native,relocation,compiled['symbols'])
    images['compiled']=compiled;packet.update(sha256=sha256(new),crc32=zlib.crc32(new))
    images['emulator']=dict(format='AFV3-CONSOLE-EMULATOR-1',native=binding,
        state=dict(ram=session_ram,bytes=0x800,saved=False),
        original_game_data_and_scores_unchanged=True,maximum_graphics_bytes=0x42008,
        additional_reset_backup_bytes=8192,save_format_changed=False,
        arena_capacity_checked=True,native_arena_sha256=sha256(core[arena_at:arena_at+32]),
        installed=True,native_gameplay_tested=False,
        room_launch_installed=bool(images.get('room')),qd_engine_installed=False,
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    images['launch_installed']=bool(images.get('room'))
    checked_runtime(equipment,blob,base)
    return equipment,{VROM:owner,RELOC:reloc}
