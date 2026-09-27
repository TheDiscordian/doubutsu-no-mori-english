"""Complete shared room music binding for original stereos and imported radios.

These contracts and hooks are category machinery, not an item installer. A
prepared contract does not enable a profile or publish an experimental build.
"""
import json
import struct
from types import SimpleNamespace

from aflib import by_vrom,CODE_RAM,CODE_VROM,sha256
from npc_mail_show import relocate_verified_data
from v3_import_storage import jump

VROM,RELOC,RAM=0x82D7F0,0x844400,0x80936710
SONG=27
SOURCES=('tools/v3_room_music.py','tools/v3_sound_programs.py',
    'overlays/v3/room_music.c','overlays/v3/room_music.h',
    'overlays/v3/room_music_native.c','overlays/v3/room_music_native.h',
    'overlays/v3/room_rigs.h','overlays/v3/room_rigs_bootstrap.c','overlays/v3/room_rigs_packet.ld')
SOURCE_FUNCTIONS=(
    (0x101960,136,'1699c6add6a7b049013ed922c43ba2014131e4632098da1cc204bb1868141f20'),
    (0x1019E8,72,'0dbe99cc3babb254a136d6b126c083f67e3ff37351ab0e834cdc8692de5951d0'),
    (0x101A30,108,'81b8ac601a7949974a50ce9f884de3030c609a2fc4be3a468b75d688731fa545'),
    (0x101A9C,296,'7fa489600820511b15f8c77bf0c063a1a10ddf3bcda71684f9796e89653324a0'),
    (0x101BC4,24,'11710f964ed8d65fb3741b875d2c17d68ad84661ea743d666ff7609d1a9f98b7'),
    (0x101BDC,32,'7928cfdfe122396209c25290ee1867c343c77269c616ece1cfe8bb527648c644'),
    (0x101BFC,148,'3620b9283764b62b7acea05b94c6057dd585dbc6c2b5f9c9c5502b31c092e97d'),
    (0x101C90,56,'f59c6dcab593de470292561a37ceb3678d7be9cbb6b95a73941c2e231803f24f'),
    (0x103ACC,204,'9073271d688406e4223163121d74eed1e82d39f04635fc7101ce3257d976ef6a'),
)
NATIVE_FUNCTIONS=(
    ('disk_dt',0x8093837C,112,'248ad49d5d1a4fef55fcc148e4b13aeb9625eaff5af65b23417e6bbdea0a9cb2'),
    ('apply',0x809383EC,260,'43fcffd00a5852eca165ecb45ed2dd9ec506202b9683bf99f35c7ec78938243d'),
    ('reserve_disk',0x809384F0,68,'e9f16f3d8d17add234ced34a34221426a075ca0c9658217f6fc9095acfa262ea'),
    ('reserve_default',0x80938534,32,'d977dd3c0f023da3d9091deced99d5b014700432546d1917b5615a3fafaaad33'),
    ('all_off',0x80938554,144,'2f2586092838336c5440550d7ccd91c71b16b973e113315bd3f40fbf5ee1488b'),
    ('one_on',0x809385E4,48,'65f5f6b09a10272d5a2f110654dbb01b82a13f6e04f988eaef68e6a7a49ebb54'),
)
CORE_FUNCTIONS=(
    ('make',0x8005E080,140,'af1774a5b0b155380d818697d81daee34eeb99aa91043ceb5f43b2a467aefe1f'),
    ('delete',0x8005E660,108,'c48221022130ae9584b037a12e46129beb004ffce73eb4f814d6ba0b65da1a05'),
    ('position',0x8005EA24,40,'2b56e36f28b5d37705368b167b66daefc844d70b6316abeeadb988574eeb9286'),
)
HOOKS=((0x8093837C,'af_v3_room_boot_music_disk_dt','27bdffe8afbf0014'),
       (0x809383EC,'af_v3_room_boot_music_apply','27bdffe0afb00018'),
       (0x809385B0,None,'000950c3314b0001'))


def source_contract(source):
    functions={}
    for at,size,digest in SOURCE_FUNCTIONS:
        raw,row=source.function(at)
        refs={16:(10,0,4,0x8009AEC8),128:(10,0,4,0x8009AF14),
              22:(6,1,6,0xA16F0),30:(4,1,6,0xA16F0)} if at==0x101BFC else {}
        if len(raw)!=size or sha256(raw)!=digest or row['relocations']!=refs:
            raise ValueError('Changed complete music ownership dependency: '+row['symbol'])
        functions[row['symbol']]=row
    return dict(functions=functions,song=SONG,interaction_mask=0x4008,
        radio_flag=0x4000,disk_flag=8,source_emission_ticks=36,source_steps_per_update=2,
        constructor='reset radio switches',destructor='restore default music when active',
        haniwa_start='reserve now; apply through ordinary owner timer',
        switched_start='exclusive switch; reserve; apply immediately',
        positional_player='all songs except aerobics',saved_format_changed=False)


