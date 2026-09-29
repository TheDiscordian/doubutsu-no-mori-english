/* Complete source manager callbacks, with explicit native placement/state.
 * The quest's independent admission word stays off until all NPC services bind. */
#include "carried_event.h"
#include "carried_quest.h"
#include "holiday_owner.h"
extern int af_cw_source_start(void *,void *),af_cw_source_stop(void *,void *),af_cw_source_in(void *,void *);
extern const u8 af_cw_native_rtc[8];
extern volatile const u8 af_cw_native_player;
extern void *af_cw_native_private(void);
extern u32 af_carried_quantity(u32);
extern int af_holiday_native_check_status(int,int);
extern AFHolidayPlace *af_holiday_native_get_place(int,u8);
#ifndef AF_CW_NATIVE_NAME
#error The installer must bind the persistent additional NPC identity
#endif
static int enabled(void) {return *(const volatile u32 *)&af_cw_available==1 && af_carried_quantity(0x2D28)==1;}
static int valid(const AFHolidayControl *c) {return c && c->type==AF_CW_NATIVE && enabled();}
Private_c *af_cw_private(void) {return af_cw_native_private();}
lbRTC_time_c *af_cw_clock(void) {return (lbRTC_time_c *)af_cw_native_rtc;}
int af_cw_player(void) {return af_cw_native_player;}
int af_cw_event_type(const aEvMgr_event_ctrl_c *c) {return c?(int)((const AFHolidayControl *)c)->type:-1;}
mEv_place_data_c *make_actor_in_free_block(EVENT_MANAGER_ACTOR *m,aEvMgr_event_ctrl_c *control,u16 name,int id,int adjust) {
    const AFHolidayControl *c=control;AFHolidayPlace *place=0;
    if(!m || !valid(c) || name!=0xD06F || id!=0x51 || adjust!=5)return 0;
    int result=af_holiday_placement_native_free(m,AF_CW_NATIVE,AF_CW_NATIVE_NAME,(u32)id,adjust,
        AF_CW_SOURCE+name+id,&place);
    return result==1?place:0;
}
mEv_place_data_c *show_actor_at_wade_checkfgcol(EVENT_MANAGER_ACTOR *m,aEvMgr_event_ctrl_c *control,int id) {
    AFHolidayControl *c=control;
    if(!m || !valid(c) || id!=0x51)return 0;
    int result=af_holiday_placement_native_show_type(m,AF_CW_NATIVE,(u32)id,&c->block);
    if(result==2)return (void *)-1;
    /* The source only tests the result's sentinel/null identity. Return the
     * actual placement, never a fabricated non-null success pointer. */
    return result==1?af_holiday_native_get_place(AF_CW_NATIVE,(u8)id):0;
}
int af_cw_manager_start(void *m,AFHolidayControl *c) {
    if(!m || !valid(c) || af_cw_player()<0 || af_cw_player()>4 || !af_cw_private())return 0;
    return af_cw_source_start(m,c);
}
int af_cw_manager_stop(void *m,AFHolidayControl *c) {
    if(!m || !valid(c) || !af_cw_private())return 0;
    return af_cw_source_stop(m,c);
}
int af_cw_manager_in(void *m,AFHolidayControl *c) {
    return m && valid(c)?af_cw_source_in(m,c):0;
}
int af_cw_manager_out(void *m,AFHolidayControl *c) {
    (void)m;return valid(c)?af_holiday_native_check_status(AF_CW_NATIVE,AF_HE_STOP):0;
}
