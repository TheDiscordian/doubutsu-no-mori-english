#ifndef AF_POST_OFFICE_CREATOR_H
#define AF_POST_OFFICE_CREATOR_H

#include "academy_score_creator.h"

/* Animal-slot descriptor: AFPO, template BE16, gift BE16, paper 55,
 * two zero reserved bytes, marker F9. No remail, condition, or foreign flag.
 */
int af_post_office_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
