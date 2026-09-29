#include <assert.h>
#include <stdint.h>
#include <string.h>
#include "../overlays/v3/reward_shrine_native.c"
static ACTOR shrine,player;
static NPC_ACTOR hem;
static int game,other,window,choice_window,private_data;
static int selected=1,normal=1,choice,rank_value=6,condition=3,perfect=1,trophy,slot=0,job;
static int disappeared,setup_ready=1,make_ok=1,find_hem=1,original_talk,ctors,dtors,forced,messages;
static int setups,effects,resets,waited,visible,can_force=1,player_ready=1;
static struct {void (*anime)(void);int flag;u32 guard;} native;
AFHPShrine *volatile af_hp_native_shrine;
static void anime(void) {native.flag=1;}
void af_rw_native_shrine_ctor(ACTOR *a,GAME *g) {
    assert(a==&shrine && g==&game);++ctors;af_hp_native_shrine=(AFHPShrine *)&native;
}
void af_rw_native_shrine_dtor(ACTOR *a,GAME *g) {
    assert(a==&shrine && g==&game);++dtors;af_hp_native_shrine=0;
}
void af_rw_native_shrine_talk(ACTOR *a,GAME *g) {assert(a==&shrine && g==&game);++original_talk;}
void af_rw_native_shrine_action(ACTOR *a,int index) {assert(a==&shrine && index==3);}
int af_v3_player_selected_equipment(u32 item) {assert(item==0x223A);return selected?0:-1;}
void *mMsg_Get_base_window_p(void) {return &window;}
int mMsg_Check_MainNormalContinue(void *w) {assert(w==&window);return normal;}
void *mChoice_Get_base_window_p(void) {return &choice_window;}
int mChoice_Get_ChoseNum(void *w) {assert(w==&choice_window);return choice;}
int af_rw_field_condition(int *r,int *x,int *z) {*r=rank_value;*x=2;*z=3;return condition;}
int mFAs_CheckGoodField(void) {return perfect;}
int af_rw_trophy_get(int index) {assert(index==29);return trophy;}
int af_rw_player(void) {return 2;}
void *af_rw_private(void) {return &private_data;}
int mPr_GetPossessionItemIdx(void *p,u16 item) {assert(p==&private_data && !item);return slot;}
int mEv_CheckFirstJob(void) {return job;}
ACTOR *af_cw_player_actor(GAME *g) {return g==&game && player_ready?&player:0;}
void af_rw_continue_message(void *w,int message) {assert(w==&window && message==0x2C50);++messages;}
void mDemo_Set_talk_return_demo_wait(int yes) {assert(yes);++waited;}
void af_rw_native_force_speak(ACTOR *a) {assert(a==&shrine || a==(ACTOR *)&hem);++forced;}
int mPlib_Check_able_force_speak_label(GAME *g,ACTOR *a) {assert(g==&game && a==&shrine);return can_force;}
int af_rw_native_message_disappear(void *w) {assert(w==&window);return disappeared;}
void *af_hp_actor_info(GAME_PLAY *g) {assert(g==&game);return &game;}
ACTOR *Actor_info_fgName_search(void *info,u16 name,int part) {
    assert(info==&game && name==0xD0CF && part==3);return find_hem?(ACTOR *)&hem:0;
}
static int make(GAME_PLAY *g,u16 name,int rx,int ry,int rz,int bx,int bz,int x,int z) {
    assert(g==&game && name==0xD0CF && rx==-1 && ry==-1 && rz==-1 && bx==2 && bz==3 && x==7 && z==8);
    ++setups;return make_ok;
}
AFRewardSetupNpc af_rw_npc_setup(void) {return setup_ready?make:0;}
int *af_rw_hem_visible(void) {return &visible;}
static void effect(int id,xyz_t p,int priority,s16 angle,GAME *g,u16 name,s16 a,s16 b) {
    assert(id==eEC_EFFECT_MAKE_HEM && p.x==shrine.world.position.x &&
        p.z==shrine.world.position.z+40 && priority==2 && !angle &&
        g==&game && name==0xFFFF && a==1 && !b);++effects;
}
const AFHPEffects af_rw_effects={.effect_make_proc=effect};
void af_rw_effect_reset(void *g) {assert(g==&game);++resets;visible=0;}
int main(void) {
    native.anime=anime;native.guard=0xA5A55A5A;
    shrine.block_x=2;shrine.block_z=3;shrine.world.position=(xyz_t){2128,0,1488};
    assert(!af_rw_shrine());af_rw_shrine_ctor(&shrine,&game);
    assert(ctors==1 && af_rw_shrine() && !af_rw_shrine_active(&game));
    af_rw_shrine()->anime_play_proc();assert(native.flag==1 && native.guard==0xA5A55A5A);
    selected=0;af_rw_shrine_talk(&shrine,&game);selected=1;
    rank_value=5;af_rw_shrine_talk(&shrine,&game);rank_value=6;
    condition=0;af_rw_shrine_talk(&shrine,&game);condition=3;
    perfect=0;af_rw_shrine_talk(&shrine,&game);perfect=1;
    trophy=1;af_rw_shrine_talk(&shrine,&game);trophy=0;
    slot=-1;af_rw_shrine_talk(&shrine,&game);slot=0;
    job=1;af_rw_shrine_talk(&shrine,&game);job=0;
    normal=0;af_rw_shrine_talk(&shrine,&game);normal=1;
    choice=1;af_rw_shrine_talk(&shrine,&game);choice=0;
    player_ready=0;af_rw_shrine_talk(&shrine,&game);player_ready=1;
    assert(original_talk==10 && !messages && !waited && !setups && !effects);
    af_rw_shrine_talk(&shrine,&game);
    assert(messages==1 && waited==1 && forced==1 && af_rw_shrine_active(&game));
    assert(!af_rw_shrine_active(&other));
    af_rw_shrine_step(&other);af_rw_shrine_step(&game);assert(!setups);
    disappeared=1;setup_ready=0;af_rw_shrine_step(&game);assert(!setups);setup_ready=1;
    make_ok=0;af_rw_shrine_step(&game);assert(setups==1 && !effects);make_ok=1;
    af_rw_shrine_step(&game);
    assert(setups==2 && effects==1 && forced==2 && af_rw_shrine()->hem_flag && !visible);
    assert(*(u32 *)(hem.native+0x14C)==(u32)(__UINTPTR_TYPE__)&shrine);
    af_rw_shrine_step(&game);assert(setups==2 && effects==1);
    af_rw_shrine()->hem_flag=0;af_rw_shrine_step(&game);assert(!af_rw_shrine_active(&game));
    assert(!trophy && perfect); /* only insertion may acknowledge either */
    af_rw_shrine_dtor(&shrine,&game);
    assert(dtors==1 && resets==1 && !af_rw_shrine() && native.guard==0xA5A55A5A);
    return 0;
}
