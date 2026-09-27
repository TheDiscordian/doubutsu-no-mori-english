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
SOURCES=('tools/v3_console_emulator.py','overlays/v3/console_emulator.c','overlays/v3/console_emulator.ld',
    'tools/v3_furniture_install.py','tools/v3_asset_loader.py','tools/v3_room_goods.py',
    'overlays/v3/console_image_native.c','overlays/v3/console_image.c','overlays/v3/console_image.h',
    'overlays/v3/console_save.c','overlays/v3/console_save.h')


def patch(native,relocation,symbols):
    if sha256(native)!=NATIVE_SHA or sha256(relocation)!=RELOC_SHA:
        raise ValueError('Changed complete native console emulator or relocations')
    sections=struct.unpack_from('>5I',relocation)
    if sections!=(0xBD30,0x1C4F0,0x400,0x6370,2853):raise ValueError('Changed native emulator dimensions')
    data=bytearray(native);changed=set();hooks=[]
    # Earlier immutable builds have the six lifecycle symbols only. Recreate
    # their exact patch before accepting a refresh; never unpatch guessed bytes.
    calls=HOOKS+((ARENA_HOOK,) if ARENA_HOOK[1] in symbols else ())
    for address,name,expected in calls:
        at=address-RAM;before=bytes.fromhex(expected);target=symbols[name]
        if data[at:at+8]!=before or not CODE<=target<CODE+METADATA or target&3:
            raise ValueError('Changed complete console call: '+name)
        data[at:at+4]=struct.pack('>I',jump(target,link=True));changed.add(at)
        hooks.append(dict(address=address,symbol=name,target=target,before=expected,after=data[at:at+8].hex()))
    retained=[];removed=[]
    for word in struct.unpack_from('>'+str(sections[4])+'I',relocation,20):
        section,kind,offset=word>>30,word>>24&63,word&0xFFFFFF
        at=sum(sections[:section-1])+offset
        if at in changed:
            if section!=1 or kind!=4:raise ValueError('Unexpected replaced console relocation')
            removed.append(word)
        else:retained.append(word)
    if sorted(w&0xFFFFFF for w in removed)!=sorted(a-RAM for a,_,_ in HOOKS):
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
            if u32(after,h['address']-RAM)!=jump(h['target'],link=True):
                raise ValueError('Console hook incorrectly receives native relocation')
    return bytes(data),bytes(reloc),dict(hooks=hooks,removed_relocations=removed,
        sha256=sha256(data),relocation_sha256=sha256(reloc),caller_delay_slots_retained=True)


def install(base,prior,blob,output,original):
    equipment=copy.deepcopy(prior['equipment_resources']);images=equipment['console_images']
    packet=images['packet'];at=packet['blob_offset'];old=bytes(blob[at:at+SIZE])
    if packet['ram']!=CODE or packet['bytes']!=SIZE or sha256(old)!=packet['sha256']:
        raise ValueError('Changed complete console reader packet')
    previous=images.get('emulator');files=by_vrom(base);original_files=by_vrom(original)
    native=original_files[VROM].extract(original);relocation=original_files[RELOC].extract(original)
    if previous:
        expected_owner,expected_reloc,expected_binding=patch(native,relocation,images['compiled']['symbols'])
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
