/* Real reward saved-state and item providers, with recording native-game doubles. */
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_state_native.c"
static u8 player_data[4][0xBD0],cards[AF_HC_BYTES],trophies[4];
static int slot,admitted=15,complete[2],give_result=1,gives,last_condition;
static u16 last_item;
static lbRTC_time_c clock_data={.year=2026,.month=9,.day=29};
static jmp_buf failure;
u32 af_test_carried_profile[8]={0x41464350,1,26,32,127,127,0,0};
u32 af_test_event_item_profile=3;
const u32 af_carried_paper_mode=1;
void *af_cw_private(void) {return slot>=0 && slot<4?player_data[slot]:0;}
int af_cw_player(void) {return slot;}
lbRTC_time_c *af_cw_clock(void) {return &clock_data;}
u8 *af_v3_card_data(void) {return cards;}
int af_v3_player_selected_equipment(u32 item) {
    return item>=0x2239 && item<=0x223C && (admitted&(1u<<(item-0x2239)))?36:-1;
}
int af_carried_type(u32 item) {return item && item!=0xFFFF?2:0;}
int af_cw_native_give(void *p,u16 item,int condition) {
    assert(p==af_cw_private());gives++;last_item=item;last_condition=condition;return give_result;
}
int af_v3_reward_flag(u32 who,u32 category,u32 trophy,u32 mark) {
    assert(who<4 && !category && trophy>=28 && trophy<=31 && mark<=1);
    if(mark)trophies[who]|=(u8)(1u<<(trophy-28));
    return !!(trophies[who]&(1u<<(trophy-28)));
}
int af_v3_creature_complete(u8 *p,unsigned kind,int prospective) {
    assert(p==af_cw_private() && kind<2 && prospective==-1);return complete[kind];
}
void af_v3_save_halt(int error) {assert(error==-1);longjmp(failure,1);}
static void reject_duplicate_trophy(int trophy) {
    if(!setjmp(failure)) {af_rw_trophy_set(trophy);assert(0);}
}
int main(void) {
    af_holiday_cards_reset(cards);assert(af_carried_save_bind(cards,3,127));
    for(slot=0;slot<4;slot++) {
        player_data[slot][0xA92]=9;player_data[slot][0xA93]=29;
        assert(af_rw_month()==9 && af_rw_day()==29 && af_rw_birthday_month()==9 && af_rw_birthday_day()==29);
        AFRewardBirthday gift={(u16)(0xE010+slot),2026},saved;
        assert(af_reward_birthday_set(cards,(unsigned)slot,&gift));
        assert(af_rw_birthday_giver()==gift.giver);af_rw_birthday_clear();
        assert(!af_rw_birthday_giver());
        assert(af_reward_birthday_get(cards,(unsigned)slot,&saved) && !saved.giver && saved.year==2026);
        for(unsigned index=0;index<4;index++) {
            int trophy=28+(int)index;u16 item=(u16)(0x2239+index);
            assert(!af_rw_trophy_get(trophy));
            give_result=0;assert(!af_rw_insert(af_rw_private(),item,0));
            assert(!inserted && !af_rw_trophy_get(trophy));
            int before=gives;
            admitted&=~(1u<<index);
            assert(af_rw_trophy_get(trophy) && !af_rw_insert(af_rw_private(),item,0) && gives==before);
            admitted|=1u<<index;give_result=1;
            assert(!af_rw_insert(af_rw_private(),item,1) && gives==before);
            assert(af_rw_insert(af_rw_private(),item,0) && last_item==item && !last_condition);
            af_rw_trophy_set(trophy);assert(af_rw_trophy_get(trophy) && !inserted);
            reject_duplicate_trophy(trophy);
        }
        assert(af_rw_insert(af_rw_private(),0x1000,1) && last_condition==1);
        assert(!af_rw_insert(player_data[(slot+1)%4],0x1000,1));
    }
    slot=0;complete[0]=complete[1]=1;
    assert(mSM_CHECK_ALL_FISH_GET() && mSM_CHECK_ALL_INSECT_GET());
    admitted=4;assert(!mSM_CHECK_ALL_FISH_GET() && !mSM_CHECK_ALL_INSECT_GET());
    admitted=15;complete[1]=0;assert(mSM_CHECK_ALL_FISH_GET() && !mSM_CHECK_ALL_INSECT_GET());
    assert(!af_rw_first_present_get());af_rw_first_present_mark(1);slot=1;
    assert(af_rw_first_present_get()==1);af_rw_first_present_mark(2);slot=2;
    assert(af_rw_first_present_get()==3);
    assert(af_holiday_cards_clear(cards,0) && af_holiday_cards_clear(cards,1));
    assert(af_rw_first_present_get()==3);
    slot=4;assert(af_rw_trophy_get(28) && !af_rw_insert(0,0x2239,0));
    assert(!mSM_CHECK_ALL_FISH_GET() && !mSM_CHECK_ALL_INSECT_GET());
    *af_rw_hem_visible()=1;af_rw_reward_reset();assert(!*af_rw_hem_visible() && !recipient && !inserted);
    puts("Native reward providers: four players, town-first flags, retained birthday year, selected collections, refused insertion, and trophy acknowledgement pass.");
}
