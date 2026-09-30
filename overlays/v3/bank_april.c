/* Included after the complete generated source April controller. The borrowed
 * two-callback bank view is distinct from the four-pointer source clip. */
typedef __UINTPTR_TYPE__ uptr;
AFBankAprilCommon af_bank_april_common;
static ACTOR *af_bank_april_owner;
static int af_bank_april_busy;
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
    if(player>=4 || af_bank_april_busy)return 0;
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
