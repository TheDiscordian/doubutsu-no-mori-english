"""Bind the complete holiday directory to expanded native daily storage.

This is the same diary/category installation path. It preserves native owners,
camper callbacks, event state semantics, and inactive actor/selection flags.
"""
import copy
import json
import struct
from types import SimpleNamespace
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from apply_translation import write_new
from npc_mail_show import relocate_verified_data
from v3_asset_loader import ROOT,compile_part
from v3_campsite_manager import RAM as OWNER,VROM,RELOC
from v3_holiday_events import TYPES
from v3_import_storage import replace_checked
from v3_npc_registry import RAM,SIZE
import v3_physical_resources as physical

DAYS,REFERENCES,IDS=0x806F1500,0x806F1900,0x806F1A80
DAY_CAPACITY,REFERENCE_CAPACITY=64,80
CORE_SHA='e6b347ba3fb99c4021c2ed4eaa95728a4ac2a9cc228c2feea1cf4047a81f2c86'
OWNER_SHA='937af8a6e83b9c52ec06c363800ea4db26b198857374b9b475de6776b26bf390'
RELOC_SHA='d6de267f91feebef41bc1a18d2460f70ca560a1664c5b20e1c94b7ab4d0db54f'
# Checked native HI/LO pairs. END consumers are deliberately distinguished from
# the adjacent original index initializer (8007E668), which stays untouched.
DAY_POINTERS=(
    (0x8007E198,0x8007E19C),(0x8007E1EC,0x8007E1F0),
    (0x8007E22C,0x8007E230),(0x8007E290,0x8007E294),
    (0x8007E2E0,0x8007E2E4),(0x8007E410,0x8007E41C),
    (0x8007E540,0x8007E544),(0x8007E60C,0x8007E618),
    (0x8007E690,0x8007E69C),(0x8007EF48,0x8007EF54),
    (0x8007F2A8,0x8007F2AC),(0x8007F920,0x8007F930),
    (0x8007FCC4,0x8007FCCC),(0x8007FD4C,0x8007FD50),
    (0x8007FDC0,0x8007FDC4),(0x8007FE18,0x8007FE1C),
    (0x8007FE8C,0x8007FE90),(0x8007FEC8,0x8007FECC),
    (0x8007FF20,0x8007FF24),(0x800800A8,0x800800AC),
    (0x80081850,0x80081868),
)
END_POINTERS=((0x8007E610,0x8007E614),(0x8007E694,0x8007E698),
    (0x8007F114,0x8007F118),(0x80081854,0x80081864))
MANAGER_POINTERS=((0x809612F8,0x809612FC),(0x809619FC,0x80961A00),
    (0x80961B38,0x80961B3C))
SOURCES=('tools/v3_holiday_native.py','overlays/v3/holiday_native.h',
    'overlays/v3/holiday_native.c','overlays/v3/holiday_native.ld',
    'tools/v3_holiday_events.py','tools/v3_asset_loader.py')


def identities():
    # Registry version one: fixed donor identities, never checkbox order.
    if sorted(TYPES)!=[1,4,5,11,12,13,14,15,16,20,35,37,41,43,56,64,*range(80,108)]:
        raise ValueError('Holiday identity registry needs an explicit version change')
    forward=bytearray([255]*128);reverse=bytearray([255]*128)
    rows=[]
    for native,source in enumerate(sorted(TYPES),71):
        forward[source]=native;reverse[native]=source
        rows.append(dict(donor_type=source,native_type=native))
    return bytes(forward+reverse),rows


def word(data,ram,address,before,after,hooks,purpose):
    replace_checked(data,address-ram,struct.pack('>I',before),struct.pack('>I',after))
    hooks.append(dict(address=address,before=before,after=after,purpose=purpose))


def pointer(data,ram,hi,lo,old,new,hooks):
    high,low=(u32(data,a-ram) for a in (hi,lo))
    register=high>>16&31
    if (high>>26!=15 or high&65535!=(old+0x8000)>>16 or
            low>>26 not in (9,43) or low>>21&31!=register or low&65535!=old&65535):
        raise ValueError(f'Changed daily-event address pair {hi:08X}/{lo:08X}')
    word(data,ram,hi,high,(high&0xFFFF0000)|((new+0x8000)>>16),hooks,'expanded event storage')
    word(data,ram,lo,low,(low&0xFFFF0000)|(new&65535),hooks,'expanded event storage')


