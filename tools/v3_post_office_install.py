"""Connected post-office native entry planning for the whole banking category.

Local shims pass relocated original functions to the resident bank wrappers.
This stage returns checked owners; only the enclosing cartridge installer may
publish them alongside the complete linked bank, text, art, and saved owner.
"""
import struct
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_submenu_tables import Owner

ENTRIES=('af_bank_menu_construct_entry','af_bank_menu_destruct_entry',
    'af_bank_menu_set_proc_entry','af_bank_pelly_business_entry',
    'af_bank_pelly_talk_entry','af_bank_pelly_destruct_entry')
MENU_VROM,MENU_RAM=0x7749C0,0x8085BAC0
MENU_SHA='0a1b26e78d268cee578724995048491101a95bd9058359a3d8d53d04252b4270'
MENU_REL_SHA='d16d58dce7c9e96eb81b1abf7d9fb99f589d0ca571b219d8fc82bd5790a72c44'
PELLY_SERVICES={
    'af_bank_pelly_window':(0x8009D1F0,16,'e4e54e5f3fc74caca37c6c0fdda0b5684e6e68d753495d23a868e75faf6af1f3'),
    'af_bank_pelly_native_number':(0x8009DBB0,48,'ef41c380e4b84047a74f2394625e8e1dce494d9cd5e5ccc891c412b23d39bc11'),
    'af_bank_pelly_continue':(0x8009E908,68,'ff7ab67f35cac9085f90c93232cc8942e01bcd1cbc8a5b6c4a90d633b25180e3'),
    'af_bank_pelly_disappeared':(0x8009D274,32,'420089418bf031f80d8249e95152ecc1a7e1aca06f7fa681ffade46b0314570a'),
    'af_bank_pelly_appeared':(0x8009D294,84,'bb12803de6ff554a120ba8db8617fa3ca8b6212383e6c7ec5c66788b4288a25d'),
    'af_bank_pelly_unlock':(0x8009E9F8,12,'0eaeaabbbaa711868cd9b1f5377531ff689c5d0706ca771afb7f137121be82ce'),
    'af_bank_pelly_force':(0x8009E9C0,16,'19d1e2f6e118f26b00e0062d08bd578e85ad48062bae953b48117fa3bbbe816f'),
    'af_bank_pelly_native_continue':(0x8009DBA4,12,'0aabf3753523c2378aee478773f4b5ce1941af7943ea67feeb34618204628be4'),
    'af_bank_pelly_native_change':(0x8009E658,96,'b4600b4be924b7444feffa94fb3f445481047b9080968b594b18a9a133007281'),
    'af_bank_pelly_appear':(0x8009D5CC,84,'8630ae2e806891ebe990c0d55a021f599475b3101679beab717ec08977f8c524'),
    'af_bank_pelly_disappear':(0x8009D510,32,'ef3aa4bcc23094d24bab6e7a8082813a72b79e1ae256f947c30d36a5fe2475f6'),
    'af_bank_pelly_order':(0x8007B49C,80,'fc9f8c7f605e55bfd50e5629400e9bd23ad8f088a9606cd129164e85fc32d319'),
    'af_bank_pelly_set_order':(0x8007B44C,80,'13ce9135ba770a01910cb33227b0ed323eaea4a9a3377a56cc5253ea0eb6fa43'),
    'af_bank_pelly_choice_window':(0x80065040,36,'31056155e65ffcf85e11b21a9605dea25feb585bdac8640a778294dd7d8ec17c'),
    'af_bank_pelly_choice':(0x800654FC,12,'9c54dc78d45abf8b60754a954f416eb99c1df88c454a1649a6f16d7beda0e3d0'),
    'af_bank_pelly_mail_count':(0x800B68E8,36,'267162826f91b89ab736147048c0bdf1bd7e1038a18004349ed889db34d3bba6'),
    'af_bank_pelly_first_job':(0x8007D6E0,84,'2bb668abaf6b473fa6427a280927a67f70466ae256ea7026ef91e6a20f30382e'),
    'af_bank_pelly_foreigner':(0x800951C0,36,'c4c23b986611a6a6e60e79eb0f70ae4d5eba5c37bbcb4da921f78a66858922f4'),
    'af_bank_pelly_native_message':(0x8007B5C0,52,'9d2c5893c41596c77b36014c8db11bcab9fd910fbfe1e42aafb74dfc5e2902d2'),
}


