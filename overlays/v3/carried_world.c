/* Apply Wisp's reward at field renewal, never while live weed actors exist.
 * The pending town flag survives event-slot cleanup and ordinary save/reload.
 * Native seasonal clearing, snowmen, growth, and event notifications remain
 * owned by the complete original renewal routine. */
#include "carried_event.h"
#include "holiday_cards.h"
extern u8 *af_v3_card_data(void);
extern const int af_cw_native_scene;
extern const u16 af_cw_native_notification;
extern u16 af_cw_native_foreground[6][5][256];
#ifdef __mips__
extern u8 *af_cw_native_grow_owner;
#define original_renew ((void (*)(lbRTC_time_c *,int *))(af_cw_native_grow_owner+0x475C))
#define original_grass ((void (*)(lbRTC_time_c *,lbRTC_time_c *,u16 *))(af_cw_native_grow_owner+0x43D0))
#else
extern void af_test_cw_renew(lbRTC_time_c *,int *);
extern void af_test_cw_grass(lbRTC_time_c *,lbRTC_time_c *,u16 *);
#define original_renew af_test_cw_renew
#define original_grass af_test_cw_grass
#endif
void af_cw_clear_grass(int pending) {
    if(pending==0 || pending==1)
        (void)af_carried_quest_set_weeds(af_v3_card_data(),(unsigned)pending);
}
void af_cw_grow_grass(lbRTC_time_c *now,lbRTC_time_c *previous,u16 *cancel) {
    if(af_carried_quest_weeds(af_v3_card_data())!=1)original_grass(now,previous,cancel);
}
void af_cw_renew_field(lbRTC_time_c *now,int *deposit) {
    int pending=af_cw_native_scene==7 && af_carried_quest_weeds(af_v3_card_data())==1;
    if(pending) {
        for(unsigned z=0;z<6;z++)for(unsigned x=0;x<5;x++)for(unsigned i=0;i<256;i++) {
            u16 item=af_cw_native_foreground[z][x][i];
            if(item>=8 && item<=10)af_cw_native_foreground[z][x][i]=0;
        }
    }
    original_renew(now,deposit);
    /* Source notifications defer completion even though weeds are cleared.
     * Keep the pending flag so the next normal renewal also suppresses growth. */
    if(pending && af_cw_native_notification!=1)af_cw_clear_grass(0);
}
