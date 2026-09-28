"""Complete shared fishing records, normalized storage, and source algorithms.

Generated donor code stays local. Preparation does not enable an event, replace
the native tournament, or claim that the save envelope already stores records.
"""
import copy
import json
import re
import subprocess
import struct
import zlib
from pathlib import Path

from aflib import by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_password_policy import function

RAM,SIZE,STATE=0x80730000,0x8000,0x7C00
GUARD=bytes.fromhex('41464846')*4
MESSAGE_FIRST,CHOICE_FIRST=0x3061,515

REFERENCES={
    'src/game/m_fishrecord.c':'bc732633475940b258dbe5b7d5bee64e2e31703192d5f6aba24097a003dcdae6',
    'src/lb_rtc.c':'fa3dc7d1f1f6f976b8e2b03c198c4f91e40bb2d614889a236a11f66eefa02ff0',
    'src/game/m_time.c':'c10ba8af934c1c167e18bd033ef74c5b52fff73df4ef119eaddea24a06805dc9',
    'include/m_personal_id.h':'60ccaa269801fb549681feb24b263e7e7b72cba93828a4cc85550b35ff6e2c21',
}
ROOTS={
    'mEv_fishRecord_set':'af_hf_source_set','mFR_fish_rndsize':'af_hf_source_size',
    'mFR_make_NpcRecord':'af_hf_source_npc_size','mEv_fishRecord_holder':'af_hf_source_holder',
    'mEv_fishday':'af_hf_source_dates','mFR_delete_after_record':'af_hf_source_delete_after',
    'mFR_delete_npc_record':'af_hf_source_delete_npc','mFR_fishRecord_last_holder':'af_hf_source_finalize',
    'mFR_sort_record':'af_hf_source_sort',
}
SOURCES=('tools/v3_holiday_fishing.py','overlays/v3/holiday_fishing.c',
    'overlays/v3/holiday_fishing.h','overlays/v3/holiday_fishing.ld','tools/v3_asset_loader.py',
    'overlays/v3/console_storage.c','overlays/v3/console_storage.h',
    'overlays/v3/save_compressed.c','overlays/v3/save_compressed.h',
    'tools/v3_room_goods.py','tools/v3_furniture_install.py','overlays/v3/surface_bootstrap.c')
PRELUDE='''#include "/source/overlays/v3/holiday_fishing.h"
#pragma GCC diagnostic ignored "-Wunused-parameter"
typedef AFHFB u8;typedef unsigned int u32;typedef unsigned short mActor_name_t;
typedef float f32;typedef unsigned char lbRTC_hour_t,lbRTC_month_t;typedef unsigned short lbRTC_year_t;
typedef AFHFPerson PersonalID_c;typedef AFHFTime lbRTC_time_c;
typedef AFDiaryDate lbRTC_ymd_c;typedef AFHFRecord mFR_record_c;
#define TRUE 1
#define FALSE 0
#define NULL ((void*)0)
#define ANIMAL_NAME_LEN 8
#define mFR_RECORD_NUM 5
enum {mFR_SIZE_SMALL,mFR_SIZE_MEDIUM,mFR_SIZE_LARGE};
enum {lbRTC_LESS=-1,lbRTC_EQUAL=0,lbRTC_OVER=1,lbRTC_WEEK=7,lbRTC_JUNE=6,lbRTC_NOVEMBER=11};
#define Save_Get(x) (ctx->x)
#define Save_GetPointer(x) (&ctx->x)
#define Common_GetPointer(x) (&ctx->x)
#define fqrand() af_hf_random(ctx)
#define RANDOM(n) ((int)(fqrand()*(n)))
#define mPr_GetPrivateIdx(p) ctx->services.player_index(ctx->opaque,p)
#define mEvMN_GetJointEventRandomNpc(p) ctx->services.event_npc(ctx->opaque,p)
#define mNpc_GetNpcWorldNameTableNo(p,n) ctx->services.npc_name(ctx->opaque,p,n)
#define mNpc_GetRandomAnimalName(p) ctx->services.random_name(ctx->opaque,p)
#define mPr_CopyPersonalID(p,q) (*(p)=*(q))
#define mPr_ClearPersonalID(p) af_hf_person_clear(p)
#define mLd_ClearLandName(p) af_hf_clear(p,8,32)
#define mem_clear af_hf_clear
#define mem_copy af_hf_copy
#define bcopy(p,q,n) af_hf_copy(q,p,n)
#define lbRTC_TimeCopy(p,q) (*(p)=*(q))
#define lbRTC_IsEqualDate af_hf_date_compare
#define lbRTC_IsOverTime af_hf_time_compare
#define lbRTC_GetDaysByMonth(y,m) ((unsigned char)af_diary_days(y,m))
#define lbRTC_Week(y,m,d) af_diary_weekday((AFDiaryDate){y,m,d})
#define lbRTC_Add_mm af_hf_add_minutes
#define lbRTC_Add_hh(t,n) af_hf_add_minutes(t,(n)*60)
#define lbRTC_Sub_YY af_hf_sub_year
#define mTM_set_renew_time(p,t) (*(p)=(AFDiaryDate){(t)->year,(t)->month,(t)->day})
'''


