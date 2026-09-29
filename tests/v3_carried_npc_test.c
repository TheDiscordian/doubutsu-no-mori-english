/* Changed registry admission, native field widths, and translucent submission.
 * Native services are doubles; this is not in-game execution. */
#include <assert.h>
#include <string.h>
#include <stdint.h>
#include <stdio.h>
#include "carried_event.h"
#include "room_rigs.h"
#include "npc_registry.h"
const u32 af_hp_available=AF_HP_TEST_AVAILABLE;
u32 af_cw_available=1;
static u32 selected=1;
static int deleted,constructed,destroyed,drawn,steps;
static u8 area[8];
static aNPC_ct_data_c callbacks;
static int descriptor;
static AFNpcExtra extra={.name=0xD0CD,.profile=0xF0,.flags=3,.descriptor=(u8 *)&descriptor};
static u32 clip[80];
const u32 *volatile af_hp_native_npc_clip=clip;
const volatile u8 af_hp_native_ticks=2;
AFHPResident af_hp_native_events[5];
u32 af_carried_quantity(u32 item) {assert(item==0x2D28);return selected;}
int af_holiday_observers_clip(void) {return 1;}
static void draw(ACTOR *a,GAME *g) {(void)a;(void)g;drawn++;}
static void move(ACTOR *a,GAME *g) {(void)a;(void)g;steps++;}
static void ctor(ACTOR *a,GAME *g) {
    assert(af_hp_admit(a,g));callbacks=(aNPC_ct_data_c){.move=move,.draw=draw};
    assert(af_hp_npc_callbacks(a,&callbacks));af_hp_constructed(a);constructed++;
}
static void dtor(ACTOR *a,GAME *g) {(void)a;(void)g;destroyed++;}
static const ACTOR_PROFILE source={.source_profile=0xB7,.actor_bytes=2392,
    .ctor=ctor,.dtor=dtor,.move=move,.draw=draw};
const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={
    {0,0,0xD9,15,8,0,7,0,&source,16},
    [22]={0xD06F,0xD0CD,0xF0,114,54,1,3,1,&source,0}
};
const AFHPNpcServices af_hp_npc_services={.draw_proc=draw};
void Actor_delete(ACTOR *a) {assert(a);deleted++;}
const AFNpcExtra *af_v3_npc_extra_owned(const void *a) {
    return a && ((const ACTOR *)a)->npc_id==extra.name?&extra:0;
}
void *mEv_get_save_area(int type,int id) {assert(type==114 && id==54);return area;}
void *mEv_reserve_save_area(int type,int id) {return mEv_get_save_area(type,id);}
int af_holiday_native_type(unsigned type) {(void)type;return -1;}
int af_hp_native_event_status(int type,int mask) {(void)type;(void)mask;return 0;}
void *af_hp_previous_descriptor(int profile) {assert(profile==0xF0);return &descriptor;}
AFHPResident *af_hp_previous_event(u16 n) {(void)n;return 0;}
void af_hp_previous_unregister(u16 n) {(void)n;}
void af_hp_previous_clear(void) {}
void af_hp_previous_free(ACTOR *a) {(void)a;}
int af_hp_native_resident_index(u16 name) {(void)name;return -1;}
int af_hp_native_resident_valid(int index,u16 name) {(void)index;(void)name;return 0;}
void af_hp_native_dying(int type,ACTOR *a) {assert(type==115 && a);}
lbRTC_time_c *af_cw_clock(void) {static lbRTC_time_c time={.hour=3,.min=59,.sec=58};return &time;}
int main(void) {
    assert(af_hp_owner_enabled(af_hp_records)==(AF_HP_TEST_AVAILABLE!=0));
    assert(af_hp_owner_enabled(af_hp_records+22));
    assert(af_hp_identity(0,0xD06F)==0xD0CD);
    assert(af_hp_name_profile(0xD0CD)==0xF0 && af_hp_name_profile(0xD0CE)==-1);
    assert(af_hp_descriptor(0xF0)==&descriptor);
    _Alignas(16) u8 bytes[2400]={0};ACTOR *actor=(ACTOR *)bytes;u16 profile=0xF0;
    memcpy(bytes,&profile,2);actor->npc_id=0xD0CD;
    const void *owner=&descriptor;memcpy(bytes+0x170,&owner,sizeof owner);
    RoomRigGraphics graphics={0};RoomRigGraphics *game=&graphics;
    assert(af_hp_owned(actor) && af_hp_admit(actor,&game));
    af_hp_ctor(actor,&game);assert(constructed==1 && !deleted);
    callbacks.move(actor,&game);assert(steps==1);
    selected=0;assert(!af_hp_owner_enabled(af_hp_records+22));
    assert(af_hp_identity(0,0xD06F)==-1 && !af_hp_admit(actor,&game));
    callbacks.move(actor,&game);assert(deleted==1 && steps==1);
    af_hp_dtor(actor,&game);assert(destroyed==1); /* teardown survives deselection */
    selected=1;af_cw_available=0;assert(!af_hp_admit(actor,&game));
    af_cw_available=1;assert(af_hp_admit(actor,&game));
    memset(bytes+0x24,0x5A,4);*af_cw_actor_specific(actor)=-123;
    assert(*(s16 *)(bytes+0x24)==-123 && bytes[0x26]==0x5A && bytes[0x27]==0x5A);
    memset(bytes+0x930,0x5A,8);*af_cw_melody(actor)=7;
    assert(*(s32 *)(bytes+0x930)==7 && bytes[0x934]==0x5A);
    assert((u8 *)af_cw_scale(actor)==bytes+0x5C && af_cw_shadow(actor)==bytes+0x108);
    assert(af_cw_seconds()==14398);
    _Alignas(8) RoomCommand commands[8]={0};graphics.xlu_head=commands;graphics.xlu_tail=(u8 *)(commands+8);
    af_cw_draw(actor,&game,140);assert(drawn==1 && graphics.xlu_head==commands+2);
    assert(commands[0].a==0xE7000000 && !commands[0].b);
    assert(commands[1].a==0xFB000000 && commands[1].b==0xFFFFFF8C);
    graphics.xlu_tail=(u8 *)(commands+3);af_cw_draw(actor,&game,1);assert(drawn==1);
    graphics.xlu_tail=(u8 *)(commands+8);af_cw_draw(actor,&game,256);assert(drawn==1);
    selected=0;af_cw_draw(actor,&game,1);assert(drawn==1);
    puts("carried NPC shared registry, native fields, and translucent commands pass");return 0;
}
