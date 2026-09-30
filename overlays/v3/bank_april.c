/* Included after the complete generated source April controller. The borrowed
 * two-callback bank view is distinct from the four-pointer source clip. */
typedef __UINTPTR_TYPE__ uptr;
AFBankAprilCommon af_bank_april_common;
static ACTOR *af_bank_april_owner;
static int af_bank_april_busy;
typedef struct {u32 vrom,end,ram,ram_end,loaded;ACTOR_PROFILE *profile;u32 filename;
    u16 allocation;u8 count,pad;} AFBankAprilDescriptor;
static AFBankAprilDescriptor af_bank_april_owned_descriptor;
static ACTOR_PROFILE af_bank_april_owned_profile;
static int af_bank_april_keep;
static int af_bank_april_scheduled(void) {
    u32 slot=af_holiday_native_index[AF_BANK_APRIL_NATIVE];
    if(af_bank_account_mode!=1 || slot>=AF_HN_DAYS)return 0;
    const AFHolidayNativeDay *day=af_holiday_native_days+slot;
    return day->type==AF_BANK_APRIL_NATIVE && day->begin==0x401 && day->end==0x401 &&
        day->hours==0xFFFFFF && (day->status&AF_HE_ACTIVE) && !(day->status&AF_HE_ERROR);
}
static int af_bank_april_area(const void *p) {
    const u8 *base=af_bank_april_native_slots;
    u32 used=(u32)base[20]<<24|(u32)base[21]<<16|(u32)base[22]<<8|base[23];
    for(u32 i=0;i<5;i++) {
        const u8 *slot=base+48*i;
        if((used&(1u<<i)) && slot[24]==AF_BANK_APRIL_NATIVE && slot[25]==0 && p==slot+32)return 1;
    }
    return 0;
}
void *af_bank_april_get(int type,int id) {
    if(type!=AF_BANK_APRIL_SOURCE || id)return 0;
    void *p=af_bank_april_native_get(AF_BANK_APRIL_NATIVE,0);
    return af_bank_april_area(p)?p:0;
}
void *af_bank_april_reserve(int type,int id) {
    if(type!=AF_BANK_APRIL_SOURCE || id || !af_bank_april_scheduled())return 0;
    void *p=af_bank_april_native_reserve(AF_BANK_APRIL_NATIVE,0);
    return af_bank_april_area(p)?p:0;
}
void af_bank_april_dying(int type,ACTOR *actor) {
    if(type==AF_BANK_APRIL_SOURCE && actor==af_bank_april_owner)
        af_bank_april_native_dying(AF_BANK_APRIL_NATIVE,actor);
}
static int af_bank_april_ready(void) {
    aAPC_Clip_c *clip=af_bank_april_common.clip.aprilfool_control_clip;
    if(af_bank_april_busy || !af_bank_april_owner || af_bank_player>=4 ||
        !af_bank_april_scheduled() || !clip || !clip->talk_chk_proc ||
        !clip->talk_set_proc || !clip->get_msg_num_proc ||
        af_bank_april_get(AF_BANK_APRIL_SOURCE,0)!=clip->event_save_data_p)return 0;
    af_bank_april_common.player_no=af_bank_player;return 1;
}
int af_bank_april_construct(ACTOR *actor,GAME *game) {
    if(!actor || ((uptr)actor&3) || af_bank_april_busy || !af_bank_april_scheduled())return 0;
    if(af_bank_april_owner)return actor==af_bank_april_owner && af_bank_april_ready();
    /* The complete donor constructor assumes reserve succeeds. Preflight the
     * actual native slot so its retained bzero can never receive NULL. */
    void *saved=af_bank_april_get(AF_BANK_APRIL_SOURCE,0);
    if(!saved)saved=af_bank_april_reserve(AF_BANK_APRIL_SOURCE,0);
    if(!saved)return 0;
    af_bank_april_busy=1;af_bank_april_owner=actor;
    aAPC_actor_ct(actor,game);
    af_bank_april_busy=0;return 1;
}
int af_bank_april_destruct(ACTOR *actor,GAME *game) {
    if(!actor || actor!=af_bank_april_owner || af_bank_april_busy)return 0;
    af_bank_april_busy=1;aAPC_actor_dt(actor,game);
    af_bank_april_owner=0;af_bank_april_busy=0;return 1;
}
int af_bank_april_player_clear(u32 player) {
    if(player>=4)return 0;
    if(af_bank_april_busy)return -1;
    aAPC_event_save_data_c *saved=af_bank_april_get(AF_BANK_APRIL_SOURCE,0);
    if(!saved)return 0;
    saved->talk_bitfield[player]=0;return 1;
}
static int af_bank_april_check(mActor_name_t name) {
    return af_bank_april_ready()?aAPC_talk_chk_proc(name):1;
}
static int af_bank_april_message(mActor_name_t name,int update) {
    return af_bank_april_ready()?aAPC_get_msg_num_proc(name,update):-1;
}
typedef struct {
    int (*talk_chk_proc)(mActor_name_t);
    int (*get_msg_num_proc)(mActor_name_t,int);
} AFBankAprilBorrowed;
static AFBankAprilBorrowed af_bank_april_borrowed={af_bank_april_check,af_bank_april_message};
AFBankAprilBorrowed *af_bank_pelly_april_clip(void) {
    return af_bank_april_ready()?&af_bank_april_borrowed:0;
}
/* Supplemental admission retains the installed Wisp/Harvest calendar chain.
 * The source row carries 0401 0000 0401 0017 00000011. ACTIVE belongs to the
 * real native hourly updater, not to this planner. */
