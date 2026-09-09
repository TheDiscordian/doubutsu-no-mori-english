#ifndef AF_MUSEUM_CREATOR_H
#define AF_MUSEUM_CREATOR_H

#include "post_office_creator.h"

/* Animal-slot descriptor: AFMU, template BE16, gift BE16, paper 24,
 * two zero reserved bytes, marker F8. No remail, condition, or foreign flag.
 */
int af_museum_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
