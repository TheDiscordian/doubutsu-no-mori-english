#ifndef AF_V3_BANK_SOURCE_ADAPTER_H
#define AF_V3_BANK_SOURCE_ADAPTER_H
#include "bank_account.h"
/* These are scoped source views, not native structs or guessed offsets. The
 * complete source numerical/controller functions run only inside the wrappers. */
typedef unsigned char u8;
typedef unsigned short mActor_name_t;
typedef unsigned int u32;
typedef AFBankMenu mBN_Ovl_c;
typedef struct {AFBankWallet inventory;u32 bank_account;} Private_c;
typedef struct {int proc_status,next_proc_status,move_drt,closed;} mSM_MenuInfo_c;
typedef struct {
    struct {int trigger,animation_flag;} menu_control;
    mBN_Ovl_c *bank_ovl;
    mSM_MenuInfo_c menu_info[23];
    void (*move_chg_base_proc)(mSM_MenuInfo_c *,int);
} Submenu_Overlay_c;
typedef struct {Submenu_Overlay_c *overlay;} Submenu;
#endif
