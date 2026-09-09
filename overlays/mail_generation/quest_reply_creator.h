#ifndef AF_QUEST_REPLY_CREATOR_H
#define AF_QUEST_REPLY_CREATOR_H
#include "shop_notice_creator.h"
/* Original player and animal identities remain intact. The eighteen-byte
 * remail input carries AFQR, rank, reserved zero, gift BE16, eight zeros,
 * marker 246, and reserved zero. condition=0, foreign=1 satisfy the unchanged
 * synchronous loader ABI; the marker distinguishes this internal request
 * from ordinary visitor mail, whose personality is in 0..5.
 */
int af_quest_reply_mail_create(AfNpcMailCreateWork *,unsigned char *,AfNpcMailSession **,unsigned int *);
#endif
