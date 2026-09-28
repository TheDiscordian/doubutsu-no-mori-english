"""Compile the whole shared source collision/search/fade path for native binding."""
import argparse
import json
from pathlib import Path
import re
import struct
import copy
import zlib

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256
from apply_translation import write_new
from v3_asset_loader import ROOT,compile_part
from v3_furniture_pipeline import Source
from v3_furniture_reactions import NATIVE_BLOCKS
from v3_password_policy import function
from v3_holiday_maps import REFERENCES as MAP_REFERENCES

REFERENCES={**{k:v for k,v in MAP_REFERENCES.items() if k in (
    'src/actor/ac_event_manager.c','src/game/m_event_map_npc.c','include/m_event.h','include/m_random_field_h.h')},
    'include/m_field_info.h':'234d10ac6c84f3039404be34a2a215a67c7bb5946f30ae4cca455ec9d374d8df',
    'include/m_field_make.h':'87ec3620ba14fb2a84743f9331909df8f6ecc072d5cdef6549e46d3c3b05185c',
    'include/m_name_table.h':'636228dda6f5a145a1c33f886d4d574e01cd460e0062dd7502d18db2a472e3cb',
    'include/m_scene_table.h':'afb8a8843e64fba1a3cd4240ea1253a6cdfe197e64f35a7a9c2860077b2454e3',
    'include/m_scene.h':'a184c6d49091f6c343a9405dec0fcf5348f4735c184cbba8e8fd728a49b5b83f',
    'include/m_demo.h':'ee115d213a0331b4fa588fa8fb6adfb4481105108ac2e39d42ef41ad7eb75786',
    'include/m_play.h':'cd1675e098635b926d4d4a366693ce59a5fd41d2053ff5748ceb2d0a6e6b4029'}
NAMES=('mEvMN_CheckLapPlayer','set_escape_unit','lap_fixed_actor','is_need2escape_unit',
       'player_lap_check','title_fade')
NATIVE=(
    ('grid',0x80088780,0x8008883C,'152f3c0f3e7b228bf609e63cfb0d7d163e441103c7b4d5e5dda6cb8f894c01a2'),
    ('position',0x80088C74,0x80088CBC,'90c8830e64e326c85ad5e1176fa9c24733c1539c1966205e697867a1e44da2cf'),
    ('origin',0x80088B3C,0x80088BC0,'b851cae30382f57df68b758ced1acf64126814117033ab175e996fee27f3e1a4'),
    ('area',0x8008D574,0x8008D6E0,'22bb2819f74d18fef5b65f7cfbbc7dc88c72961f586cd1a72bf7cc92382211ab'),
    ('landmark',0x80089440,0x80089538,'12d336e1c03fc00a812cdca55cab5d13c5100a0fd96d656c05365ba232eaf4ab'),
    ('police',0x8008D884,0x8008D928,'cabc9d1a23a7e08be17d441343699c8469434fb2cffbabaef5bd84251b37f1a2'),
    ('space',0x800ADC8C,0x800ADD20,'eb654e519600fb5e452e1df13eb64b50a449fc89a816dbda4a93cfe71faa89dc'),
    ('gate',0x800AFDA8,0x800B0010,'9119a0efd6e0742763dff4968b1a766f8b8f6d583dd39b7c550ac184e67d3b1b'))
SCENE_NATIVE=(
    ('demo_busy',0x8007D048,0x8007D080,'6f9165781257d834bb96d367bb086a6020ff080679c28e3d8f82185e19f755de'),
    ('player_ok',0x8007F950,0x8007F988,'571f1a81df18b4678bed592c74ca4c3240cf92d0d7dcd97b3d68963fc15d7d8c'),
    ('correct',0x800B5AB8,0x800B5B1C,'88996635145eb885ee1c97eefd6cd39bb17ad8d12164bb4aef9dfe13d63b8b57'),
    ('goto',0x800C6C10,0x800C6D14,'8026e2a597cfb160c631899b120ba36369e26cf302a62229967f0af7772858e1'),
    ('warp',0x800B3A48,0x800B3A60,'6eb3f1178d564e3a2ba3629cfbda5ecfd30af90316bfc86a3f853680cb7ef3fa'),
    ('bgm',0x8005EDC4,0x8005EDD8,'6b949eea80ff1df0f2d4d066720e183c832d0c6162041d859e6201dcc78990c9'))