def dialogue(base):
    """Convert the complete controller-selected conversation and branch closure."""
    from gc_adapter import remove_redundant_article_suppression
    from gc_text import decode_gc
    from runtime_module import module_command_info
    from textcodec import encode,tokenize,LATIN
    from textvalidate import expanded_bound
    from v3_camper_text import donor,DONOR_FILES
    from v3_holiday_dialogue import credit
    root=ROOT/'local/ac-decomp'
    paths=('src/actor/ac_turi_clip.c_inc','src/actor/npc/event/ac_ev_angler_move.c_inc')
    sources={p:(root/p).read_text() for p in paths}
    clip=sources[paths[0]];angler=sources[paths[1]]
    selector=function(clip,'aTRC_clip_get_msgno')
    cases=re.findall(r'case ITM_FISH(\d+):\s*return (0x[0-9A-Fa-f]+);',selector)
    if [int(n) for n,_ in cases]!=list(range(40)):
        raise ValueError('Changed complete forty-fish message selector')
    fish=[int(n,16) for _,n in cases]
    roots=set(fish)|{int(n,16) for n in re.findall(r'return (0x[0-9A-Fa-f]+);',selector)}
    roots.update(int(n,16) for n in re.findall(r'(?:msg_no\s*=|return|case)\s*(0x[0-9A-Fa-f]+)',angler))
    # The source bass result readers add one/two to the entry-message number.
    for name,delta in (('get_message_number_fish_zannen',1),('get_message_number_fish_omedeto',2)):
        body=function(angler,name)
        if f'return aTRC_clip_get_msgno(item) + {delta};' not in body:
            raise ValueError('Changed bass result-message arithmetic')
        roots.update(fish[i]+delta for i in (5,6,7))
    messages,choices,decoder=donor();info=module_command_info(base)
    pending=set(roots);ready={};edits={};selects=set();orders=set()
    allowed={0,1,2,3,4,5,9,13,14,15,16,22,25,36,37,38,49,80,83,84,94,114,115}
    while pending:
        n=min(pending);pending.remove(n)
        if not 0<=n<len(messages):raise ValueError('Fishing branch escapes donor bank')
        text,edits[n]=remove_redundant_article_suppression(decode_gc(messages[n],decoder))
        data=encode(text,info);tokens=list(tokenize(data,info))
        if (not tokens or tokens[-1].data not in (b'\x7f\0',b'\x7f\1') or
                sum(t.kind=='cmd' and t.data[1] in (0,1) for t in tokens)!=1 or
                any(t.kind!='cmd' and (t.kind!='text' or t.data[0] not in LATIN|{0xCD}) for t in tokens) or
                any(t.kind=='cmd' and t.data[1] not in allowed for t in tokens) or expanded_bound(data,info)>1024):
            raise ValueError(f'Unreviewed fishing text/control/buffer bound: {n:04X}')
        ready[n]=data
        for t in tokens:
            if t.kind!='cmd':continue
            op=t.data[1]
            if op==9:
                index,value=t.data[2],int.from_bytes(t.data[3:],'big')
                if not (index==0 and value in {*range(1,24),255} or
                        index==1 and value in (2,10,11,12,14) or index==9 and 1<=value<=4):
                    raise ValueError('Unreviewed fishing NPC demo order')
                orders.add((index,value))
            if 14<=op<=24:
                refs=struct.unpack('>'+'H'*((len(t.data)-2)//2),t.data[2:])
                if op<=21:pending.update(set(refs)-ready.keys())
                else:selects.update(refs)
    if sorted(ready)!=[*range(0x10E8,0x1124),*range(0x17E5,0x17EB),*range(0x2FAF,0x2FB7)]:
        raise ValueError('Changed complete fishing conversation closure')
    if sorted(selects)!=[0xB,0x18,0x30,0x44,0xE2,0xE5,0xE6]:
        raise ValueError('Changed complete fishing choices')
    mapping={n:MESSAGE_FIRST+i for i,n in enumerate(sorted(ready))}
    choice_map={n:CHOICE_FIRST+i for i,n in enumerate(sorted(selects))}
    rows=[];extra=[];new_choices=[];choice_rows=[];credits=[]
    def attribution(identity,n,original,data,adaptations):
        row=credit(identity,n,original,data,adaptations)
        row['locales']['en']['locator']=['tools/v3_holiday_fishing.py:dialogue',identity]
        return row
    for n,data in sorted(ready.items()):
        out=bytearray(data)
        for t in tokenize(data,info):
            if t.kind=='cmd' and 14<=t.data[1]<=24:
                refs=mapping if t.data[1]<=21 else choice_map
                for at in range(2,len(t.data),2):
                    struct.pack_into('>H',out,t.offset+at,refs[int.from_bytes(t.data[at:at+2],'big')])
        out=bytes(out);extra.append(out)
        adaptations=['Native encoding; preserve official wording, pages, pauses, formatting, and handover controls',
                     'Remap the complete message/choice graph to stable additive native IDs']
        if edits[n]:adaptations.append('Remove redundant article-suppression flags before native string insertions')
        credits.append(attribution(f'message:{mapping[n]:04X}',f'message:{n:04X}',messages[n],out,adaptations))
        rows.append(dict(donor_id=n,id=mapping[n],source_sha256=sha256(messages[n]),
            sha256=sha256(out),bytes=len(out),expanded_bound=expanded_bound(out,info)))
    for n,target in choice_map.items():
        data=encode(decode_gc(choices[n],decoder),info)
        if not 1<=len(data)<=20 or any(c not in LATIN for c in data):raise ValueError('Invalid fishing choice')
        new_choices.append(data);choice_rows.append(dict(donor_id=n,id=target,bytes=len(data),sha256=sha256(data)))
        credits.append(attribution(f'select:{target:04X}',f'select:{n:04X}',choices[n],data,
            ['Native encoding; unchanged official choice']))
    from textbanks import Bank
    from v3_holiday_dialogue import STRING_FILES
    directory=ROOT/'build/gamecube/files/forest_1st.arc.unpacked/data'
    strings={n:(directory/n).read_bytes() for n in STRING_FILES}
    if any(sha256(data)!=STRING_FILES[n] for n,data in strings.items()):raise ValueError('Changed donor units bank')
    bank=Bank('string',0,0,strings['string_data.bin'],strings['string_data_table.bin']).entries()
    inches=encode(decode_gc(bank[0x29E],decoder),info)
    from aflib import CODE_RAM,CODE_VROM
    files=by_vrom(base);core=files[CODE_VROM].extract(base)
    hi,lo=struct.unpack_from('>2I',core,0x800C3F1C-CODE_RAM)
    if hi>>16!=0x3C18 or lo>>16!=0x2718:raise ValueError('Changed complete native unit bank reader')
    vrom=((hi&65535)<<16)+((lo&32767)-(lo&32768))
    cm=Bank('string',0,0,files[vrom].extract(base),files[0xD18000].extract(base)).entries()[0x29E]
    if cm!=b'cm' or inches!=b'inches':raise ValueError('Changed official measurement labels')
    credits.append(attribution('v3/fishing/unit/inches','string:029E',bank[0x29E],inches,
        ['Native encoding; unchanged official measurement label']))
    credits.append(dict(id='v3/fishing/unit/cm',native_sha256=sha256(cm),locales=dict(en=dict(
        credit='original',locator=['tools/v3_holiday_fishing.py:dialogue','N64/string/029E'],
        encoded_sha256=sha256(cm)))))
    return extra,new_choices,dict(first_id=MESSAGE_FIRST,count=len(extra),first_choice=CHOICE_FIRST,
        choice_count=len(new_choices),rows=rows,choices=choice_rows,roots=sorted(roots),
        fish_messages=[dict(source_index=i,donor_id=n,id=mapping[n]) for i,n in enumerate(fish)],
        mapping=mapping,default_message=mapping[0x10F2],npc_orders=sorted(orders),
        max_expanded_bytes=max(r['expanded_bound'] for r in rows),source_banks={**DONOR_FILES,**STRING_FILES},
        units=[cm.hex(),inches.hex()],
        source_files={p:sha256(s.encode()) for p,s in sources.items()},provenance_entries=credits)


def prepare_live(base,prior,output):
    """Link all record/name/size/text providers against the installed storage."""
    from aflib import CODE_RAM,CODE_VROM
    from v3_furniture_effect_rigs import checked_native
    output=output.resolve()
    fishing=prior['equipment_resources']['holiday_fishing']
    if not fishing['storage_installed'] or fishing['loaded_code']['bytes']>0x4000:
        raise ValueError('Live fishing readers require retained storage below their reservation')
    packet=fishing['packet'];raw=base[packet['physical']:packet['physical']+packet['bytes']]
    at=0x80734000-packet['ram']
    if sha256(raw)!=packet['sha256'] or any(raw[at:-16]):
        raise ValueError('Occupied fishing reader/state reservation')
    output.mkdir(parents=True,exist_ok=False)
    messages,choices,text=dialogue(base)
    mapping='const unsigned short af_hf_message_map[][2] = {'+','.join(
        '{'+str(n)+','+str(target)+'}' for n,target in text['mapping'].items())+'};\n'
    mapping+='const unsigned int af_hf_message_count = 74;\n'
    mapping+='const unsigned char af_hf_unit_text[2][16] = {'+','.join(
        '{'+','.join(str(c) for c in bytes.fromhex(value))+'}' for value in text['units'])+'};\n'
    generated=output/'text-map.c';write_new(generated,mapping.encode())
    native=(
        ('af_hf_native_event_area',0x8008033C,0x800804AC,'e3f773780ce82da3b43a46975c07e1c0c37815fbc95bca00f3b00ce8869adec3'),
        ('af_hf_native_event_npc',0x80082DA0,0x80082E40,'7320c27a330d9a1af4abd372c83a41c1bdc315ddab337547630c3472276339c1'),
        ('af_hf_native_window',0x8009D1F0,0x8009D200,'e4e54e5f3fc74caca37c6c0fdda0b5684e6e68d753495d23a868e75faf6af1f3'),
        ('random resident selection',0x800ACE90,0x800ACF84,'4b884aa4eb36432b9c7f5be2b2fb8cfcfe7880d17bf673ded51074d4315c242b'))
    core=by_vrom(base)[CODE_VROM].extract(base);checked_native(base)
    for name,a,b,digest in native:
        if sha256(core[a-CODE_RAM:b-CODE_RAM])!=digest:raise ValueError('Changed complete native fishing provider: '+name)
    bindings={n:v for n,v in fishing['code']['symbols'].items()
        if n.startswith(('af_holiday_fish_','af_hf_')) or n in ('af_v3_fishing_data','memcpy')}
    bindings.update({n:a for n,a,_,_ in native if n.startswith('af_')})
    bindings.update(af_hf_live=RAM+STATE+AFHF_BYTES,af_hf_controller_person=0x8070501C,af_hf_native_clock=0x80136FBC,
        af_hf_native_player=0x80136FD8,af_hf_native_players=0x80126EC0,
        af_hf_native_animals=0x80130DB8,af_hf_native_random=0x8002C9AC,
        af_hf_native_name=prior['villager_text']['code']['symbols']['af_v3_load_name'],
        af_hf_native_string=0x8009D6D0)
    try:
        code,compiled=compile_part('holiday_fishing_live',output/'code',
            extra_sources=(str(generated.relative_to(ROOT)),),link_symbols=bindings)
    except subprocess.CalledProcessError as error:raise ValueError(error.stderr) from error
    report=dict(text=text,code=compiled,bindings=bindings,
        native_functions=[dict(symbol=n,start=a,end=b,sha256=s) for n,a,b,s in native],
        installed=False,actors_active=False,native_execution_verified=False,
        memory=dict(code=dict(ram=0x80734000,bytes=0x3C00),state=dict(ram=RAM+STATE+AFHF_BYTES,bytes=768)),
        pending=['controller enter/leave and native angler/clip bindings','winner mail',
            'measurement/calendar selection and activation'])
    write_new(output/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
    for label,rows in (('messages',messages),('choices',choices)):
        write_new(output/(label+'.json'),(json.dumps([d.hex() for d in rows])+'\n').encode())
    return report


AFHF_BYTES=176


def install_live(base,prior,blob,core,output):
    from aflib import CODE_RAM,CODE_VROM,u32
    from v3_decoration_actor import install as controllers
    from v3_camper_text import extend_bank
    from v3_event_text import MESSAGE,TABLE,CHOICE_TABLE,patch_bounds
    from v3_holiday_dialogue import check_provenance
    del blob
    if prior['equipment_resources']['holiday_fishing'].get('live'):
        raise ValueError('Fishing live providers are already installed')
    directory=output/'fishing-live'
    live=prepare_live(base,prior,directory);text=live['text'];check_provenance(text)
    equipment,changes,updates,writes=controllers(base,prior,output,fishing_live=live)
    # The controller owns native descriptor hooks in the same core as the text
    # readers. Merge those edits into the shared buffer; a separate full-core
    # replacement would overwrite this installation's new reader bounds.
    previous_core=by_vrom(base)[CODE_VROM].extract(base)
    controller_core=changes.pop(CODE_VROM)
    if len(controller_core)!=len(previous_core) or len(core)!=len(previous_core):
        raise ValueError('Changed native core extent during controller refresh')
    for at in range(0,len(previous_core),4):
        before,after=previous_core[at:at+4],controller_core[at:at+4]
        if before!=after:
            if core[at:at+4] not in (before,after):
                raise ValueError('Controller refresh conflicts with another native core edit')
            core[at:at+4]=after
    if len(writes)!=1:raise ValueError('Controller refresh must retain the single holiday packet')
    resource,raw=writes[0];raw=bytearray(raw);fish=equipment['holiday_fishing'];packet=fish['packet']
    code=(directory/'code/code.bin').read_bytes();at=0x80734000-packet['ram']
    if any(raw[at:at+len(code)]):raise ValueError('Occupied live fishing code allocation')
    raw[at:at+len(code)]=code
    # Storage installation combines the entire old holiday packet and the new
    # fishing code under one startup descriptor. Retire only that proven complete
    # duplicate, leaving every prior cartridge file untouched on disk.
    old=prior['equipment_resources']['holiday_fishing']['input_packet']
    previous=next(r for r in updates['physical_resources'] if r['id']==old['id'])
    original=base[old['physical']:old['physical']+old['bytes']]
    current=prior['equipment_resources']['holiday_fishing']['packet']
    from v3_asset_loader import BLOB
    boot=prior['equipment_resources']['surface_bootstrap']['code']
    e=prior['equipment_resources'];resident=by_vrom(base)[BLOB].extract(base)
    table=e['blob_offset']+boot['symbols']['packets']-e['ram']
    descriptors=[struct.unpack_from('>5I',resident,table+i*20) for i in range(18)]
    if (old['id']!='holiday-decoration-actors-GAFE01-r0' or old['ram']!=current['ram'] or
            old['bytes']!=prior['equipment_resources']['holiday_fishing']['preserved_prefix_bytes'] or
            sha256(original)!=old['sha256'] or previous['sha256']!=old['sha256'] or
            base[current['physical']:current['physical']+len(original)]!=original or
            any(p&0x80000000 and (p&0x7FFFFFFF)<old['physical']+old['bytes']
                and old['physical']<(p&0x7FFFFFFF)+n
                for _,p,n,_,_ in descriptors) or
            descriptors[17][:3]!=(current['ram'],current['physical']|0x80000000,current['bytes'])):
        raise ValueError('Superseded holiday packet is not a complete unloaded duplicate')
    live['retired_duplicate']=copy.deepcopy(previous)
    updates['physical_resources']=[r for r in updates['physical_resources'] if r['id']!=old['id']]
    text['choice_vrom']=prior['import_storage']['choice_vrom'];text['hooks']=patch_bounds(core,MESSAGE_FIRST,text['count'])
    for a,op in ((0x80065544,0x2A010000),(0x80065DAC,0x28810000)):
        if u32(core,a-CODE_RAM)!=op|CHOICE_FIRST:raise ValueError('Changed fishing choice predecessor')
        after=op|(CHOICE_FIRST+text['choice_count']);struct.pack_into('>I',core,a-CODE_RAM,after)
        text['hooks'].append(dict(address=a,before=op|CHOICE_FIRST,after=after))
    messages=[bytes.fromhex(s) for s in json.loads((directory/'messages.json').read_bytes())]
    choices=[bytes.fromhex(s) for s in json.loads((directory/'choices.json').read_bytes())]
    files=by_vrom(base);cv=text['choice_vrom']
    new_m,new_t=extend_bank(files[MESSAGE].extract(base),files[TABLE].extract(base),messages,MESSAGE_FIRST)
    new_c,new_ct=extend_bank(files[cv].extract(base),files[CHOICE_TABLE].extract(base),choices,CHOICE_FIRST)
    text['resources']=[]
    for v,data in ((MESSAGE,new_m),(TABLE,new_t),(cv,new_c),(CHOICE_TABLE,new_ct)):
        filename=f'fishing-live/text-{v:08X}.bin';write_new(output/filename,data)
        text['resources'].append(dict(vrom=v,file=filename,bytes=len(data),sha256=sha256(data),
            original_sha256=sha256(files[v].extract(base))))
    packet.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    equipment['holiday_state']['packet']=copy.deepcopy(packet)
    resource.update(sha256=packet['sha256'])
    for r in updates['physical_resources']:
        if r['id']==packet['id']:r['sha256']=packet['sha256']
    live.update(installed=True,services_installed=True,service_admission=False,
        loaded_code=dict(ram=0x80734000,bytes=len(code),sha256=sha256(code)),
        sources={s:sha256((ROOT/s).read_bytes()) for s in (
            'tools/v3_holiday_fishing.py','tools/v3_decoration_actor.py','tools/v3_holiday_dialogue.py',
            'tools/v3_event_text.py','tools/v3_resource_capacity.py',
            'overlays/v3/holiday_fishing_live.c','overlays/v3/holiday_fishing_live.h',
            'overlays/v3/holiday_fishing_live.ld','overlays/v3/decoration_actor.c','overlays/v3/decoration_actor.h',
            'translations/provenance.json')})
    live['pending']=['native angler/clip and winner-mail bindings','measurement/calendar selection and event activation']
    # The controller refresh retains the original fishing core, not the region
    # deliberately filled by this connected provider installation.
    controller=equipment['npc_extra']['events']['decorations']['controllers']
    controller['preserved']=[r for r in controller['preserved'] if r['ram']!=RAM]
    controller['preserved'].append(dict(ram=RAM,bytes=0x4000,sha256=sha256(raw[RAM-packet['ram']:at])))
    fish['live']=live
    fish['pending']=['native angler/clip and winner-mail consumers',
        'measurement/calendar WebUI choice and event activation','connected native gameplay/save verification']
    controller['pending']=copy.deepcopy(fish['pending'])+['Harvest profile/save admission and exercise-card menus']
    equipment['npc_extra']['sources'].update(live['sources'])
    write_new(directory/'installed.json',(json.dumps(live,indent=2)+'\n').encode())
    write_new(directory/'packet.bin',raw)
    return equipment,changes,updates,[(resource,bytes(raw))]


def generate(source,directory):
    refs={}
    for name,digest in REFERENCES.items():
        data=(ROOT/'local/ac-decomp'/name).read_bytes()
        if sha256(data)!=digest:raise ValueError('Changed complete fishing reference: '+name)
        refs[name]=digest
    text=(ROOT/'local/ac-decomp/src/game/m_fishrecord.c').read_text()
    text=re.sub(r'/\*.*?\*/|//[^\n]*','',text,flags=re.S)
    found=list(re.finditer(r'(?:extern|static)\s+[^;{}]*?\b(\w+)\s*\([^;{}]*\)\s*\{',text))
    functions={m[1]:function(text,m[1]) for m in found}
    used=set(ROOTS);pending=list(ROOTS)
    while pending:
        name=pending.pop()
        for call in re.findall(r'\b(\w+)\s*\(',functions[name].split('{',1)[1]):
            if call in functions and call not in used:used.add(call);pending.append(call)
    names={n:ROOTS.get(n,'af_hf_donor_'+n) for n in used}
    functions={n:f for n,f in functions.items() if n in used}
    declarations=[];bodies=[];receipts=[]
    for name,body in functions.items():
        address=int(re.search(r'^'+re.escape(name)+r' = \.text:0x([0-9A-Fa-f]+);',source.symbols,re.M)[1],16)
        code,receipt=source.function(address)
        receipt.update(source_function_sha256=sha256(body.encode()),sha256=sha256(code));receipts.append(receipt)
        head,body=body.split('{',1)
        match=re.fullmatch(r'\s*(static|extern)\s+(.+?)\b'+name+r'\s*\((.*?)\)\s*',head,re.S)
        if not match:raise ValueError('Unsupported complete fishing signature: '+name)
        params=match[3].strip();params='' if params=='void' else params
        signature=('extern' if name in ROOTS else 'static')+' '+match[2]+names[name]+'(AFHolidayFish *ctx'+(', '+params if params else '')+')'
        for old,new in names.items():
            body=re.sub(r'\b'+re.escape(old)+r'\s*\(\s*',new+'(ctx, ',body)
        body=body.replace('(ctx, )','(ctx)')
        if name=='mEv_fishday_day':
            if body.count('static lbRTC_ymd_c ymd;')!=1:raise ValueError('Changed static fishing date')
            body=body.replace('static lbRTC_ymd_c ymd;','lbRTC_ymd_c *ymd = &ctx->scratch_day;')
            body=body.replace('ymd.','ymd->').replace('return &ymd;','return ymd;')
        if name=='mFR_fish_rndsize':
            if body.count('/ 2.54f')!=3:raise ValueError('Changed source measurement rules')
            body=body.replace('/ 2.54f','/ (ctx->units==AF_HF_INCHES ? 2.54f : 1.0f)')
        body=body.replace('static u8 l_name[]','static const u8 l_name[]')
        declarations.append(signature+';');bodies.append(signature+'{'+body)
    data=(PRELUDE+'\n'.join(declarations)+'\n'+'\n\n'.join(bodies)+'\n').encode()
    path=directory/'source-records.c';write_new(path,data)
    return path,dict(functions=receipts,references=refs,source_rel_sha256=sha256(source.rel),
        source_symbols_sha256=sha256(source.symbols.encode()),generated_sha256=sha256(data),
        source_functions=len(functions),record_count=5,record_bytes=32,serialized_bytes=176,
        source_date_static_moved_to_context=True,source_units_divisor=2.54,
        retained_source_quirks=['holder1 uses record zero for its player-wins branch',
            'sort retains the donor repeated nonzero-record predicate',
            'IsOverTime returns OVER for identical timestamps'],
        pending=['native event providers and complete message identities',
            'saved envelope/profile and WebUI measurement choice','winner-mail delivery and live actor activation'])


def prepare(base,prior,output):
    from v3_console_disk_install import reservations
    if any(a<RAM+SIZE and RAM<b for a,b in reservations(prior)):
        raise ValueError('Fishing code/state overlaps a retained RAM allocation')
    output.mkdir(parents=True,exist_ok=False)
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    generated,report=generate(source,output)
    native=by_vrom(base)[0x3B40000].extract(base)
    if sha256(native[0x23C:0x2FC])!='1e8d4a9aa49b0466a23eabc678c3cc414bceaa04150da330d0f096fd884f1c51':
        raise ValueError('Changed complete native fishing size formula')
    # The complete retained native size function has the same three formulae,
    # without the donor's inches divisor. It is not replaced by this preparation.
    report['native_size_function']=dict(vrom=0x3B40000,start=0x80A8FF2C,end=0x80A8FFEC,
        sha256=sha256(native[0x23C:0x2FC]))
    symbols=prior['equipment_resources']['npc_extra']['world']['code']['symbols']
    bindings={n:symbols[n] for n in ('af_diary_days','af_diary_weekday')}
    holiday=prior['equipment_resources']['holiday_state']
    bindings.update({n:holiday['code']['symbols'][n] for n in
        ('af_diary_reset','af_diary_valid','af_diary_upgrade','af_diary_player_clear')})
    bindings.update({n:holiday['bindings'][n] for n in ('af_v3_require_save_state',
        'af_v3_save_halt','af_v3_save_check_extended','af_v3_save_pack_extended','af_v3_creature_player_clear')})
    bindings['af_v3_fishing_state']=RAM+STATE
    flags=prior['equipment_resources']['diaries']['compiled']['flags']
    defines=tuple(f[2:] for f in flags if f.startswith('-D'))+(
        'AF_V3_HOLIDAY_STORAGE=1','AF_V3_FISHING_STORAGE=1')
    try:
        code,compiled=compile_part('holiday_fishing',output/'code',
            extra_sources=(str(generated.relative_to(ROOT)),
                'overlays/v3/console_storage.c','overlays/v3/save_compressed.c'),
            defines=defines,link_symbols=bindings)
    except subprocess.CalledProcessError as error:
        raise ValueError(error.stderr) from error
    report.update(code=compiled,bindings=bindings,
        memory=dict(code=dict(ram=RAM,bytes=STATE),state=dict(ram=RAM+STATE,bytes=SIZE-STATE)),
        source_files={s:sha256((ROOT/s).read_bytes()) for s in SOURCES},
        installed=False,native_execution_verified=False,saved_format_changed=False)
    write_new(output/'prepared.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def install(base,prior,blob,core,output):
    """Bind the complete storage path without enabling unfinished live events."""
    del blob,core
    from v3_console_disk_install import reservations
    from v3_import_storage import jump,replace_checked
    import v3_physical_resources as physical
    equipment=copy.deepcopy(prior['equipment_resources'])
    if equipment.get('holiday_fishing') or prior['save_codec']['format_version']!=12:
        raise ValueError('Fishing storage requires the current format-twelve proposal')
    diary=equipment['diaries'];holiday=equipment['holiday_state']
    memory=diary['memory']['scratch'];scratch_end=memory['ram']+memory['bytes']
    if memory!={'ram':0x80682000,'bytes':120128} or any(
            a<scratch_end+176 and scratch_end<b for a,b in reservations(prior)):
        raise ValueError('Fishing scratch extension overlaps retained memory')
    directory=output/'holiday-fishing'
    report=prepare(base,prior,directory)
    code=(directory/'code/code.bin').read_bytes()
    raw=code.ljust(SIZE-16,b'\0')+GUARD
    if len(raw)!=SIZE or len(code)>STATE:raise ValueError('Fishing packet exceeds reservation')
    resources=copy.deepcopy(prior['physical_resources']);physical.verify(base,resources)
    writes=[];prefix=None
    compiled=report['code'];redirects=[]
    # Both the original diary entry points and the directly linked holiday
    # counterparts must reach the new storage adapter. Existing callers keep
    # their addresses; no UI, creature, or FlashRAM owner is silently bypassed.
    for label,packet,old in (('diary',diary['packets']['storage'],diary['compiled']),
                            ('holiday',holiday['packet'],holiday['code'])):
        data=bytearray(base[packet['physical']:packet['physical']+packet['bytes']])
        if sha256(data)!=packet['sha256'] or sha256(data[:old['bytes']])!=old['sha256']:
            raise ValueError('Changed complete '+label+' storage owner')
        start=packet['ram'];symbols=old['symbols']
        addresses=sorted({v for v in symbols.values() if start<=v<start+old['bytes']})
        for name,target in compiled['symbols'].items():
            if not name.startswith('af_v3_') or name not in symbols or not RAM<=target<RAM+len(code):continue
            address=symbols[name]
            if not start<=address<start+old['bytes']:continue
            after=next((v for v in addresses if v>address),start+old['bytes'])
            if after-address<8:raise ValueError('Storage entry too short to redirect: '+name)
            at=address-start;before=bytes(data[at:at+8]);replacement=struct.pack('>2I',jump(target),0)
            if label=='diary':
                previous=next(r for r in old['holiday_redirects'] if r['name']==name)
                if before.hex()!=previous['after']:raise ValueError('Changed prior holiday storage redirect')
                previous.update(target=target,after=replacement.hex())
            replace_checked(data,at,before,replacement)
            redirects.append(dict(owner=label,name=name,address=address,target=target,
                before=before.hex(),after=replacement.hex()))
        previous_sha=packet['sha256'];packet.update(sha256=sha256(data),crc32=zlib.crc32(data))
        resources=[dict(r,sha256=packet['sha256']) if r['id']==packet['id'] else r for r in resources]
        write=dict(next(r for r in resources if r['id']==packet['id']),previous_sha256=previous_sha)
        writes.append((write,bytes(data)))
        old.update(sha256=sha256(data[:old['bytes']]),fishing_redirects=[r for r in redirects if r['owner']==label])
        if label=='holiday':prefix=bytes(data)
        write_new(directory/(label+'-storage.bin'),data)
    required={'af_v3_save_check','af_v3_save_pack','af_v3_console_storage_reset',
        'af_v3_console_storage_valid','af_v3_console_storage_commit','af_v3_console_player_clear',
        'af_v3_diary_measure'}
    for owner in ('diary','holiday'):
        if not required<={r['name'] for r in redirects if r['owner']==owner}:
            raise ValueError('Incomplete fishing storage redirect set')
    old_packet=copy.deepcopy(holiday['packet'])
    if prefix is None or old_packet['ram']+len(prefix)!=RAM:
        raise ValueError('Fishing module is not adjacent to its retained holiday packet')
    combined=prefix+raw
    # Pending prefix writes have new hashes, but unchanged physical extents.
    # Allocate against the verified input records, then publish all writes.
    allocation=physical.allocate(base,prior['physical_resources'],combined,'holiday-fishing-GAFE01-r0')
    resources.append(allocation);writes.append((allocation,combined))
    packet=dict(allocation,ram=old_packet['ram'],crc32=zlib.crc32(combined),
        storage='physical-ROM',guard=GUARD.hex())
    holiday['packet']=packet
    memory['bytes']+=176
    report.update(format='AFV3-HOLIDAY-FISHING-1',installed=True,storage_installed=True,
        packet=copy.deepcopy(packet),preserved_prefix_bytes=len(prefix),input_packet=old_packet,
        loaded_code=dict(ram=RAM,bytes=len(code),sha256=sha256(code)),
        redirects=redirects,save_format=13,diary_format=2,serialized_bytes=176,
        live_event_bound=False,additional_resident_bytes=SIZE+176,saved_format_changed=True,
        saved_profile_changed=False,scratch=copy.deepcopy(memory),
        pending=['native fishing actor/record/text consumers','winner-mail delivery',
            'measurement/calendar WebUI choice and event activation','connected native gameplay/save verification'])
    equipment['holiday_fishing']=report
    equipment['console_storage'].update(diary_runtime=copy.deepcopy(diary['compiled']),save_format=13,
        fishing_runtime=copy.deepcopy(compiled))
    updates={k:copy.deepcopy(prior[k]) for k in ('save_runtime','save_codec','clothing','room_surfaces')}
    updates['save_runtime']['diary_runtime_code']=copy.deepcopy(diary['compiled'])
    updates['save_codec'].update(format_version=13,active_storage_code=copy.deepcopy(diary['compiled']),
        holiday_state_code=copy.deepcopy(holiday['code']),fishing_storage_code=copy.deepcopy(compiled))
    updates['clothing']['save_extension'].update(format_version=13,active_storage_code=copy.deepcopy(diary['compiled']))
    updates['clothing']['save_extension']['legacy_formats_read']=list(dict.fromkeys(
        [*updates['clothing']['save_extension']['legacy_formats_read'],'AFS3-v12']))
    updates['room_surfaces']['save']['disk_format_version']=13
    warning=('Format-13 experimental saves require this or a newer compatible build. '
        'Compatible older saves migrate forward, retaining town, console, and diary data; '
        'new fishing records start empty. V2 and format-12-or-earlier V3 cannot load new saves. '
        'Preserve backups. Native diary/event gameplay and save/reload remain unverified.')
    updates.update(physical_resources=resources,saved_format_changed=True,save_warning=warning)
    diary['sources'].update(report['source_files']);equipment['npc_extra']['sources'].update(report['source_files'])
    write_new(directory/'installed.json',(json.dumps(report,indent=2)+'\n').encode())
    write_new(directory/'packet.bin',combined)
    return equipment,{},updates,writes


if __name__=='__main__':
    import argparse
    from v3_furniture_install import inputs
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-lock',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();base,prior=inputs(args.base_lock)
    report=prepare(base,prior,args.output.resolve())
    print(json.dumps(dict(functions=report['source_functions'],bytes=report['code']['bytes'],installed=False)))
