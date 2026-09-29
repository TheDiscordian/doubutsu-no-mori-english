#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "carried_event.h"
#include "holiday_cards.h"
static u8 cards[AF_HC_BYTES];
int af_cw_native_scene;
u16 af_cw_native_notification,af_cw_native_foreground[6][5][256];
const unsigned af_carried_paper_mode=0;
unsigned af_test_carried_profile[8],af_test_event_item_profile;
static unsigned renewals,growths;
static lbRTC_time_c now,previous;
static u16 cancel[30*16];
static int deposit;
u8 *af_v3_card_data(void) {return cards;}
extern void af_cw_renew_field(lbRTC_time_c *,int *);
extern void af_cw_grow_grass(lbRTC_time_c *,lbRTC_time_c *,u16 *);
void af_test_cw_grass(lbRTC_time_c *n,lbRTC_time_c *p,u16 *c) {
    assert(n==&now && p==&previous && c==cancel);growths++;
}
void af_test_cw_renew(lbRTC_time_c *n,int *d) {
    assert(n==&now && d==&deposit);renewals++;
    if(af_cw_native_scene==7 && af_cw_native_notification!=1)
        af_cw_grow_grass(n,&previous,cancel);
}
static void seed(void) {
    for(unsigned z=0;z<6;z++)for(unsigned x=0;x<5;x++)for(unsigned i=0;i<256;i++)
        af_cw_native_foreground[z][x][i]=(u16)i;
}
static void check(unsigned cleared) {
    for(unsigned z=0;z<6;z++)for(unsigned x=0;x<5;x++)for(unsigned i=0;i<256;i++)
        assert(af_cw_native_foreground[z][x][i]==(cleared && i>=8 && i<=10?0:i));
}
int main(void) {
    af_holiday_cards_reset(cards);assert(af_carried_save_bind(cards,0,64));
    assert(af_carried_quest_weeds(cards)==0);seed();
    af_cw_clear_grass(1);assert(af_carried_quest_weeds(cards)==1);check(0);
    /* Neither a player reset nor a completed/expired hunt cancels the reward. */
    assert(af_carried_quest_set_day(cards,0x091D));
    assert(af_holiday_cards_clear(cards,2));assert(af_carried_quest_set_day(cards,0));
    assert(af_carried_save_bind(cards,0,64) && af_carried_quest_weeds(cards)==1);
    af_cw_clear_grass(2);assert(af_carried_quest_weeds(cards)==1);
    af_cw_native_scene=2;af_cw_renew_field(&now,&deposit);check(0);
    assert(renewals==1 && !growths && af_carried_quest_weeds(cards)==1);
    af_cw_native_scene=7;af_cw_native_notification=1;
    af_cw_renew_field(&now,&deposit);check(1);
    assert(renewals==2 && !growths && af_carried_quest_weeds(cards)==1);
    seed();af_cw_native_notification=0;af_cw_renew_field(&now,&deposit);check(1);
    assert(renewals==3 && !growths && !af_carried_quest_weeds(cards));
    seed();af_cw_renew_field(&now,&deposit);check(0);
    assert(renewals==4 && growths==1);
    cards[15]=4;assert(!af_holiday_cards_valid(cards));
    cards[15]=2;cards[8]=0;assert(!af_holiday_cards_valid(cards));
    cards[15]=0;assert(af_holiday_cards_valid(cards));
    af_cw_clear_grass(1);assert(af_carried_quest_weeds(cards)==-1 && !cards[15]);
    puts("deferred town-wide weed reward, renewal timing, retained growth, and saved ownership pass");
}