MEMORY_NATIVE=tuple(row for row in NATIVE_BLOCKS if row[0] in ('memcpy','memset'))
SOURCES=('tools/v3_holiday_transition.py','overlays/v3/holiday_transition.c',
    'overlays/v3/holiday_transition.h','overlays/v3/holiday_transition_source.h',
    'overlays/v3/holiday_transition.ld','overlays/v3/holiday_transition_native.c',
    'overlays/v3/holiday_transition_identity.c','overlays/v3/holiday_scene_native.h',
    'tools/v3_asset_loader.py','tools/v3_furniture_install.py')


def generate(source):
    texts={}
    for path,digest in REFERENCES.items():
        raw=(ROOT/'local/ac-decomp'/path).read_bytes()
        if sha256(raw)!=digest:raise ValueError('Changed complete source event transition: '+path)
        texts[path]=re.sub(r'/\*.*?\*/|//[^\n]*','',raw.decode(),flags=re.S)
    parts=[];receipts=[]
    for name in NAMES:
        path='src/game/m_event_map_npc.c' if name.startswith('mEvMN') else 'src/actor/ac_event_manager.c'
        parts.append(function(texts[path],name))
        matches=[at for at,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Ambiguous complete transition source: '+name)
        _,row=source.function(matches[0]);receipts.append(row)
    bodies='\n\n'.join(parts)
    anchor='event_type = mEvMN_GetEventTypeMap();'
    if bodies.count(anchor)!=1:raise ValueError('Changed complete collision layout selector')
    bodies=bodies.replace(anchor,anchor+'\n    if (event_type == AF_HT_ORIGINAL_LAYOUT)\n'
        '        return af_holiday_transition_original(evmgr, block_ux, block_uz);')
    # Check both complete search tables against the actual relocated donor
    # data, not just the decompiled initializer's spelling.
    search=next(r for r in receipts if r['symbol']=='player_lap_check')
    offsets=sorted({r[3] for r in search['relocations'].values() if r[0] in (4,6) and tuple(r[1:3])==(1,5)})
    tables=re.findall(r'static int delta((?:\[\d+\])+)\s*=\s*(\{[^;]+\});',parts[4])
    if len(offsets)!=2 or len(tables)!=2:raise ValueError('Changed complete escape-table references')
    arrays=[]
    for at,(dimensions,text) in zip(offsets,tables,strict=True):
        shape=[int(n) for n in re.findall(r'\d+',dimensions)]
        values=[int(n) for n in re.findall(r'-?\d+',text)]
        name,start,size=source.containing(at,exact=True)
        data=struct.pack('>'+str(len(values))+'i',*values)
        if size!=len(data) or source.data[start:start+size]!=data:
            raise ValueError('Decompiled escape table differs from complete donor resource')
        arrays.append(dict(symbol=name,offset=at,bytes=size,shape=shape,sha256=sha256(data)))
    # Helpers acquire the explicit context their source globals require. There
    # is no temporary global manager or differently laid-out native struct cast.
    for name in NAMES[:4]:
        bodies=re.sub(r'\b'+name+r'\(',name+'(evmgr, ',bodies)
        bodies=re.sub(r'((?:static|extern)\s+(?:int|void)\s+'+name+r'\()evmgr, ',
            r'\1EVENT_MANAGER_ACTOR* evmgr, ',bodies)
    bodies=bodies.replace('extern int mEvMN_CheckLapPlayer','static int mEvMN_CheckLapPlayer')
    if bodies.count('static int delta[')!=2:raise ValueError('Changed complete escape offset tables')
    bodies=bodies.replace('static int delta[','static const int delta[')
    enums=[];macros={}
    identifiers=set(re.findall(r'\b\w+\b',bodies))
    for path,text in texts.items():
        if not path.startswith('include/'):continue
        for m in re.finditer(r'\benum\b[^;{}]*\{[^{}]*\}\s*;',text,re.S):
            declared=set(re.findall(r'(?:^|,)\s*([A-Za-z_]\w*)',m[0].split('{',1)[1].rsplit('}',1)[0]))
            if identifiers&declared:enums.append(m[0])
        for m in re.finditer(r'^#define (\w+)([^\n]*)',text,re.M):macros[m[1]]=m[0]
    selected={n for n in identifiers if n in macros}
    while True:
        more={n for text in (macros[n] for n in selected) for n in re.findall(r'\b\w+\b',text) if n in macros}
        if more<=selected:break
        selected|=more
    code='\n'.join(['#include "holiday_transition_source.h"',*enums,
        *(macros[n] for n in sorted(selected)),
        '_Static_assert((int)NAME_TYPE_STRUCT==(int)AF_HT_SOURCE_STRUCTURE,"Source structure category");',bodies,
        'int af_holiday_transition_collision(AFHolidayTransition *evmgr,int x,int z) {',
        ' if(!af_holiday_transition_ready(evmgr))return -1;',
        ' int result=mEvMN_CheckLapPlayer(evmgr,x,z);return evmgr->failed?-1:result;}',
        'int af_holiday_transition_escape(AFHolidayTransition *evmgr,AFHolidayShortPosition *out,',
        ' AFHolidayPosition *pos,unsigned int kind,unsigned int donor) {',
        ' if(!out || !pos || donor>=128 || !af_holiday_transition_ready(evmgr))return -1;',
        ' int result=player_lap_check(evmgr,out,pos,kind,donor);return evmgr->failed?-1:result;}',
        'int af_holiday_transition_run(AFHolidayTransition *evmgr,unsigned int donor,unsigned int title,unsigned int kind) {',
        ' if(donor>=128 || !af_holiday_transition_ready(evmgr))return -1;',
        ' int result=title_fade(evmgr,donor,title,kind);return evmgr->failed?-1:result;}',
        ''])
    return code,dict(references=REFERENCES,functions=receipts,
        escape_tables=arrays,
        explicit_helper_context=list(NAMES[:4]),immutable_escape_tables=2,
        retained_groundhog_branch=True,retained_transition_gates=True)


def prepare(output,build_lock=None,*,base=None,prior=None,refresh=False):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored preparation directory')
    from v3_furniture_install import inputs
    from v3_console_disk_install import reservations
    if build_lock:base,prior=inputs(build_lock)
    core=bytearray(by_vrom(base)[CODE_VROM].extract(base))
    events=prior['equipment_resources']['npc_extra']['events']
    if refresh:
        demo=events['demo']
        if not demo.get('scene_services'):raise ValueError('Live transition needs installed scene services')
        hook=next(h for h in demo['hooks'] if h['symbol']=='af_holiday_demo_busy')
        at=hook['address']-CODE_RAM
        if core[at:at+8]!=bytes.fromhex(hook['after']):raise ValueError('Changed installed demo busy entry')
        core[at:at+8]=bytes.fromhex(hook['before'])
    for name,lo,hi,digest in (*NATIVE,*SCENE_NATIVE):
        if sha256(core[lo-CODE_RAM:hi-CODE_RAM])!=digest:
            raise ValueError('Changed complete native transition primitive: '+name)
    # Complete original fade establishes every native common/player/manager
    # offset written by the bridge. Do not infer these from donor structs.
    owner=by_vrom(base)[0x03800000].extract(base)
    fade_digest=sha256(owner[0x8095EC24-0x8095B8B0:0x8095EDE4-0x8095B8B0])
    if fade_digest!='b62918cfef9ac362adddec67011807bcaa9d775decd64498790f2a5257c68549':
        raise ValueError('Changed complete native fade state/scene contract')
    if core[0x800B1C84-CODE_RAM:0x800B1C90-CODE_RAM]!=bytes.fromhex('8c821c9003e0000800000000'):
        raise ValueError('Changed complete native player accessor')
    for name,vrom,ram,at,size,digest in MEMORY_NATIVE:
        raw=by_vrom(base)[vrom].extract(base)
        if sha256(raw[at-ram:at-ram+size])!=digest:
            raise ValueError('Changed complete native transition memory helper: '+name)
    if not refresh and any(a<0x80700000 and 0x806FC000<b for a,b in reservations(prior)):
        raise ValueError('Planned transition range overlaps an existing allocation')
    maps=prior['equipment_resources']['npc_extra']['events']['reserved']
    source=Source((ROOT/'build/gamecube/files/foresta.rel.szs.decoded').read_bytes(),
        (ROOT/'local/ac-decomp/config/GAFE01_00/foresta/symbols.txt').read_bytes())
    code,contract=generate(source);output.mkdir(parents=True)
    code=code.replace('"holiday_transition_source.h"','"/source/overlays/v3/holiday_transition_source.h"')
    path=output/'source.c';write_new(path,code.encode())
    bindings={f'af_holiday_transition_{n}':lo for n,lo,_,_ in (*NATIVE,*SCENE_NATIVE)}
    bindings['af_holiday_map_get']=maps['code']['symbols']['af_holiday_map_get']
    bindings.update(af_holiday_native_game=0x8010EF90,af_holiday_transition_common=0x80136EA0,
        af_holiday_transition_scene=0x80126EB4,af_holiday_transition_player=0x800B1C84,
        af_holiday_native_type=prior['equipment_resources']['npc_extra']['events']['native_directory']['code']['symbols']['af_holiday_native_type'])
    bindings.update({name:at for name,_,_,at,_,_ in MEMORY_NATIVE})
    extra=(str(path.relative_to(ROOT)),'overlays/v3/holiday_transition_native.c')
    live={}
    if refresh:
        # Retain the original layout directory, including the null Halloween
        # entry and both separate native moon events. No source ID aliases it.
        types=struct.unpack_from('>15I',core,0x80105030-CODE_RAM)
        if types!=(11,12,10,8,7,9,13,3,20,2,16,21,22,6,14):
            raise ValueError('Changed complete native layout priority')
        if [r['event'] for r in maps['maps']]!=[32,20,15,13,12,14,49,1,29,54,35,43,56,64,3,7,37]:
            raise ValueError('Changed complete source layout priority')
        original_functions=(
            (0x80081EEC,0x80081F5C,'6a9ff34c6ae1f461cdf45bf1de4192412565d35b95926df1ca46eda2b88f2220'),
            (0x80082E40,0x80082F9C,'9dd69b66b9720bb0831b69efb3bc4b6abbc59c3463f743e19b32367f667a83b8'),
            (0x80105030,0x80105624,'575346e9af4b9dbd5baaf81ce92580124d9840f62a30c04e9f8e6114bdd8091e'),
            (0x8008930C,0x80089348,'9debc21ff1a4c34dc513d9fd0ce51e2101ca9224fd2a06cea0d1ade00310b59b'),
            (0x80056E1C,0x80056E88,'8ebf0f4a4e623ecef92d2985d14ee3f8ae6054f4da7ce50c9fec974b14ffb6bf'))
        original_receipts=[]
        for a,b,digest in original_functions:
            raw=core[a-CODE_RAM:b-CODE_RAM]
            if sha256(raw)!=digest:raise ValueError('Changed complete native layout/state consumer: '+hex(a))
            original_receipts.append(dict(address=a,bytes=b-a,sha256=digest))
        maps_row=next(row for row in maps['resources'] if row['file'].endswith('/maps.bin'))
        if maps_row['bytes']!=1496:raise ValueError('Changed complete live layout graph')
        controllers=events['decorations']['controllers']
        directory_symbols=events['native_directory']['code']['symbols']
        bindings.update(af_holiday_native_days=directory_symbols['af_holiday_native_days'],
            af_holiday_native_index=directory_symbols['af_holiday_native_index'],
            af_holiday_transition_maps=maps_row['ram'],af_holiday_transition_native_map=0x80081EEC,
            af_holiday_transition_native_collision=0x80082E40,
            af_decor_actor_resolve=controllers['code']['symbols']['af_decor_actor_resolve'],
            af_holiday_scene_bind=demo['code']['symbols']['af_holiday_scene_bind'])
        extra+=('overlays/v3/holiday_transition_identity.c',)
        live=dict(native_layout_types=list(types),native_functions=original_receipts,
            original_collision_preserved=True,decoration_resolver_reused=True,
            source_status_uses_native_directory=True,scene_services_bound=True)
    compiled,report=compile_part('holiday_transition',output/'code',
        extra_sources=extra,link_symbols=bindings)
    write_new(output/'code.bin',compiled)
    report=dict(code=report,contract=contract,generated_sha256=sha256(code.encode()),
        native_functions=(*NATIVE,*SCENE_NATIVE),native_fade_sha256=fade_digest,
        native_memory_helpers=MEMORY_NATIVE,
        bindings=bindings,input_rom_sha256=sha256(base),
        installed=False,native_scene_bridge_compiled=True,native_scene_services_bound=refresh,
        live=live,planned_code_range=[0x806FC000,0x806FE000],planned_packet_growth_bytes=0 if refresh else 0x4000,
        pending=['Live dedicated-owner dispatch and remaining actor services'] if refresh else [
            'Actual source-to-installed identities and ACTIVE status for original and imported layouts',
            'Native scene providers and live dedicated-owner dispatch'],
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'transition.json',(json.dumps(report,indent=2)+'\n').encode())
    return report


def install(base,prior,blob,core,output):
    del blob,core
    e=copy.deepcopy(prior['equipment_resources']);events=e['npc_extra']['events']
    old=events['transition']
    if old.get('native_scene_services_bound'):raise ValueError('Live transition is already bound')
    directory=output/'holiday-transition'
    prepared=prepare(directory,base=base,prior=prior,refresh=True)
    code=(directory/'code.bin').read_bytes();p=e['holiday_state']['packet']
    raw=bytearray(base[p['physical']:p['physical']+p['bytes']]);a=0x806FC000-p['ram'];b=0x806FE000-p['ram']
    previous=old['loaded_code']
    if (p!=e['holiday_fishing']['packet'] or sha256(raw)!=p['sha256'] or
            previous['ram']!=0x806FC000 or previous['bytes']>b-a or len(code)>b-a or
            sha256(raw[a:a+previous['bytes']])!=previous['sha256'] or any(raw[a+previous['bytes']:b])):
        raise ValueError('Changed or occupied live transition reservation')
    raw[a:b]=code+bytes(b-a-len(code))
    old.update(prepared,installed=True,native_execution_verified=False,
        prepared_directory=str(directory.relative_to(ROOT)),
        loaded_code=dict(ram=0x806FC000,bytes=len(code),sha256=sha256(code)),additional_resident_bytes=0)
    previous_digest=p['sha256'];p.update(sha256=sha256(raw),crc32=zlib.crc32(raw))
    e['holiday_fishing']['packet']=copy.deepcopy(p)
    resources=copy.deepcopy(prior['physical_resources']);matches=[r for r in resources if r['id']==p['id']]
    if len(matches)!=1:raise ValueError('Ambiguous combined live transition packet')
    matches[0]['sha256']=p['sha256']
    events['decorations']['controllers']['preserved'].append(old['loaded_code'])
    e['npc_extra']['sources'].update(old['sources'])
    write_new(directory/'installed.json',(json.dumps(old,indent=2)+'\n').encode())
    write_new(directory/'packet.bin',raw)
    return e,{},dict(physical_resources=resources),[(dict(matches[0],previous_sha256=previous_digest),bytes(raw))]


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--build-lock',type=Path,required=True)
    args=parser.parse_args();result=prepare(args.output,args.build_lock)
    print(json.dumps(dict(bytes=result['code']['bytes'],sha256=result['code']['sha256'],installed=False),indent=2))
