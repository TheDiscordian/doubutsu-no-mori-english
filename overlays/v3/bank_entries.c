#include "bank_entries.h"
#include "bank_native.h"
#include "bank_pelly.h"

void af_bank_menu_construct_entry(void *s,AFBankMenuOriginal original) {
    /* Native construction establishes all common motion/drawing callbacks and
     * the ordinary numerical state. It performs no loan or wallet transfers. */
    original(s);(void)af_bank_native_construct(s);
}
void af_bank_menu_destruct_entry(void *s,AFBankMenuOriginal original) {
    if(af_bank_native_destruct(s)>=0)original(s);
}
void af_bank_menu_set_proc_entry(void *s,AFBankMenuOriginal original) {
    if(!af_bank_native_set_proc(s))original(s);
}
void af_bank_pelly_business_entry(void *a,void *g,AFBankPellyOriginal original) {
    if(!af_bank_pelly_native_business(a,g))original(a,g);
}
void af_bank_pelly_talk_entry(void *a,AFBankMenuOriginal original,AFBankMenuOriginal status) {
    /* Original greeting refreshes native mail/loan status before dispatch. The
     * bank view may add its bit, but never writes that bit to native status. */
    status(a);if(!af_bank_pelly_native_talk(a))original(a);
}
void af_bank_pelly_destruct_entry(void *a,void *g,AFBankPellyOriginal original) {
    if(af_bank_pelly_native_release(a)>=0)original(a,g);
}