def native_binding_contract(core,library,pelly,text):
    """Check real native APIs and the startup-installed sixteen-byte setter.

    The ROM's setter entry contains a one-shot loader, not a field setter. Bind
    that entry only with the entire reviewed text owner, its current CRC, and
    the retained setter initialization. Dynamic actor/event providers are not
    assigned fake addresses or replaced by empty implementations.
    """
    from v3_bank_frontend import NATIVE_SERVICES
    from v3_furniture_reactions import NATIVE_BLOCKS
    from text_catchphrases import PROFILE,SYMBOLS
    services={};bindings={}
    for name,(address,size,digest) in dict(NATIVE_SERVICES,**PELLY_SERVICES).items():
        raw=core[address-CODE_RAM:address-CODE_RAM+size]
        if len(raw)!=size or sha256(raw)!=digest:
            raise ValueError('Changed complete native post-office service: '+name)
        services[name]=dict(address=address,bytes=size,sha256=digest,vrom=CODE_VROM)
        if name!='af_bank_open_queue':bindings[name]=address
    for name,vrom,ram,address,size,digest in NATIVE_BLOCKS:
        if name not in ('memcpy','memset'):continue
        raw=library[address-ram:address-ram+size]
        if len(raw)!=size or sha256(raw)!=digest:
            raise ValueError('Changed complete native post-office service: '+name)
        services[name]=dict(address=address,bytes=size,sha256=digest,vrom=vrom)
        bindings[name]=address
    # The sole installed V3 change in the complete text owner raises its name
    # bound. Restoring that checked instruction recovers the reviewed V2 owner,
    # including its entire relocation table, field state, and startup hook.
    original=bytearray(text)
    if len(original)!=PROFILE['blob_bytes'] or u32(original,0x4B8)!=0x2C4200EE:
        raise ValueError('Changed complete extended post-office text owner')
    struct.pack_into('>I',original,0x4B8,0x2C4200D8)
    if sha256(original)!=PROFILE['blob_sha256']:
        raise ValueError('Changed complete extended post-office text owner')
    loader=core[0x8009D6D0-CODE_RAM:0x8009D820-CODE_RAM]
    if sha256(loader)!='f17fa59988a2a5786fafe48a2b6d731471918ee3847f62b2d1ccfa13b6e41274':
        raise ValueError('Changed complete post-office text startup loader')
    crc=zlib.crc32(text)
    if struct.unpack_from('>II',core,0x8009D758-CODE_RAM)!=(
            0x3C030000|((crc+0x8000)>>16&65535),0x24630000|(crc&65535)):
        raise ValueError('Post-office text startup CRC does not match its owner')
    bindings['af_bank_pelly_free_string']=0x8009D6D0
    # Both actual reads in the whole guarded native loan formatter establish
    # the current-private pointer. The current-player and home fields are also
    # guarded by the enclosing admission contract, never donor structure offsets.
    for address,word in ((0x809C364C,0x3C0E8013),(0x809C3650,0x8DCE6FD8),
            (0x809C3698,0x3C0F8013),(0x809C369C,0x8DEF6FD8)):
        if u32(pelly,address-0x809C3420)!=word:
            raise ValueError('Changed native post-office current-private reader')
    bindings.update(af_bank_now_private=0x80136FD8,af_bank_player=0x80136EA3,
        af_bank_native_homes=0x8012A428,af_bank_home_arrangement=0x80135DFA)
    return bindings,dict(services=services,globals={n:bindings[n] for n in (
        'af_bank_now_private','af_bank_player','af_bank_native_homes','af_bank_home_arrangement')},
        free_string=dict(address=0x8009D6D0,vrom=0x03A00000,bytes=len(text),
            sha256=sha256(text),crc32=f'{crc:08X}',field_bytes=16,
            setter_offset=SYMBOLS['af_free_set'],initialization_offset=SYMBOLS['af_text_fields_init'],
            one_shot_loader_sha256=sha256(loader),startup_installed=True),
        unresolved_providers=['af_bank_native_account','af_bank_account_mode','af_bank_pelly_april_clip'],
        installed=False,native_execution_verified=False)


