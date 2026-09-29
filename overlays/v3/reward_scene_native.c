/* One native demo slot remains untouched. The source's additional gift
 * controller has its own pending house exit and scene-owned admission. */
#include "reward_birthday_native.h"
#include "holiday_cards.h"
#include "constants.h"
#include "actors.h"
extern u8 *af_v3_card_data(void);
extern const s32 af_rw_native_scene;
extern const s16 af_rw_native_demo_profile;
extern int mEv_CheckRealArbeit(void),mEv_CheckFirstJob(void);
extern int af_rw_calendar_clean(void);
extern int af_v3_player_selected_equipment(u32);
extern void af_rw_native_house_door(void *,int,ACTOR *);
extern void af_rw_native_actors_init(GAME *,void *,void *);
extern void af_rw_native_actors_move(GAME *,void *),af_rw_native_actors_destroy(void *,GAME *);
extern ACTOR *af_hp_native_make(void *,GAME *,int,f32,f32,f32,int,int,int,int,int,int,u16,int,int,int);
extern ACTOR *mDemo_Get_talk_actor(void);
extern void mDemo_Set_talk_return_demo_wait(int),af_rw_effect_reset(void *);
extern void af_v3_save_halt(int) __attribute__((noreturn));
typedef struct {int armed,type,player;u16 giver,year;} Pending;
static Pending pending;
static GAME *scene;
static int expected=-1,starting,axe_return;
volatile s32 af_rw_birthday_mode=0;

static int birthday_enabled(void) {
    int mode=af_rw_birthday_mode;
    if(mode<0 || mode>1)af_v3_save_halt(-1);
    return mode;
}

