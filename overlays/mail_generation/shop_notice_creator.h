#ifndef AF_SHOP_NOTICE_CREATOR_H
#define AF_SHOP_NOTICE_CREATOR_H

#include "museum_creator.h"

/* Animal-slot descriptor: AFSN, template BE16, item BE16, paper 55,
 * recipient flag (0 = cleared leaflet, 1 = supplied player), zero, marker F7.
 * Reopening templates have item zero. No remail, condition, or foreign flag.
 * Publication and notification ownership remain outside this transaction.
 */
int af_shop_notice_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
