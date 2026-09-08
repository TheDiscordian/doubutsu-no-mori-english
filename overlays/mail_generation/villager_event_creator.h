#ifndef AF_VILLAGER_EVENT_CREATOR_H
#define AF_VILLAGER_EVENT_CREATOR_H

#include "departed_creator.h"

/* Synchronous eighteen-byte reply-origin descriptor: native NPC identity (12),
 * template (2), gift (2), FC marker, paper. Condition zero, foreign one, animal
 * null. The player remains the original sixteen-byte recipient identity.
 */
int af_villager_event_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);

#endif
