/* Keep the N64 Shrine model, action table, assessment, apologies, and drawing.
 * The added appearance state lives here, not in the native eight-byte clip or
 * actor padding. The gift insertion alone acknowledges the axe and streak. */
#include "reward_event.h"
#include "constants.h"
extern AFHPShrine *volatile af_hp_native_shrine;
extern int af_v3_player_selected_equipment(u32);
extern void af_rw_native_shrine_ctor(ACTOR *,GAME *),af_rw_native_shrine_dtor(ACTOR *,GAME *);
extern void af_rw_native_shrine_talk(ACTOR *,GAME *),af_rw_native_shrine_action(ACTOR *,int);
extern int af_rw_native_message_disappear(void *),mMsg_Check_MainNormalContinue(void *);
extern int mChoice_Get_ChoseNum(void *);
extern void *mChoice_Get_base_window_p(void);
extern void mDemo_Set_talk_return_demo_wait(int),af_rw_native_force_speak(ACTOR *);
extern int mPlib_Check_able_force_speak_label(GAME *,ACTOR *),mEv_CheckFirstJob(void);
extern void af_rw_effect_reset(void *);
static ACTOR *owner;
static GAME *scene;
static AFHPShrine *native_clip;
static AFRewardShrine clip;
static unsigned phase;

static void animation(void) {
    if(owner && native_clip && af_hp_native_shrine==native_clip && native_clip->anime_play_proc) {
        native_clip->anime_play_proc();clip.play_flag=1;
    }
}
AFRewardShrine *af_rw_shrine(void) {
    return owner && scene && native_clip && af_hp_native_shrine==native_clip?&clip:0;
}
int af_rw_shrine_active(GAME *game) {
    return game && game==scene && af_rw_shrine() && phase &&
        af_v3_player_selected_equipment(0x223A)>=0;
}
void af_rw_shrine_ctor(ACTOR *actor,GAME *game) {
    af_rw_native_shrine_ctor(actor,game);
    if(actor && game && af_hp_native_shrine && !owner) {
        owner=actor;scene=game;native_clip=af_hp_native_shrine;
        clip=(AFRewardShrine){animation,0,0};phase=0;
    }
}
void af_rw_shrine_dtor(ACTOR *actor,GAME *game) {
    if(actor==owner && game==scene) {
        /* Native Global_light still exists here. Its node is detached before
         * either the Shrine clip or the enclosing scene can be released. */
        af_rw_effect_reset(game);
        owner=0;scene=0;native_clip=0;clip=(AFRewardShrine){0};phase=0;
    }
    af_rw_native_shrine_dtor(actor,game);
}
void af_rw_shrine_talk(ACTOR *actor,GAME *game) {
    void *window=mMsg_Get_base_window_p();
    if(actor!=owner || game!=scene || !af_rw_shrine() || phase ||
       af_v3_player_selected_equipment(0x223A)<0 || !window ||
       !mMsg_Check_MainNormalContinue(window) ||
       mChoice_Get_ChoseNum(mChoice_Get_base_window_p())!=0) {
        af_rw_native_shrine_talk(actor,game);return;
    }
    int rank,x,z;
    int condition=af_rw_field_condition(&rank,&x,&z);
    /* Native assessment has NoCase=3, not the donor's dust/tree enum order.
     * A native perfect assessment has no offending acre or rubbish condition. */
    if(rank!=6 || condition!=3 || !mFAs_CheckGoodField() || af_rw_trophy_get(29) ||
       af_rw_player()<0 || af_rw_player()>=4 || !af_rw_private() ||
       mPr_GetPossessionItemIdx(af_rw_private(),0)<0 || mEv_CheckFirstJob() ||
       !af_cw_player_actor(game)) {
        af_rw_native_shrine_talk(actor,game);return;
    }
    af_rw_continue_message(window,0x2C50);
    phase=1;
    mDemo_Set_talk_return_demo_wait(1);
    af_rw_native_force_speak(actor);
    af_rw_native_shrine_action(actor,3); /* complete native talk-end action */
}
void af_rw_shrine_step(GAME *game) {
    if(game==scene && phase==2 && !clip.hem_flag)phase=0;
    if(!af_rw_shrine_active(game) || phase!=1 ||
       *(const u32 *)((const u8 *)owner+0x14C))return;
    void *window=mMsg_Get_base_window_p();
    AFRewardSetupNpc setup=af_rw_npc_setup();
    if(!window || !af_rw_native_message_disappear(window) || !setup)return;
    if(!setup(game,0xD0CF,-1,-1,-1,owner->block_x,owner->block_z,7,8))return;
    ACTOR *hem=Actor_info_fgName_search(af_hp_actor_info(game),0xD0CF,3);
    if(!hem)return;
    *(u32 *)((u8 *)hem+0x14C)=(u32)(__UINTPTR_TYPE__)owner;
    clip.hem_flag=1;*af_rw_hem_visible()=0;
    xyz_t position=owner->world.position;position.z+=40.0f;
    af_rw_effects.effect_make_proc(eEC_EFFECT_MAKE_HEM,position,2,0,game,0xFFFF,1,0);
    phase=2;
    /* Source acknowledges too early at spawn. The complete gift callback
     * marks the trophy and clears GoodField only after actual insertion. */
    if(af_cw_player_actor(game) && mPlib_Check_able_force_speak_label(game,owner))
        af_rw_native_force_speak(hem);
}
