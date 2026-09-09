#ifndef AF_NOTICE_OWNER_H
#define AF_NOTICE_OWNER_H

#include "notice_treasure_creator.h"

/* The fixed native bridge supplies AFNR | parent-frame BE32 | phase | 0 | 0 | 244.
 * Phase one owns original burial and a sixteen-byte stack-only undo record.
 * Phase two creates, copies only the 96-byte message, and publishes the post.
 * The bridge rolls burial back after any phase-two loader/creator failure.
 */
int af_notice_owner_create(AfNpcMailCreateWork *, unsigned char *, AfNpcMailSession **,
                            unsigned int *);

#endif
