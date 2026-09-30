"""Complete source April controller and the bank's borrowed live-clip adapter.

Construction requires the genuine native daily row and event save slot.
The linked manager/lifecycle adapters require enclosing cartridge installation.
"""
import re
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,u32
from v3_asset_loader import ROOT
from v3_holiday_participants import clean,constants,read
from v3_password_policy import function

REFERENCES={
    'src/actor/ac_aprilfool_control.c':'dde6d3b283758cc3c054b5e2c9d8c66570fe0264a4be1ecf7226e873e132280e',
    'include/ac_aprilfool_control.h':'3e37b4f6f2a1df1351aed93c388d5890ef0db73a0cc06d9dcd40b47a01f8c518',
    'include/ac_aprilfool_control_h.h':'65541b9f56ac21d972f49da081fe44784a42b72586fb3eb5cccf744d524a27f5',
    'include/m_actor.h':'faf1bfbbfa807f37cad98debad69360071e94c8e149af7f745c4ff5352171412',
    'include/m_name_table.h':'636228dda6f5a145a1c33f886d4d574e01cd460e0062dd7502d18db2a472e3cb',
    'include/m_event.h':'7d479a212f933197a93b1abc80dc356940fd682beaf375503477728c4a2ef2f6',
    'include/types.h':'e05027e9cfee0101ba42f025d55f6b28c69f842b14a301f7f9ed67167f759528',
    'include/m_private.h':'160ffd2557dfbb1442fd053f9b6ca12f8f192e4054a35ad726da2461a9dba8bd',
    'src/actor/ac_event_manager.c':'bb6f890571e68532d6edd8b741acc4975051b192f69b06a3863223552e2efe55',
}
FUNCTIONS=('aAPC_actor_ct','aAPC_actor_dt','aAPC_get_data_idx',
    'aAPC_talk_chk_proc','aAPC_talk_set_proc','aAPC_get_msg_num_proc')
NPCS=(0xD00E,0xD008,0xD06D,0xD070,0xD071,0xD00D,0xD010,0xD003,0xD012,0xD011,0xD072)
MESSAGES=(0x3BB5,0x3BAC,0x3BB0,0x3BB1,0x3BB2,0x3BB3,0x3BB4,0x3BAE,0x3BAF,0x3BAD,0x3BB6)
NATIVE_SERVICES={
    'af_bank_april_delete':(CODE_VROM,CODE_RAM,0x800567E8,24,
        'd0772f05c1eea44df9220576f516b75782baa311d11196db4f5867de06305647'),
    'af_bank_april_make':(CODE_VROM,CODE_RAM,0x80057E24,428,
        'df7e3f153b3dc51fb7ea11caeb714a0575ba791fdc8470a9f87d79cf1aa6c244'),
    'af_bank_april_native_set_status':(CODE_VROM,CODE_RAM,0x8007FDA8,204,
        'a83ce9302aa672d27bcb96368fb87388964771aefb73e470b4fc1bd7800aaccb'),
    'af_bank_april_native_clear_status':(CODE_VROM,CODE_RAM,0x8007FE74,148,
        '0990f6a96cb84d0965e07c8bf3ff97b9dc26888f37a4c6d03bd3912a16a4d6ec'),
    'af_bank_april_native_get':(CODE_VROM,CODE_RAM,0x8008033C,368,
        'e3f773780ce82da3b43a46975c07e1c0c37815fbc95bca00f3b00ce8869adec3'),
    'af_bank_april_native_reserve':(CODE_VROM,CODE_RAM,0x80080080,384,
        'bf96a81786bddfa774c104c56d1d5f6c5b9b8e316471578860fa6debfd12ae40'),
    'af_bank_april_native_dying':(CODE_VROM,CODE_RAM,0x800814B8,312,
        '72281c6c433ac10c4ff6242f0c613873d6af6e1a0c58c0a2dd7ed40c6fe635d0'),
    'af_bank_april_none':(CODE_VROM,CODE_RAM,0x8009AC74,8,
        'eaa4cc6ffee781be48a0e79ade7e6f121fcad300f9ec9172a3073da12f82f26d'),
    'af_bank_april_zero':(0x1060,0x80025C60,0x8002F4C0,160,
        '6cb49ba97859396e62e39990cd9a31a7a775d8e8b5618695b03027823a7b2863'),
}


