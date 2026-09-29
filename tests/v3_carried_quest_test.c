/* Real quest planner/directory services; native allocation and clock doubled. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/carried_quest.h"
#define CHECK(x) do {if(!(x)){fprintf(stderr,"line %u: %s\n",__LINE__,#x);exit(1);}}while(0)
typedef unsigned char u8;
typedef unsigned int u32;
AFCarriedQuest af_cw_state;
u32 af_cw_available=1,af_holiday_native_count,af_test_event_item_profile;
u32 af_test_carried_profile[8];
AFHolidayNativeDay af_holiday_native_days[AF_HN_DAYS];
u8 af_holiday_native_index[128];
const u8 af_cw_native_rtc[8]={0,0,0,6,0,5,0x07,0xEA}; /* 2026-05-06 */
static u8 cards[AF_HC_BYTES],saved[40],marker[40];
static int selected=1,has_saved,has_marker,allocation_fails,prior_calls,random_calls;
static float random_value;
static void *bound_common;
static const volatile unsigned short *bound_status;
u8 *af_v3_card_data(void){return cards;}
u32 af_carried_quantity(u32 item){return selected && item==0x2D28;}
float fqrand(void){random_calls++;return random_value;}
int af_cw_prior_calendar_before_cleanup(void){prior_calls++;return 17;}
void af_carried_spirit_event_bind(void *p,const volatile unsigned short *s){bound_common=p;bound_status=s;}
void *af_cw_native_get_save(int type,int id){CHECK(type==115 && id==54);return has_saved?saved:0;}
void *af_cw_native_reserve_save(int type,int id){CHECK(type==115 && id==54);if(allocation_fails)return 0;has_saved=1;return saved;}
void *af_cw_native_get_common(int type,int id){CHECK(type==115 && id==55);return has_marker?marker:0;}
void *af_cw_native_reserve_common(int type,int id){CHECK(type==115 && id==55);if(allocation_fails)return 0;memset(marker,0,40);has_marker=1;return marker;}
static void reset_directory(void){
    memset(af_holiday_native_index,255,sizeof(af_holiday_native_index));
    memset(af_holiday_native_days,255,sizeof(af_holiday_native_days));af_holiday_native_count=0;
}
static void reset_cards(void){af_holiday_cards_reset(cards);CHECK(af_carried_save_bind(cards,0,64));}
int main(void){
    reset_cards();reset_directory();
    /* The source rerolls only on expiry, with an inclusive seven-day window. */
    AFDiaryDate date={2026,5,6};random_value=0.0f;
    CHECK(af_cw_plan(cards,date,fqrand)==0 && af_carried_quest_day(cards)==0x0508 && random_calls==1);
    CHECK(af_cw_plan(cards,date,fqrand)==0 && random_calls==1);
    date.day=8;CHECK(af_cw_plan(cards,date,fqrand)==1 && random_calls==1);
    date.day=15;CHECK(af_cw_plan(cards,date,fqrand)==1 && random_calls==1);
    date.day=16;random_value=0.999f;
    CHECK(af_cw_plan(cards,date,fqrand)==0 && af_carried_quest_day(cards)==0x0514 && random_calls==2);
    CHECK(af_carried_quest_set_day(cards,0));date=(AFDiaryDate){2026,12,30};random_value=0.4f;
    CHECK(af_cw_plan(cards,date,fqrand)==0 && af_carried_quest_day(cards)==0x0102);
    date=(AFDiaryDate){2027,1,2};CHECK(af_cw_plan(cards,date,fqrand)==1);
    CHECK(af_carried_quest_set_day(cards,0x0C1F));CHECK(af_cw_plan(cards,date,fqrand)==1);
    for(unsigned leap=0;leap<2;leap++){
        CHECK(af_carried_quest_set_day(cards,0));date=(AFDiaryDate){2027+leap,2,27};random_value=0;
        CHECK(af_cw_plan(cards,date,fqrand)==0);
        CHECK(af_carried_quest_day(cards)==(leap?0x021D:0x0301));
    }
    u8 before[48];memcpy(before,cards,48);date=(AFDiaryDate){2026,2,29};
    CHECK(af_cw_plan(cards,date,fqrand)==-1 && !memcmp(before,cards,48));
    CHECK(af_carried_quest_set_day(cards,0));random_value=1;
    CHECK(af_cw_plan(cards,(AFDiaryDate){2026,5,6},fqrand)==-1 && !af_carried_quest_day(cards));
    /* Native allocation, independent keep state, complete 44-byte common area. */
    CHECK(!af_cw_reserve_save(114,54) && !af_cw_reserve_common(114,55));
    CHECK(af_carried_quest_set_day(cards,0x0506));random_value=0;
    CHECK(af_cw_calendar_before_cleanup()==17 && prior_calls==1 && af_holiday_native_count==1);
    unsigned slot=af_holiday_native_index[115];AFHolidayNativeDay *d=af_holiday_native_days+slot;
    CHECK(d->hours==15 && d->begin==0x0101 && d->end==0x0C1F && d->status==AF_HE_EXIST);
    CHECK(!af_cw_get_save(114,54));allocation_fails=1;
    CHECK(!af_cw_reserve_save(114,54) && !af_cw_reserve_common(114,55));allocation_fails=0;
    CHECK(af_cw_reserve_save(114,54)==saved && af_cw_get_save(114,54)==saved);
    CHECK(!af_cw_get_save(115,54) && !af_cw_get_save(114,55));
    af_cw_state.placement=(void *)1;memset(&af_cw_state.common,0xAB,44);
    CHECK(af_cw_reserve_common(114,55)==&af_cw_state.common && bound_status==&d->status);
    for(unsigned i=0;i<44;i++)CHECK(!((u8 *)&af_cw_state.common)[i]);
    CHECK(af_cw_state.placement==(void *)1 && bound_common==&af_cw_state.common);
    d->status|=AF_HE_RUN;af_cw_state.common.flags=0x4000;af_cw_set_keep(115);
    CHECK(af_cw_check_keep(115) && !af_cw_check_keep(114));
    CHECK(af_cw_calendar_before_cleanup()==17 && af_holiday_native_count==1 && (d->status&AF_HE_RUN));
    has_marker=0;CHECK(!af_cw_check_keep(115));CHECK(!af_cw_get_common(114,55) && !bound_common && !bound_status);
    CHECK(af_cw_reserve_common(114,55));af_cw_set_keep(115);af_cw_clear_keep(115);
    CHECK(!af_cw_check_keep(115) && !bound_common);
    af_cw_finish_hunt();CHECK(!af_carried_quest_day(cards));
    reset_directory();selected=0;CHECK(af_cw_calendar_before_cleanup()==17 && !af_holiday_native_count);
    CHECK(!af_cw_reserve_save(114,54));selected=1;af_cw_available=0;
    CHECK(af_cw_calendar_before_cleanup()==17 && !af_holiday_native_count);
    /* Full or corrupt directories reject atomically; they never alias slots. */
    for(unsigned i=0;i<64;i++)CHECK(af_holiday_native_append(i,1,0x0101,0x0C1F)==1);
    CHECK(af_holiday_native_append(115,15,0x0101,0x0C1F)==-2 && af_holiday_native_index[115]==255);
    CHECK(af_holiday_native_append(128,1,0,0)==-1 && af_holiday_native_count==64);
    af_holiday_native_index[20]=255;
    CHECK(af_holiday_native_append(115,15,0,0)==-1 && af_holiday_native_count==64);
    puts("Source hunt dates, leap/year wrap, real event flags, complete common-state lifetime, native allocation failure, disabled profiles, and atomic directory rejection pass. Native services are doubled.");
    return 0;
}
