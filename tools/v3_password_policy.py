"""Compile shared password eligibility from pinned donor rules and actual disc tables.

The generated host evaluator is local-only. Its result describes donor permission,
not installed N64 identities or permission to enable unfinished imports.
"""
import json
import re
import struct
import subprocess

from aflib import sha256,u32
from apply_translation import write_new
from v3_asset_loader import ROOT
from v3_holiday_rewards import compile_kernel

REFERENCES={
    'src/game/m_mail_password_check.c':'aad4e6de15db2d48b579456e981c139ff1501e199227443fb4f5c4d308218405',
    'src/game/m_shop.c':'3616d41cf113fa4459a59ce09b07976b54648da124d06bcffdece5c6e5174d37',
    'src/game/m_room_type.c':'4070ad37f947cdc825ca6ed704acabd7133457ad1e0fd64db125aecedb3f13c1',
    'src/game/m_name_table.c':'ef269034d6e3924bf510afd450789b99ffc5205fbdb36045fcfb1e26124a95c0',
    'include/m_ftr_def.h':'cd1aee31675504adcad31d1f1463c4bb86dd9857f34e61555f3a382970a236aa',
    'include/m_name_table.h':'636228dda6f5a145a1c33f886d4d574e01cd460e0062dd7502d18db2a472e3cb',
    'include/m_room_type.h':'bb8d51c514d50142d236561bdcbdc25bba397d33f46701afc181a7d6bf9fe4d3',
    'include/m_shop.h':'78c68484c94e98ff38b423b2b28cfc1c398f7b83b1cb8f08125cd26285a201ec',
    'include/m_mail_password_check.h':'060f66ac33e46176b5b09bd3dfec3bb5869ba93e5fc0dcd8049a8f58128bf2dc',
    'src/actor/npc/ac_npc_shop_common.c':'621b422db37e32f3a9cb62fbfd15b2386a9bc0492ec260999c97add43cedc256',
}
SOURCES=('tools/v3_password_policy.py','tools/v3_furniture_pipeline.py','tools/v3_holiday_rewards.py',
         'tools/v3_optional_composition.py','tools/v3_surface_selection.py','tools/v3_registry.py',
         'overlays/v3/password_policy.c','overlays/v3/password_policy.h','overlays/v3/password.h')


def reference_texts():
    result={}
    for name,digest in REFERENCES.items():
        raw=(ROOT/'local/ac-decomp'/name).read_bytes()
        if sha256(raw)!=digest:raise ValueError('Changed pinned password policy reference: '+name)
        result[name]=re.sub(r'/\*.*?\*/|//[^\n]*','',raw.decode(),flags=re.S)
    return result