def generate(source):
    receipts={};texts={p:read(p,receipts) for p in REFERENCES}
    if any(receipts[p]['sha256']!=digest for p,digest in REFERENCES.items()):
        raise ValueError('Changed complete source April controller reference')
    body=clean(texts['src/actor/ac_aprilfool_control.c'])
    body=re.sub(r'^\s*#include[^\n]*','',body,flags=re.M)
    names=re.findall(r'^static [\w *]+\b(aAPC_\w+)\([^;{}]*\)\s*\{',body,re.M)
    if tuple(names)!=FUNCTIONS:raise ValueError('Incomplete source April functions')
    rows=[]
    for name in names:
        matches=[at for at,entries in source.functions.items() if any(n==name for n,_ in entries)]
        if len(matches)!=1:raise ValueError('Ambiguous source April function: '+name)
        rows.append(source.function(matches[0])[1])
    offsets={r['offset'] for r in rows}
    if offsets!={at for at in source.functions if min(offsets)<=at<=max(offsets)}:
        raise ValueError('Incomplete contiguous April controller')
    tables=[]
    for symbol,expected in (('npc_data_table$387',b''.join(struct.pack('>HH',n,i) for i,n in enumerate(NPCS))),
            ('msg_num_table$417',struct.pack('>11I',*MESSAGES))):
        raw=source.raw(symbol);at,_=source.symbol(symbol)
        if raw!=expected:raise ValueError('Changed complete source April table: '+symbol)
        tables.append(dict(symbol=symbol,offset=at,bytes=len(raw),sha256=sha256(raw)))
    profile=source.raw('Aprilfool_Control_Profile')
    if len(profile)!=36 or sha256(profile)!='06dd85bfbef64349af37a4d3b476f090c13d5f4f227124ebecfce323e5d1ff6e':
        raise ValueError('Changed complete source April actor profile')
    # Preserve every constructor/destructor operation; silence genuinely unused
    # source parameters under the native compiler's checked warning policy.
    for name in FUNCTIONS[:2]:
        original=function(body,name);body=body.replace(original,original.replace('{','{\n    (void)game;',1))
    manager_text='\n'.join(function(texts['src/actor/ac_event_manager.c'],n)
        for n in ('make_control_actor','aprilfool_start','aprilfool_stop'))
    macros=constants(body+'\n'+manager_text,receipts,headers=tuple(p.removeprefix('include/')
        for p in REFERENCES if p.startswith('include/')))
    default='#define mActor_NONE_PROC1 ((mActor_proc)none_proc1)\n'
    if macros.count(default)!=1:raise ValueError('Changed source April default callback ABI')
    macros=macros.replace(default,'') # The adapter binds the same native no-op ABI.
    if any(receipts[p]['sha256']!=digest for p,digest in REFERENCES.items()):
        raise ValueError('Changed complete source April constants')
    from v3_campsite_event import SCHEDULE_SHA
    from v3_registry import BANK_APRIL_CONTROLLER
    schedule=source.raw('event_schedule_data')
    april_rows=[(i,schedule[i:i+12]) for i in range(0,len(schedule),12)
        if struct.unpack_from('>I',schedule,i+8)[0]==17]
    if (len(schedule)!=1608 or sha256(schedule)!=SCHEDULE_SHA or
            april_rows!=[(516,bytes.fromhex('040100000401001700000011'))] or
            BANK_APRIL_CONTROLLER!={'source_profile':232,'profile':246,'source_event':17,'event':117}):
        raise ValueError('Changed complete source April calendar or stable identity')
    manager=[];manager_rows=[]
    for at,name,digest in ((705552,'make_control_actor','5d931277389f68b3b598f532ecd17affd10268e3b3a4cd8cf51c8d85fd93bdd1'),
            (715156,'aprilfool_start','b393d1900dfe18ed7e3bfc0345aaf1d10f7806b93804e458d9a32ae862110a36'),
            (715292,'aprilfool_stop','8a367ffc3aa96f86a99c774cd7426d38aa87b89aeee1d06d259f85b0a42f7b3f')):
        _,receipt=source.function(at)
        if receipt['symbol']!=name or receipt['sha256']!=digest:
            raise ValueError('Changed complete source April manager function: '+name)
        manager_rows.append(receipt);manager.append(clean(function(texts['src/actor/ac_event_manager.c'],name)))
    manager='\n'.join(manager)
    for old,new in (('EVENT_MANAGER_ACTOR','AFBankAprilManagerView'),('aEvMgr_event_ctrl_c','AFHolidayControl'),
            ('&((GAME_PLAY*)gamePT)->actor_info','af_bank_april_actor_info(af_bank_april_game)'),
            ('gamePT','af_bank_april_game'),('Actor_info_make_actor','af_bank_april_make'),
            ('mAc_PROFILE_APRILFOOL_CONTROL','AF_BANK_APRIL_PROFILE'),
            ('mEv_clear_status','af_bank_april_clear_status'),('mEv_set_status','af_bank_april_set_status'),
            ('mEv_check_keep','af_bank_april_check_keep'),('mEv_set_keep','af_bank_april_set_keep'),
            ('mEv_clear_keep','af_bank_april_clear_keep')):
        manager=manager.replace(old,new)
    # Stop has a genuinely unused source manager argument.
    stop=function(manager,'aprilfool_stop')
    manager=manager.replace(stop,stop.replace('{','{\n    (void)evmgr;',1))
    row=april_rows[0][1]
    generated='#include "bank_april_manager.h"\n#include "april_constants.h"\n'+body+'\n'+manager+'\n'+\
        'const u8 af_bank_april_schedule[12]={'+','.join(str(n) for n in row)+'};\n'+\
        (ROOT/'overlays/v3/bank_april.c').read_text()
    return {'april_source.c':generated,'april_constants.h':macros},dict(
        format='AFV3-BANK-APRIL-1',references=receipts,functions=rows,tables=tables,
        profile_sha256=sha256(profile),source_type=17,native_type=117,actor_bytes=0x184,
        identity=BANK_APRIL_CONTROLLER,manager_functions=manager_rows,
        schedule=dict(offset=source.symbol('event_schedule_data')[0]+516,bytes=12,
            row_hex=row.hex(),sha256=sha256(row),table_sha256=SCHEDULE_SHA),
        saved_bytes=8,source_clip_bytes=16,borrowed_clip_bytes=8,
        npc_identities=list(NPCS),messages=list(MESSAGES),
        compiled=True,calendar_installed=False,actor_installed=False,player_clear_installed=False,
        text_installed=False,native_execution_verified=False)


