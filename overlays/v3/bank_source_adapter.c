/* Included after the generated complete source functions. No source view
 * escapes this call; sound requests are returned, never played by a host test. */
static int source_open(AFBankMenu *menu,const AFBankWallet *wallet,u32 balance,
    Submenu *submenu,Submenu_Overlay_c *overlay) {
    if(af_bank_source_view || !menu || !wallet || !submenu || !overlay)return 0;
    af_bank_source_storage.inventory=*wallet;af_bank_source_storage.bank_account=balance;
    af_bank_source_view=&af_bank_source_storage;af_bank_source_sound=0;
    overlay->bank_ovl=menu;overlay->move_chg_base_proc=af_bank_source_close;
    submenu->overlay=overlay;return 1;
}
int af_bank_source_init(AFBankMenu *menu,const AFBankWallet *wallet,u32 balance) {
    Submenu submenu;Submenu_Overlay_c overlay={0};
    if(!source_open(menu,wallet,balance,&submenu,&overlay))return 0;
    mBN_bank_ovl_init(&submenu);af_bank_source_view=0;return 1;
}
int af_bank_source_step(AFBankMenu *menu,AFBankWallet *wallet,u32 *balance,u32 trigger,u32 *sound) {
    Submenu submenu;Submenu_Overlay_c overlay={0};
    if(!balance || !sound || !source_open(menu,wallet,*balance,&submenu,&overlay))return -1;
    overlay.menu_control.trigger=(int)trigger;
    mBN_move_Play(&submenu,&overlay.menu_info[mSM_OVL_BANK]);
    *sound=af_bank_source_sound;af_bank_source_view=0;
    if(!overlay.menu_info[mSM_OVL_BANK].closed)return AF_BANK_PREVIEW;
    if(trigger&BUTTON_B)return AF_BANK_CANCEL;
    *wallet=af_bank_source_storage.inventory;*balance=af_bank_source_storage.bank_account;return AF_BANK_CONFIRM;
}
