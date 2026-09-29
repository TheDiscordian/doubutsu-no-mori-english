#ifndef AF_V3_HOLIDAY_EXERCISE_H
#define AF_V3_HOLIDAY_EXERCISE_H
#include "holiday_participants.h"
/* Complete exercise source uses the same native NPC prefix as every imported
 * participant. These views are explicit services, never a cast of GC save data
 * or a success stub for an uninstalled card/handover owner. */
typedef AFHPFrame cKF_FrameControl_c;
typedef void (*aNPC_SUB_PROC)(NPC_ACTOR *,GAME_PLAY *);
typedef struct {s8 measure;f32 measure_progress;u16 tempo;} Radio_c;
typedef u8 lbRTC_day_t;
typedef struct {u16 year;u8 month,day;} lbRTC_ymd_c;
typedef struct {u8 sec,min,hour,day,weekday,month;u16 year;} lbRTC_time_c;
typedef struct {lbRTC_ymd_c last_date;u8 days;} mPr_day_day_c;
typedef struct {mPr_day_day_c radiocard;} Private_c;
typedef void mMsg_Window_c;
Private_c *af_he_private(void);
const lbRTC_time_c *af_he_clock(void);
int af_he_player(void),af_he_block_x(GAME *),af_he_block_z(GAME *);
u32 af_he_frame(GAME *);
int af_he_player_events(void);
int af_he_message(int);
int af_he_begin(ACTOR *,int),af_he_finish(int);
void *af_he_handover_master(void);
int af_he_handover_mode(void);
void af_he_handover_after(int);
void af_he_npc_save(ACTOR *,GAME *);
int mEv_check_status(int,int);
int sAdos_GetRadioCounter(Radio_c *);
int lbRTC_IsEqualDate(int,int,int,int,int,int);
void mCD_calendar_event_on(int,int,int,int);
int mCD_calendar_event_check(int,int,int,int,int);
u8 mSC_get_soncho_event(void);
void mSC_item_string_set(u16,int),mSC_event_name_set(int),mSC_set_free_str_number(int,u32);
u16 mSC_trophy_item(int);
int mSC_trophy_get(int);
void mSC_trophy_set(int);
int mPr_SetFreePossessionItem(void *,u16,int);
void mIN_copy_name_str(u8 *,u16);
int mIN_get_item_article(u16);
mMsg_Window_c *mMsg_Get_base_window_p(void);
void mMsg_Set_free_str_art(mMsg_Window_c *,int,const u8 *,int,int);
void mMsg_Set_free_str(mMsg_Window_c *,int,const u8 *,int);
int mFont_UnintToString(u8 *,int,u32,int,int,int,int);
void mMsg_Set_LockContinue(mMsg_Window_c *),mMsg_Unset_LockContinue(mMsg_Window_c *);
int mMsg_Get_msg_num(mMsg_Window_c *),mMsg_Check_MainNormalContinue(mMsg_Window_c *);
void mMsg_Set_continue_msg_num(mMsg_Window_c *,int);
u16 mDemo_Get_OrderValue(int,int);
void mDemo_Set_OrderValue(int,int,u16);
int mPlib_request_main_give_type1(GAME *,u16,int,int,int);
#ifdef __mips__
_Static_assert(sizeof(Radio_c)==12,"Complete donor radio counter");
_Static_assert(sizeof(mPr_day_day_c)==6,"Complete source card date/stamp state");
#endif
#endif
