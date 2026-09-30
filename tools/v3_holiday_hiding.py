"""Complete source cover classifiers and flat hiding search for native placement.

Generated resources stay local. Preserve every cover class, including explicit
unsupported native buildings, rather than substituting ordinary free placement.
"""
import re
import struct

from aflib import CODE_RAM,CODE_VROM,by_vrom,sha256,verified_rom
from v3_asset_loader import ROOT
from v3_holiday_participants import DONOR,clean,constants
from v3_password_policy import function

REFERENCES={
    'src/game/m_all_grow_ovl.c':'2f4b30ccf13622c7d1369ac0b5793fe01f1e67af2e560a16a30de2fb3fa24631',
    'src/game/m_npc.c':'53fa38241f3fe71aae861fc5ecc60d57a1457c9912be1977578d8a40ee6698c0',
    'src/actor/ac_event_manager.c':'bb6f890571e68532d6edd8b741acc4975051b192f69b06a3863223552e2efe55',
}
CLASSES=('mAGrw_CheckCancel12','mAGrw_CheckCancel32','mAGrw_CheckCancel22','mAGrw_CheckHide36',
    'mAGrw_CheckCancelLeft45','mAGrw_CheckCancelRight45','mAGrw_CheckCancel46',
    'mAGrw_CheckCancel23','mAGrw_CheckCancel57','mAGrw_CheckCancel68','mAGrw_CheckCancel77')
TABLES=('hide_3_2','hide_2_2','hide_3_6','hide_4_6','hide_2_3','hide_5_7','hide_6_8','hide_7_7')
PLACEMENT=('search_empty_hide_unit','search_empty_hide_unit_sub','search_empty_hide_unit_player',
    'search_empty_hide_unit_toudai','make_actor_in_free_block_hide','walk_actor_at_wade_hide',
    'show_actor_at_wade','harvestfestival_turkey_start','harvestfestival_turkey_stop',
    'harvestfestival_turkey_in','turkey_behind')
NATIVE={
    'af_holiday_hide_native_hard':(0x800ADC28,0x800ADC8C),
    'af_holiday_hide_native_check':(0x800ADC8C,0x800ADD20),
    'af_holiday_hide_native_police':(0x80085D64,0x80085D94),
    'af_holiday_hide_native_block':(0x80088710,0x80088780),
    'af_holiday_hide_native_kind':(0x80089440,0x800894D0),
}