def native_bindings(base,prior):
    files=by_vrom(base);bindings={};services={}
    for name,(vrom,ram,address,size,digest) in NATIVE_SERVICES.items():
        data=files[vrom].extract(base)[address-ram:address-ram+size]
        if len(data)!=size or sha256(data)!=digest:
            raise ValueError('Changed complete native April service: '+name)
        bindings[name]=address
        services[name]=dict(vrom=vrom,address=address,bytes=size,sha256=digest)
    core=files[CODE_VROM].extract(base)
    # The real reserve service uses the expanded day/index owners, not the old
    # native addresses. Bind only the actual guarded instruction destinations.
    for address,expected in ((0x8008009C,0x3C0E804A),(0x800800A4,0x91CE2B00),
            (0x800800A8,0x3C18806F),(0x800800AC,0x27181500)):
        if u32(core,address-CODE_RAM)!=expected:
            raise ValueError('Changed native April daily storage binding')
    bindings.update(af_holiday_native_index=0x804A2B00,af_holiday_native_days=0x806F1500,
        af_bank_april_native_slots=0x80135CE0,af_bank_april_game=0x8010EF90)
    # Delegate through the authenticated current registry chain. Replacing only
    # the native caller leaves this older public entry intact and non-recursive.
    from v3_import_storage import jump
    harvest=prior['equipment_resources']['harvest'];quest=prior['equipment_resources']['carried_items']['quest']
    retained=[]
    participants=prior['equipment_resources']['npc_extra']['events']['participants']
    for owner in (harvest,quest,participants):
        packet=owner['packet'];raw=base[packet['physical']:packet['physical']+packet['bytes']]
        if len(raw)!=packet['bytes'] or sha256(raw)!=packet['sha256']:
            raise ValueError('Changed complete retained April calendar/registry packet')
        retained.append(dict(packet=packet))
    hs=harvest['code']['symbols'];qs=quest['code']['symbols']
    descriptor=participants['code']['symbols']['af_hp_descriptor']
    packet=participants['packet']
    if (not packet['ram']<=descriptor<descriptor+8<=packet['ram']+packet['bytes'] or
            core[0x80057E4C-CODE_RAM:0x80057E54-CODE_RAM]!=struct.pack('>II',jump(descriptor,link=True),0x00C02025) or
            core[0x8007F630-CODE_RAM:0x8007F638-CODE_RAM]!=struct.pack('>II',jump(hs['af_hr_calendar_before_cleanup'],link=True),0)):
        raise ValueError('Changed complete installed April registry/calendar chain')
    bindings.update(af_bank_april_previous_descriptor=descriptor,
        af_bank_april_prior_calendar=hs['af_hr_calendar_before_cleanup'],
        af_bank_april_native_rtc=qs['af_cw_native_rtc'],
        af_holiday_native_append=qs['af_holiday_native_append'])
    return bindings,dict(services=services,retained_owners=retained,
        globals={n:a for n,a in bindings.items() if n not in services},
        calendar_installed=False,actor_installed=False)