def patch_core(core):
    if sha256(core[0x8007D140-CODE_RAM:0x80081E48-CODE_RAM])!=CORE_SHA:
        raise ValueError('Changed complete native event core')
    found=set()
    for address in range(0x8007D140,0x80081E48,4):
        w=u32(core,address-CODE_RAM)
        if w>>26 in (9,32,36,40,43) and w&65535 in (0x9F98,0xA098):found.add(address)
    expected={lo for _,lo in DAY_POINTERS+END_POINTERS}|{0x8007E668}
    if found!=expected:raise ValueError('Unreviewed native daily-event storage consumer')
    hooks=[]
    for hi,lo in DAY_POINTERS:pointer(core,CODE_RAM,hi,lo,0x80139F98,DAYS,hooks)
    for hi,lo in END_POINTERS:pointer(core,CODE_RAM,hi,lo,0x8013A098,DAYS+DAY_CAPACITY*16,hooks)
    for address,before,after in (
        (0x8007E238,0x24050010,0x24050000|DAY_CAPACITY),
        (0x8007E2B0,0x28410010,0x28410000|DAY_CAPACITY),
        (0x8007F640,0x24110047,0x24110073),(0x8007F660,0x24110047,0x24110073)):
        word(core,CODE_RAM,address,before,after,hooks,'expanded daily admission and all-type cleanup')
    return hooks


def patch_manager(base):
    files=by_vrom(base);before=files[VROM].extract(base);rel=files[RELOC].extract(base)
    if sha256(before)!=OWNER_SHA or sha256(rel)!=RELOC_SHA:
        raise ValueError('Changed complete camper/native manager')
    owner=bytearray(before);head=list(struct.unpack_from('>5I',rel))
    if head[:4]!=[len(owner),0,0,0]:raise ValueError('Changed manager relocation layout')
    rows=list(struct.unpack_from('>'+str(head[4])+'I',rel,20));hooks=[];removed=[]
    for hi,lo in MANAGER_POINTERS:
        pointer(owner,OWNER,hi,lo,0x809623D8,REFERENCES,hooks)
        # The old pointers moved with the overlay. The new storage is resident:
        # leaving either relocation here corrupts the destination when loaded.
        for address,kind in ((hi,5),(lo,6)):
            entry=0x40000000|kind<<24|(address-OWNER)
            if rows.count(entry)!=1:raise ValueError('Missing exact manager-pointer relocation')
            rows.remove(entry);removed.append(entry)
    pointer(owner,OWNER,0x8096503C,0x80965040,0x80139F98,DAYS,hooks)
    word(owner,OWNER,0x8096502C,0x2C640010,0x2C640000|DAY_CAPACITY,hooks,'camper uses expanded daily list')
    # Native code stores in the branch delay slot BEFORE rejecting count 32.
    # Use the already-current s1 control pointer and guard before any store.
    old=(0x00107940,0x028FC021,0x0002C880,0x02794021,0x28410020,
         0x10200003,0xAD180000,0x24490001,0xAE490000)
    new=(0x2C410000|REFERENCE_CAPACITY,0x10200007,0x0002C880,0x02794021,
         0xAD110000,0x24490001,0xAE490000,0,0)
    for i,(a,b) in enumerate(zip(old,new)):
        word(owner,OWNER,0x8096131C+i*4,a,b,hooks,'check manager capacity before writing')
    head[4]=len(rows)
    reloc=(struct.pack('>5I',*head)+struct.pack('>'+str(len(rows))+'I',*rows)).ljust(len(rel)-4,b'\0')+rel[-4:]
    if len(reloc)!=len(rel):raise ValueError('Unexpected manager relocation growth')
    allowed={i for h in hooks for i in range(h['address']-OWNER,h['address']-OWNER+4)}
    bases=(0x801A0010,0x802F8010)
    for address in bases:
        old_image=relocate_verified_data(SimpleNamespace(ram=OWNER,resident_bytes=len(before),
            sections=struct.unpack_from('>5I',rel)),before,rel,address)
        new_image=relocate_verified_data(SimpleNamespace(ram=OWNER,resident_bytes=len(owner),
            sections=tuple(head)),bytes(owner),reloc,address)
        if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(old_image,new_image))):
            raise ValueError('Event storage changes unrelated relocated manager code')
    return {VROM:bytes(owner),RELOC:reloc},dict(hooks=hooks,removed_relocations=removed,
        owner_sha256=sha256(owner),relocation_sha256=sha256(reloc),relocation_count=len(rows),
        relocation_test_bases=list(bases),today_pointer_capacity=REFERENCE_CAPACITY)