int af_bank_april_calendar_before_cleanup(void) {
    int result=af_bank_april_prior_calendar();
    const u8 *row=af_bank_april_schedule;
    if(af_bank_account_mode==1 && af_bank_april_native_rtc[5]==row[0] &&
            af_bank_april_native_rtc[3]==row[1])
        (void)af_holiday_native_append(AF_BANK_APRIL_NATIVE,0xFFFFFF,
            (u32)row[0]*256u+row[1],(u32)row[4]*256u+row[5]);
    return result;
}
void *af_bank_april_actor_info(GAME_PLAY *game) {return game?(u8 *)game+0x1C78:0;}
static int af_bank_april_identity(const ACTOR *actor) {
    return actor && !((uptr)actor&3) && *(const s16 *)actor==AF_BANK_APRIL_PROFILE &&
        *(void *const *)((const u8 *)actor+0x170)==&af_bank_april_owned_descriptor;
}
void *af_bank_april_descriptor(int profile) {
    if(profile!=AF_BANK_APRIL_PROFILE)return af_bank_april_previous_descriptor(profile);
    if(!af_bank_april_scheduled())return 0;
    if(!af_bank_april_owned_descriptor.profile) {
        af_bank_april_owned_profile=Aprilfool_Control_Profile;
        af_bank_april_owned_profile.source_profile=AF_BANK_APRIL_PROFILE;
        af_bank_april_owned_profile.ctor=af_bank_april_ctor;
        af_bank_april_owned_profile.dtor=af_bank_april_dtor;
        af_bank_april_owned_profile.move=af_bank_april_step;
        af_bank_april_owned_descriptor.profile=&af_bank_april_owned_profile;
    }
    return &af_bank_april_owned_descriptor;
}
void af_bank_april_ctor(ACTOR *actor,GAME *game) {
    if(!game || !af_bank_april_identity(actor) || !af_bank_april_construct(actor,game))
        af_bank_april_delete(actor);
}
void af_bank_april_dtor(ACTOR *actor,GAME *game) {
    if(af_bank_april_identity(actor))(void)af_bank_april_destruct(actor,game);
    /* Ordinary Actor_dt/free owns the descriptor load count and allocation. */
}
void af_bank_april_step(ACTOR *actor,GAME *game) {
    if(!game || !af_bank_april_identity(actor) || actor!=af_bank_april_owner ||
            !af_bank_april_scheduled() || !af_bank_april_keep)
        af_bank_april_delete(actor);
    else af_bank_april_none(actor,game);
}
int af_bank_april_check_keep(int type) {
    return type==AF_BANK_APRIL_NATIVE && af_bank_april_keep!=0;
}
void af_bank_april_set_keep(int type) {if(type==AF_BANK_APRIL_NATIVE)af_bank_april_keep=1;}
void af_bank_april_clear_keep(int type) {if(type==AF_BANK_APRIL_NATIVE)af_bank_april_keep=0;}
void af_bank_april_set_status(int type,int status) {
    if(type==AF_BANK_APRIL_NATIVE)af_bank_april_native_set_status(type,status);
}
void af_bank_april_clear_status(int type,int status) {
    if(type==AF_BANK_APRIL_NATIVE)af_bank_april_native_clear_status(type,status);
}
static int af_bank_april_view(void *manager,AFHolidayControl *ctrl,AFBankAprilManagerView *view) {
    if(!manager || ((uptr)manager&3) || !ctrl || ctrl->type!=AF_BANK_APRIL_NATIVE)return 0;
    view->shrine_block_exists=((const int *)manager)[0x234/4]!=0;return 1;
}
int af_bank_april_manager_start(void *manager,AFHolidayControl *ctrl) {
    AFBankAprilManagerView view;
    return af_bank_april_scheduled() && af_bank_april_view(manager,ctrl,&view)?
        aprilfool_start(&view,ctrl):0;
}
int af_bank_april_manager_stop(void *manager,AFHolidayControl *ctrl) {
    AFBankAprilManagerView view;
    return af_bank_april_view(manager,ctrl,&view)?aprilfool_stop(&view,ctrl):0;
}
#ifdef __mips__
_Static_assert(sizeof(AFBankAprilDescriptor)==32,"Complete native April descriptor");
#endif
