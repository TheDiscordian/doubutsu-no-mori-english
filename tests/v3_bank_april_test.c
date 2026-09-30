#include "bank_april_manager.h"
#include "bank_pelly.h"
#include <assert.h>
#include <string.h>
extern ACTOR_PROFILE Aprilfool_Control_Profile;
typedef struct {
    int (*talk_chk_proc)(mActor_name_t);
    int (*get_msg_num_proc)(mActor_name_t,int);
} AFBankAprilBorrowed;
extern AFBankAprilBorrowed *af_bank_pelly_april_clip(void);
extern int af_bank_pelly_native_number(void *),af_bank_pelly_message_unmap(int);
extern void *af_bank_pelly_window(void);
AFHolidayNativeDay af_holiday_native_days[AF_HN_DAYS];
u8 af_holiday_native_index[128];
u8 af_bank_april_native_slots[264] __attribute__((aligned(8)));
int af_bank_april_test_foreigner;
static int allocations,notifications,exhausted;
static int calendars,appends,makes,deletes;
static u8 game_bytes[0x2000] __attribute__((aligned(8)));
GAME_PLAY *af_bank_april_game=(GAME_PLAY *)game_bytes;
u8 af_bank_april_native_rtc[8];
static APRILFOOL_CONTROL_ACTOR managed;
int af_bank_april_prior_calendar(void) {calendars++;return 9;}
int af_holiday_native_append(unsigned type,unsigned hours,unsigned begin,unsigned end) {
    assert(type==117 && hours==0xFFFFFF && begin==0x401 && end==0x401);appends++;
    return 1;
}
void *af_bank_april_previous_descriptor(int profile) {assert(profile!=0xF6);return (void *)game_bytes;}
void af_bank_april_native_set_status(int type,int status) {
    assert(type==117);af_holiday_native_days[2].status|=status;
}
void af_bank_april_native_clear_status(int type,int status) {
    assert(type==117);af_holiday_native_days[2].status&=~status;
}
void af_bank_april_delete(ACTOR *actor) {assert(actor);deletes++;}
ACTOR *af_bank_april_make(void *info,GAME *game,int profile,f32 x,f32 y,f32 z,
        int rx,int ry,int rz,int bx,int bz,int arg,u16 name,int params,int npc,int extra) {
    assert(info==game_bytes+0x1C78 && game==(GAME *)game_bytes && profile==0xF6);
    assert(!x && !y && !z && !rx && !ry && !rz && bx==-1 && bz==-1 && arg==-1 &&
        !name && params==-1 && npc==-1 && extra==-1);makes++;
    memset(&managed,0,sizeof(managed));*(s16 *)&managed=profile;
    *(void **)((u8 *)&managed+0x170)=af_bank_april_descriptor(profile);
    af_bank_april_ctor(&managed.actor_class,game);return &managed.actor_class;
}
void *af_bank_april_native_get(int type,int id) {
    assert(type==AF_BANK_APRIL_NATIVE && !id);
    return af_bank_april_native_slots[23]&1?af_bank_april_native_slots+32:0;
}
void *af_bank_april_native_reserve(int type,int id) {
    assert(type==AF_BANK_APRIL_NATIVE && !id);allocations++;
    if(exhausted)return 0;
    af_bank_april_native_slots[23]|=1;af_bank_april_native_slots[24]=AF_BANK_APRIL_NATIVE;
    memset(af_bank_april_native_slots+32,0,40);return af_bank_april_native_slots+32;
}
void af_bank_april_native_dying(int type,ACTOR *actor) {
    assert(type==AF_BANK_APRIL_NATIVE && actor);notifications++;
}
void af_bank_april_zero(void *p,u32 n) {assert(p && n==8);memset(p,0,n);}
void af_bank_april_none(ACTOR *actor,GAME *game) {(void)actor;(void)game;}
void af_bank_april_test(void) {
    APRILFOOL_CONTROL_ACTOR actor={0},second={0};
    static const mActor_name_t names[11]={0xD00E,0xD008,0xD06D,0xD070,0xD071,0xD00D,
        0xD010,0xD003,0xD012,0xD011,0xD072};
    static const int messages[11]={0x3BB5,0x3BAC,0x3BB0,0x3BB1,0x3BB2,0x3BB3,
        0x3BB4,0x3BAE,0x3BAF,0x3BAD,0x3BB6};
    memset(af_holiday_native_index,255,sizeof(af_holiday_native_index));
    memset(af_bank_april_native_slots,0,sizeof(af_bank_april_native_slots));
    af_bank_account_mode=1;af_bank_player=0;
    assert(!af_bank_pelly_april_clip() && !af_bank_april_construct(&actor.actor_class,0));
    assert(!allocations);
    af_holiday_native_index[AF_BANK_APRIL_NATIVE]=2;
    AFHolidayNativeDay *day=af_holiday_native_days+2;
    *day=(AFHolidayNativeDay){AF_BANK_APRIL_NATIVE,0xFFFFFF,0x401,0x401,AF_HE_ACTIVE,0};
    af_bank_account_mode=0;assert(!af_bank_april_construct(&actor.actor_class,0));
    af_bank_account_mode=1;day->status|=AF_HE_ERROR;
    assert(!af_bank_april_construct(&actor.actor_class,0));day->status=AF_HE_ACTIVE;
    day->begin=0x402;assert(!af_bank_april_construct(&actor.actor_class,0));day->begin=0x401;
    exhausted=1;assert(!af_bank_april_construct(&actor.actor_class,0));
    assert(!af_bank_pelly_april_clip() && !af_bank_april_common.clip.aprilfool_control_clip);
    exhausted=0;assert(af_bank_april_construct(&actor.actor_class,0));
    assert(!af_bank_april_construct(&second.actor_class,0));
    assert(af_bank_april_construct(&actor.actor_class,0) && allocations==2);
    assert(actor.clip.talk_chk_proc && actor.clip.talk_set_proc && actor.clip.get_msg_num_proc);
    aAPC_event_save_data_c *saved=actor.clip.event_save_data_p;
    assert((void *)saved==af_bank_april_native_slots+32);
    for(u32 player=0;player<4;player++) {
        af_bank_player=(u8)player;
        AFBankAprilBorrowed *clip=af_bank_pelly_april_clip();assert(clip);
        assert((void *)clip!=(void *)&actor.clip);
        assert(clip->talk_chk_proc(0xD004) && clip->get_msg_num_proc(0xD004,1)==-1);
        assert(!saved->talk_bitfield[player]);
        for(u32 i=0;i<11;i++) {
            assert(!clip->talk_chk_proc(names[i]));
            assert(clip->get_msg_num_proc(names[i],0)==messages[i]);
            assert(!(saved->talk_bitfield[player]&(1u<<i)));
            assert(clip->get_msg_num_proc(names[i],1)==messages[i]);
            assert(clip->talk_chk_proc(names[i]));
        }
        assert(saved->talk_bitfield[player]==0x7FF);
    }
    af_bank_player=0;assert(af_bank_april_player_clear(0));
    af_bank_april_test_foreigner=1;
    assert(af_bank_pelly_april_clip()->talk_chk_proc(names[7]));
    assert(!saved->talk_bitfield[0]);af_bank_april_test_foreigner=0;
    actor.clip.talk_set_proc(names[0]);assert(saved->talk_bitfield[0]==1);
    /* Drive the actual donor Pelly greeting through the live borrowed clip.
     * Phyllis must use source D012, not the draw-type arithmetic's D004. */
    for(int variant=0;variant<2;variant++) {
        AFBankPelly s={variant,4,0,0,0,0,0,0,1};
        assert(af_bank_pelly_step(&s,AF_BANK_PELLY_TALK));
        assert(af_bank_pelly_message_unmap(af_bank_pelly_native_number(af_bank_pelly_window()))==messages[7+variant]);
        assert(saved->talk_bitfield[0]&(1u<<(7+variant)));
    }
    for(u32 i=1;i<4;i++)assert(saved->talk_bitfield[i]==0x7FF);
    assert(!af_bank_april_player_clear(4));af_bank_player=4;assert(!af_bank_pelly_april_clip());
    af_bank_player=0;day->status=0;assert(!af_bank_pelly_april_clip());day->status=AF_HE_ACTIVE;
    af_bank_april_native_slots[24]=114;assert(!af_bank_pelly_april_clip());
    af_bank_april_native_slots[24]=AF_BANK_APRIL_NATIVE;
    u16 retained=saved->talk_bitfield[0];
    assert(!af_bank_april_destruct(&second.actor_class,0));
    assert(af_bank_april_destruct(&actor.actor_class,0) && notifications==1);
    assert(!af_bank_pelly_april_clip() && !af_bank_april_common.clip.aprilfool_control_clip);
    assert(!af_bank_april_destruct(&actor.actor_class,0));
    assert(af_bank_april_construct(&actor.actor_class,0));assert(saved->talk_bitfield[0]==retained);
    assert(af_bank_april_destruct(&actor.actor_class,0) && notifications==2);
    day->status=0;af_bank_account_mode=0;
    assert(af_bank_april_player_clear(1) && !saved->talk_bitfield[1]);
    assert(saved->talk_bitfield[0]==retained && saved->talk_bitfield[2]==0x7FF &&
        saved->talk_bitfield[3]==0x7FF);
    af_bank_account_mode=1;day->status=AF_HE_ACTIVE;
    /* Complete source manager and native lifecycle wrappers, with real source
     * creation arguments, scalar keep ownership, and inherited scheduling. */
    assert(af_bank_april_calendar_before_cleanup()==9 && calendars==1 && !appends);
    af_bank_april_native_rtc[5]=4;af_bank_april_native_rtc[3]=1;
    af_bank_account_mode=0;assert(af_bank_april_calendar_before_cleanup()==9 && !appends);
    af_bank_account_mode=1;assert(af_bank_april_calendar_before_cleanup()==9 && appends==1);
    af_bank_april_native_rtc[3]=2;assert(af_bank_april_calendar_before_cleanup()==9 && appends==1);
    assert(af_bank_april_descriptor(0xF5)==game_bytes);
    int manager[0x250/4]={0};AFHolidayControl control={.type=117};
    day->status=AF_HE_ACTIVE;
    assert(!af_bank_april_manager_start(manager,&control) && !makes);
    assert(!(day->status&AF_HE_ACTIVE) && (day->status&AF_HE_ERROR));
    assert(!af_bank_april_descriptor(0xF6));
    manager[0x234/4]=1;day->status=AF_HE_ACTIVE;
    assert(af_bank_april_manager_start(manager,&control)==1 && makes==1);
    assert(af_bank_april_check_keep(117) && !af_bank_april_check_keep(115));
    assert(af_bank_pelly_april_clip());
    af_bank_april_step(&managed.actor_class,(GAME *)game_bytes);assert(!deletes);
    assert(af_bank_april_manager_stop(manager,&control)==1 && !af_bank_april_check_keep(117));
    assert(af_bank_april_manager_stop(manager,&control)==2);
    af_bank_april_step(&managed.actor_class,(GAME *)game_bytes);assert(deletes==1);
    af_bank_april_dtor(&managed.actor_class,(GAME *)game_bytes);
    assert(!af_bank_pelly_april_clip() && notifications==3);
    control.type=115;assert(!af_bank_april_manager_start(manager,&control));
    assert(!af_bank_april_manager_stop(manager,&control));
    control.type=117;af_bank_account_mode=0;
    assert(!af_bank_april_descriptor(0xF6));
    af_bank_april_ctor(&managed.actor_class,(GAME *)game_bytes);assert(deletes==2);
    af_bank_account_mode=1;day->status=AF_HE_ACTIVE;
}