def function(text,name):
    match=re.search(r'(?:extern|static)\s+[^;{}]*?\b'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{',text)
    if not match:raise ValueError('Missing complete reference function: '+name)
    depth=1;end=match.end()
    while depth and end<len(text):
        depth+=(text[end]=='{')-(text[end]=='}');end+=1
    if depth:raise ValueError('Unterminated reference function')
    return text[match.start():end]


def constants(text):
    # Preserve enum order and their internal macro definitions, including the
    # donor's generated four-rotation X() declarations. No game structs needed.
    enums=list(re.finditer(r'\benum\b[^;{}]*\{.*?\}\s*;',text,re.S))
    pieces=[(m.start(),m.group()) for m in enums]
    for m in re.finditer(r'^#(?:define|undef)\b(?:[^\n]*\\\n)*[^\n]*',text,re.M):
        if not any(e.start()<=m.start()<e.end() for e in enums):pieces.append((m.start(),m.group()))
    return '\n'.join(value for _,value in sorted(pieces))+'\n'


def c_array(kind,name,values):
    return f'static {kind} {name}[]={{'+','.join(str(v) for v in values)+'};\n'


def evaluator(source):
    from v3_furniture_art import verify_sources
    verify_sources(source.rel,source.symbols.encode())
    texts=reference_texts();tables=[];bodies=[];receipts=[]
    def values(name,code):
        raw=source.raw(name);width=struct.calcsize('>'+code)
        if len(raw)%width or source.pointers(*source.symbol(name)):
            raise ValueError('Invalid complete scalar policy table: '+name)
        tables.append(dict(symbol=name,offset=source.symbol(name)[0],bytes=len(raw),sha256=sha256(raw)))
        return list(struct.unpack('>'+str(len(raw)//width)+code,raw))
    def pointers(name,count):
        at,n=source.symbol(name)
        if n!=count*4 or any(source.raw(name)):raise ValueError('Incomplete policy pointer directory: '+name)
        refs={loc-at:target for loc,target in source.pointers(at,n).items()}
        tables.append(dict(symbol=name,offset=at,bytes=n,pointers=refs))
        return refs
    def target_name(target):
        name,at,n=source.containing(target,exact=True)
        if at!=target:raise ValueError('Policy pointer is not a complete source object')
        return name
    prelude='''#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;typedef uint16_t u16;typedef uint32_t u32;
typedef u16 mActor_name_t;typedef void GAME;
typedef struct { u16 year; } lbRTC_time_c;typedef u16 lbRTC_year_t;
#define TRUE 1
#define FALSE 0
#define PLAYER_NAME_LEN 8
#define Common_Get(x) ((lbRTC_time_c){2001})
#define Save_Get(x) ITM_FOOD_APPLE
'''
    for name in ('m_ftr_def','m_name_table','m_room_type','m_shop','m_mail_password_check'):
        prelude+=constants(texts['include/'+name+'.h'])
    prelude+='''typedef struct {u16 item;u8 npc_type,npc_code,type,hit_rate_index,checksum;
    u8 str0[8],str1[8];} mMpswd_password_c;
'''
    birth=values('mRmTp_birth_type','B')
    if len(birth)!=1266 or max(birth)>=38:raise ValueError('Changed complete donor birth categories')
    prelude+=c_array('u8','mRmTp_birth_type',birth)
    famicom=values('pswd_famicom_list','H');maximum=values('pswd_famicom_list_max','I')
    if maximum!=[len(famicom)] or len(famicom)!=15 or max(famicom)>=len(birth):
        raise ValueError('Changed complete Famicom permission list')
    prelude+=c_array('u16','pswd_famicom_list',famicom)+f'static u32 pswd_famicom_list_max={len(famicom)};\n'
    roots=pointers('mSP_goods_seg_inf',6)
    if set(roots)!=set(range(0,24,4)):raise ValueError('Incomplete policy goods roots')
    root_names=[]
    for kind in range(6):
        refs=pointers(target_name(roots[kind*4]),23);names=[]
        for group in range(23):
            if group*4 not in refs:names.append('NULL');continue
            ids=values(target_name(refs[group*4]),'H')
            if not ids or ids[-1] or 0 in ids[:-1]:raise ValueError('Unterminated source goods list')
            name=f'goods_{kind}_{group}';names.append(name);prelude+=c_array('u16',name,ids)
        name=f'goods_{kind}';root_names.append(name)
        prelude+=f'static u16 *{name}[23]={{'+','.join(names)+'};\n'
    prelude+='static u16 **mSP_goods_seg_inf[6]={'+','.join(root_names)+'};\n'
    price_roots=pointers('l_price_info',16);price_names=[]
    for category in range(16):
        if category*4 not in price_roots:price_names.append('NULL');continue
        root=target_name(price_roots[category*4]);leaf=pointers(root,1)
        if set(leaf)!={0}:raise ValueError('Missing complete price binding')
        name=target_name(leaf[0]);prices=values(name,'H')
        if prices[-1]!=65535 or 65535 in prices[:-1]:raise ValueError('Unbounded donor price table')
        prelude+=c_array('u16',name,prices)+f'static u16 *{root}={name};\n';price_names.append('&'+root)
    prelude+='static u16 **l_price_info[16]={'+','.join(price_names)+'};\n'
    prelude+=c_array('u16','mSP_item1_start_idx_table',values('mSP_item1_start_idx_table','H'))
    prices=values('ftr_price_table','H')
    if len(prices)!=1267 or prices[-1]!=65535 or 65535 in prices[:-1]:raise ValueError('Unbounded furniture prices')
    prelude+=c_array('u16','ftr_price_table',prices)
    def add(file,name,address):
        text=function(texts['src/game/'+file+'.c'],name);raw,receipt=source.function(address)
        if receipt['symbol']!=name:raise ValueError('Changed complete policy function identity')
        bodies.append(text);receipts.append(receipt)
    add('m_room_type','mRmTp_FtrItemNo2FtrIdx',0x775D0)
    add('m_room_type','mRmTp_FtrIdx2FtrItemNo',0x77614)
    add('m_name_table','mNT_FishIdx2FishItemNo',0x58EA8)
    add('m_room_type','mRmTp_FtrItemNo2Item1ItemNo',0x76364)
    add('m_room_type','mRmTp_FurnitureIdx2FurnitureKind',0x768C8)
    add('m_shop','mSP_SelectListFromPriority',0x777FC)
    bodies.append('''static void mSP_GetGoodsPriority(u8 *p,int category) {
    assert(category>=0&&category<6);p[0]=0;p[1]=1;p[2]=2;
}
static mActor_name_t *mSP_GetItemList(mActor_name_t **lists,u8 *priorities,int type) {
    assert(type!=mSP_LISTTYPE_ABC);
    return mSP_SelectListFromPriority(lists,priorities,type);
}''')
    add('m_shop','mSP_CountElementInCommonList',0x77C94)
    add('m_shop','mSP_SearchItemCategoryPriority',0x78700)
    add('m_shop','mSP_CountPriceTableElement',0x78408)
    add('m_shop','mSP_ItemNo2ItemPrice',0x784E0)
    for name,address in (('famicom',0x4E160),('user',0x4E1E8),('other',0x4E734)):
        add('m_mail_password_check','mMpswd_check_present_'+name,address)
    add('m_mail_password_check','mMpswd_check_present',0x4E8B0)
    # No player state can change the answer: ABC queries cover all three
    # priorities; all five local/foreign fruit prices are positive; the year
    # path (grab bag) is unreachable from check_present_user.
    footer='''
int main(void) {
    static u8 result[65536];mMpswd_password_c v={0};
    assert(NPC_NUM==236&&mMpswd_SPECIAL_NPC_NUM==32);
    assert(mMpswd_CODETYPE_FAMICOM==0&&mMpswd_CODETYPE_USER==4&&mMpswd_CODETYPE_MAGAZINE==3);
    assert(!mMpswd_check_present_user(ITM_HUKUBUKURO_BAG));
    assert(mSP_FOREIGN_FRUIT_PRICE>0);
    for(unsigned i=0;i<5;i++)assert(food_price_table[i]>0);
    for(unsigned item=0;item<65536;item++) {
        v.item=(u16)item;v.type=0;result[item]=(u8)mMpswd_check_present(&v);
        v.type=4;result[item]|=(u8)(mMpswd_check_present(&v)<<1);
        v.type=3;result[item]|=(u8)(mMpswd_check_present(&v)<<2);
    }
    assert(fwrite(result,1,sizeof(result),stdout)==sizeof(result));return 0;
}
'''
    rates=values('hit_rate_magazine$729','f')
    if rates!=[80.,60.,30.,0.,100.]:raise ValueError('Changed source magazine probabilities')
    return prelude+'\n'.join(bodies)+footer,dict(reference_files=REFERENCES,tables=tables,
        functions=receipts,magazine_rates=[int(r) for r in rates],normal_npcs=236,special_npcs=32,
        source_rel_sha256=sha256(source.rel),source_symbols_sha256=sha256(source.symbols.encode()))


def compact(masks,report):
    if len(masks)!=65536 or any(v>7 for v in masks) or masks[65535]!=7:
        raise ValueError('Invalid complete source permission matrix')
    rows=[];start=0
    while start<65536:
        end=start+1
        while end<65536 and masks[end]==masks[start]:end+=1
        if masks[start]:rows.append((start,end-1,masks[start],0))
        start=end
    size=32+6*len(rows)
    if size>65535:raise ValueError('Policy exceeds bounded packet')
    header=struct.pack('>4s6H',b'AFPE',1,len(rows),size,report['normal_npcs'],report['special_npcs'],65535)
    return header+bytes(report['magazine_rates'])+bytes(11)+b''.join(struct.pack('>HHBB',*r) for r in rows),rows


def destination_map(lock):
    """Bind implemented imports to their actual live selection fields.

    Existing native-item correspondence and display-parent aliases remain
    separate mapping work. Never guess either from equal donor/native numbers.
    """
    import v3_optional_composition as optional
    from aflib import by_vrom
    from v3_asset_loader import BLOB
    optional.use_build_lock(lock);image,report=optional.inputs()
    catalog=optional.catalogue(image,report);blob=by_vrom(image)[BLOB].extract(image)
    rows=[]
    for key,row in catalog.items():
        if row['kind']=='villager':continue
        donor=int(key.rsplit('/',1)[1],16);native=int(row['item_id'],16)
        at=row['enable_offset'];width=row['enable_bytes'];ram=row.get('enable_ram')
        if ram is None:
            if row['kind']!='clothing' or not 0<=at<0xC000:raise ValueError('Unbound import selection address')
            ram=0x80460000+at
        if (width not in (1,4) or len(blob[at:at+width])!=width
                or int.from_bytes(blob[at:at+width],'big')!=1
                or not 0x80400000<=ram<=0x80800000-width or width==4 and ram%4):
            raise ValueError('Invalid complete destination enable field')
        rotations=4 if row['kind']=='furniture' else 1
        if rotations==4 and (donor&3 or native&3):raise ValueError('Unaligned furniture identity')
        for rotation in range(rotations):
            rows.append(dict(source_item=donor+rotation,item=native+rotation,enable_ram=ram,
                enable_bytes=width,enable_offset=at,id=key,kind=row['kind']))
    rows.sort(key=lambda r:r['source_item'])
    if len({r['source_item'] for r in rows})!=len(rows):raise ValueError('Ambiguous password import destination')
    size=16+len(rows)*12
    if size>65535:raise ValueError('Password destination map exceeds bounded format')
    data=struct.pack('>4s6H',b'AFPM',1,len(rows),12,size,0,0)+b''.join(
        struct.pack('>HHIB3x',r['source_item'],r['item'],r['enable_ram'],r['enable_bytes']) for r in rows)
    return data,dict(bytes=len(data),sha256=sha256(data),rows=rows,imports=len({r['id'] for r in rows}),
        base_rom_sha256=sha256(image),base_report_sha256=sha256((optional.BASE/'build.json').read_bytes()),
        runtime_abi=report['runtime_abi'],saved_format=report['save_codec']['format_version'],
        native_correspondence_complete=False,display_aliases_complete=False,runtime_installed=False)


def prepare(source,output,*,lock):
    output=output.resolve()
    if output.exists() or not output.is_relative_to(ROOT/'build'):raise ValueError('Use a fresh ignored policy output')
    code,report=evaluator(source);mapping,destinations=destination_map(lock);output.mkdir(parents=True)
    write_new(output/'donor-policy.c',code.encode())
    compiled=subprocess.run(['cc','-std=c11','-O1','-g','-fsanitize=address,undefined',
        '-fno-omit-frame-pointer',str(output/'donor-policy.c'),'-o',str(output/'donor-policy')],
        capture_output=True,text=True,timeout=30)
    if compiled.returncode:raise ValueError('Donor policy compilation failed:\n'+compiled.stderr)
    result=subprocess.run([str(output/'donor-policy')],capture_output=True,timeout=30)
    if result.returncode:raise ValueError('Donor policy evaluation failed:\n'+result.stderr.decode())
    data,rows=compact(result.stdout,report)
    write_new(output/'donor-permissions.bin',result.stdout);write_new(output/'password-policy.bin',data)
    write_new(output/'password-destinations.bin',mapping)
    report.update(format='AFV3-PASSWORD-POLICY-1',bytes=len(data),sha256=sha256(data),ranges=rows,
        donor_matrix_sha256=sha256(result.stdout),donor_permission_counts={
            key:sum(bool(v&bit) for v in result.stdout) for key,bit in (('famicom',1),('user',2),('other',4))},
        generated_source_sha256=sha256(code.encode()),runtime_installed=False,acquisition_installed=False,
        destination_bindings_installed=False,destinations=destinations,kernel=compile_kernel(output,name='password_policy'),
        sources={p:sha256((ROOT/p).read_bytes()) for p in SOURCES})
    write_new(output/'password-policy.json',(json.dumps(report,indent=2,sort_keys=True)+'\n').encode())
    return report
