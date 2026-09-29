#ifndef AF_V3_CARRIED_EVENT_H
#define AF_V3_CARRIED_EVENT_H
/* Complete carried-quest source uses the shared native NPC prefix. Additional
 * world/save services are explicit link dependencies, never donor-layout casts
 * or successful placeholders. This preparation does not register an actor. */
#include "holiday_participants.h"
typedef struct {u16 year;u8 month,day;} lbRTC_ymd_c;
typedef struct {u8 sec,min,hour,day,weekday,month;u16 year;} lbRTC_time_c;
typedef struct {u8 block_x[5],block_z[5];} mEv_gst_hitodama_block_c;
typedef struct {mEv_gst_hitodama_block_c hitodama_block_data;u16 flags;u8 reserved[32];} mEv_gst_common_c;
typedef struct {u16 okoruhito_str_no,flags;lbRTC_ymd_c renew_time;} mEv_gst_c;
typedef void Private_c;
typedef void mMsg_Window_c;
typedef void EVENT_MANAGER_ACTOR;
typedef void aEvMgr_event_ctrl_c;
typedef void mEv_place_data_c;
_Static_assert(sizeof(mEv_gst_common_c)==44,"Complete quest common storage");
_Static_assert(sizeof(mEv_gst_c)==8,"Complete quest saved date/flags");

Private_c *af_cw_private(void);
lbRTC_time_c *af_cw_clock(void);
int af_cw_player(void),af_cw_seconds(void),af_cw_schedule(const ACTOR *);
ACTOR *af_cw_player_actor(GAME *);
s16 *af_cw_actor_specific(ACTOR *);
u8 *af_cw_shadow(ACTOR *);
s32 *af_cw_melody(ACTOR *);
xyz_t *af_cw_scale(ACTOR *);
void af_cw_change_schedule(NPC_ACTOR *,GAME *,int);
void af_cw_draw(ACTOR *,GAME *,unsigned);
void af_cw_dying(int,ACTOR *);
void *af_cw_handover_master(void);
void af_cw_finish_hunt(void),af_cw_clear_grass(int),af_cw_set_roof(int,unsigned);
void *mEv_get_common_area(int,int);
void *mEv_reserve_common_area(int,int);
int af_cw_event_type(const aEvMgr_event_ctrl_c *);
mEv_place_data_c **af_cw_placement(void);
mEv_place_data_c *make_actor_in_free_block(EVENT_MANAGER_ACTOR *,aEvMgr_event_ctrl_c *,u16,int,int);
mEv_place_data_c *show_actor_at_wade_checkfgcol(EVENT_MANAGER_ACTOR *,aEvMgr_event_ctrl_c *,int);
int mEv_check_keep(int);
void mEv_set_keep(int),mEv_clear_keep(int);
void mTM_set_renew_time(lbRTC_ymd_c *,lbRTC_time_c *);
int mFI_GetItemNumField_BCT(u16,u16),mFI_GetItemNumField(u16,u16);
int mFI_Wpos2BlockNum(int *,int *,xyz_t),mHS_get_arrange_idx(int);
void mString_Load_StringFromRom(u8 *,unsigned,int);
int mSP_CollectCheck(u16),mPr_SetFreePossessionItem(void *,u16,int);
u16 mRmTp_FtrItemNo2Item1ItemNo(u16,int);
u16 af_cw_reward_native(u16),af_cw_reward_at(int,const u16 *);
int af_cw_reward_supported(u16);
void mIN_copy_name_str(u8 *,u16);
int mIN_get_item_article(u16);
mMsg_Window_c *mMsg_Get_base_window_p(void);
void *mChoice_Get_base_window_p(void);
int mChoice_Get_ChoseNum(void *),mMsg_Check_MainNormalContinue(mMsg_Window_c *);
void mMsg_Set_item_str(mMsg_Window_c *,int,const u8 *,int);
void mMsg_Set_item_str_art(mMsg_Window_c *,int,const u8 *,int,int);
void mMsg_Set_LockContinue(mMsg_Window_c *),mMsg_Unset_LockContinue(mMsg_Window_c *);
void mMsg_Set_continue_msg_num(mMsg_Window_c *,int),mMsg_sound_set_voice_click(mMsg_Window_c *);
u16 mDemo_Get_OrderValue(int,int);
void mDemo_Set_OrderValue(int,int,u16);
int mPlib_request_main_give_type1(GAME *,u16,int,int,int);
void sAdo_SysTrgStart(u32);
#endif
