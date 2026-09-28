/* Exercise the real native adapter with bounded N64 field/actor I/O doubles. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uintptr_t owner_function(unsigned int);
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))owner_function(at))
#include "holiday_dedicated_native.c"
#include "holiday-native-data.h"
#include "holiday_dispatch.h"
#include "holiday_active.h"
#include "npc_registry.h"
AFHolidayDedicatedCommon af_holiday_dedicated_common;
const AFNpcExtras af_v3_npc_extras={.magic=AF_NPC_EXTRA_MAGIC,.version=1,.count=1,.stride=44,
    .rows={{.name=0xD090,.profile=0xCC,.flags=3}}};
typedef struct {
    unsigned short source,name,profile,owner,source_dummy,native_dummy;
    unsigned int dependencies;void (*callbacks[4])(void *,void *);
} Decoration;
const Decoration af_decor_actor_records[18]={
    {.source=0x582A,.name=0x5F00,.dependencies=7},
    {.source=0x5846,.name=0x5F0F,.dependencies=16}};
const unsigned int af_holiday_decoration_ready=7;
const unsigned int af_holiday_manager_descriptor[8]={
    0x03800000,0x0380A590,0x8095B8B0,0x80965E40,0x80100000,0,0,0};
unsigned int af_holiday_owner_keep[2];
static AFHolidayPlace places[128][256];
static unsigned char present[128][256];
static unsigned int status[128],clean_calls,control_calls,effect_calls,delete_calls,show_calls,pool_calls;
static int manager[0x250/4],inside,structure_ok=1,unresolved,fade_ok=1,wade,show_result=1,clear_calls,errors;
static unsigned int last_type,last_id,last_flags;
static unsigned int unavailable_kind,unavailable_source;
unsigned short af_holiday_native_field_id(void) {return inside?0x1000:0;}
int af_holiday_native_check_field(void) {return !inside;}
int af_holiday_native_pool_variant(void) {pool_calls++;return 0;}
int af_holiday_native_landmark(int *x,int *z,unsigned int k) {
    (void)k;*x=2;*z=3;return 1;
}
AFHolidayPlace *af_holiday_native_get_place(int t,unsigned char i) {
    assert(t>=AF_HN_FIRST && t<AF_HN_END);return present[t][i]?&places[t][i]:0;
}
AFHolidayPlace *af_holiday_native_reserve_place(int t,unsigned char i) {
    assert(t>=AF_HN_FIRST && t<AF_HN_END);present[t][i]=1;return &places[t][i];
}
void af_holiday_native_clear_place(int t,unsigned char i) {
    assert(t>=AF_HN_FIRST && t<AF_HN_END);present[t][i]=0;clear_calls++;
}
int af_holiday_native_structure(unsigned short name,int bx,int bz,int ux,int uz,int mode) {
    assert(name && bx>=1 && bx<=5 && bz>=1 && bz<=6 && ux>=0 && ux<16 && uz>=0 && uz<16);
    assert(mode==0 || mode==1);return structure_ok;
}
int af_holiday_native_check_status(int t,int flags) {assert(t>=71 && t<115);return status[t]&flags;}
void af_holiday_native_set_status(int t,int flags) {
    assert(t>=71 && t<115);last_type=t;last_flags=flags;status[t]|=flags;errors+=!!(flags&AF_HE_ERROR);
}
void af_holiday_native_clear_status(int t,int flags) {assert(t>=71 && t<115);status[t]&=~flags;}
int af_holiday_placement_native_show_id(void *m,unsigned int donor,unsigned int id,AFHolidayBlock *b) {
    assert(m==manager && donor<128 && id<256);last_type=af_holiday_native_type(donor);last_id=id;
    *b=(AFHolidayBlock){3,2};return show_result;
}
static void native_clean(void *m,unsigned int kind) {
    assert(m==manager && (kind==4 || kind==32768));clean_calls++;
}
static int native_control(void *m,AFHolidayControl *c,short p) {
    assert(m==manager && c->type>=71 && c->type<115 && p==0x123);control_calls++;return 1;
}
static AFHolidayPlace *native_show(void *m,AFHolidayControl *c,unsigned char id) {
    assert(m==manager);show_calls++;return af_holiday_native_get_place(c->type,id);
}
static void native_effect(int e) {assert(e==0x34);effect_calls++;}
static void native_delete(int e) {assert(e==0x34);delete_calls++;}
static uintptr_t owner_function(unsigned int address) {
    switch(address-0x80100000) {
    case 0x19D0:return (uintptr_t)native_clean;
    case 0x2170:return (uintptr_t)native_control;
    case 0x2740:return (uintptr_t)native_show;
    case 0x2B54:return (uintptr_t)native_effect;
    case 0x2BEC:return (uintptr_t)native_delete;
    default:assert(0);return 0;
    }
}
static int identity(void *c,unsigned int kind,unsigned int source) {
    (void)c;assert(source<65536);
    if(unresolved || (source==unavailable_source && kind==unavailable_kind))return -1;
    return kind==AF_HD_NAME?0xD090:kind==AF_HD_PROFILE?0x123:0x34;
}
static int fade_event(void *c,void *m,unsigned int donor,unsigned int type,unsigned int title,unsigned int kind) {
    (void)c;assert(m==manager && (int)type==af_holiday_native_type(donor));
    assert(title==1 || title==9);assert(kind==0 || kind==4 || kind==32768);return fade_ok;
}
void af_holiday_native_unable_wade(int v) {wade=v;}
int af_holiday_transition_live_fade(void *c,void *m,unsigned int donor,unsigned int type,unsigned int title,unsigned int kind) {
    return fade_event(c,m,donor,type,title,kind);
}
int main(void) {
    manager[0x214/4]=4;manager[0x218/4]=3;manager[0x21C/4]=1;
    manager[0x22C/4]=3;manager[0x230/4]=2;manager[0x234/4]=1;
    AFHolidayDedicatedServices s={0,identity,fade_event,maps,sizeof(maps)};
    AFHolidayDedicatedCommon common={-1,-1};AFHolidayControl ctrl={0};
    const unsigned int donors[]={64,12,13,15,14,16,20,1,35,11,41,43,56,37};
    for(unsigned int i=0;i<14;i++) {
        unsigned int donor=donors[i];ctrl.type=af_holiday_native_type(donor);common=(AFHolidayDedicatedCommon){-1,-1};
        af_holiday_dedicated_common=common;
        assert(af_holiday_dedicated_ready(donor,&s));
        assert(af_holiday_dedicated_dispatch(manager,&ctrl,&s,0)==1);
        assert(af_holiday_dedicated_dispatch(manager,&ctrl,&s,2)==(donor==11 || donor==41 || donor==16?0:1));
        status[ctrl.type]=AF_HE_STOP;
        assert(af_holiday_dedicated_dispatch(manager,&ctrl,&s,3)==(donor==11 || donor==41 || donor==16?0:1));
        assert(af_holiday_dedicated_dispatch(manager,&ctrl,&s,1)==(donor==11 || donor==41?0:1));
    }
    assert(clean_calls && control_calls && effect_calls && delete_calls && show_calls && pool_calls && !errors && !wade);
    /* Remove each required identity in turn. No scene/foreground/keep/state
     * mutation may precede the missing-dependency rejection. */
    for(unsigned int i=0;i<14;i++) {
        const AFHolidayNeeds *r=&af_holiday_owner_needs[i];ctrl.type=af_holiday_native_type(r->donor);
        for(unsigned int j=0;j<r->count;j++) {
            const AFHolidayNeed *need=&af_holiday_identity_needs[r->first+j];
            unavailable_kind=need->kind;unavailable_source=need->source;
            unsigned int calls=clean_calls+control_calls+effect_calls+delete_calls+show_calls;
            unsigned int kept[2];memcpy(kept,af_holiday_owner_keep,sizeof kept);
            AFHolidayDedicatedCommon saved=af_holiday_dedicated_common;int count=errors;
            assert(!af_holiday_dedicated_ready(r->donor,&s));
            assert(!af_holiday_dedicated_dispatch(manager,&ctrl,&s,0));
            assert(errors==count+1 && calls==clean_calls+control_calls+effect_calls+delete_calls+show_calls);
            assert(!memcmp(kept,af_holiday_owner_keep,sizeof kept));
            assert(!memcmp(&saved,&af_holiday_dedicated_common,sizeof saved));
        }
    }
    unavailable_source=0;unavailable_kind=0;
    ctrl.type=af_holiday_native_type(1);memset(af_holiday_owner_keep,0,sizeof af_holiday_owner_keep);
    for(int bad=-1;bad<=2;bad+=3) {
        unsigned int clean=clean_calls;int count=errors;fade_ok=bad;
        assert(!af_holiday_dedicated_dispatch(manager,&ctrl,&s,0));
        assert(errors==count+1 && clean_calls==clean);
        assert(!(af_holiday_owner_keep[0]|af_holiday_owner_keep[1]));
    }
    fade_ok=1;
    AFHolidayDedicatedServices live;assert(af_holiday_dedicated_bind(&live));
    assert(live.resolve(0,AF_HD_NAME,0x582A)==0x5F00);
    assert(live.resolve(0,AF_HD_NAME,0x5846)==-1); /* Real Harvest provider not ready. */
    assert(live.resolve(0,AF_HD_NAME,0xD074)==0xD090);
    assert(live.resolve(0,AF_HD_NAME,0xD03D)==-1);
    assert(live.resolve(0,AF_HD_NAME,0xD02D)==-1);
    assert(live.resolve(0,AF_HD_PROFILE,0x7F)==-1 && live.resolve(0,AF_HD_EFFECT_ID,0)==-1);
    assert(!af_holiday_dedicated_ready(1,&live));
    ctrl.type=af_holiday_native_type(11);
    assert(af_holiday_dedicated_start(manager,&ctrl)==1);
    assert(!af_holiday_dedicated_stop(manager,&ctrl) && !af_holiday_dedicated_in(manager,&ctrl));
    assert(!af_holiday_dedicated_out(manager,&ctrl) && !af_holiday_dedicated_behind(manager,&ctrl));
    ctrl.type=af_holiday_native_type(1);Native n={manager,0x80100000,&ctrl,&s};
    assert(places[ctrl.type][7].unit.x==11 && places[ctrl.type][7].unit.z==6);
    assert(places[ctrl.type][7].block.x==2 && places[ctrl.type][7].block.z==3);
    /* Strict delete retains a failed decoration; source sports cleanup clears
     * its common placement even if the foreground removal fails. */
    assert(operation(&n,AF_HD_FOREGROUND,1,6,4,6));structure_ok=0;int cleared=clear_calls;
    assert(!operation(&n,AF_HD_DELETE_FOREGROUND,1,6,0,0) && clear_calls==cleared);
    assert(last_type==ctrl.type && last_flags==AF_HE_ERROR && present[ctrl.type][6]);
    assert(operation(&n,AF_HD_DELETE_FOREGROUND_UNCHECKED,1,6,0,0)==1);
    assert(clear_calls==cleared+1 && !present[ctrl.type][6]);structure_ok=1;
    unsigned int pools=pool_calls;inside=1;
    assert(!operation(&n,AF_HD_ACTOR,64,7,32768,7) && pool_calls==pools);inside=0;
    assert(operation(&n,AF_HD_ACTOR,1,7,4,7) && pool_calls==pools);
    unresolved=1;af_holiday_native_clear_place(ctrl.type,7);int e=errors;
    assert(!operation(&n,AF_HD_ACTOR,1,7,4,7) && errors==e+1 && !present[ctrl.type][7]);
    unsigned int controls=control_calls;assert(!operation(&n,AF_HD_CONTROL,1,100,0,0));
    assert(control_calls==controls);unresolved=0;
    assert(!operation(&n,AF_HD_ACTOR,1,7,32768,7)); /* layout/landmark mismatch */
    operation(&n,AF_HD_ACTOR,1,7,4,7);
    show_result=2;assert(operation(&n,AF_HD_SHOW,1,7,1,0)==-1);
    show_result=0;assert(operation(&n,AF_HD_SHOW,1,7,1,0)==0);
    show_result=1;assert(operation(&n,AF_HD_SHOW,1,7,1,0)==(intptr_t)&places[ctrl.type][7]);
    assert(last_type==ctrl.type && last_id==7 && ctrl.block.x==2 && ctrl.block.z==3);
    assert(af_holiday_dedicated_native(manager,&ctrl,&common,&s,5)==-1);
    s.fade=0;assert(af_holiday_dedicated_native(manager,&ctrl,&common,&s,0)==-1);s.fade=fade_event;
    ctrl.type=0;assert(af_holiday_dedicated_native(manager,&ctrl,&common,&s,0)==-1);
    puts("All 14 owners reach shared dispatch/common state and full source callbacks; every missing identity rejects before mutation, and negative fades never start events. Native I/O remains doubled.");
}
