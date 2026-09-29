/* Real reward saved-state and item providers, with recording native-game doubles. */
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_state_native.c"
#include "../overlays/v3/reward_field_native.c"
#include "reward_field_source.c"
#include "reward_clock_reference.c"
static u8 player_data[4][0xBD0],cards[AF_HC_BYTES],trophies[4];
static int slot,admitted=15,complete[2],give_result=1,gives,last_condition;
static u16 last_item;
static lbRTC_time_c clock_data={.year=2026,.month=9,.day=29};
static jmp_buf failure;
static int native_rank=6,native_sets,native_conditions;
void af_rw_native_rank_set(void) {native_sets++;}
int af_rw_native_rank_get(void) {return native_rank;}
int af_rw_native_rank_condition(int *rank,int *x,int *z) {
    native_conditions++;*rank=native_rank;*x=2;*z=3;return 3;
}
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
    AFRewardGoodField streak;
    af_rw_field_rank();assert(native_sets==1 && !mFAs_CheckGoodField());
    assert(af_reward_good_field_get(cards,&streak) && !streak.days && streak.rtc[3]==29);
    clock_data.hour=23;af_rw_field_rank();assert(!mFAs_CheckGoodField());
    /* Repeated calls, seconds, and an equal clock cannot count another day. */
    for(unsigned i=0;i<100;i++)af_rw_field_rank();
    assert(af_reward_good_field_get(cards,&streak) && !streak.days && !streak.rtc[2]);
    clock_data.day=30;clock_data.hour=0;af_rw_field_rank();
    assert(af_reward_good_field_get(cards,&streak) && streak.days==1);
    clock_data.month=10;clock_data.day=14;af_rw_field_rank();assert(mFAs_CheckGoodField());
    clock_data.day=20;af_rw_field_rank();assert(af_reward_good_field_get(cards,&streak) && streak.days==15);
    clock_data.day=19;af_rw_field_rank();assert(!mFAs_CheckGoodField());
    assert(af_reward_good_field_get(cards,&streak) && !streak.days && streak.rtc[3]==19);
    clock_data.month=11;af_rw_field_rank();assert(mFAs_CheckGoodField());
    native_rank=5;int rank=-1,x=-1,z=-1;
    assert(af_rw_field_condition(&rank,&x,&z)==3 && rank==5 && x==2 && z==3 && native_conditions==1);
    assert(af_reward_good_field_get(cards,&streak) && !streak.days);
    for(unsigned i=0;i<8;i++)assert(!streak.rtc[i]);
    assert(af_rw_field_condition(0,&x,&z)==-1 && native_conditions==1);
    native_rank=6;clock_data=(lbRTC_time_c){.year=2028,.month=2,.day=28};af_rw_field_rank();
    clock_data.month=3;clock_data.day=1;af_rw_field_rank();
    assert(af_reward_good_field_get(cards,&streak) && streak.days==2);
    AFRewardGoodField before_streak=streak;
    assert(af_holiday_cards_clear(cards,3) && af_reward_good_field_get(cards,&streak));
    assert(!memcmp(streak.rtc,before_streak.rtc,8) && streak.days==before_streak.days);
    admitted=1;clock_data.day=16;af_rw_field_rank();
    assert(af_reward_good_field_get(cards,&streak) && streak.days==2);
    admitted=15;af_rw_field_rank();assert(mFAs_CheckGoodField());
    mFAs_ClearGoodField();assert(!mFAs_CheckGoodField());
    assert(af_reward_good_field_get(cards,&streak) && !streak.days);
    const AFRewardGoodField invalid_fields[]={{{0},1},{{0,0,0,30,0,2,7,234},0},
        {{0,0,24,29,0,9,7,234},0},{{0,0,0,29,7,9,7,234},0},{{0,0,0,29,0,9,7,234},16}};
    for(unsigned i=0;i<sizeof(invalid_fields)/sizeof(*invalid_fields);i++) {
        u8 saved_cards[AF_HC_BYTES];memcpy(saved_cards,cards,sizeof(cards));
        assert(!af_reward_good_field_set(cards,invalid_fields+i) && !memcmp(saved_cards,cards,sizeof(cards)));
    }
    for(unsigned i=60;i<64;i++) {cards[i]=1;assert(!af_holiday_cards_valid(cards));cards[i]=0;}
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
    puts("Native reward providers: four players, town-first flags, birthday year, selected collections, refused insertion, trophy acknowledgement, whole-source perfect-town streak, leap days, backward clocks, and player clearing pass.");
}
