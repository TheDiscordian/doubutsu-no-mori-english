/* Native observations and explicitly owned gift save fields. The actor family
 * must be registered and admitted before callers reach these providers. */
#include "reward_event.h"
#include "holiday_cards.h"
extern u8 *af_v3_card_data(void);
extern int af_v3_player_selected_equipment(u32);
extern int af_v3_creature_complete(u8 *,unsigned,int);
extern int af_v3_reward_flag(u32,u32,u32,u32);
extern int af_cw_native_give(void *,u16,int),af_carried_type(u32);
extern void af_v3_save_halt(int) __attribute__((noreturn));
static void *recipient;
static u8 inserted;
static int visible;

static void invalid(void) {af_v3_save_halt(-1);}
void *af_rw_private(void) {return af_cw_private();}
int af_rw_player(void) {return af_cw_player();}
int af_rw_month(void) {return af_cw_clock()->month;}
int af_rw_day(void) {return af_cw_clock()->day;}
int af_rw_birthday_month(void) {
    const u8 *p=af_rw_private();return p?p[0xA92]:0;
}
int af_rw_birthday_day(void) {
    const u8 *p=af_rw_private();return p?p[0xA93]:0;
}
int *af_rw_hem_visible(void) {return &visible;}
u8 af_rw_first_present_get(void) {
    int flags=af_reward_first_present(af_v3_card_data(),3);
    if(flags<0)invalid();
    return (u8)flags;
}
void af_rw_first_present_mark(u8 mask) {
    if(!mask || !af_reward_mark_first_present(af_v3_card_data(),mask))invalid();
}
u16 af_rw_birthday_giver(void) {
    int slot=af_rw_player();AFRewardBirthday gift;
    if(slot<0 || slot>=4 || !af_reward_birthday_get(af_v3_card_data(),(unsigned)slot,&gift))invalid();
    return gift.giver;
}
void af_rw_birthday_clear(void) {
    int slot=af_rw_player();AFRewardBirthday gift;
    if(slot<0 || slot>=4 || !af_reward_birthday_get(af_v3_card_data(),(unsigned)slot,&gift))invalid();
    gift.giver=0;
    if(!af_reward_birthday_set(af_v3_card_data(),(unsigned)slot,&gift))invalid();
}
static int selected(int trophy) {
    return trophy>=28 && trophy<=31 &&
        af_v3_player_selected_equipment(0x2239u+(unsigned)trophy-28u)>=0;
}
int af_rw_trophy_get(int trophy) {
    int slot=af_rw_player();
    if(slot<0 || slot>=4 || !af_rw_private() || !selected(trophy))return 1;
    int result=af_v3_reward_flag((u32)slot,0,(u32)trophy,0);
    if(result<0)invalid();
    return result!=0;
}
void af_rw_trophy_set(int trophy) {
    int slot=af_rw_player();
    if(slot<0 || slot>=4 || !selected(trophy) || recipient!=af_rw_private() ||
       !(inserted&(1u<<(trophy-28))) ||
       af_v3_reward_flag((u32)slot,0,(u32)trophy,1)!=1)invalid();
    inserted&=(u8)~(1u<<(trophy-28));
}
int af_rw_insert(void *player,u16 item,int condition) {
    int slot=af_rw_player();
    if(slot<0 || slot>=4 || !player || player!=af_rw_private() ||
       condition<0 || condition>1 || af_carried_type(item)<=0)return 0;
    int golden=item>=0x2239 && item<=0x223C;
    if(golden && (condition || !selected(28+item-0x2239)))return 0;
    if(af_cw_native_give(player,item,condition)!=1)return 0;
    if(recipient!=player) {recipient=player;inserted=0;}
    if(golden)inserted|=(u8)(1u<<(item-0x2239));
    return 1;
}
int mSM_CHECK_ALL_FISH_GET(void) {
    return af_rw_player()>=0 && af_rw_player()<4 && selected(31) &&
        af_v3_creature_complete(af_rw_private(),0,-1);
}
int mSM_CHECK_ALL_INSECT_GET(void) {
    return af_rw_player()>=0 && af_rw_player()<4 && selected(28) &&
        af_v3_creature_complete(af_rw_private(),1,-1);
}
void af_rw_reward_reset(void) {recipient=0;inserted=0;visible=0;}