def checked_functions(raw,origin,functions):
    rows=[]
    for name,address,size,digest in functions:
        data=raw[address-origin:address-origin+size]
        if len(data)!=size or sha256(data)!=digest:
            raise ValueError('Changed complete room-music native dependency: '+name)
        rows.append(dict(name=name,address=address,bytes=size,sha256=digest))
    return rows


def note_contract(image,report):
    """Reuse the complete original N64 musical-note effect and all its artwork."""
    from v3_room_effects import INSTALLED_VROM,INSTALLED_GRAPHICS
    files=by_vrom(image);c=report['equipment_resources']['room_rigs']['effects']['controller']
    controller=files[INSTALLED_VROM].extract(image)
    if not c.get('installed') or sha256(controller)!=c['sha256'] or c['graphics_vrom']!=INSTALLED_GRAPHICS:
        raise ValueError('Missing installed complete effect controller')
    wanted=('008fd520008fdd6080a35a8080a362c080a3623c','0600c9c00600cf38','00')
    for table,hexadecimal in zip(c['tables'],wanted,strict=True):
        at=table['offset']+32*table['stride']
        if controller[at:at+table['stride']].hex()!=hexadecimal:
            raise ValueError('Changed original musical-note effect mapping')
    code=files[0x8FD520].extract(image)
    art=files[INSTALLED_GRAPHICS].extract(image)[0xC9C0:0xCF38]
    if (len(code)!=2112 or sha256(code)!='8b99f97621a942b94996f8f5a3832aa02314997fe20759f1d2b9ebeede3d034b' or
            len(art)!=1400 or sha256(art)!='7736b5fe44a543429fd41d6019c3e0483b6f5809914dd959fe2e4274d860ee76'):
        raise ValueError('Changed complete musical-note code or artwork')
    return dict(effect=32,code_vrom=0x8FD520,code_bytes=len(code),code_sha256=sha256(code),
        graphics_vrom=INSTALLED_GRAPHICS,graphics_offset=0xC9C0,graphics_bytes=len(art),
        graphics_sha256=sha256(art),models=3,colours=5,argument0=1,argument1=0,
        native_lifetime=36,source_lifetime=72,native_damping=.8,
        adaptation='Retain the complete native note effect, including its native growth curve and debug scaling',
        exact_source_particle_integration=False,new_effect_slots=0)


def native_contract(image,report):
    from v3_sound_programs import shared_bgms
    files=by_vrom(image);owner=files[VROM].extract(image);core=files[CODE_VROM].extract(image)
    music=report['equipment_resources']['room_rigs'].get('music')
    if music and music.get('binding'):owner=restore_owner(owner,music,report['equipment_resources']['room_rigs'])
    return dict(owner_vrom=VROM,owner_ram=RAM,owner_bytes=0x4E0,actor_bytes=0x740,
        music_offset=0x45C,music_bytes=24,haniwa_offset=0x130,clip=0x80136F2C,
        functions=checked_functions(owner,RAM,NATIVE_FUNCTIONS),
        core=checked_functions(core,CODE_RAM,CORE_FUNCTIONS),
        music=shared_bgms(image,core,[SONG],native_mix=True),note=note_contract(image,report),
        installed=False)


def lifecycle(profile):
    from v3_furniture_composite import ROTATED_CATEGORY
    a=profile.get('callback_adapter',{})
    if (a.get('category')!=ROTATED_CATEGORY or profile['interaction_flags']!=0x4000 or profile['contact_action'] or
            a['rotation_y']!=-0x7000 or a['model_order']!=['opaque'] or a['draw_arena']!='opaque' or
            a['emitter']!=dict(source_period=36,height=-3.0,angle_offset=-0x1000,source_effect=32,
                source_item=0x1FCC,arg0=1,arg1=0,switch='equals-one')):
        raise ValueError('Incomplete rotated radio lifecycle')
    return dict(category=ROTATED_CATEGORY,mode=12,song=SONG,emitter=a['emitter'],
        rotation_y=a['rotation_y'],start_disabled=True,exclusive_music=True,destruction=True,
        native_note_effect_retained=True,saved_format_changed=False)


def parameters(row):
    life=lifecycle(row['profile']);a=row['profile']['callback_adapter'];p=a['constant_palette']
    palettes=[r for r in row['resources'] if r['kind']=='palette' and r['donor_offset']==p['donor_offset']]
    if (len(palettes)!=1 or palettes[0]['bytes']!=32 or palettes[0]['source_sha256']!=p['source_sha256'] or
            set(row['model_offsets'])!={'opaque'}):raise ValueError('Incomplete radio model or fixed palette')
    return 0x06000000+row['model_offsets']['opaque'],0x06000000+palettes[0]['native_offset'],life


