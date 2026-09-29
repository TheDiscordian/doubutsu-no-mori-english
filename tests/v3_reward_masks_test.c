#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "../overlays/v3/reward_masks_native.c"
static int game,live=1,enabled=1,active=1,spawns,releases;
static u16 giver=0xE001;
static PRESENT_DEMO_ACTOR demo;
static mDemo_Clip_c demo_clip;
mDemo_Clip_c *af_rw_demo_clip=&demo_clip;
static AFHPResident resident;
const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT]={
    [24]={.name=0xD0CE,.count=1,.kind=AF_HP_REWARD},
    [25]={.name=0xD0CF,.count=1,.kind=AF_HP_REWARD|AF_HP_SPECIAL},
    [26]={.name=0xD0D0,.count=1,.kind=AF_HP_REWARD|AF_HP_SPECIAL},
};
static int spawn(GAME_PLAY *g,u16 name,int rx,int ry,int rz,int bx,int bz,int x,int z) {
    assert(g==&game && (name==0xD0CE || name==0xD0CF || name==0xD0D0));
    assert(rx==-1 && ry==-1 && rz==-1 && bx==2 && bz==3 && x==6 && z==6);
    ++spawns;return 1;
}
static u32 native_clip[0x11C/4];
const u32 *volatile af_hp_native_npc_clip=native_clip;
int af_holiday_observers_clip(void) {return live;}
int af_cw_native_field_width(void) {return 6;}
int af_cw_native_field_height(void) {return 8;}
int af_hp_owned(const ACTOR *a) {return a==&demo.actor_class || (a && a->npc_id==0xD0CE);}
u16 af_rw_birthday_giver(void) {return giver;}
AFHPResident *af_hp_event_lookup(u16 name) {return name==0xD0CE && resident.used?&resident:0;}
int af_hp_resident_bind(u16 source,u16 animal,u16 cloth) {
    assert(source==0xD073 && !cloth);
    if(animal!=0xE001)return -1;
    resident=(AFHPResident){0xD0CE,animal,animal,cloth,0,1,0};return 0xD0CE;
}
void *af_hp_descriptor(int profile) {assert(profile==0xF4);return enabled?&demo:0;}
int af_rw_owner_enabled(const AFHPRecord *r) {return enabled && (r->kind&AF_HP_REWARD);}
int af_rw_owner_active(const AFHPRecord *r,GAME *g) {(void)r;return active && g==&game;}
void af_hp_event_unregister(u16 name) {assert(name==0xD0CE);++releases;resident.used=0;}
int main(void) {
    native_clip[0]=(u32)(__UINTPTR_TYPE__)spawn;
    demo_clip=(mDemo_Clip_c){&demo,mDemo_CLIP_TYPE_PRESENT_DEMO};
    *(s16 *)&demo.actor_class=0xF1;
    demo.type=aPRD_TYPE_BIRTHDAY;
    assert(af_rw_present_name()==0xD0CE && !mNpc_GetSameMaskNpc(0xD0CE));
    assert(!mNpc_RegistMaskNpc(0xD0CE,SP_NPC_EV_SONCHO,0));
    assert(mNpc_RegistMaskNpc(0xD0CE,giver,0) && mNpc_GetSameMaskNpc(0xD0CE)==&resident);
    AFRewardSetupNpc make=af_rw_npc_setup();assert(make);
    assert(make(&game,0xD0CE,-1,-1,-1,2,3,6,6) && spawns==1);
    assert(!make(&game,0xD0CE,-1,-1,-1,6,3,6,6));
    assert(!make(&game,0xD0CE,-1,-1,-1,2,8,6,6));
    assert(!make(&game,0xD0CE,-1,-1,-1,2,3,16,6));
    assert(!make(&game,0xD0CE,0,-1,-1,2,3,6,6));
    assert(!make(&game,0xD090,-1,-1,-1,2,3,6,6));
    giver=0xE002;assert(!mNpc_GetSameMaskNpc(0xD0CE) &&
        !make(&game,0xD0CE,-1,-1,-1,2,3,6,6));giver=0xE001;
    demo.type=aPRD_TYPE_GOLDEN_ROD;
    assert(af_rw_present_name()==0xD0D0 && !mNpc_GetSameMaskNpc(0xD0D0));
    assert(mNpc_RegistMaskNpc(0xD0D0,SP_NPC_EV_SONCHO,0));
    assert(!mNpc_RegistMaskNpc(0xD0D0,giver,0) && !mNpc_RegistMaskNpc(0xD0CE,SP_NPC_EV_SONCHO,0));
    assert(make(&game,0xD0D0,-1,-1,-1,2,3,6,6) && spawns==2);
    assert(!make(&game,0xD0CE,-1,-1,-1,2,3,6,6));
    enabled=0;assert(!mNpc_RegistMaskNpc(0xD0D0,SP_NPC_EV_SONCHO,0) &&
        !make(&game,0xD0D0,-1,-1,-1,2,3,6,6));enabled=1;
    active=0;assert(!make(&game,0xD0CF,-1,-1,-1,2,3,6,6));active=1;
    assert(make(&game,0xD0CF,-1,-1,-1,2,3,6,6) && spawns==3);
    demo.type=aPRD_TYPE_SONCHO_VACATION0_STARTED;
    assert(!af_rw_present_name() && !mNpc_RegistMaskNpc(0xD0D0,SP_NPC_EV_SONCHO,0));
    live=0;assert(!af_rw_npc_setup());live=1;
    ACTOR birthday={0};birthday.npc_id=0xD0CE;af_rw_release_gift_mask(&birthday);
    assert(releases==1 && !resident.used);
    af_rw_release_gift_mask(0);assert(releases==1);
    return 0;
}
