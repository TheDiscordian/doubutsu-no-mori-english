/* The whole donor streak routines operate on an owned saved-state shadow,
 * never on native Save padding. Flush follows each mutating source routine.
 * Native assessment keeps its N64 geometry, tree counts, and ranked acres.
 */
#include "reward_event.h"
#include "holiday_cards.h"
extern u8 *af_v3_card_data(void);
extern void af_v3_save_halt(int) __attribute__((noreturn));
extern int af_v3_player_selected_equipment(u32);
extern void af_rw_native_rank_set(void);
extern int af_rw_native_rank_get(void),af_rw_native_rank_condition(int *,int *,int *);
static AFRewardField field;
AFRewardField *af_rw_good_field(void) {
    AFRewardGoodField s;
    if(!af_reward_good_field_get(af_v3_card_data(),&s))af_v3_save_halt(-1);
    field.renew_time=(lbRTC_time_c){s.rtc[0],s.rtc[1],s.rtc[2],s.rtc[3],s.rtc[4],s.rtc[5],
        (u16)((u32)s.rtc[6]*256+s.rtc[7])};
    field.perfect_day_streak=(int)s.days;
    return &field;
}
void af_rw_flush_good_field(void) {
    const lbRTC_time_c *t=&field.renew_time;
    AFRewardGoodField s={{t->sec,t->min,t->hour,t->day,t->weekday,t->month,
        (u8)(t->year>>8),(u8)t->year},(unsigned)field.perfect_day_streak};
    if(!af_reward_good_field_set(af_v3_card_data(),&s))af_v3_save_halt(-1);
}
int af_rw_times_equal(const lbRTC_time_c *a,const lbRTC_time_c *b) {
    return a && b && a->sec==b->sec && a->min==b->min && a->hour==b->hour &&
        a->day==b->day && a->weekday==b->weekday && a->month==b->month && a->year==b->year;
}
void af_rw_field_rank(void) {
    af_rw_native_rank_set();
    if(af_v3_player_selected_equipment(0x223A)>=0)af_rw_record_rank(af_rw_native_rank_get());
}
int af_rw_field_condition(int *rank,int *x,int *z) {
    if(!rank || !x || !z)return -1;
    int result=af_rw_native_rank_condition(rank,x,z);
    if(rank && af_v3_player_selected_equipment(0x223A)>=0)af_rw_record_rank(*rank);
    return result;
}
