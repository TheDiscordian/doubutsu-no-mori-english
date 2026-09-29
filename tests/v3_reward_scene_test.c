#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/reward_scene_native.c"
static unsigned char game_data[2][0x2300],player_data[0xBD0],house[0x954];
static int player,selected=15,fish=1,insects=1,clean=1,job,arbeit,free_slot;
static int friendship=1,setup_ready=1,make_ok=1,make_count,moves,destroys,light_resets;
static int shrine_steps,shrine_active,return_ok=1,returns,wait_flag=1,birthday_mode;
static void *handover;
static ACTOR *talk;
static PRESENT_DEMO_ACTOR director;
static mDemo_Clip_c demo;
static AFRewardBirthday saved;
static lbRTC_time_c clock_data={.year=2026,.month=9,.day=29};
const s32 af_rw_native_scene=7;
const s16 af_rw_native_demo_profile=0xC9;
mDemo_Clip_c *af_rw_demo_clip;
u8 *af_v3_card_data(void) {return player_data;}
int af_rw_player(void) {return player;}
void *af_rw_private(void) {return player>=0 && player<4?player_data:0;}
lbRTC_time_c *af_cw_clock(void) {return &clock_data;}
int af_rw_birthday_month(void) {return birthday_mode?9:1;}
int af_rw_birthday_day(void) {return birthday_mode?29:1;}
int af_rw_calendar_clean(void) {return clean;}
int mEv_CheckFirstJob(void) {return job;}
int mEv_CheckRealArbeit(void) {return arbeit;}
int af_rw_birthday_friendship(void) {return friendship;}
u16 af_rw_birthday_choose(void) {return 0xE015;}
int af_rw_trophy_get(int trophy) {assert(trophy==28 || trophy==31);return 0;}
int mSM_CHECK_ALL_FISH_GET(void) {return fish && selected&8;}
int mSM_CHECK_ALL_INSECT_GET(void) {return insects && selected&1;}
int mPr_GetPossessionItemIdx(void *p,u16 item) {assert(p==player_data && !item);return free_slot;}
int af_v3_player_selected_equipment(u32 item) {
    return item>=0x2239 && item<=0x223C && (selected&(1<<(item-0x2239)))?0:-1;
}
int af_reward_birthday_get(const u8 *cards,unsigned who,AFRewardBirthday *value) {
    assert(cards==player_data && who==(unsigned)player);*value=saved;return 1;
}
int af_reward_birthday_set(u8 *cards,unsigned who,const AFRewardBirthday *value) {
    assert(cards==player_data && who==(unsigned)player);saved=*value;return 1;
}
void af_rw_native_house_door(void *door,int type,ACTOR *actor) {
    assert(door && type>=0 && type<4 && actor==(ACTOR *)house);
}
void af_rw_native_actors_init(GAME *g,void *info,void *entry) {assert(g && info && entry);}
void af_rw_native_actors_move(GAME *g,void *info) {assert(g && info);moves++;}
void af_rw_native_actors_destroy(void *info,GAME *g) {
    assert(info && g && light_resets==destroys+1);destroys++;
}
ACTOR *af_cw_player_actor(GAME *g) {return g?(ACTOR *)player_data:0;}
void *af_cw_handover_master(void) {return handover;}
AFRewardSetupNpc af_rw_npc_setup(void) {return setup_ready?(AFRewardSetupNpc)1:0;}
void *af_hp_actor_info(GAME *g) {return (u8 *)g+0x1C78;}
int af_hp_owned(const ACTOR *a) {return a==(ACTOR *)&director;}
int af_rw_shrine_active(GAME *g) {return g==scene && shrine_active;}
void af_rw_shrine_step(GAME *g) {assert(g==scene);shrine_steps++;}
ACTOR *mDemo_Get_talk_actor(void) {return talk;}
void mDemo_Set_talk_return_demo_wait(int value) {wait_flag=value;}
int mPlib_request_main_demo_get_golden_item2_type1(GAME *g,int type) {
    assert(g==scene && !type);returns++;return return_ok;
}
void af_rw_effect_reset(void *g) {assert(g==scene);light_resets++;}
void af_rw_reward_reset(void) {}
void af_v3_save_halt(int error) {(void)error;abort();}
ACTOR *af_hp_native_make(void *info,GAME *g,int profile,f32 x,f32 y,f32 z,
        int rx,int ry,int rz,int bx,int bz,int unit,u16 name,int arg,int sx,int sz) {
    assert(info==af_hp_actor_info(g) && profile==0xF1 && !x && !y && !z &&
        !rx && !ry && !rz && bx==-1 && bz==-1 && unit==-1 && !name &&
        arg==-1 && sx==-1 && sz==-1);
    AFHPRecord record={.profile=0xF1,.kind=AF_HP_REWARD};
    assert(af_rw_owner_active(&record,g));make_count++;
    if(!make_ok)return 0;
    memset(&director,0,sizeof(director));*(s16 *)&director=0xF1;
    director.type=expected;demo=(mDemo_Clip_c){&director,mDemo_CLIP_TYPE_PRESENT_DEMO};
    af_rw_demo_clip=&demo;return (ACTOR *)&director;
}
static void arm(void) {
    *(s16 *)house=0x66;*(s32 *)(house+0x948)=player;
    af_rw_house_door(player_data,0,(ACTOR *)house);
}
static void enter(void) {af_rw_actors_init(game_data[0],game_data[0],game_data[0]);}
static void move(void) {af_rw_actors_move(game_data[0],game_data[0]);}
static void leave(void) {af_rw_actors_destroy(game_data[0],game_data[0]);}
int main(void) {
    arm();assert(pending.armed && pending.type==aPRD_TYPE_GOLDEN_ROD);
    enter();setup_ready=0;move();assert(!make_count && pending.armed);
    setup_ready=1;make_ok=0;move();assert(make_count==1 && pending.armed && !af_rw_demo_clip);
    make_ok=1;move();assert(make_count==2 && !pending.armed && af_rw_demo_clip);
    AFHPRecord rod={.profile=0xF4,.kind=AF_HP_REWARD},birth={.profile=0xF2,.kind=AF_HP_REWARD};
    assert(af_rw_owner_active(&rod,scene) && !af_rw_owner_active(&birth,scene));
    move();assert(make_count==2);leave();assert(!scene && !af_rw_demo_clip);
    fish=0;arm();assert(pending.type==aPRD_TYPE_GOLDEN_NET);enter();move();leave();
    birthday_mode=1;arm();assert(pending.type==aPRD_TYPE_GOLDEN_NET && !saved.year);
    af_rw_birthday_mode=1;arm();assert(pending.type==aPRD_TYPE_BIRTHDAY && !saved.year);
    enter();make_ok=0;move();assert(!saved.year && !saved.giver);
    make_ok=1;move();assert(saved.year==2026 && saved.giver==0xE015);
    assert(af_rw_owner_active(&birth,scene) && !af_rw_owner_active(&rod,scene));leave();
    arm();assert(pending.type==aPRD_TYPE_GOLDEN_NET);pending=(Pending){0};
    saved=(AFRewardBirthday){0};clean=0;arm();assert(pending.type==aPRD_TYPE_GOLDEN_NET);
    clean=1;arbeit=1;arm();assert(pending.type==aPRD_TYPE_GOLDEN_NET);
    arbeit=0;friendship=0;arm();assert(pending.type==aPRD_TYPE_GOLDEN_NET);
    friendship=1;free_slot=-1;arm();assert(!pending.armed);free_slot=0;
    job=1;arm();assert(!pending.armed);job=0;
    selected=0;af_rw_birthday_mode=0;arm();assert(!pending.armed);
    af_rw_birthday_mode=1;arm();assert(pending.armed && pending.type==aPRD_TYPE_BIRTHDAY);
    enter();af_rw_birthday_mode=0;move();assert(!pending.armed);leave();
    selected=15;
    arm();enter();player=1;move();assert(!pending.armed);player=0;leave();
    arm();enter();mDemo_Set_talk_return_get_golden_axe_demo(1);
    talk=(ACTOR *)house;move();assert(!returns);
    talk=0;handover=house;move();assert(!returns);
    handover=0;return_ok=0;move();assert(returns==1 && axe_return && wait_flag);
    return_ok=1;move();assert(returns==2 && !axe_return && !wait_flag);leave();
    assert(moves && shrine_steps && destroys==light_resets);
    puts("Reward scenes: profile gates, rod/net/birthday priority, refused construction rollback, one spawn, player changes, acknowledgement return, and light-before-scene cleanup pass. Native services are doubled.");
}