def native_bindings(base,prior):
    """Resolve the fixed services only after checking their enclosing owners."""
    from v3_bank_frontend import native_contract,admission_contract
    files=by_vrom(base);core=files[CODE_VROM].extract(base);pelly=files[0x8A6C10].extract(base)
    native_contract(files[0x79B120].extract(base),files[0x79BF10].extract(base),core)
    admission_contract(pelly,files[0x8A8A10].extract(base),core)
    bindings,report=native_binding_contract(core,files[0x1060].extract(base),pelly,files[0x03A00000].extract(base))
    # Message selection already goes through the complete shared announcement
    # owner, also used by Harvest. Preserve that installed API and verify its
    # real resident body rather than restoring an obsolete native implementation.
    demo=prior['equipment_resources']['npc_extra']['events']['demo']
    packet=prior['equipment_resources']['holiday_fishing']['packet']
    from v3_holiday_scene import DEMO_RAM
    at=packet['physical']+DEMO_RAM-packet['ram'];code=demo['code']
    target=demo['code']['symbols']['af_holiday_demo_message']
    if (not demo['installed'] or not DEMO_RAM<=target<DEMO_RAM+code['bytes'] or
            not packet['physical']<=at<at+code['bytes']<=packet['physical']+packet['bytes'] or
            sha256(base[at:at+code['bytes']])!=code['sha256'] or
            struct.unpack_from('>II',core,0x8007B5C0-CODE_RAM)!=(0x08000000|(target>>2&0x3FFFFFF),0)):
        raise ValueError('Changed complete installed post-office message dispatcher')
    report['message_dispatch']=dict(ram=DEMO_RAM,bytes=code['bytes'],sha256=code['sha256'],
        physical=at,entry=target,native_entry=0x8007B5C0,retained_shared_owner=True)
    return bindings,report


def local_owner(data,relocation,ram):
    """Flatten section locations without moving any native code/data/BSS byte."""
    sections=struct.unpack_from('>5I',relocation)
    if len(data)!=sum(sections[:3]) or len(relocation)<24+sections[4]*4:
        raise ValueError('Changed complete bank overlay dimensions')
    rows=[]
    for word, in struct.iter_unpack('>I',relocation[20:20+sections[4]*4]):
        section,kind,offset=word>>30,word>>24&63,word&0xFFFFFF
        if section not in (1,2,3) or kind not in (2,4,5,6) or offset&3 or offset+4>sections[section-1]:
            raise ValueError('Invalid complete bank overlay relocation')
        rows.append(0x40000000|kind<<24|sum(sections[:section-1])+offset)
    flat=data+bytes(sections[3]);n=(24+4*len(rows)+15)&~15
    rel=(struct.pack('>5I',len(flat),0,0,0,len(rows))+
        struct.pack('>'+str(len(rows))+'I',*rows)+bytes(n-24-4*len(rows))+struct.pack('>I',n))
    for load in (0x80200010,0x80348010):
        before=relocate_verified_data(Image(ram,sum(sections[:4]),sections),data,relocation,load)
        after=relocate_verified_data(Image(ram,len(flat),struct.unpack_from('>5I',rel)),flat,rel,load)
        if before!=after:raise ValueError('Flattened banking owner changes native loaded bytes')
    return Owner(flat,rel,ram)


def shim(owner,resident,arguments):
    """Tail-call resident code, with local original pointers in ABI arguments."""
    if resident&3 or not 0x80400000<=resident<0x80800000:
        raise ValueError('Bank entry has no aligned Expansion Pak code address')
    words=[];fixups=[]
    for register,address in arguments:
        if register not in (5,6,7) or address&3 or not owner.ram<=address<owner.ram+len(owner.original):
            raise ValueError('Bank shim original function is outside its native owner')
        fixups.extend(((len(words)*4,5),(len(words)*4+4,6)))
        words.extend((0x3C000000|register<<16|((address+0x8000)>>16&65535),
            0x24000000|register<<21|register<<16|address&65535))
    words.extend((0x08000000|(resident>>2&0x3FFFFFF),0))
    address=owner.append(struct.pack('>'+str(len(words))+'I',*words))
    for at,kind in fixups:owner.rows.append(0x40000000|kind<<24|address-owner.ram+at)
    return address


