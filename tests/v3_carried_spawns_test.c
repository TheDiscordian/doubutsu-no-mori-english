#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "creature_carried.h"
#include "creature_insect_manager.h"
int af_carried_insect_spawn(void *,GAME *);
const u8 af_insect_calendar[]={
#include "calendar.inc"
};
const u32 af_insect_calendar_bytes=sizeof(af_insect_calendar);
static AfSpiritCommon common;
static u16 status,fg[256],deposit[16];
static u32 collision[256],block;
static int enabled,ordinary,occupied,colony,weather,rank=6,countdown,has_lake,created,creation_fails;
static unsigned random_calls,random_length;
static float random_values[32];
static AfInsectInit birth;
static GAME *const game=(GAME *)&birth;
static ACTOR actor;
static ACTOR *make(AfInsectInit *init,int released) {
    assert(!released);birth=*init;++created;return creation_fails?0:&actor;
}
static AfNativeInsectClip clip={make,0,0,0};
AfNativeInsectClip *af_insect_native_clip=&clip;
u32 af_carried_quantity(u32 item) {assert(item==0x2D28);return enabled;}
float fqrand(void) {
    assert(random_calls<32);unsigned n=random_calls++;
    return n<random_length?random_values[n]:0;
}
int af_v3_insect_spawn(void *m,GAME *g) {assert(m && g==game);++ordinary;return 7;}
u32 af_insect_block_kind(int x,int z) {assert(x>0 && z>0);return block;}
int af_insect_occupied_acre(int x,int z) {(void)x;(void)z;return occupied;}
int af_insect_colony_present(int x,int z,GAME *g) {(void)x;(void)z;assert(g==game);return colony;}
const u16 *af_insect_foreground(int x,int z) {(void)x;(void)z;return fg;}
const u16 *af_insect_deposits(int x,int z) {(void)x;(void)z;return deposit;}
const u32 *af_insect_collision_map(int x,int z) {(void)x;(void)z;return collision;}
int af_insect_weather(void) {return weather;}
int af_insect_rank(void) {return rank;}
void af_insect_tile_position(xyz_t *p,int x,int z,int ux,int uz) {
    *p=(xyz_t){x*640.0f+ux*40.0f,17,z*640.0f+uz*40.0f};
}
int af_holiday_calendar_status(int event,int mask) {assert(event==6 && mask==1);return countdown;}
int af_carried_find_block(int *x,int *z,u32 kind) {assert(kind==0x8000);*x=2;*z=3;return has_lake;}
int mCoBG_CheckWaterAttribute(u32 a) {return (a>=12 && a<=21) || a==24;}
int mCoBG_CheckHole_OrgAttr(u32 a) {return a<3;}
static void reset(void) {created=ordinary=0;random_calls=random_length=0;}
int main(void) {
    union {u32 align;u8 bytes[0x4188];} manager={0};
    int *acre=(int *)(manager.bytes+0x4180);acre[0]=2;acre[1]=3;
    common.flags=0x4000;common.hitodama_block_data.block_x[0]=2;
    common.hitodama_block_data.block_z[0]=3;status=0x10;enabled=1;
    af_carried_spirit_event_bind(0,0);
    assert(af_carried_insect_spawn(&manager,game)==7 && ordinary==1);
    af_carried_spirit_event_bind(&common,&status);
    for(unsigned i=0;i<4;i++) {
        reset();enabled=i!=0;status=i==1?0:i==2?0x30:0x10;common.flags=i==3?0:0x4000;
        assert(af_carried_insect_spawn(&manager,game)==7 && ordinary==1 && !created);
    }
    enabled=1;status=0x10;common.flags=0x4000;reset();
    assert(af_carried_insect_spawn(&manager,game)==1 && created==1 && !ordinary);
    assert(birth.type==40 && !birth.extra && birth.game==game && random_calls==3);
    assert(birth.position.x==1380 && birth.position.z==2020 && birth.position.y==17);
    for(unsigned i=0;i<5;i++) {
        memset(&common.hitodama_block_data,0,sizeof(common.hitodama_block_data));
        common.hitodama_block_data.block_x[i]=2;common.hitodama_block_data.block_z[i]=3;
        reset();assert(af_carried_insect_spawn(&manager,game)==1 && created==1);
    }
    reset();acre[0]=1;occupied=1;
    assert(af_carried_insect_spawn(&manager,game)==7 && ordinary==1);acre[0]=2;occupied=0;
    for(unsigned i=0;i<3;i++) {
        reset();occupied=i==0;colony=i==1;block=i==2?0x400000:0;
        assert(!af_carried_insect_spawn(&manager,game) && !created && !ordinary && !random_calls);
    }
    occupied=colony=0;block=0x200000;reset();
    assert(af_carried_insect_spawn(&manager,game)==7 && ordinary==1);block=0;
    /* Retain the complete habitat/rank rules, including food suppression. */
    reset();fg[2*16+2]=0x2806;
    assert(!af_carried_insect_spawn(&manager,game) && !created && !ordinary);fg[2*16+2]=0;
    reset();rank=0;random_values[0]=.75f;random_length=1;
    assert(!af_carried_insect_spawn(&manager,game) && !created);rank=6;
    reset();creation_fails=1;assert(!af_carried_insect_spawn(&manager,game) && created==1);creation_fails=0;
    reset();af_insect_native_clip=0;assert(!af_carried_insect_spawn(&manager,game));af_insect_native_clip=&clip;
    /* Source countdown relocates a lake spirit, then uses the ordinary acre
     * plan. Forbidden column, row, and 0/2/4 duplicates consume source RNG. */
    memset(&common.hitodama_block_data,0,sizeof(common.hitodama_block_data));
    common.hitodama_block_data.block_x[0]=2;common.hitodama_block_data.block_z[0]=3;
    common.hitodama_block_data.block_x[2]=1;common.hitodama_block_data.block_z[2]=1;
    countdown=has_lake=1;reset();
    float sequence[]={.25f,0, 0,.45f, 0,0, .45f,.65f};
    memcpy(random_values,sequence,sizeof(sequence));random_length=8;
    assert(af_carried_insect_spawn(&manager,game)==7 && !created && ordinary==1 && random_calls==8);
    assert(common.hitodama_block_data.block_x[0]==3 && common.hitodama_block_data.block_z[0]==4);
    assert(!af_carried_insect_spawn(0,game) && !af_carried_insect_spawn(&manager,0));
    puts("Carried spawning: real event binding, five acres, native delegation, habitat, group creation, and countdown pass");
}
