/* Exercise the real native adapter with bounded N64 field/actor I/O doubles. */
#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
static uintptr_t owner_function(unsigned int);
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))owner_function(at))
#include "holiday_dedicated_native.c"
#include "holiday-native-data.h"
const unsigned int af_holiday_manager_descriptor[8]={
    0x03800000,0x0380A590,0x8095B8B0,0x80965E40,0x80100000,0,0,0};
unsigned int af_holiday_owner_keep[2];
static AFHolidayPlace places[128][256];
static unsigned char present[128][256];
static unsigned int status[128],clean_calls,control_calls,effect_calls,delete_calls,show_calls,pool_calls;
static int manager[0x250/4],inside,structure_ok=1,unresolved,fade_ok=1,wade,show_result=1,clear_calls,errors;
static unsigned int last_type,last_id,last_flags;
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
    (void)c;assert(source<65536);if(unresolved)return -1;
    return kind==AF_HD_NAME?0xD090:kind==AF_HD_PROFILE?0x123:0x34;
}
static int fade_event(void *c,void *m,unsigned int donor,unsigned int type,unsigned int title,unsigned int kind) {
    (void)c;assert(m==manager && (int)type==af_holiday_native_type(donor));
    assert(title==1 || title==9);assert(kind==0 || kind==4 || kind==32768);return fade_ok;
}
static void lock_wade(void *c,int v) {(void)c;wade=v;}
int main(void) {
    manager[0x214/4]=4;manager[0x218/4]=3;manager[0x21C/4]=1;
    manager[0x22C/4]=3;manager[0x230/4]=2;manager[0x234/4]=1;
    AFHolidayDedicatedServices s={0,identity,fade_event,lock_wade,maps,sizeof(maps)};
    AFHolidayDedicatedCommon common={-1,-1};AFHolidayControl ctrl={0};
    const unsigned int donors[]={64,12,13,15,14,16,20,1,35,11,41,43,56,37};
    for(unsigned int i=0;i<14;i++) {
        unsigned int donor=donors[i];ctrl.type=af_holiday_native_type(donor);common=(AFHolidayDedicatedCommon){-1,-1};
        assert(af_holiday_dedicated_native(manager,&ctrl,&common,&s,0)==1);
        assert(af_holiday_dedicated_native(manager,&ctrl,&common,&s,2)==(donor==11 || donor==41 || donor==16?0:1));
        status[ctrl.type]=AF_HE_STOP;
        assert(af_holiday_dedicated_native(manager,&ctrl,&common,&s,3)==(donor==11 || donor==41 || donor==16?0:1));
        assert(af_holiday_dedicated_native(manager,&ctrl,&common,&s,1)==(donor==11 || donor==41?0:1));
    }
    assert(clean_calls && control_calls && effect_calls && delete_calls && show_calls && pool_calls && !errors && !wade);
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
    puts("All 14 dedicated owners reach the actual adapter; native IDs, field placement, cleanup variants, and failures pass. N64 I/O and unbound identity/transition providers are doubles.");
}
