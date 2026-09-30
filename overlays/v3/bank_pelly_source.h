#ifndef AF_V3_BANK_PELLY_SOURCE_H
#define AF_V3_BANK_PELLY_SOURCE_H
#include "bank_pelly.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef struct AFBankPellyActor NPC_POSTGIRL_ACTOR;
typedef NPC_POSTGIRL_ACTOR ACTOR;
typedef struct {int open_flag;} AFBankPellySubmenu;
typedef struct {AFBankPellySubmenu submenu;} GAME_PLAY;
typedef GAME_PLAY GAME;
typedef void mMsg_Window_c;
struct AFBankPellyActor {
    struct {struct {int draw_type;} draw;} npc_class;
    int status,is_desk_full,has_bank_account,action,next_action;
    void (*setup_action)(NPC_POSTGIRL_ACTOR *,GAME_PLAY *,int);
    unsigned short npc_id;
};
typedef struct {
    int (*talk_chk_proc)(unsigned short);
    int (*get_msg_num_proc)(unsigned short,int);
} AFBankPellyApril;
extern AFBankPellyApril *af_bank_pelly_april_clip(void);
extern void af_bank_pelly_message(int);
#define CLIP(name) af_bank_pelly_april_clip()
#define mDemo_Set_msg_num af_bank_pelly_message
typedef struct {struct {u32 loan;} inventory;u32 bank_account;} AFBankPellyPrivate;
extern void *af_bank_pelly_window(void);
extern int af_bank_pelly_message_number(void *);
extern int af_bank_pelly_continue(void *);
extern int af_bank_pelly_disappeared(void *);
extern int af_bank_pelly_appeared(void *);
extern void af_bank_pelly_unlock(void *);
extern void af_bank_pelly_force(void *);
extern void af_bank_pelly_set_continue(void *,int);
extern void af_bank_pelly_change(void *,int);
extern void af_bank_pelly_free_string(void *,int,const u8 *,int);
extern void af_bank_pelly_appear(void *,int);
extern void af_bank_pelly_disappear(void *);
extern int af_bank_pelly_order(int,int);
extern void af_bank_pelly_set_order(int,int,int);
extern void *af_bank_pelly_choice_window(void);
extern int af_bank_pelly_choice(void *);
extern int af_bank_pelly_mail_count(void);
extern int af_bank_pelly_first_job(void);
extern int af_bank_pelly_foreigner(void);
extern void af_bank_pelly_loan_balance(void);
extern void af_bank_pelly_open_menu(AFBankPellySubmenu *,int,int,int);
/* Use the complete compiled donor formatter, not the distinct N64 ABI. */
extern int mFont_UnintToString(u8 *,int,u32,int,int,int,int);
#define mMsg_Get_base_window_p af_bank_pelly_window
#define mMsg_Get_msg_num af_bank_pelly_message_number
#define mMsg_Check_MainNormalContinue af_bank_pelly_continue
#define mMsg_Check_main_wait af_bank_pelly_disappeared
#define mMsg_Check_not_series_main_wait af_bank_pelly_appeared
#define mMsg_Unset_LockContinue af_bank_pelly_unlock
#define mMsg_Set_ForceNext af_bank_pelly_force
#define mMsg_Set_continue_msg_num af_bank_pelly_set_continue
#define mMsg_ChangeMsgData af_bank_pelly_change
#define mMsg_Set_free_str af_bank_pelly_free_string
#define mMsg_request_main_appear_wait_type2 af_bank_pelly_appear
#define mMsg_request_main_disappear_wait_type2 af_bank_pelly_disappear
#define mDemo_Get_OrderValue af_bank_pelly_order
#define mDemo_Set_OrderValue af_bank_pelly_set_order
#define mChoice_Get_base_window_p af_bank_pelly_choice_window
#define mChoice_Get_ChoseNum af_bank_pelly_choice
#define mPO_get_keep_mail_sum af_bank_pelly_mail_count
#define mEv_CheckFirstJob af_bank_pelly_first_job
#define mLd_PlayerManKindCheck af_bank_pelly_foreigner
#define aPG_set_loan_balance af_bank_pelly_loan_balance
#define mSM_open_submenu af_bank_pelly_open_menu
#endif
