#ifndef AF_V3_BANK_NATIVE_H
#define AF_V3_BANK_NATIVE_H
#include "bank_frontend.h"
/* These providers are installed only with real per-player saved-town ownership,
 * mechanic selection, and Pelly's reviewed house/resident eligibility. */
extern unsigned char *af_bank_native_account(void);
extern int af_bank_native_eligible(void),af_bank_native_selected(void);
extern void *af_bank_now_private;
extern unsigned char af_bank_player;
extern void af_bank_native_set_pocket(void *,int,unsigned short,unsigned int);
extern void af_bank_native_sound(unsigned int);
extern int af_bank_native_string_width(const unsigned char *,int,int);
/* Checked native field readers and all-or-nothing inventory/account publication. */
int af_bank_native_wallet(const void *,AFBankWallet *);
int af_bank_native_commit(unsigned char *,const unsigned char *,const unsigned char *,
    void *,const AFBankWallet *,const AFBankWallet *);
/* Pelly requests this mode before opening the existing repayment slot. Each
 * native lifecycle wrapper falls through to original repayment when unowned. */
int af_bank_native_request(void *);
/* Opening queues program 7 before the native linker raises open_flag. Treat
 * only this still-owned request as open while Pelly waits for construction. */
int af_bank_native_pending(void *);
int af_bank_native_construct(void *);
int af_bank_native_set_proc(void *);
int af_bank_native_destruct(void *);
int af_bank_native_cancel(void *);
#ifndef __mips__
extern void *af_bank_test_pointer(const void *,unsigned int);
extern void af_bank_test_store_pointer(void *,unsigned int,void *);
#endif
#endif
