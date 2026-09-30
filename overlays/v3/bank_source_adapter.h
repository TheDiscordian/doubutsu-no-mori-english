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
typedef struct AFBankSourceSubmenu Submenu;
typedef struct AFBankSourceGame GAME;
typedef struct {
    int proc_status,next_proc_status,move_drt,closed;
#ifdef AF_BANK_FRONTEND
    float position[2];
    void (*pre_move_func)(Submenu *);
    void (*pre_draw_func)(Submenu *,GAME *);
#endif
} mSM_MenuInfo_c;
typedef struct {
    struct {
        int trigger,animation_flag;
#ifdef AF_BANK_FRONTEND
        float texture_pos[2];
        void (*menu_move_func)(Submenu *);
        void (*menu_draw_func)(Submenu *,GAME *);
#endif
    } menu_control;
    mBN_Ovl_c *bank_ovl;
    mSM_MenuInfo_c menu_info[23];
    void (*move_chg_base_proc)(mSM_MenuInfo_c *,int);
#ifdef AF_BANK_FRONTEND
    void (*move_Move_proc)(Submenu *,mSM_MenuInfo_c *);
    void (*move_End_proc)(Submenu *,mSM_MenuInfo_c *);
    void (*set_char_matrix_proc)(void *);
#endif
} Submenu_Overlay_c;
struct AFBankSourceSubmenu {Submenu_Overlay_c *overlay;};
#endif