def generate(source,image,prior):
    texts={};references={}
    for path,digest in REFERENCES.items():
        raw=(DONOR/path).read_bytes()
        if sha256(raw)!=digest:raise ValueError('Changed complete hiding source: '+path)
        texts[path]=clean(raw.decode());references[path]=dict(bytes=len(raw),sha256=digest)
    grow=texts['src/game/m_all_grow_ovl.c'];npc=texts['src/game/m_npc.c']
    functions=[]
    names=CLASSES+('mAGrw_HideOn','mAGrw_SetHideOn','mAGrw_SetHideUtInfo',
        'mNpc_GetMakeUtNuminBlock_hide_hard_area')+PLACEMENT
    for name in names:
        matches=[p for p,rows in source.functions.items() if any(n==name for n,_ in rows)]
        if len(matches)!=1:raise ValueError('Missing whole hiding function: '+name)
        functions.append(source.function(matches[0])[1])
    # Retain the complete actual table and every offset array. Scalar values
    # and relocated pointers must agree with the donor source declarations.
    data=grow[grow.index('typedef struct hide_area_s'):grow.index('static mActor_name_t l_magrw_change_tree')]
    arrays={};receipts=[]
    for name in TABLES:
        match=re.search(r'\b'+name+r'\[\d+\]\s*=\s*\{(.*?)\};',data,re.S)
        if not match:raise ValueError('Missing complete source cover array: '+name)
        pairs=[tuple(map(int,p)) for p in re.findall(r'\{\s*(-?\d+)\s*,\s*(-?\d+)\s*\}',match[1])]
        raw=source.raw(name)
        if raw!=b''.join(struct.pack('>ii',*p) for p in pairs):raise ValueError('Cover offsets disagree with disc')
        arrays[name]=pairs;receipts.append(dict(symbol=name,bytes=len(raw),sha256=sha256(raw)))
    table=source.raw('l_hide_area_table');at,n=source.symbol('l_hide_area_table')
    refs={offset-at:target for offset,target in source.pointers(at,n).items()}
    expected=(None,*TABLES[:3],None,None,*TABLES[3:])
    if n!=88 or len(expected)!=11:raise ValueError('Incomplete cover-class table')
    for index,name in enumerate(expected):
        count,pointer=struct.unpack_from('>II',table,index*8)
        if count!=(len(arrays[name]) if name else 0) or pointer or (
                refs.get(index*8+4)!=(source.symbol(name)[0] if name else None)):
            raise ValueError('Changed full cover pointer/count table')
    receipts.append(dict(symbol='l_hide_area_table',bytes=n,sha256=sha256(table),pointers=refs))
    pieces=[data,'typedef int (*mAGrw_CHECK_CANCEL_UT_PROC)(mActor_name_t);']
    pieces.extend(function(grow,name) for name in CLASSES)
    pieces.extend(function(grow,name) for name in ('mAGrw_HideOn','mAGrw_SetHideOn','mAGrw_SetHideUtInfo'))
    code='\n\n'.join(pieces)
    before='(*check_hide[i])(*items)'
    if code.count(before)!=1:raise ValueError('Changed complete cover classifier dispatch')
    code=code.replace(before,'(*check_hide[i])(af_holiday_hide_source_item(*items))')
    code=code.replace('extern void mAGrw_SetHideUtInfo(u16* hide, mActor_name_t* items)',
        'void af_holiday_hide_mask(u16* hide, const mActor_name_t* items)')
    unit=function(npc,'mNpc_GetMakeUtNuminBlock_hide_hard_area')
    unit=unit.replace('extern int mNpc_GetMakeUtNuminBlock_hide_hard_area(', 'int af_holiday_hide_unit(')
    unit=unit.replace('int restrict_area) {','int restrict_area, const AFHolidayHiding *h) {')
    unit=unit.replace('static u16 hide_ut_bit[UT_Z_NUM];','u16 hide_ut_bit[UT_Z_NUM];')
    unit=unit.replace('mCoBG_Collision_u* col_top;','const u32* col_top;')
    unit=unit.replace('mActor_name_t* fg_top;','const mActor_name_t* fg_top;')
    unit=unit.replace('col_top = mFI_GetBkNum2ColTop(bx, bz);',
        'if (!ut_x || !ut_z || !h || !h->collision || !h->foreground || !h->hard_allowed) return FALSE;\n'
        '    col_top = h->collision(h->placement.context, bx, bz);')
    unit=unit.replace('fg_top = mFI_BkNumtoUtFGTop(bx, bz);',
        'fg_top = h->foreground(h->placement.context, bx, bz);')
    unit=unit.replace('bzero(hide_ut_bit, sizeof(hide_ut_bit));',
        'for (int row=0; row<UT_Z_NUM; ++row) hide_ut_bit[row]=0;')
    unit=unit.replace('mAGrw_SetHideUtInfo','af_holiday_hide_mask').replace(
        'mNpc_CheckNpcSet_fgcol_hard','h->hard_allowed')
    shifts=dict(center=26,top_left=21,bot_left=16,top_right=11,bot_right=6,unit_attribute=0)
    def collision(match):
        mask=63 if match[2]=='unit_attribute' else 31
        return f'(({match[1]} >> {shifts[match[2]]}) & {mask}u)'
    unit=re.sub(r'(col_top\[[^\]]+\])\.data\.(\w+)',collision,unit)
    if 'mFI_' in unit or '.data.' in unit or unit.count('const AFHolidayHiding *h')!=1:
        raise ValueError('Unadapted whole flat-unit search')
    code+='\n\n'+unit+'\n'
    # These platform mappings are supported by whole original growth selectors,
    # actual imported house-marker records, and the existing complete tent.
    mapping='''unsigned short af_holiday_hide_source_item(unsigned short item) {
    if(item>=0xF200 && item<0xF214)return (unsigned short)(NPC_HOUSE_START+216+item-0xF200);
    if(item>=0x5000 && item<0x50EE)return item;
    if(item==0x5843)return TOUDAI;
    if(item==0x5849)return TENT;
    if(item>=0x5800 && item<=0x5808)return item;
    if(item==0x580C || item==0x5829)return item;
    /* Museum/Able Sisters are not native buildings. Never classify coincident
     * native IDs as imported facilities; their source classes remain intact. */
    if(item>=0x5000)return EMPTY_NO;
    return item;
}
'''
    header=constants(code+mapping,references,headers=(
        'm_name_table.h','m_all_grow_ovl.h','m_field_make.h'))
    prefix='''#include "holiday_hiding.h"
typedef unsigned short u16;typedef unsigned int u32;typedef unsigned short mActor_name_t;
#define TRUE 1
#define FALSE 0
#define ABS(x) ((x)<0?-(x):(x))
#include "hiding-constants.h"
'''
    generated={'hiding-constants.h':header,'hiding-source.c':prefix+mapping+code}
    callbacks=('harvestfestival_turkey_start','harvestfestival_turkey_stop',
        'harvestfestival_turkey_in','turkey_behind')
    manager='\n\n'.join(function(texts['src/actor/ac_event_manager.c'],name) for name in callbacks)
    for name,phase in zip(callbacks,('start','stop','in','behind')):
        manager=manager.replace('static int '+name+'(','int af_hr_source_'+phase+'(')
    manager_constants=constants(manager,references,headers=('m_event.h','m_name_table.h'))
    replacements={'mEv_check_keep':'af_hr_manager_check_keep','mEv_set_keep':'af_hr_manager_set_keep',
        'mEv_clear_keep':'af_hr_manager_clear_keep','mEv_set_status':'af_hr_manager_native_set_status',
        'mEv_clear_status':'af_hr_manager_native_clear_status','mEv_check_status':'af_hr_manager_native_check_status',
        'make_actor_in_free_block_hide':'af_hr_manager_make_hide',
        'walk_actor_at_wade_hide':'af_hr_manager_walk_hide','show_actor_at_wade':'af_hr_manager_show'}
    for old,new in replacements.items():manager=re.sub(r'\b'+old+r'\b',new,manager)
    generated['hiding-manager-constants.h']=manager_constants
    generated['hiding-manager-source.c']=('''#include "harvest_manager.h"
#include "hiding-manager-constants.h"
#pragma GCC diagnostic ignored "-Wunused-parameter"
typedef AFHarvestManagerView EVENT_MANAGER_ACTOR;
typedef AFHolidayControl aEvMgr_event_ctrl_c;
typedef AFHolidayPlace mEv_place_data_c;
#define FALSE 0
#define aEvMgr_SHOW_ACTOR_RESULT_NOT_SHOWN ((void *)-1)
static mEv_place_data_c *tpppp;
'''+manager+'\n')
    files=by_vrom(image);core=files[CODE_VROM].extract(image)
    original=by_vrom(verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes()))[CODE_VROM]
    native_image=verified_rom((ROOT/'local/rom/Doubutsu no Mori (Japan).z64').read_bytes())
    original_core=original.extract(native_image);native=[]
    for name,(start,end) in NATIVE.items():
        raw=core[start-CODE_RAM:end-CODE_RAM]
        if not raw or raw!=original_core[start-CODE_RAM:end-CODE_RAM]:
            raise ValueError('Changed complete native hiding service: '+name)
        native.append(dict(symbol=name,address=start,bytes=len(raw),sha256=sha256(raw)))
    # Full native building classifiers establish the actual platform mapping,
    # including lighthouse 5843 versus the donor's 5844.
    growth=prior['equipment_resources']['scenery']['daily_growth']
    owner=files[growth['vrom']].extract(image)
    if sha256(owner)!=growth['output_sha256']:raise ValueError('Changed original growth selector owner')
    native_selectors=owner[0x80AB34EC-growth['ram']:0x80AB36A4-growth['ram']]
    old_growth=by_vrom(native_image)[growth['vrom']].extract(native_image)
    original_selectors=bytearray(old_growth[0x80AB34EC-growth['ram']:0x80AB36A4-growth['ram']])
    slot=0x80AB3554-0x80AB34EC
    if struct.unpack_from('>I',original_selectors,slot)[0]!=0x284150DB:
        raise ValueError('Changed native house cover bound')
    struct.pack_into('>I',original_selectors,slot,0x284150EE)
    if native_selectors!=original_selectors:
        raise ValueError('Changed complete native building classifiers')
    native.append(dict(symbol='native_cover_building_classifiers',address=0x80AB34EC,
        bytes=len(native_selectors),sha256=sha256(native_selectors)))
    from v3_campsite_manager import RAM as manager_ram,VROM
    manager=files[VROM].extract(image)
    retained_manager=bytearray(manager)
    hooks=prior['equipment_resources']['carried_items']['quest']['rewards']['installed_hooks']
    for row in hooks:
        if row['vrom']!=VROM:continue
        offset=row['address']-manager_ram
        if struct.unpack_from('>I',retained_manager,offset)[0]!=row['after']:
            raise ValueError('Changed installed shared reward manager hook')
        struct.pack_into('>I',retained_manager,offset,row['before'])
    if sha256(retained_manager)!=prior['campsite_manager']['output_sha256']:
        raise ValueError('Changed complete native event manager')
    # Existing native world helpers are called through their relocated owner.
    # Verify whole bodies and the concrete shrine/fluctuation initialization.
    for start,end in ((0x8095B8B0,0x8095B96C),(0x8095CC88,0x8095CD98)):
        raw=manager[start-manager_ram:end-manager_ram]
        from v3_holiday_placement import OWNER_GUARDS
        digest=next(digest for a,b,digest in OWNER_GUARDS if (a,b)==(start,end))
        if sha256(raw)!=digest:raise ValueError('Changed whole loaded manager placement primitive')
        native.append(dict(symbol='native_manager_world',address=start,bytes=len(raw),sha256=sha256(raw)))
    init=manager[0x80961800-manager_ram:0x80961884-manager_ram]
    if (struct.unpack_from('>I',init,0x24)[0]!=0xAC3823D4 or
            struct.unpack_from('>I',init,0x74)[0]!=0xAE000234):
        raise ValueError('Changed native fluctuation/shrine initializer')
    return generated,dict(references=references,functions=functions,tables=receipts,classes=11,
        native_services=native,bindings={name:start for name,(start,end) in NATIVE.items()},
        source_rel_sha256=sha256(source.rel),generated_sha256={n:sha256(v.encode()) for n,v in generated.items()},
        native_ball_position=0x8013790C,native_police_position=0x80106478,
        native_manager_fluctuation_offset=0x6B24,native_manager_shrine_exists_offset=0x234,
        platform_adaptations=['Native z/x coordinate order',
            'Native four-landmark exclusion; no nonexistent island dock',
            'Native lighthouse 5843 maps to source TOUDAI; full imported tent keeps 5849',
            'Additive F200..F213 house markers map to their actual source houses',
            'Retain all cover classes without importing Museum/Able Sisters',
            'Per-call hiding mask instead of a shared scratch buffer',
            'Preserve arrival fallback search result and wait for its actual acre'],
        installed=False,native_execution_verified=False)
