"""Prepare complete native April manager/descriptor hooks for the bank packet.

This is a bounded resource plan, not a cartridge installation or gameplay test.
Preserve the installed Wisp/Harvest chain and every native relocated control.
"""
import struct
from types import SimpleNamespace

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from npc_mail_show import relocate_verified_data
from v3_campsite_manager import RAM as OWNER_RAM,VROM,RELOC,METADATA,CONTROL_COUNT
from v3_import_storage import jump
from v3_registry import BANK_APRIL_CONTROLLER


def native_owners(image,prior,symbols,*,code_bounds,entry_core):
    low,high=code_bounds
    names=('af_bank_april_manager_start','af_bank_april_manager_stop',
        'af_bank_april_calendar_before_cleanup','af_bank_april_descriptor')
    if any(n not in symbols or not low<=symbols[n]<high or symbols[n]&3 for n in names):
        raise ValueError('April native owners require actual linked callbacks')
    files=by_vrom(image);old=files[VROM].extract(image);oldrel=files[RELOC].extract(image)
    previous=prior['campsite_manager'];harvest=prior['equipment_resources']['harvest']
    count=previous['control_count'];table=previous['table'];head=struct.unpack_from('>5I',oldrel)
    if (count!=75 or table-OWNER_RAM+count*32!=len(old) or
            sha256(old)!=harvest['manager']['sha256'] or
            u32(old,CONTROL_COUNT-OWNER_RAM)!=count or head[:4]!=(len(old),0,0,0) or
            sha256(oldrel)!=previous['relocation_sha256'] or
            previous['today_pointer_capacity']<count+1 or
            u32(old,len(old)-32)!=116 or
            any(u32(old,table-OWNER_RAM+i*32)==117 for i in range(count)) or
            any(row['profile']>=BANK_APRIL_CONTROLLER['profile'] for row in harvest['registry']['rows'])):
        raise ValueError('Changed complete retained April manager or identity capacity')
    data=bytearray(old);struct.pack_into('>I',data,CONTROL_COUNT-OWNER_RAM,count+1)
    data.extend(struct.pack('>8I',117,symbols[names[0]],symbols[names[1]],0,0,0,0,0))
    reloc=bytearray(oldrel);struct.pack_into('>I',reloc,0,len(data))
    if len(data)+len(reloc)>0xC000 or VROM+len(data)>RELOC or OWNER_RAM+len(data)>0x809670B0:
        raise ValueError('April manager exceeds the complete retained allocation')
    for address in (0x801A0010,0x802F8010):
        before=relocate_verified_data(SimpleNamespace(ram=OWNER_RAM,resident_bytes=len(old),sections=head),
            old,oldrel,address)
        after=relocate_verified_data(SimpleNamespace(ram=OWNER_RAM,resident_bytes=len(data),
            sections=(len(data),0,0,0,head[4])),bytes(data),bytes(reloc),address)
        allowed=range(CONTROL_COUNT-OWNER_RAM,CONTROL_COUNT-OWNER_RAM+4)
        if (any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(before,after))) or
                after[len(old):]!=data[len(old):] or
                before[table-OWNER_RAM:len(old)]!=after[table-OWNER_RAM:len(old)]):
            raise ValueError('April changes retained relocated native controls')
    original=files[CODE_VROM].extract(image);core=bytearray(entry_core);patches=[]
    if len(core)!=len(original):raise ValueError('Changed complete bank core dimensions')
    def patch(address,before,after):
        at=address-CODE_RAM
        if original[at:at+len(before)]!=before or core[at:at+len(before)]!=before:
            raise ValueError('Changed or overlapping complete April core hook')
        core[at:at+len(after)]=after
        patches.append(dict(address=address,before=before.hex(),after=after.hex()))
    hs=harvest['code']['symbols']
    patch(0x8007F630,struct.pack('>2I',jump(hs['af_hr_calendar_before_cleanup'],link=True),0),
        struct.pack('>2I',jump(symbols[names[2]],link=True),0))
    for address in (0x8007F640,0x8007F660):
        patch(address,struct.pack('>I',0x24110075),struct.pack('>I',0x24110076))
    descriptor=prior['equipment_resources']['npc_extra']['events']['participants']['code']['symbols']['af_hp_descriptor']
    patch(0x80057E4C,struct.pack('>2I',jump(descriptor,link=True),0x00C02025),
        struct.pack('>2I',jump(symbols[names[3]],link=True),0x00C02025))
    patch(METADATA,struct.pack('>4I',VROM,VROM+len(old),OWNER_RAM,OWNER_RAM+len(old)),
        struct.pack('>4I',VROM,VROM+len(data),OWNER_RAM,OWNER_RAM+len(data)))
    return {VROM:bytes(data),RELOC:bytes(reloc),CODE_VROM:bytes(core)},dict(
        vrom=VROM,reloc=RELOC,ram=OWNER_RAM,table=table,control_count=count+1,
        retained_controls=count,identity=BANK_APRIL_CONTROLLER,
        callbacks={n:symbols[n] for n in names},bytes=len(data),sha256=sha256(data),
        previous_sha256=sha256(old),relocation_sha256=sha256(reloc),relocation_bytes=len(reloc),
        core_sha256=sha256(core),core_patches=patches,daily_type_bound=118,
        original_controls_and_relocations_retained=True,additional_owner_bytes=32,
        additional_resident_bytes=0,installed=False,native_execution_verified=False)
