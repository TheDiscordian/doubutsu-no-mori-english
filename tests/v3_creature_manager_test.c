#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#define AF_V3_CLOTHING_PROFILE 1
#define AF_V3_REWARD_PROFILE 1
#define AF_V3_SURFACE_PROFILE 1
#define AF_V3_CREATURE_PROFILE 1
#define AF_FISH_CALENDAR_BYTES 3340
#include "../overlays/v3/creature_manager.c"
#include "../overlays/v3/creature_save.c"
#include "../overlays/v3/creature_spawns.c"
struct AfSaveRuntime af_creature_test_state;
u8 af_spawn_test_rtc[8]={0,0,12,10,0,6,7,214}; /* June 10, 2006 */
u8 af_spawn_test_history[4],af_spawn_test_event_area;
u32 af_spawn_test_history_slot,af_v3_fish_spawn_mode;
const u8 *af_spawn_test_calendar;
static unsigned mask=0x1FFFF,block=0x800,ground[256],draws,creates,original_calls;
static SpawnNativeData last;
static float value=0.9f;
static int event,weather,terrain=1;
int af_spawn_original(void *m,void *g) {assert(m && g);original_calls++;return 73;}
int af_spawn_make(void *m,SpawnNativeData *d,void *g) {
    assert(m && g && d->spawn==1 && d->extra==0 && d->x>=2 && d->x<14 && d->z>=2 && d->z<14);
    last=*d;creates++;return 1;
}
float af_patrol_random(void) {draws++;return value;}
int af_spawn_event(int id,int active) {assert((id==2 || id==20) && active==1);return event;}
int af_spawn_weather(void) {return weather;}
int af_spawn_rank(void) {return 3;}
const unsigned *af_spawn_collision(int x,int z) {assert(x==3 && z==4);return ground;}
unsigned af_water_block(int x,int z) {assert(x==3 && z==4);return block;}
int af_v3_water_site(void *ctx,unsigned actor,unsigned x,unsigned z) {
    FishWaterBlock *b=ctx;assert(b->bx==3 && b->bz==4 && b->collision==ground);
    assert(actor<45 && (actor<32 || actor>=35));assert(x>=2 && x<14 && z>=2 && z<14);
    return terrain;
}
int af_creature_item_type(u32 item) {
    u32 i=item<0x2D00 ? item-0x2320 : item-0x2D20+9;
    return i<17 && (mask&(1u<<i)) ? (i<9 ? 8 : 18) : 0;
}
void af_v3_require_save_state(void) {}
void af_v3_save_halt(int e) {(void)e;abort();}
static void history_clear(void) {memset(af_spawn_test_history,0,4);af_spawn_test_history_slot=0;}
int main(int argc,char **argv) {
    assert(argc==2);FILE *f=fopen(argv[1],"rb");assert(f);
    u8 data[AF_FISH_CALENDAR_BYTES];assert(fread(data,1,sizeof(data),f)==sizeof(data));assert(fgetc(f)==EOF);fclose(f);
    af_spawn_test_calendar=data;
    union {unsigned align;u8 data[0x42E8];} m;memset(&m,0,sizeof(m));
    int *acre=(int *)(m.data+0x4180);acre[0]=3;acre[1]=4;
    mask=0;
    assert(af_v3_fish_spawn(m.data,&m)==73 && original_calls==1 && draws==0);
    mask=0x1FFFF;
    value=0.0f;
    assert(af_v3_fish_spawn(m.data,&m)==73 && original_calls==2);
    assert(!af_spawn_test_history_slot && !af_spawn_test_history[0]);
    assert(!af_creature_test_state.working[AF_SAVE_CREATURE_OFFSET+22]);
    value=0.99f;
    assert(af_v3_fish_spawn(m.data,&m)==1 && last.actor>=39 && last.actor<=42);
    assert(!af_creature_test_state.working[AF_SAVE_CREATURE_OFFSET+22]);
    history_clear();block=0;
    assert(af_v3_fish_spawn(m.data,&m)==1 && last.actor>=36 && last.actor<=38);
    assert(original_calls==2); /* Pond has no artificial native/no-fish mass. */
    history_clear();block=0x800;value=0.9f;creates=0;
    af_v3_fish_spawn_mode=1;
    assert(af_v3_fish_spawn(m.data,&m)==1 && last.actor>=39 && last.actor<=42);
    assert(creates==1 && af_creature_test_state.working[AF_SAVE_CREATURE_OFFSET+22]==1);
    unsigned previous=draws;assert(af_v3_fish_spawn(m.data,&m)==0 && draws==previous);
    history_clear();previous=draws;
    assert(af_v3_fish_spawn(m.data,&m)==1 && draws==previous+2); /* No season reroll. */
    mask=0;history_clear();assert(af_v3_fish_spawn(m.data,&m)==0);
    mask=0x1FFFF;block=0;history_clear();assert(af_v3_fish_spawn(m.data,&m)==1);
    assert(last.actor==36 || last.actor==37); /* Whole pond calendar, not native twenty-row storage. */
    block=0x80|0x8000;event=1;value=0.5f;history_clear();
    assert(af_v3_fish_spawn(m.data,&m)==1 && last.actor>=4 && last.actor<=6);
    event=0;terrain=0;history_clear();previous=creates;
    assert(af_v3_fish_spawn(m.data,&m)==0 && creates==previous);
    af_spawn_test_rtc[2]=24;history_clear();previous=draws;
    assert(af_v3_fish_spawn(m.data,&m)==0 && draws==previous);
    puts("pass: both population alternatives, selected sea/pond spawning, tournament, acre protection, saved seasons, invalid inputs");
}