def restore_owner(owner,music,runtime):
    binding=music['binding'];data=bytearray(owner)
    if not music.get('installed') or not binding.get('installed'):
        raise ValueError('Room music hooks are not installed')
    expected=[]
    for address,name,before in HOOKS:
        target=runtime['bootstrap']['symbols'][name] if name else None
        after=struct.pack('>2I',jump(target),0) if name else bytes.fromhex('312b400800000000')
        row=dict(address=address,symbol=name,target=target,before=before,after=after.hex());expected.append(row)
        at=address-RAM
        if owner[at:at+8]!=after:raise ValueError('Changed installed room music hook')
        data[at:at+8]=bytes.fromhex(before)
    if binding['hooks']!=expected:raise ValueError('Changed room music bootstrap identity')
    return bytes(data)


def publish_owner(base,prior,equipment,changes):
    """Rebind after every packet rebuild, preserving other owner modifications."""
    files=by_vrom(base);runtime=equipment['room_rigs'];music=runtime['music']
    old=prior['equipment_resources']['room_rigs'];owner=changes.get(VROM,files[VROM].extract(base))
    if old.get('music'):owner=restore_owner(owner,old['music'],old)
    code,binding=patch_native(owner,changes.get(RELOC,files[RELOC].extract(base)),runtime['bootstrap']['symbols'])
    binding['installed']=True;music.update(binding=binding,installed=True);changes[VROM]=code


def checked_binding(source,image,report):
    runtime=report['equipment_resources']['room_rigs'];music=runtime.get('music',{})
    if (not music.get('installed') or music.get('source')!=json.loads(json.dumps(source_contract(source))) or
            music.get('native')!=native_contract(image,report) or '-DAF_V3_ROOM_MUSIC' not in runtime['code']['flags']):
        raise ValueError('Missing complete installed room music ownership')
    blob=by_vrom(image)[RELOC].extract(image)
    if sha256(blob)!=music['binding']['relocation_sha256']:raise ValueError('Changed music owner relocation')
    symbols=runtime['code']['symbols'];boot=runtime['bootstrap']
    for key,name in (('APPLY','apply'),('DISK_DT','disk_dt')):
        flag=f'-DAF_ROOM_MUSIC_{key}=0x{symbols["af_v3_room_music_native_"+name]:X}u'
        if flag not in boot['flags']:raise ValueError('Changed checked-loader music destination')
    return music


def patch_native(owner,relocation,symbols):
    """Bridge original music entry points through the checked resident loader."""
    checked_functions(owner,RAM,NATIVE_FUNCTIONS)
    sections=struct.unpack_from('>5I',relocation)
    if sections[:4]!=(0x10E50,0x5BE0,0x1E0,0x22F0):
        raise ValueError('Changed room music owner dimensions')
    data=bytearray(owner);hooks=[];changed=set()
    for address,name,before in HOOKS:
        at=address-RAM;target=symbols[name] if name else None
        if owner[at:at+8].hex()!=before or target is not None and (target&3 or not 0x804B1800<=target<0x804B1E00):
            raise ValueError('Changed music bridge input or loader bounds')
        # andi t3,t1,4008 replaces the old shift-and-mask of music bit three.
        after=struct.pack('>2I',jump(target),0) if name else bytes.fromhex('312b400800000000')
        data[at:at+8]=after;changed.update(range(at,at+8))
        hooks.append(dict(address=address,symbol=name,target=target,before=before,after=after.hex()))
    for word in struct.unpack_from('>'+str(sections[4])+'I',relocation,20):
        section,offset=word>>30,word&0xFFFFFF
        at=sum(sections[:section-1])+offset
        if at in changed:raise ValueError('Unexpected relocation inside room music bridge')
    spec=SimpleNamespace(ram=RAM,resident_bytes=0x18F00,sections=sections)
    for base in (0x801A0010,0x802F8010,0x803D0010):
        before=relocate_verified_data(spec,owner,relocation,base)
        after=relocate_verified_data(spec,data,relocation,base)
        if any(a!=b and at not in changed for at,(a,b) in enumerate(zip(before,after,strict=True))):
            raise ValueError('Music hooks alter unrelated relocated instructions or data')
        for h in hooks:
            at=h['address']-RAM
            if after[at:at+8].hex()!=h['after']:raise ValueError('Music bootstrap call relocates incorrectly')
    return bytes(data),dict(hooks=hooks,owner_sha256=sha256(data),relocation_sha256=sha256(relocation),
        input_owner_sha256=sha256(owner),saved_format_changed=False,actor_allocation_changed=False,
        original_stereos_share_owner=True,installed=False)
