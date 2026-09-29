/* Verified sparse native fields; real world adapters with recording services. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_world_native.c"
const volatile u8 af_rw_native_cheated=1;
static _Alignas(16) u8 game_data[0x2300],private_data[0xBD0];
static NPC_ACTOR npc;
static ACTOR player,tool_actor;
static int owned=1,admitted=1,observers=1,have_player=1,state;
static int waits,rewards,saves,tools,effects,kills,last_effect,last_type;
static AFHPResident resident_data;
u8 af_hp_native_animals[15][0x528];
const s16 af_rw_native_weather=1;
static u32 clip_data[0x11C/4];
const u32 *volatile af_hp_native_npc_clip=clip_data;
const AFHPNpcServices af_hp_npc_services={0};
static void save(ACTOR *a,GAME *g) {assert(a==(ACTOR *)&npc && g==game_data);saves++;}
static ACTOR *tool(int kind,int action,ACTOR *a,GAME *g,int arg,void *bank) {
    assert(kind==17 && action==3 && a==(ACTOR *)&npc && g==game_data && arg==-1 && !bank);
    tools++;return &tool_actor;
}
static const AFHPTools native_tools={tool};
const AFHPTools *volatile af_hp_native_tools=&native_tools;
int af_holiday_observers_clip(void) {return observers;}
int af_hp_owned(const ACTOR *a) {return owned && a==(ACTOR *)&npc;}
int af_hp_admit(ACTOR *a,GAME *g) {return admitted && af_hp_owned(a) && g==game_data;}
AFHPResident *af_hp_event_lookup(u16 name) {return name==0xD0CE?&resident_data:0;}
int af_hp_native_resident_index(u16 name) {return name==0xE010?3:-1;}
int af_hp_native_resident_valid(int i,u16 name) {return i==3 && name==0xE010;}
ACTOR *af_cw_player_actor(GAME *g) {return g==game_data && have_player?&player:0;}
int af_hp_native_player_state(GAME *g) {assert(g==game_data && have_player);return state;}
void af_rw_native_wait(GAME *g) {assert(g==game_data && have_player);waits++;}
int af_v3_reward_event(void *g,int type) {assert(g==game_data && have_player);rewards++;last_type=type;return 1;}
void *af_rw_private(void) {return private_data;}
void af_rw_effect_request(int id,xyz_t p,int prio,s16 angle,void *g,u16 item,s16 a,s16 b) {
    assert(prio==1 && !angle && g==game_data && item==0xD0CF && a==2 && b==0 && p.x==40);
    effects++;last_effect=id;
}
void af_rw_effect_kill(int id,u16 item) {assert(item==0xD0CF);kills++;last_effect=id;}
int main(void) {
    assert(!af_rw_calendar_clean());
    assert(sizeof(__UINTPTR_TYPE__)>=4 && (__UINTPTR_TYPE__)save<=0xFFFFFFFFu);
    clip_data[0xC8/4]=(u32)(__UINTPTR_TYPE__)save;
    game_data[0xE4]=2;game_data[0xE5]=3;
    assert(af_rw_block_x(game_data)==2 && af_rw_block_z(game_data)==3);
    assert(af_rw_block_x(0)==-1 && af_rw_block_z(0)==-1 && !af_rw_menu_refuse(0));
    memset(game_data+0x1D9D,0xA5,3);*af_rw_menu_refuse(game_data)=1;
    assert(game_data[0x1D9D]==0xA5 && game_data[0x1D9E]==1 && game_data[0x1D9F]==0xA5);
    assert(af_rw_weather()==1);
    memset(npc.native+0x728,0xA5,3);*af_rw_sub_animation(&npc)=1;
    assert(npc.native[0x728]==0xA5 && npc.native[0x729]==1 && npc.native[0x72A]==0xA5);
    assert(!af_rw_sub_animation(0));
    npc.native[0x85F]=17;assert(af_rw_umbrella(&npc)==17);
    assert(af_rw_tools.aTOL_birth_proc(17,aTOL_ACTION_S_TAKEOUT,(ACTOR *)&npc,game_data,-1,0)==&tool_actor);
    assert(tools==1 && !af_rw_tools.aTOL_birth_proc(32,aTOL_ACTION_S_TAKEOUT,(ACTOR *)&npc,game_data,-1,0));
    assert(!af_rw_tools.aTOL_birth_proc(17,aTOL_ACTION_TAKEOUT,(ACTOR *)&npc,game_data,-1,0));
    assert(!af_rw_tools.aTOL_birth_proc(17,aTOL_ACTION_S_TAKEOUT,(ACTOR *)&npc,game_data,-1,&npc));
    npc.actor_class.npc_id=0xD0CE;resident_data=(AFHPResident){0xD0CE,0xE010,0xE010,0,0,1,0};
    *(u32 *)(npc.native+0x174)=(u32)(__UINTPTR_TYPE__)af_hp_native_animals[3];
    assert(af_rw_is_resident(&npc));
    *(u32 *)(npc.native+0x174)=0;assert(!af_rw_is_resident(&npc));
    resident_data.resident=0xD090;assert(!af_rw_is_resident(&npc));
    assert(af_rw_npc_services()==&af_hp_npc_services);
    af_rw_npc_save((ACTOR *)&npc,game_data);assert(saves==1);
    observers=0;af_rw_npc_save((ACTOR *)&npc,game_data);assert(saves==1 && !af_rw_npc_services());
    observers=1;admitted=0;af_rw_npc_save((ACTOR *)&npc,game_data);assert(saves==1);
    assert(!af_rw_tools.aTOL_birth_proc(17,aTOL_ACTION_S_TAKEOUT,(ACTOR *)&npc,game_data,-1,0));
    owned=0;assert(!af_rw_sub_animation(&npc) && af_rw_umbrella(&npc)==0xFFFF && !af_rw_is_resident(&npc));
    for(state=-1;state<121;state++) {
        int expected=state==0 || state==1 || state==5 || state==17 || state==71;
        assert(mPlib_check_player_actor_main_index_OutDoorMove2(game_data)==expected);
    }
    for(int i=0;i<4;i++)assert(mPlib_request_main_demo_get_golden_item2_type1(game_data,i) && last_type==i);
    assert(rewards==4 && !mPlib_request_main_demo_get_golden_item2_type1(game_data,4));
    mPlib_request_main_wait_type3(game_data);assert(waits==1);
    have_player=0;assert(mPlib_check_player_actor_main_index_OutDoorMove2(game_data));
    mPlib_request_main_wait_type3(game_data);assert(waits==1);
    assert(!mPlib_request_main_demo_get_golden_item2_type1(game_data,0) && rewards==4);
    assert(mPlib_check_player_actor_main_index_OutDoorMove2(0));
    memset(private_data+0x14,0xFF,30);private_data[0x14+28]=0x22;private_data[0x14+29]=0x3A;
    assert(mPr_GetPossessionItemIdx(private_data,0x223A)==14);
    assert(mPr_GetPossessionItemIdx(private_data,0)==-1 && mPr_GetPossessionItemIdx(0,0x223A)==-1);
    const int source_ids[]={eEC_EFFECT_MAKE_HEM,eEC_EFFECT_MAKE_HEM_KIRA,eEC_EFFECT_MAKE_HEM_LIGHT};
    for(unsigned i=0;i<3;i++) {
        af_rw_effects.effect_make_proc(source_ids[i],(xyz_t){40,0,0},1,0,game_data,0xD0CF,2,0);
        assert(last_effect==(int)(122+i));
        af_rw_effects.effect_kill_proc(source_ids[i],0xD0CF);assert(last_effect==(int)(122+i));
    }
    af_rw_effects.effect_make_proc(1,(xyz_t){40,0,0},1,0,game_data,0xD0CF,2,0);
    af_rw_effects.effect_kill_proc(1,0xD0CF);assert(effects==3 && kills==3);
    puts("Native reward world: exact menu/sub-animation bytes, resident identity, umbrella action, NPC save guard, player exits, pocket lookup, and three effect IDs pass.");
}
