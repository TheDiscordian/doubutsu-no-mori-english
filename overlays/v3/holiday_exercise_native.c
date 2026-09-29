/* Native observations for the complete exercise actor. Card inventory, actor
 * admission, and talk transport remain required providers, not success stubs. */
#include "holiday_exercise.h"
#include "constants.h"
extern int af_holiday_native_type(unsigned int),af_holiday_native_notify(unsigned int,void *);
extern int af_he_native_status(int,int),af_holiday_observers_clip(void);
extern int af_he_native_radio(Radio_c *);
extern const u32 *volatile af_hp_native_npc_clip;
extern volatile u8 af_hp_player_index;
extern const volatile u8 af_he_native_rtc[8];
#define FN(at,ret,...) ((ret (*)(__VA_ARGS__))(at))

u32 af_he_frame(GAME *game) {
    /* Actual original Taisou loads at 809E404C/809E427C. This is the Game
     * update counter, not Game_Play's separate render counter at 1EA0. */
    return game?*(const u32 *)((const u8 *)game+0xA0):0;
}
int af_he_block_x(GAME *game) {return game?((const s8 *)game)[0xE4]:-1;}
int af_he_block_z(GAME *game) {return game?((const s8 *)game)[0xE5]:-1;}
const lbRTC_time_c *af_he_clock(void) {
    static lbRTC_time_c t;
    t=(lbRTC_time_c){af_he_native_rtc[0],af_he_native_rtc[1],af_he_native_rtc[2],
        af_he_native_rtc[3],af_he_native_rtc[4],af_he_native_rtc[5],
        (u16)((u32)af_he_native_rtc[6]*256+af_he_native_rtc[7])};
    return &t;
}
int af_he_player(void) {return af_hp_private()?(int)af_hp_player_index:-1;}
int mEv_check_status(int source,int mask) {
    if(source!=mEv_EVENT_MORNING_AEROBICS && source!=mEv_EVENT_SPORTS_FAIR_AEROBICS)return 0;
    int native=af_holiday_native_type((u32)source);
    return native>=0 && af_he_native_status(native,mask);
}
void mEv_actor_dying_message(int source,ACTOR *actor) {
    if(source==mEv_EVENT_MORNING_AEROBICS || source==mEv_EVENT_SPORTS_FAIR_AEROBICS)
        af_holiday_native_notify((u32)source,actor);
}
int af_he_player_events(void) {
    return mEv_check_status(mEv_EVENT_MORNING_AEROBICS,mEv_STATUS_RUN) ||
        mEv_check_status(mEv_EVENT_SPORTS_FAIR_AEROBICS,mEv_STATUS_RUN);
}
int af_he_player_status(int native,int mask) {
    /* Existing player controls keep both original calendar checks. The added
     * event is considered only at those same RUN queries, not for all events. */
    return af_he_native_status(native,mask) ||
        (mask==mEv_STATUS_RUN && (native==8 || native==16) && af_he_player_events());
}
int sAdos_GetRadioCounter(Radio_c *counter) {
    return counter?af_he_native_radio(counter):-1;
}
void af_he_npc_save(ACTOR *actor,GAME *game) {
    if(actor && game && af_hp_owned(actor) && af_hp_native_npc_clip && af_holiday_observers_clip())
        FN(af_hp_native_npc_clip[0xC8/4],void,ACTOR *,GAME *)(actor,game);
}
