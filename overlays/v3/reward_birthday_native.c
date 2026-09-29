/* The complete source friendship and giver-selection routines use a native
 * sparse view, never a cast to the donor's larger save record. */
#include "reward_birthday_native.h"
#include "holiday_cards.h"
extern u8 af_hp_native_animals[15][0x528];
extern volatile s32 af_rw_birthday_mode;
extern int af_rw_native_birthday_mail(AFRewardPersonalID *,int);
extern int af_rw_native_same_town(const u8 *,u16);
extern u8 *af_v3_card_data(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
static struct {int active;AFRewardBirthdayMailState state;} mail_context;
AFRewardAnimal *af_rw_birthday_animals(void) {
    return (AFRewardAnimal *)af_hp_native_animals;
}
AFRewardBirthdayMailState *af_rw_birthday_mail_state(void) {
    if(!mail_context.active)af_v3_save_halt(-1);
    return &mail_context.state;
}
u16 af_rw_birthday_current_giver(void) {
    return mail_context.active?mail_context.state.giver:af_rw_birthday_giver();
}
int af_rw_birthday_same_town(AFRewardPersonalID *pid) {
    if(!pid)return 0;
    return af_rw_native_same_town(pid->bytes+6,(u16)((u16)pid->bytes[14]<<8|pid->bytes[15]));
}
int af_rw_birthday_mail(AFRewardPersonalID *pid,int player) {
    int mode=af_rw_birthday_mode;
    if(mode==0)return af_rw_native_birthday_mail(pid,player);
    if(mode!=1 || player<0 || player>=4 || mail_context.active)af_v3_save_halt(-1);
    AFRewardBirthday saved;
    if(!af_reward_birthday_get(af_v3_card_data(),(unsigned)player,&saved))af_v3_save_halt(-1);
    mail_context.state=(AFRewardBirthdayMailState){saved.giver,saved.year};mail_context.active=1;
    int result=af_rw_birthday_source_mail(pid,player);
    saved=(AFRewardBirthday){mail_context.state.giver,mail_context.state.year};mail_context.active=0;
    if(!af_reward_birthday_set(af_v3_card_data(),(unsigned)player,&saved))af_v3_save_halt(-1);
    return result;
}
