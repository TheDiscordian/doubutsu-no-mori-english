/* Franklin uses the actual native event areas and their existing date/cleanup
 * lifetime. His full 22-byte saved record fits the native forty-byte area;
 * neither a second save codec nor another player's identity is substituted. */
#include "harvest_state.h"
extern int af_carried_type(unsigned int),af_cw_player(void);
extern void *af_cw_private(void);
extern int af_cw_native_give(void *,unsigned short,int);
extern int af_hr_prior_calendar_before_cleanup(void);
extern void *af_cw_native_get_save(int,int),*af_cw_native_reserve_save(int,int);
extern void *af_cw_native_get_common(int,int),*af_cw_native_reserve_common(int,int);
extern void af_hr_native_set_status(int,int);
extern void af_v3_save_halt(int) __attribute__((noreturn));
static void *recipient;
static unsigned int inserted;

unsigned int af_hr_enabled_mask(void) {
    unsigned int mask=0;
    /* Cutlery has no stack quantity: its selected ordinary category is 47. */
    if(af_carried_type(0x2530)!=47)return 0;
    for(unsigned int i=0;i<AF_HR_REWARDS;i++) {
        unsigned int item=af_hr_reward_items[i];
        if(item && af_carried_type(item)==(i<10?10:12))mask|=1u<<i;
    }
    return mask;
}
unsigned short af_hr_reward(unsigned int i) {
    return i<AF_HR_REWARDS && (af_hr_enabled_mask()&(1u<<i))?af_hr_reward_items[i]:0;
}
static AFHolidayNativeDay *day(unsigned int type) {
    unsigned int slot=af_holiday_native_index[type];
    if(slot>=AF_HN_DAYS)return 0;
    AFHolidayNativeDay *d=af_holiday_native_days+slot;
    return d->type==type && (d->status&AF_HE_EXIST) && !(d->status&AF_HE_ERROR)?d:0;
}
int af_hr_calendar_before_cleanup(void) {
    int result=af_hr_prior_calendar_before_cleanup();
    AFHolidayNativeDay *harvest=day(AF_HR_HARVEST_NATIVE);
    if(harvest && af_hr_enabled_mask())
        (void)af_holiday_native_append(AF_HR_NATIVE,harvest->hours,harvest->begin,harvest->end);
    recipient=0;inserted=0;
    return result;
}
static int valid(int source,int id) {
    return source==AF_HR_SOURCE && id==0 && af_hr_enabled_mask() && day(AF_HR_NATIVE);
}
void *af_hr_get_save(int source,int id) {
    if(!valid(source,id))return 0;
    AFHarvestSaved *saved=af_cw_native_get_save(AF_HR_NATIVE,id);
    if(saved && (saved->given_present_bitfield&~AF_HR_ALL))af_v3_save_halt(-1);
    return saved;
}
void *af_hr_reserve_save(int source,int id) {
    if(!valid(source,id))return 0;
    AFHarvestSaved *saved=af_hr_get_save(source,id);
    if(saved)return saved;
    saved=af_cw_native_reserve_save(AF_HR_NATIVE,id);
    if(saved) {
        /* The shared actor constructor reserves the area before entering the
         * source constructor. Initialise the complete source identity here,
         * once, so source SetupSaveData does not mistake native zeroes for an
         * existing identity. Keep the remaining native area bytes untouched. */
        unsigned char *bytes=(unsigned char *)saved;
        for(unsigned int i=0;i<sizeof(*saved);i++)bytes[i]=0;
        af_hr_clear_personal_id(&saved->pid);
    }
    return saved;
}
void *af_hr_get_common(int source,int id) {
    return valid(source,id)?af_cw_native_get_common(AF_HR_NATIVE,id):0;
}
void *af_hr_reserve_common(int source,int id) {
    return valid(source,id)?af_cw_native_reserve_common(AF_HR_NATIVE,id):0;
}
void af_hr_clear_personal_id(AFHarvestPersonalID *pid) {
    if(!pid)return;
    for(unsigned int i=0;i<8;i++)pid->player_name[i]=pid->land_name[i]=32;
    pid->player_id=pid->land_id=65535;
}
void af_hr_set_status(int source,int status) {
    if(source==AF_HR_SOURCE && day(AF_HR_NATIVE))af_hr_native_set_status(AF_HR_NATIVE,status);
}
void af_hr_dying(int source,void *actor) {
    if(source==AF_HR_SOURCE && actor && day(AF_HR_NATIVE))
        af_holiday_native_death(AF_HR_NATIVE,actor);
}
int af_hr_insert(void *player,unsigned short item,int condition) {
    if(!player || player!=af_cw_private() || af_cw_player()<0 || af_cw_player()>=4 ||
       condition || inserted || !valid(AF_HR_SOURCE,0))return 0;
    unsigned int index=0;
    for(;index<AF_HR_REWARDS && af_hr_reward(index)!=item;index++);
    if(!item || index==AF_HR_REWARDS || !af_hr_get_save(AF_HR_SOURCE,0) ||
       af_cw_native_give(player,item,condition)!=1)return 0;
    recipient=player;inserted=1u<<index;
    return 1;
}
void af_hr_report(unsigned int index,unsigned short bits) {
    AFHarvestSaved *saved=af_hr_get_save(AF_HR_SOURCE,0);
    if(index>=AF_HR_REWARDS || !saved || recipient!=af_cw_private() ||
       inserted!=(1u<<index) || !(bits&inserted) || bits!=saved->given_present_bitfield ||
       !(af_hr_enabled_mask()&inserted))af_v3_save_halt(-1);
    recipient=0;inserted=0;
}
