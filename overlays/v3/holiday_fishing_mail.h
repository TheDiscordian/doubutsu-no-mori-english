#ifndef AF_V3_HOLIDAY_FISHING_MAIL_H
#define AF_V3_HOLIDAY_FISHING_MAIL_H
#include "holiday_fishing_live.h"
#include "../../runtime/mail/catalog.h"
extern const AFHFH af_hf_prizes[],af_hf_prize_limits[3];
extern const unsigned int af_hf_services_ready;
extern const AFHFB af_hf_native_save[];
extern const AFHFH af_hf_native_rare;
extern unsigned int af_mail_generation_capital;
extern void *af_hf_mail_alloc(unsigned int);
extern void af_hf_mail_free(void *),af_hf_mail_clear(AFHFB *);
extern void af_hf_mail_copy(AFHFB *,const AFHFB *),af_hf_mail_timecopy(void *,const void *);
extern int af_hf_mail_house(unsigned int),af_hf_mail_slot(AFHFB *,int);
extern int af_hf_mail_kept(void),af_hf_mail_receipt(AFHFB *,int);
extern int af_hf_mail_selected(unsigned int),af_hf_mail_owned(const AFHFB *,unsigned int);
extern int af_hf_mail_item_name(AFHFB *,unsigned int,unsigned int);
unsigned int af_hf_mail_prize(unsigned int);
/* -1 means invalid state, zero retains pending deliveries, one completes them.
 * Acknowledgement is published only after the actual native delivery succeeds.
 * Mailbox or allocation exhaustion is retryable, never a deleted record.
 */
int af_hf_mail_deliver(void);
void af_hf_mail_notice(void *,const void *);
#endif
