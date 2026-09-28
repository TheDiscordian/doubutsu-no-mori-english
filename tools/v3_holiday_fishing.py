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