def install(base,prior,blob,core,output):
    if prior['equipment_resources']['npc_extra'].get('events',{}).get('native_directory'):
        from v3_holiday_placement import install as install_placement
        return install_placement(base,prior,blob,core,output)
    del blob
    equipment=copy.deepcopy(prior['equipment_resources']);npc=equipment['npc_extra']
    if not npc.get('events') or npc['events'].get('native_directory'):
        raise ValueError('Native directory requires installed source events without duplicate binding')
    physical.verify(base,prior['physical_resources'])
    packet=npc['packet'];data=bytearray(base[packet['physical']:packet['physical']+SIZE])
    if (len(data)!=SIZE or sha256(data)!=packet['sha256'] or
            0x7400+npc['events']['code']['bytes']>0x8300 or any(data[0x8300:0x9800]) or
            0xC000+npc['record']['slots']*npc['record']['slot_stride']>DAYS-RAM or
            any(data[DAYS-RAM:IDS-RAM+256])):
        raise ValueError('Changed holiday code/state reservations')
    ids,registry=identities();data[IDS-RAM:IDS-RAM+256]=ids
    exports=npc['events']['code']['symbols']
    bindings={name:exports[name] for name in ('af_holiday_event_plan','af_holiday_event_current',
        'af_holiday_event_field','af_holiday_event_cleanup')}
    bindings.update(af_holiday_native_days=DAYS,af_holiday_native_index=0x804A2B00,
        af_holiday_native_count=0x80104F98,af_holiday_native_ids=IDS,af_holiday_source_ids=IDS+128,
        af_holiday_event_data=RAM+0x9800,af_holiday_native_death=0x800814B8)
    directory=output/'holiday-native'
    code,compiled=compile_part('holiday_native',directory/'code',link_symbols=bindings)
    if len(code)>0x1500:raise ValueError('Native holiday code exceeds retained packet')
    data[0x8300:0x8300+len(code)]=code
    hooks=patch_core(core);owners,manager=patch_manager(base)
    calendar=copy.deepcopy(prior['campsite_calendar']);calendar['today_capacity']=DAY_CAPACITY
    manager_report=copy.deepcopy(prior['campsite_manager'])
    manager_report.update(today_pointer_capacity=REFERENCE_CAPACITY,output_sha256=manager['owner_sha256'],
        relocation_sha256=manager['relocation_sha256'],relocation_count=manager['relocation_count'])
    manager_report['native_directory']=manager
    replacement=next(copy.deepcopy(r) for r in prior['physical_resources'] if r['id']==packet['id'])
    previous=packet['sha256'];replacement['sha256']=sha256(data)
    records=[replacement if r['id']==replacement['id'] else copy.deepcopy(r) for r in prior['physical_resources']]
    packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
    npc['events']['native_directory']=dict(format='AFV3-HOLIDAY-NATIVE-1',code=compiled,
        identities=registry,identity_ram=IDS,identity_sha256=sha256(ids),identity_version=1,
        days_ram=DAYS,day_capacity=DAY_CAPACITY,manager_references_ram=REFERENCES,
        manager_reference_capacity=REFERENCE_CAPACITY,core_hooks=hooks,manager=manager,
        compiled_bridge_installed=True,native_storage_bound=True,native_schedule_caller_bound=False,
        native_actor_owners_bound=False,actor_active=False,native_execution_verified=False,
        saved_format_changed=False,additional_resident_bytes=0)
    npc['sources'].update({p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(directory/'directory.json',(json.dumps(npc['events']['native_directory'],indent=2)+'\n').encode())
    write_new(directory/'packet.bin',data)
    return equipment,owners,dict(physical_resources=records,campsite_calendar=calendar,
        campsite_manager=manager_report),[(dict(replacement,previous_sha256=previous),bytes(data))]
