#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include "holiday_placement.h"
#include "holiday_owner.h"
#include "holiday_native.h"
#include "npc_registry.h"
#include "holiday-placement-data.h"
unsigned int af_holiday_owner_keep[2];
const unsigned short af_holiday_owner_names[2]={0xD090,0};
const AFNpcExtras af_v3_npc_extras={.magic=AF_NPC_EXTRA_MAGIC,.version=1,.count=1,.stride=44,
    .rows={{.name=0xD090,.flags=3}}};
static unsigned int expected_type=80;
typedef AFHolidayBlock BlockOrUnit_c;
typedef struct {AFHolidayBlock block_max;} aEvMgr_field_info_c;
typedef struct {
    aEvMgr_field_info_c field_info;
    AFHolidayBlock pool_block,station_block,shrine_block,player_home_block,dock_block;
} EVENT_MANAGER_ACTOR;
typedef struct {unsigned int type;} aEvMgr_event_ctrl_c;
typedef struct {int month,day,sec,hour;} lbRTC_time_c;
static lbRTC_time_c rtc;
#define Common_GetPointer(x) (&rtc)
#define FALSE 0
#define TRUE 1
#define UT_X_NUM 16
#define UT_Z_NUM 16
static int attempt,busy_mode,other_mode,unit_mode;
static int mFI_CheckBgDma(int x,int z) {return busy_mode==2 || (busy_mode==1 && (x+z)%2);}
static int mEv_use_block_by_other_event(unsigned int t,AFHolidayBlock b) {
    return other_mode==2 || (other_mode==1 && (t+b.x+b.z)%3);
}
static int mNpc_GetMakeUtNuminBlock(int *x,int *z,int bx,int bz) {
    int n=attempt++;
    if(unit_mode==2 || (unit_mode==1 && n%3))return 0;
    *x=1+(bx+n)%14;*z=1+(bz+n)%14;return 1;
}
#include "holiday-placement-reference.inc"
static int outdoor=1,stored,reserve_fail,errors,flattened,spawned,spawn_result=1;
static int forwards=1,height_hit,height_count;
static AFHolidayPlace place;
static AFHolidayBlock next_forward;
static int outdoors(void *c) {(void)c;return outdoor;}
static int busy(void *c,int x,int z) {(void)c;return mFI_CheckBgDma(x,z);}
static int other(void *c,unsigned int t,AFHolidayBlock b) {(void)c;return mEv_use_block_by_other_event(t,b);}
static int unit(void *c,int *x,int *z,int bx,int bz) {(void)c;return mNpc_GetMakeUtNuminBlock(x,z,bx,bz);}
static int height(void *c,int bx,int bz,int x,int z) {
    (void)c;assert(bx==place.block.x && bz==place.block.z);assert(x>=1 && x<=14 && z>=1 && z<=14);
    return height_count++==height_hit;
}
static AFHolidayPlace *get(void *c,unsigned int t,unsigned int id) {
    (void)c;assert(t==expected_type && id==0x51);return stored?&place:0;
}
static AFHolidayPlace *reserve(void *c,unsigned int t,unsigned int id) {
    (void)c;assert(t==expected_type && id==0x51);if(reserve_fail)return 0;stored=1;return &place;
}
static int forward(void *c,int *x,int *z) {(void)c;*x=next_forward.x;*z=next_forward.z;return forwards;}
static void flatten(void *c,AFHolidayPlace *p) {(void)c;assert(p==&place);flattened++;}
static int spawn(void *c,AFHolidayPlace *p) {(void)c;assert(p==&place);spawned++;return spawn_result;}
static void error(void *c,unsigned int type) {(void)c;assert(type==expected_type);errors++;}
static const AFHolidayField *current_field;
static const AFHolidayPlacementOps *current_ops;
static int stopped;
int af_holiday_native_type(unsigned int donor) {return donor<128 && af_holiday_native_ids[donor]!=255?af_holiday_native_ids[donor]:-1;}
void af_holiday_native_set_status(int type,int status) {assert(type==(int)expected_type && status==AF_HE_ERROR);errors++;}
int af_holiday_placement_native_make(void *m,unsigned int donor,unsigned int name,unsigned int donor_name,AFHolidayPlace **p) {
    assert(m==current_field);AFHolidayOwner owner;
    assert(af_holiday_event_owner(af_holiday_event_data,812,donor,&owner)==1);
    return af_holiday_placement_make(current_field,current_ops,af_holiday_native_type(donor),name,0x51,owner.kind,
        donor+donor_name+0x51,p);
}
int af_holiday_placement_native_show(void *m,unsigned int donor,AFHolidayBlock *b) {
    assert(m==current_field);return af_holiday_placement_show(current_field,current_ops,af_holiday_native_type(donor),0x51,b);
}
int af_holiday_placement_native_cull(unsigned int donor) {assert(af_holiday_native_type(donor)==(int)expected_type);return stopped;}
int main(void) {
    int raw_manager[0x248/4]={0};
    raw_manager[0x1E8/4]=8;raw_manager[0x1EC/4]=7;
    raw_manager[0x20C/4]=4;raw_manager[0x210/4]=5;
    for(int i=0;i<4;i++) {raw_manager[0x214/4+i*3]=i+1;raw_manager[0x218/4+i*3]=i+2;}
    unsigned char raw_clock[8]={29,0,13,20,0,6,7,234};AFHolidayField decoded;
    assert(af_holiday_placement_field(raw_manager,raw_clock,&decoded));
    assert(decoded.maximum.x==7 && decoded.maximum.z==8 && decoded.next.x==5 && decoded.next.z==4);
    assert(decoded.shrine.x==4 && decoded.shrine.z==3 && decoded.exclusions==4);
    assert(decoded.excluded[0].x==2 && decoded.excluded[0].z==1);
    assert(decoded.month==6 && decoded.day==20 && decoded.hour==13 && decoded.second==29);
    AFHolidayField f={.maximum={8,7},.next={-1,-1},.shrine={3,2},
        .excluded={{2,1},{3,2},{4,3},{5,4},{6,5}},.exclusions=5,.month=6,.day=20,.hour=13,.second=29};
    AFHolidayPlacementOps o={0,outdoors,busy,other,unit,height,get,reserve,forward,flatten,spawn,error};
    EVENT_MANAGER_ACTOR manager={{f.maximum},f.excluded[0],f.excluded[1],f.excluded[2],f.excluded[3],f.excluded[4]};
    aEvMgr_event_ctrl_c ctrl={80};rtc=(lbRTC_time_c){6,20,29,13};
    unsigned int comparisons=0;
    for(int wandering=0;wandering<2;wandering++)for(busy_mode=0;busy_mode<3;busy_mode++)
    for(other_mode=0;other_mode<3;other_mode++)for(unit_mode=0;unit_mode<3;unit_mode++) {
        AFHolidayBlock b=f.shrine,u={0,0};attempt=0;
        int reference=wandering?search_free_unit(&manager,&ctrl,&b,&u,1,0xD123):
            search_select_unit(&manager,&ctrl,&b,&u,2);
        int reference_attempts=attempt;attempt=0;stored=0;errors=0;
        AFHolidayPlace *result=0;
        int got=af_holiday_placement_make(&f,&o,80,0xD090,0x51,wandering?AF_HE_WANDER:AF_HE_SHRINE,0xD123,&result);
        assert((got==1)==(reference!=0));assert(attempt==reference_attempts);
        if(reference)assert(result==&place && place.block.x==b.x && place.block.z==b.z &&
            place.unit.x==u.x && place.unit.z==u.z && place.name==0xD090 && place.flags==1 && !errors);
        else assert(!result && errors==1 && !stored);
        comparisons++;
    }
    busy_mode=other_mode=unit_mode=0;stored=0;errors=0;AFHolidayPlace *result=0;
    outdoor=0;assert(af_holiday_placement_make(&f,&o,80,0xD090,0x51,AF_HE_SHRINE,1,&result)==0 && !errors);
    AFHolidayBlock seen={0,0};assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==2);
    outdoor=1;reserve_fail=1;
    assert(af_holiday_placement_make(&f,&o,80,0xD090,0x51,AF_HE_SHRINE,1,&result)==-1 && errors==1);
    reserve_fail=0;assert(af_holiday_placement_make(&f,&o,80,0xD090,0x51,AF_HE_SHRINE,1,&result)==1);
    int attempts=attempt;assert(af_holiday_placement_make(&f,&o,80,0xD090,0x51,AF_HE_SHRINE,1,&result)==1);
    assert(attempt==attempts);next_forward=place.block;
    static const int dx[9]={0,1,-1,0,1,-1,0,1,-1},dz[9]={0,0,0,1,1,1,-1,-1,-1};
    for(height_hit=0;height_hit<9;height_hit++) {
        place.unit=(AFHolidayBlock){8,8};height_count=0;flattened=spawned=0;
        assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==1);
        assert(place.unit.x==8+dx[height_hit] && place.unit.z==8+dz[height_hit]);
        assert(height_count==height_hit+1 && flattened==1 && spawned==1);
    }
    height_hit=-1;height_count=0;attempts=attempt;
    assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==1 && attempt==attempts+1);
    unit_mode=2;flattened=spawned=0;
    assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==2 && !flattened && !spawned);
    unit_mode=0;height_hit=0;height_count=0;spawn_result=0;
    assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==0);spawn_result=1;
    f.next=place.block;flattened=spawned=0;
    assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==2 && !flattened && !spawned);
    f.next=(AFHolidayBlock){-1,-1};forwards=0;
    assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==2);forwards=1;
    next_forward.x++;assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==2);
    next_forward=place.block;place.unit.x=INT_MAX;errors=0;
    assert(af_holiday_placement_show(&f,&o,80,0x51,&seen)==0 && errors==1);
    stored=0;f.shrine.x=-1;errors=0;
    assert(af_holiday_placement_make(&f,&o,80,0xD090,0x51,AF_HE_SHRINE,1,&result)==-1 && errors==1);
    f.shrine.x=2;current_field=&f;current_ops=&o;unsigned int owners=0;
    for(unsigned int donor=0;donor<128;donor++) {
        AFHolidayOwner owner;if(af_holiday_event_owner(af_holiday_event_data,812,donor,&owner)!=1)continue;
        expected_type=af_holiday_native_type(donor);AFHolidayControl control={.type=expected_type};
        stored=0;errors=0;unit_mode=other_mode=busy_mode=0;attempt=0;
        if(owner.kind==AF_HE_SHRINE || owner.kind==AF_HE_WANDER) {
            assert(af_holiday_owner_start(&f,&control)==1 && !errors && stored);
            assert(af_holiday_owner_start(&f,&control)==2 && !errors);
            next_forward=place.block;height_hit=height_count=0;spawn_result=1;forwards=1;
            assert(af_holiday_owner_in(&f,&control)==1 && control.block.x==place.block.x && control.block.z==place.block.z);
            stopped=0;assert(af_holiday_owner_out(&f,&control)==0);
            stopped=1;assert(af_holiday_owner_out(&f,&control)==1);
            assert(af_holiday_owner_stop(&f,&control)==1);assert(af_holiday_owner_stop(&f,&control)==2);
            owners++;
        } else if(owner.kind==AF_HE_HALLOWEEN || owner.kind==AF_HE_DEDICATED) {
            assert(af_holiday_owner_start(&f,&control)==0 && errors==1 && !stored);
        }
    }
    assert(!af_holiday_owner_keep[0] && !af_holiday_owner_keep[1]);
    AFHolidayControl invalid={.type=70};assert(af_holiday_owner_start(&f,&invalid)==0);
    printf("native owner callbacks: %u shared owners reach actual placement core, enter/cull/stop; missing dedicated/costume owners reject\n",owners);
    printf("holiday placement: %u complete donor-search comparisons; reserve, reuse, terrain, spawn, and boundary checks pass\n",comparisons);
}
