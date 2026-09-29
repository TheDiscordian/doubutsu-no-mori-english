"""Shared stationery adapters for complete retained native owners.

Only creation applies the quantity policy. Display/counter adapters normalize
their temporary lookup register, never the item stored in a pocket or world.
"""
import struct

from aflib import sha256,u32
from catalogue_names import Image
from npc_mail_show import relocate_verified_data
from v3_import_storage import jump
from v3_submenu_tables import Owner


def native_owner(data,reloc,ram,*,address_constants=()):
    """Materialize BSS and flatten section-relative relocations before append."""
    sections=struct.unpack_from('>5I',reloc)
    if sum(sections[:3])!=len(data):raise ValueError('Changed complete stationery owner sections')
    material=bytes(data)+bytes(sections[3]);rows=[]
    for word in struct.unpack_from('>'+str(sections[4])+'I',reloc,20):
        section=word>>30
        if section not in (1,2,3):raise ValueError('Invalid stationery owner relocation section')
        rows.append(0x40000000|(word&0x3F000000)|(sum(sections[:section-1])+(word&0xFFFFFF)))
    size=(24+4*len(rows)+15)&~15
    flat=(struct.pack('>5I',len(material),0,0,0,len(rows))+
        struct.pack('>'+str(len(rows))+'I',*rows)+bytes(size-24-4*len(rows))+struct.pack('>I',size))
    for base in (0x80200010,0x80348010):
        before=relocate_verified_data(Image(ram,len(material),sections),data,reloc,base,address_constants=address_constants)
        after=relocate_verified_data(Image(ram,len(material),(len(material),0,0,0,len(rows))),material,flat,base,address_constants=address_constants)
        if before!=after:raise ValueError('Flattened stationery owner changes native relocation or BSS')
    owner=Owner(material,flat,ram,address_constants=address_constants)
    owner.source=dict(bytes=len(data),resident_bytes=len(material),sha256=sha256(data),relocation_sha256=sha256(reloc))
    return owner


def append_hook(owner,entry,expected,words,*,local_jumps=(),moved=()):
    """Retain original relocation order when moving a high/low instruction pair."""
    address=owner.append(struct.pack('>'+str(len(words))+'I',*words))
    for old_index,new_index in moved:
        offset=entry-owner.ram+old_index*4;row=owner.locations.get(offset)
        if row is None:raise ValueError('Missing moved stationery relocation')
        index=owner.rows.index(row)
        owner.rows[index]=(row&0xFF000000)|(address-owner.ram+new_index*4)
    for index in local_jumps:owner.rows.append(0x44000000|(address-owner.ram+index*4))
    for index,before in enumerate(expected):owner.patch(entry+index*4,before,jump(address) if not index else 0)
    owner.rows.append(0x44000000|(entry-owner.ram))
    return dict(entry=entry,address=address,bytes=len(words)*4)


def normalize(register):
    """Map additional quantities to the existing generic paper drawing/counter.

    Only register and at change. Original style IDs remain untouched. Existing
    generic paper artwork and counter wording do not depend on the style.
    """
    return [0x24010000|register<<21|0xDFC0,0x2C210004,0x14200005,0,
        0x24010000|register<<21|0xD1C0,0x2C2100C0,0x10200002,0,
        0x24002000|register<<16]


def shop_floor(owner):
    """All reserve/floor/removal paths; retain the existing furniture hooks."""
    if owner.ram!=0x80953E20:raise ValueError('Changed shop-design owner')
    result=[]
    # Patch outside the furniture branch delay slots. The original item stays
    # in v1. Only the original scratch predicate is changed.
    for entry,expected,yes,no,tail in (
        (0x80953E7C,(0x14200005,0x28612041),0x80953E8C,0x80953E94,()),
        (0x80954890,(0x14200002,0x28612041),0x80954918,0x8095489C,(0x28612600,)),
        (0x80954BE0,(0x28612000,0x14200006),0x80954BF8,0x80954C00,(0x3C188013,))):
        # Additional pack reservation OR native/orange range; no C call and no
        # mutation of the quantity carried by floor-selection return values.
        delay=tail[0] if tail else 0
        words=[0x2461D1C0,0x2C2100C0,0x14200005,0,0x2461E000,
            0x2C210044,0x10200003,0,jump(yes),delay,jump(no),delay]
        result.append(append_hook(owner,entry,expected,words,local_jumps=(8,10)))
    return result


def shop_counter(owner,spec):
    """Keep full name/price IDs; normalize only the bounded counter lookup."""
    if owner.ram!=spec.ram:raise ValueError('Changed shop counter owner')
    entry=spec.handler+0x30
    words=[0x97A2003A,*normalize(2),0x24010001,jump(entry+8),0]
    return append_hook(owner,entry,(0x97A2003A,0x24010001),words,local_jumps=(11,))


def room_drawing(owner):
    """Keep all 50 model rows/resources and normalize three temporary queries."""
    if owner.ram!=0x80962A20:raise ValueError('Changed complete loose-item drawing owner')
    result=[]
    for entry,expected,register,moved in (
        (0x80963174,(0x00004025,0x97A30056),3,()),
        (0x80963800,(0x3C028096,0x24423CD0),4,((0,0),(1,1))),
        (0x809638C8,(0x3C028096,0x24423CD0),4,((0,0),(1,1)))):
        words=[*expected,*normalize(register),jump(entry+8),0]
        result.append(append_hook(owner,entry,expected,words,local_jumps=(11,),moved=moved))
    return result


def first_job(owner,symbols):
    """Creation and displayed handover share one policy, including replacements."""
    if owner.ram!=0x809C7FF0:raise ValueError('Changed first-job owner')
    # Native set_itemNo and matching handover rows retain their full identities.
    for address in (0x809C9F4C,0x809CA020):
        if struct.unpack_from('>H',owner.data,address-owner.ram+6)!=(0x2037,):
            raise ValueError('Changed first-job stationery identity')
        if struct.unpack_from('>H',owner.data,address-owner.ram+14)!=(0x2037,):
            raise ValueError('Changed repeat first-job stationery identity')
    # Wrappers are called only at this actor's creation/display boundaries.
    # All existing possession setters elsewhere keep transfer semantics.
    result=[]
    for address,target,handler in (
        (0x809C850C,0x800B8B8C,'af_carried_paper_first_job_give'),
        (0x809C8540,0x800B8B8C,'af_carried_paper_first_job_give'),
        (0x809C8BC4,0x8007B44C,'af_carried_paper_first_job_show')):
        owner.patch(address,jump(target,link=True),jump(symbols[handler],link=True))
        result.append(dict(address=address,target=symbols[handler],original=target))
    return result
