#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "creature_insect_manager.h"
#include "calendar.h"
const u8 af_insect_rtc[]={0,0,12,15,0,7,7,212}; /* 2004-07-15 noon */
u32 af_v3_insect_spawn_mode;
static unsigned selected,original_calls,season_calls,made,colony_calls,live,colony;
static int weather;static float random_number;
static AfInsectInit created;
static u16 fg[256],deposit[16];static SpawnU32 collision[256];
static unsigned block;
static int manager[0x42E8/4];static int game;
float fqrand(void) {return random_number;}
u32 af_v3_creature_profile_byte(u32 byte) {return byte==1?(selected&127)<<1:byte==2?selected>>7:0;}
int af_insect_spawn_original(void *m,GAME *g) {assert(m==manager && g==(GAME *)&game);++original_calls;return 7;}
static void acre(int x,int z) {assert(x==3 && z==4);}
const u16 *af_insect_foreground(int x,int z) {acre(x,z);return fg;}
const u16 *af_insect_deposits(int x,int z) {acre(x,z);return deposit;}
const SpawnU32 *af_insect_collision_map(int x,int z) {acre(x,z);return collision;}
u32 af_insect_block_kind(int x,int z) {acre(x,z);return block;}
int af_insect_weather(void) {return weather;}
int af_insect_rank(void) {return 6;}
void af_insect_tile_position(xyz_t *p,int bx,int bz,int x,int z) {
    acre(bx,bz);assert(x>=2 && x<14 && z>=2 && z<14);
    *p=(xyz_t){bx*640.0f+x*40.0f,0,bz*640.0f+z*40.0f};
}
int af_insect_occupied_acre(int x,int z) {acre(x,z);return live;}
int af_insect_colony_present(int x,int z,GAME *g) {acre(x,z);assert(g==(GAME *)&game);return colony;}
int af_insect_saved_season(SpawnTerms *t,SpawnDate d,SpawnRandom r,void *p) {
    (void)r;(void)p;assert(d.year==2004 && d.month==7 && d.day==15);
    ++season_calls;*t=(SpawnTerms){6,6,1};return 1;
}
int af_insect_make_colony(AfInsectInit *i,int x,int z) {acre(x,z);created=*i;++colony_calls;return 1;}
static ACTOR *make(AfInsectInit *i,int release) {assert(!release);created=*i;++made;return (ACTOR *)&created;}
static AfNativeInsectClip clip={make,0,0,0};AfNativeInsectClip *af_insect_native_clip=&clip;
int mCoBG_CheckWaterAttribute(u32 a) {return (a>=12 && a<=21) || a==24;}
int mCoBG_CheckHole_OrgAttr(u32 a) {return a==0;}
int main(void) {
    manager[0x4180/4]=3;manager[0x4184/4]=4;
    assert(af_v3_insect_spawn(manager,(GAME *)&game)==7 && original_calls==1);
    af_v3_insect_spawn_mode=1;selected=1;weather=1;
    for (unsigned i=0;i<256;i++) {fg[i]=0xFFFF;collision[i]=7;}
    fg[5*16+6]=0x845;
    assert(af_v3_insect_spawn(manager,(GAME *)&game)==1);
    assert(created.type==32 && created.position.x==2180 && created.position.z==2780 && created.game==(GAME *)&game);
    assert(season_calls==1 && made==1 && !colony_calls);
    assert(af_v3_insect_spawn(manager,(GAME *)&game)==1 && season_calls==1 && made==2);
    live=1;assert(!af_v3_insect_spawn(manager,(GAME *)&game) && made==2);live=0;
    colony=1;assert(!af_v3_insect_spawn(manager,(GAME *)&game) && made==2);colony=0;
    af_v3_insect_spawn_reset();assert(af_v3_insect_spawn(manager,(GAME *)&game)==1 && season_calls==2);
    selected=64;weather=0;fg[5*16+6]=0x2806;
    assert(af_v3_insect_spawn(manager,(GAME *)&game)==1 && created.type==38 && colony_calls==1 && made==3);
    assert(season_calls==3);
    /* A disabled ant cannot create a colony even when candy is present. */
    selected=0;assert(!af_v3_insect_spawn(manager,(GAME *)&game) && colony_calls==1);
    af_v3_insect_spawn_mode=0;selected=64;random_number=0;
    assert(af_v3_insect_spawn(manager,(GAME *)&game)==7 && original_calls==2);
    random_number=.9999f;assert(af_v3_insect_spawn(manager,(GAME *)&game)==1 && colony_calls==2);
    block=0x400000;assert(!af_v3_insect_spawn(manager,(GAME *)&game));block=0;
    manager[0x4180/4]=-1;assert(!af_v3_insect_spawn(manager,(GAME *)&game));manager[0x4180/4]=3;
    af_insect_native_clip=0;assert(!af_v3_insect_spawn(manager,(GAME *)&game));
    puts("Native insect manager: source spawning, creation, cache, selection, colonies, and original fallback pass");
}