def native_entries(base,symbols,*,code_bounds):
    """Bind all Pelly/menu consumers together, retaining full original bodies.

    Bounds belong to the enclosing linked packet. No synthetic symbol, empty
    service, or installed-cartridge claim is generated here.
    """
    from v3_bank_frontend import native_contract,admission_contract
    low,high=code_bounds
    if not 0x80400000<=low<high<=0x80800000 or any(
            name not in symbols or not low<=symbols[name]<high or symbols[name]&3 for name in ENTRIES):
        raise ValueError('Bank consumers require the complete linked entry set')
    files=by_vrom(base);core=bytearray(files[CODE_VROM].extract(base))
    repay=files[0x79B120].extract(base);repay_rel=files[0x79BF10].extract(base)
    pelly=files[0x8A6C10].extract(base);pelly_rel=files[0x8A8A10].extract(base)
    native_contract(repay,repay_rel,core);admission_contract(pelly,pelly_rel,core)
    menu=bytearray(files[MENU_VROM].extract(base))
    menu_rel=files[0x7778B0].extract(base)
    if sha256(menu)!=MENU_SHA or sha256(menu_rel)!=MENU_REL_SHA:
        raise ValueError('Changed complete connected submenu owner/relocation')
    r=local_owner(repay,repay_rel,0x808979C0)
    lifecycle=[shim(r,symbols[name],[(5,original)]) for name,original in zip(ENTRIES[:3],
        (0x80898688,0x80898710,0x80898520))]
    rdata,rrel,rreport=r.finish()
    descriptor_at=0x2AF0;before=struct.pack('>8I',0x79B120,0x79BF10,0x808979C0,0x808987E0,
        0x80898688,0x80898710,0x80898520,0)
    if menu[descriptor_at:descriptor_at+32]!=before:raise ValueError('Changed complete native repayment lifecycle')
    after=struct.pack('>8I',0x79B120,0x79B120+len(rdata),r.ram,r.ram+len(rdata),*lifecycle,0)
    menu[descriptor_at:descriptor_at+32]=after
    head=struct.unpack_from('>5I',menu_rel);spec=Image(MENU_RAM,sum(head[:4]),head)
    for load in (0x80200010,0x80348010):
        old=relocate_verified_data(spec,files[MENU_VROM].extract(base),menu_rel,load)
        new=relocate_verified_data(spec,menu,menu_rel,load)
        if (new[descriptor_at:descriptor_at+32]!=after or any(x!=y for i,(x,y) in enumerate(zip(old,new))
                if not descriptor_at<=i<descriptor_at+32)):
            raise ValueError('Bank descriptor changes unrelated native menu allocation bytes')
    # VROM relocation is deliberately left to the ordinary resource allocator;
    # the enlarged file must never overwrite the original following fixups.
    growth=((len(rdata)+63)&~63)-((len(repay)+48+63)&~63)
    pool=0x800C4B10-CODE_RAM;word=u32(core,pool)
    if word!=0x25CEEA60 or growth<0 or (word^(word+growth))&0xFFFF8000:
        raise ValueError('Changed or overflowing complete native submenu arena')
    struct.pack_into('>I',core,pool,word+growth)
    p=local_owner(pelly,pelly_rel,0x809C3420)
    business=shim(p,symbols[ENTRIES[3]],[(6,0x809C3BE8)])
    talk=shim(p,symbols[ENTRIES[4]],[(5,0x809C4EA8),(6,0x809C3708)])
    destruct=shim(p,symbols[ENTRIES[5]],[(6,0x809C3510)])
    for address,kind in ((0x809C512C,2),(0x809C5014,2),(0x809C4F08,5),(0x809C4F0C,6)):
        at=address-p.ram
        if p.locations.get(at)!=0x40000000|kind<<24|at:
            raise ValueError('Changed local Pelly entry relocation ownership')
    p.patch(0x809C512C,0x809C3BE8,business)
    p.patch(0x809C5014,0x809C3510,destruct)
    p.patch(0x809C4F08,0x3C06809C,0x3C060000|((talk+0x8000)>>16&65535))
    p.patch(0x809C4F0C,0x24C64EA8,0x24C60000|(talk&65535))
    # Replaced references remain local, so all original fixups are retained.
    pdata,prel,preport=p.finish()
    rreport.update(original_sha256=sha256(repay),original_relocation_sha256=sha256(repay_rel),
        original_bss_bytes=48,original_loaded_bytes_preserved=True,entries=lifecycle)
    preport.update(original_relocation_sha256=sha256(pelly_rel),
        entries=dict(business=business,talk=talk,destruct=destruct),original_bodies_preserved=True)
    report=dict(repayment=rreport,pelly=preport,
        descriptor=dict(vrom=MENU_VROM,offset=descriptor_at,before=before.hex(),after=after.hex(),
            relocation_sha256=sha256(menu_rel),whole_loaded_images_checked=True),
        arena=dict(address=pool+CODE_RAM,before=word,after=word+growth,additional_pool_bytes=growth),
        installed=False,resource_relocation_required=True,native_execution_verified=False)
    return {0x79B120:rdata,0x79BF10:rrel,0x8A6C10:pdata,0x8A8A10:prel,
        MENU_VROM:bytes(menu),CODE_VROM:bytes(core)},report
