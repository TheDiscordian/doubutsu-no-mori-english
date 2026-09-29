/* The complete shared registry runs unchanged with recorded native services.
 * Scene admission is doubled; this does not claim native actor execution. */
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "holiday_participants.h"
#include "npc_registry.h"
static unsigned enabled=1,active=1,deleted,constructed,destroyed,areas,statuses;
const u32 af_hp_available=0;
const volatile u8 af_hp_native_ticks=2;
AFHPResident af_hp_native_events[5];
static AFNpcExtra special;
static int game;
static void ctor(ACTOR *a,GAME *g) {
    assert(g==&game && af_hp_admit(a,g));++constructed;af_hp_constructed(a);
}
static void dtor(ACTOR *a,GAME *g) {(void)a;assert(g==&game);++destroyed;}
static void step(ACTOR *a,GAME *g) {(void)a;assert(g==&game);}
static const ACTOR_PROFILE director={.source_profile=0xC6,.actor_bytes=400,
    .ctor=ctor,.dtor=dtor,.move=step,.draw=step};
static const ACTOR_PROFILE gift={.source_profile=0xC7,.actor_bytes=2392,
    .ctor=ctor,.dtor=dtor,.move=step,.draw=step};
static const ACTOR_PROFILE hem={.source_profile=0xF2,.actor_bytes=2388,
    .ctor=ctor,.dtor=dtor,.move=step,.draw=step};
const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={
    [23]={0,0,0xF1,0,0,0,7,AF_HP_REWARD,&director,16},
    [24]={0xD073,0xD0CE,0xF2,0,0,1,3,AF_HP_REWARD,&gift,0},
    [25]={0xD08E,0xD0CF,0xF3,0,0,1,3,AF_HP_REWARD|AF_HP_SPECIAL,&hem,0},
    [26]={0xD073,0xD0D0,0xF4,0,0,1,3,AF_HP_REWARD|AF_HP_SPECIAL,&gift,0},
};
int af_rw_owner_enabled(const AFHPRecord *r) {return enabled && (r->kind&AF_HP_REWARD);}
int af_hp_owner_enabled(const AFHPRecord *r) {return af_rw_owner_enabled(r);}
int af_rw_owner_active(const AFHPRecord *r,GAME *g) {
    return g==&game && af_rw_owner_enabled(r) && active;
}
void Actor_delete(ACTOR *a) {assert(a);++deleted;}
void *mEv_get_save_area(int event,int slot) {(void)event;(void)slot;++areas;return 0;}
void *mEv_reserve_save_area(int event,int slot) {(void)event;(void)slot;++areas;return 0;}
int af_holiday_native_type(unsigned source) {(void)source;++statuses;return -1;}
int af_hp_native_event_status(int event,int status) {(void)event;(void)status;++statuses;return 0;}
const AFNpcExtra *af_v3_npc_extra_owned(const void *a) {(void)a;return &special;}
void *af_hp_previous_descriptor(int profile) {
    assert(profile==0xF3 || profile==0xF4);return (void *)(uintptr_t)(0x1000+profile*32);
}
AFHPResident *af_hp_previous_event(u16 name) {(void)name;return 0;}
void af_hp_previous_unregister(u16 name) {(void)name;}
void af_hp_previous_clear(void) {}
void af_hp_previous_free(ACTOR *a) {assert(a);}
int af_hp_native_resident_index(u16 name) {return name==0xE001?1:-1;}
int af_hp_native_resident_valid(int index,u16 name) {return index==1 && name==0xE001;}
#include "../overlays/v3/holiday_participants_registry.c"
static void actor(u8 *bytes,int index) {
    const AFHPRecord *r=af_hp_records+index;void *descriptor=af_hp_descriptor(r->profile);
    assert(descriptor);memset(bytes,0,2400);
    memcpy(bytes,&r->profile,2);memcpy(bytes+6,&r->name,2);
    memcpy(bytes+0x170,&descriptor,sizeof descriptor);
    if(r->kind&AF_HP_SPECIAL)special=(AFNpcExtra){.flags=3,.profile=r->profile,.descriptor=descriptor};
    assert(af_hp_owned((ACTOR *)bytes));
}
int main(void) {
    _Static_assert(AF_HP_OWNER_COUNT==27 && AF_HP_RESIDENT_COUNT==19 && AF_HP_LIVE_COUNT==28,
        "Complete connected reward capacity");
    _Alignas(16) u8 bytes[2400];ACTOR *a=(ACTOR *)bytes;
    assert(!af_hp_available && af_hp_identity(1,0xC6)==0xF1);
    assert(af_hp_identity(0,0xD073)==0xD0CE);
    assert(af_hp_name_profile(0xD0CE)==0xF2 && af_hp_name_profile(0xD0CF)==0xF3 &&
        af_hp_name_profile(0xD0D0)==0xF4);
    assert(af_hp_resident_bind(0xD073,0xD06E,0)==-1);
    assert(af_hp_resident_bind(0xD073,0xE001,0)==0xD0CE);
    assert(af_hp_event_lookup(0xD0CE)->resident==0xE001);
    for(int index=23;index<27;++index) {
        actor(bytes,index);active=0;
        assert(!af_hp_admit(a,&game));af_hp_ctor(a,&game);
        assert(deleted==(unsigned)(index-22) && constructed==(unsigned)(index-23));
        active=1;assert(af_hp_admit(a,&game) && !af_hp_admit(a,0));
        af_hp_ctor(a,&game);assert(constructed==(unsigned)(index-22));
        af_hp_dtor(a,&game);assert(destroyed==constructed);
    }
    assert(!areas && !statuses); /* no fabricated event storage or calendar RUN */
    enabled=0;assert(af_hp_identity(1,0xC6)==-1 && af_hp_identity(0,0xD073)==-1);
    assert(af_hp_resident_bind(0xD073,0xE001,0)==-1);
    return 0;
}
