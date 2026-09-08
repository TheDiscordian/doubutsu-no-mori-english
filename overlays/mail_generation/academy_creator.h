#ifndef AF_ACADEMY_CREATOR_H
#define AF_ACADEMY_CREATOR_H

#include "villager_event_creator.h"

/* HRA welcome/advice: twelve zero bytes, template BE16, zero gift BE16,
 * FB marker, paper 51. Original player, null animal, condition zero, foreign one.
 * Score/reward letters require their own complete field capture before use.
 */
int af_academy_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
