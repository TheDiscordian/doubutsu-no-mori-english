/* Changed participant lifetime and temporary-identity path; native services are
 * doubles. This is not native gameplay or an event-activation test. */
#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "holiday_participants.h"
static int deleted,ctor_count,dtor_count,init_count,move_count,draw_count,free_count;
static int previous_event,previous_clear,previous_unregister,area_present=1;
static u8 area[128];
#ifndef AF_HP_TEST_AVAILABLE
#define AF_HP_TEST_AVAILABLE 1
#endif
const u32 af_hp_available=AF_HP_TEST_AVAILABLE;
const volatile u8 af_hp_native_ticks=2;
AFHPResident af_hp_native_events[5];
static aNPC_ct_data_c callbacks;
static void move(ACTOR *a,GAME *g) {(void)a;(void)g;++move_count;}
static void draw(ACTOR *a,GAME *g) {(void)a;(void)g;++draw_count;}
static void ctor(ACTOR *a,GAME *g) {
    assert(af_hp_admit(a,g));++ctor_count;
    callbacks=(aNPC_ct_data_c){.move=move,.draw=draw};
    assert(af_hp_npc_callbacks(a,&callbacks));af_hp_constructed(a);
}
static void dtor(ACTOR *a,GAME *g) {(void)a;(void)g;++dtor_count;}
static void init(ACTOR *a,GAME *g) {(void)a;(void)g;++init_count;}
static const ACTOR_PROFILE source={.source_profile=0x71,.actor_bytes=2400,.ctor=ctor,.dtor=dtor,.move=init,.draw=draw};
const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={
    {0,0,0xD9,15,8,0,7,0,&source,16},
    {0,0,0xDA,14,9,0,7,0,&source,16},
    {0,0,0xDB,1,7,0,7,0,&source,16},
    {0xD02D,0xD0A0,0xDC,15,8,1,3,0,&source,0},
    {0xD02E,0xD0A1,0xDD,15,8,4,3,0,&source,0},
    {0xD05F,0xD0A5,0xDE,14,9,1,3,0,&source,0},
    {0xD060,0xD0A6,0xDF,14,9,4,3,0,&source,0},
    {0xD058,0xD0AA,0xE0,1,7,4,3,0,&source,0},
};
void Actor_delete(ACTOR *a) {assert(a);++deleted;}
void *mEv_get_save_area(int event,int slot) {
    assert((event==15 && slot==8)||(event==14 && slot==9)||(event==1 && slot==7));
    return area_present?area:0;
}
void *mEv_reserve_save_area(int event,int slot) {
    area_present=1;return mEv_get_save_area(event,slot);
}
void *af_hp_previous_descriptor(int profile) {assert(profile==7);return (void *)(uintptr_t)0x1234;}
AFHPResident *af_hp_previous_event(u16 name) {assert(name==0xD010);++previous_event;return af_hp_native_events;}
void af_hp_previous_unregister(u16 name) {assert(name==0xD010);++previous_unregister;}
void af_hp_previous_clear(void) {++previous_clear;}
void af_hp_previous_free(ACTOR *a) {assert(a);++free_count;}
int af_hp_native_resident_index(u16 name) {return name>=0xE000 && name<0xE00F?name-0xE000:-1;}
int af_hp_native_resident_valid(int index,u16 name) {return index>=0 && index<15 && name==0xE000+index;}
typedef struct {u32 vrom,end,ram,ram_end,loaded;ACTOR_PROFILE *profile;u32 filename;u16 allocation;u8 count,pad;} Descriptor;
static void actor(u8 *storage,u16 profile,u16 name,Descriptor *owner) {
    memset(storage,0,2400);memcpy(storage,&profile,2);memcpy(storage+6,&name,2);
    memcpy(storage+0x170,&owner,sizeof owner);++owner->count;
}
int main(void) {
    if(!AF_HP_TEST_AVAILABLE) {
        assert(af_hp_identity(0,0xD02D)==-1 && af_hp_identity(1,0x71)==-1 && af_hp_identity(2,118)==-1);
        return 0;
    }
    assert(af_hp_identity(1,0x71)==0xD9 && af_hp_identity(2,118)==119);
    assert(af_hp_identity(0,0xD05C)==-1 && af_hp_identity(1,0x72)==-1);
    assert(af_hp_identity(2,70)==-1 && af_hp_identity(3,118)==-1);
    assert(af_hp_descriptor(7)==(void *)(uintptr_t)0x1234);
    assert(af_hp_name_profile(0xD0A0)==0xDC && af_hp_name_profile(0xD0AD)==0xE0);
    assert(af_hp_name_profile(0xD0AE)==-1 && af_hp_name_profile(0xD010)==-1);
    assert(af_hp_event_lookup(0xD010)==af_hp_native_events && previous_event==1);
    af_hp_event_unregister(0xD010);assert(previous_unregister==1);
    assert(af_hp_resident_bind(0xD02D,0xD010,0)==-1);
    af_hp_native_events[0]=(AFHPResident){.resident=0xE000,.used=1};
    assert(af_hp_resident_bind(0xD02D,0xE000,0)==-1);
    memset(af_hp_native_events,0,sizeof af_hp_native_events);
    int slot=0;
    for(unsigned int r=0;r<AF_HP_OWNER_COUNT;r++)for(int i=0;i<af_hp_records[r].count;i++,slot++) {
        assert(af_hp_identity(0,af_hp_records[r].source_name+i)==af_hp_records[r].name+i);
        assert(af_hp_resident_bind(af_hp_records[r].source_name+i,0xE000+slot,0)==af_hp_records[r].name+i);
    }
    assert(slot==14);
    assert(af_hp_resident_bind(0xD02D,0xE000,0)==0xD0A0);
    assert(af_hp_resident_bind(0xD02D,0xE000,1)==-1);
    assert(af_hp_resident_bind(0xD02D,0xE001,0)==-1);
    assert(af_hp_resident_bind(0xD05C,0xE00E,0)==-1);
    _Alignas(16) u8 storage[2400];ACTOR *a=(ACTOR *)storage;int game;
    Descriptor *owner=af_hp_descriptor(0xDC);
    assert(owner && owner->profile->actor_bytes==2400 && owner->profile->part==3);
    actor(storage,0xDC,0xD0A1,owner);assert(!af_hp_owned(a));--owner->count;
    actor(storage,0xDC,0xD0A0,owner);assert(af_hp_owned(a));
    area_present=0;af_hp_ctor(a,&game);assert(ctor_count==1 && !deleted);
    af_hp_step(a,&game);assert(init_count==1);
    callbacks.move(a,&game);callbacks.draw(a,&game);assert(move_count==1 && draw_count==1);
    af_hp_event_unregister(0xD0A0);assert(deleted==1 && af_hp_event_lookup(0xD0A0));
    assert(af_hp_resident_bind(0xD02D,0xE000,0)==-1);
    callbacks.move(a,&game);callbacks.draw(a,&game);
    assert(deleted==2 && move_count==1 && draw_count==1);
    area_present=0;af_hp_dtor(a,&game);assert(dtor_count==1 && !af_hp_event_lookup(0xD0A0));
    af_hp_free(a);assert(owner->count==0 && free_count==1);
    assert(af_hp_resident_bind(0xD02D,0xE000,0)==0xD0A0);
    af_hp_events_clear();assert(previous_clear==1 && !af_hp_event_lookup(0xD0A0));
    assert(af_hp_countdown(0)==0 && af_hp_countdown(1)==0 && af_hp_countdown(2)==0 && af_hp_countdown(7)==5);
    assert(af_hp_elapsed()==2);
    return 0;
}
