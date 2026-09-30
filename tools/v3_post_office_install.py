"""Connected post-office native entry planning for the whole banking category.

Local shims pass relocated original functions to the resident bank wrappers.
This stage returns checked owners; only the enclosing cartridge installer may
publish them alongside the complete linked bank, text, art, and saved owner.
"""
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_bank_frontend import native_contract,admission_contract
from v3_submenu_tables import Owner

ENTRIES=('af_bank_menu_construct_entry','af_bank_menu_destruct_entry',
    'af_bank_menu_set_proc_entry','af_bank_pelly_business_entry',
    'af_bank_pelly_talk_entry','af_bank_pelly_destruct_entry')
MENU_VROM,MENU_RAM=0x7749C0,0x8085BAC0
MENU_SHA='0a1b26e78d268cee578724995048491101a95bd9058359a3d8d53d04252b4270'
MENU_REL_SHA='d16d58dce7c9e96eb81b1abf7d9fb99f589d0ca571b219d8fc82bd5790a72c44'


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
