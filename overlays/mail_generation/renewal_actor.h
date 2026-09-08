#ifndef AF_RENEWAL_ACTOR_H
#define AF_RENEWAL_ACTOR_H

#include "leaflet.h"

/* Original native helper imports; host fixtures supply isolated equivalents. */
extern unsigned char af_renewal_save[];
extern unsigned int af_mail_generation_capital;
void *af_renewal_malloc(unsigned int);
void af_renewal_free(void *);
int af_renewal_house_player(unsigned int);
int af_renewal_working_player(unsigned int);
int af_renewal_free_mail(unsigned char *,unsigned int);
void af_renewal_clear_mail(unsigned char *);
void af_renewal_copy_id(unsigned char *,const unsigned char *);
void af_renewal_copy_mail(unsigned char *,const unsigned char *);

/* Return one only when complete preparation/publication succeeds, or when
 * the native eligibility rules select no recipients. Caller clears its saved
 * notification flag only after this succeeds. No pending heap pointer escapes.
 */
int af_renewal_deliver(unsigned int shop_level,const unsigned char *reopening_time);

#endif
