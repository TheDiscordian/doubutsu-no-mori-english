#ifndef AF_NPC_MAIL_CREATOR_H
#define AF_NPC_MAIL_CREATOR_H

#include "npc_capture.h"

typedef struct {
    AfNpcMailCaptureWork captured;
    unsigned char stage[164] __attribute__((aligned(16)));
    AfMailGenerateWork generation;
} AfNpcMailCreateWork;

/* Synchronous whole-creator transaction. The caller owns this aligned work,
 * the complete immutable overlay/resources, a 164-byte destination, the
 * resident active-session pointer, and the sticky capitalization word.
 * Set only captured.session's player/animal/remail/condition/foreign inputs.
 * All other work fields are reset by this function, including stale capture.
 * Failure preserves the complete destination and capitalization. The active
 * pointer is restored before returning; nested active sessions are rejected.
 * Return one only after complete native metadata and English text publication.
 * This does not allocate, load cartridge code, or submit/deliver the letter.
 */
int af_npc_mail_create(AfNpcMailCreateWork *, unsigned char *, AfNpcMailSession **, unsigned int *);

#endif