static int gifts_enabled(void) {
    int birthday=birthday_enabled();
    return birthday || af_v3_player_selected_equipment(0x2239)>=0 ||
        af_v3_player_selected_equipment(0x223C)>=0;
}
static int birthday_eligible(void) {
    if(!birthday_enabled())return 0;
    int player=af_rw_player();AFRewardBirthday birthday;
    const lbRTC_time_c *clock=af_cw_clock();
    if(player<0 || player>=4 || !af_rw_private() || !clock ||
       !af_reward_birthday_get(af_v3_card_data(),(unsigned)player,&birthday))return 0;
    return af_rw_calendar_clean() && !mEv_CheckRealArbeit() &&
        clock->month==af_rw_birthday_month() && clock->day==af_rw_birthday_day() &&
        clock->year!=birthday.year && mPr_GetPossessionItemIdx(af_rw_private(),0)>=0 &&
        af_rw_birthday_friendship();
}
void af_rw_house_door(void *door,int type,ACTOR *actor) {
    af_rw_native_house_door(door,type,actor);
    pending=(Pending){0};
    /* Native Psel's player field and home-exit type are verified in its
     * whole door routine. Other exits retain the original native demo. */
    int player=af_rw_player();
    if(!door || !actor || type!=0 || *(const s16 *)actor!=0x66 ||
       player<0 || player>=4 || *(const s32 *)((const u8 *)actor+0x948)!=player ||
       !af_rw_private() || !gifts_enabled() || mEv_CheckFirstJob() ||
       af_rw_native_demo_profile!=0xC9)return;
    int reward=-1;u16 giver=0;
    if(birthday_eligible()) {reward=aPRD_TYPE_BIRTHDAY;giver=af_rw_birthday_choose();}
    /* The native controller has priority over imported mayor gifts. Its
     * ordinary slot is C9 when empty; no donor second-slot write is made. */
    else if(af_rw_native_demo_profile==0xC9 && mPr_GetPossessionItemIdx(af_rw_private(),0)>=0) {
        if(mSM_CHECK_ALL_FISH_GET() && !af_rw_trophy_get(31))reward=aPRD_TYPE_GOLDEN_ROD;
        else if(mSM_CHECK_ALL_INSECT_GET() && !af_rw_trophy_get(28))reward=aPRD_TYPE_GOLDEN_NET;
    }
    if(reward>=0)pending=(Pending){1,reward,player,giver,af_cw_clock()->year};
}
int af_rw_owner_enabled(const AFHPRecord *record) {
    if(!record || !(record->kind&AF_HP_REWARD))return 0;
    if(record->profile==0xF3)return af_v3_player_selected_equipment(0x223A)>=0;
    return record->profile==0xF1 || record->profile==0xF2 || record->profile==0xF4?
        gifts_enabled():0;
}
int af_rw_owner_active(const AFHPRecord *record,GAME *game) {
    if(!af_rw_owner_enabled(record) || !game)return 0;
    if(record->profile==0xF3)return af_rw_shrine_active(game);
    if(game!=scene || af_rw_native_scene!=7 || af_rw_player()<0 || af_rw_player()>=4)return 0;
    if(record->profile==0xF1 && starting)return 1;
    mDemo_Clip_c *clip=af_rw_demo_clip;
    ACTOR *director=clip?(ACTOR *)clip->demo_class:0;
    if(!director || clip->type!=mDemo_CLIP_TYPE_PRESENT_DEMO ||
       *(const s16 *)director!=0xF1 || !af_hp_owned(director))return 0;
    PRESENT_DEMO_ACTOR *gift=(PRESENT_DEMO_ACTOR *)director;
    if(gift->type!=expected || gift->type<0 || gift->type>aPRD_TYPE_GOLDEN_NET)return 0;
    if(record->profile==0xF1)return 1;
    return record->profile==0xF2?gift->type==aPRD_TYPE_BIRTHDAY:
        record->profile==0xF4 && gift->type!=aPRD_TYPE_BIRTHDAY;
}
void af_rw_actors_init(GAME *game,void *info,void *entry) {
    int original_demo=af_rw_native_demo_profile;
    af_rw_native_actors_init(game,info,entry);
    scene=game;expected=-1;starting=0;axe_return=0;
    if(!pending.armed)return;
    if(!game || af_rw_native_scene!=7 || pending.player!=af_rw_player() ||
       pending.year!=af_cw_clock()->year || mEv_CheckFirstJob() ||
       original_demo!=0xC9)pending=(Pending){0};
}
static void gift_start(GAME *game) {
    if(!pending.armed || game!=scene || !af_rw_private() || af_rw_demo_clip ||
       !af_cw_player_actor(game) || !af_rw_npc_setup() || af_cw_handover_master())return;
    if(pending.player!=af_rw_player() || pending.year!=af_cw_clock()->year ||
       mPr_GetPossessionItemIdx(af_rw_private(),0)<0 || !gifts_enabled() ||
       (pending.type==aPRD_TYPE_BIRTHDAY && !birthday_enabled())) {
        pending=(Pending){0};return;
    }
    AFRewardBirthday before;
    if(!af_reward_birthday_get(af_v3_card_data(),(unsigned)pending.player,&before))
        af_v3_save_halt(-1);
    AFRewardBirthday next={pending.type==aPRD_TYPE_BIRTHDAY?pending.giver:0,before.year};
    if(pending.type==aPRD_TYPE_BIRTHDAY)next.year=pending.year;
    if(!af_reward_birthday_set(af_v3_card_data(),(unsigned)pending.player,&next))
        af_v3_save_halt(-1);
    expected=pending.type;starting=1;
    ACTOR *director=af_hp_native_make(af_hp_actor_info(game),game,0xF1,
        0,0,0,0,0,0,-1,-1,-1,0,-1,-1,-1);
    starting=0;
    if(!director) {
        expected=-1;
        if(!af_reward_birthday_set(af_v3_card_data(),(unsigned)pending.player,&before))
            af_v3_save_halt(-1);
        return;
    }
    pending=(Pending){0};
}
void mDemo_Set_talk_return_get_golden_axe_demo(int enabled) {
    if(enabled<0 || enabled>1)af_v3_save_halt(-1);
    axe_return=enabled;
}
void af_rw_actors_move(GAME *game,void *info) {
    if(game==scene) {
        gift_start(game);
        af_rw_shrine_step(game);
        if(axe_return && !mDemo_Get_talk_actor() && !af_cw_handover_master() &&
           mPlib_request_main_demo_get_golden_item2_type1(game,0)) {
            axe_return=0;mDemo_Set_talk_return_demo_wait(0);
        }
    }
    af_rw_native_actors_move(game,info);
}
void af_rw_actors_destroy(void *info,GAME *game) {
    if(game==scene)af_rw_effect_reset(game);
    af_rw_native_actors_destroy(info,game);
    if(game==scene) {
        scene=0;expected=-1;starting=0;axe_return=0;af_rw_demo_clip=0;
        af_rw_reward_reset();
    }
    /* The pending home exit belongs to the next foreground scene, not the
     * scene being released. Init consumes or rejects it there. */
}
