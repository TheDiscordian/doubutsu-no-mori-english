#ifndef AF_NOTICE_TREASURE_CREATOR_H
#define AF_NOTICE_TREASURE_CREATOR_H

#include "quest_reply_creator.h"

/* Optional first dispatcher for the existing synchronous creator loader.
 * player points to the native selected animal identity (at least sixteen
 * readable bytes); animal points to this twelve-byte descriptor:
 *   AFNT | BE16 template | BE16 item | row | column | zero | 245
 * condition, foreign, and remail are zero. The marker cannot be a personality.
 * Caller supplies the original selected template/item/coordinates. The creator
 * looks up the article by native item identity and verifies the complete name.
 *
 * Success publishes 96 compact notice bytes plus 68 zero staging bytes to the
 * loader's required 164-byte destination. No timestamp, saved post, buried item,
 * or eligibility flag is changed here. The native owner must copy just the
 * message and publish only after success, with a defined failure recovery path.
 */
int af_notice_treasure_create(AfNpcMailCreateWork *, unsigned char *, AfNpcMailSession **,
                               unsigned int *);

#endif
