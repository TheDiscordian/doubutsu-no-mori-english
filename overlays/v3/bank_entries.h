#ifndef AF_V3_BANK_ENTRIES_H
#define AF_V3_BANK_ENTRIES_H
/* Local overlay shims supply relocated original functions. Resident wrappers
 * never call nominal overlay addresses after the native loader moves them. */
typedef void (*AFBankMenuOriginal)(void *);
typedef void (*AFBankPellyOriginal)(void *,void *);
void af_bank_menu_construct_entry(void *,AFBankMenuOriginal);
void af_bank_menu_destruct_entry(void *,AFBankMenuOriginal);
void af_bank_menu_set_proc_entry(void *,AFBankMenuOriginal);
void af_bank_pelly_business_entry(void *,void *,AFBankPellyOriginal);
void af_bank_pelly_talk_entry(void *,AFBankMenuOriginal,AFBankMenuOriginal);
void af_bank_pelly_destruct_entry(void *,void *,AFBankPellyOriginal);
#endif
