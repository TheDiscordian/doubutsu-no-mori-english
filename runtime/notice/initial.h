#ifndef AF_NOTICE_INITIAL_H
#define AF_NOTICE_INITIAL_H

#include "record.h"
#include "../mail/catalog.h"

typedef struct {
    unsigned int length;
    unsigned char text[AF_MAIL_TEXT_BYTES];
} AfNoticeText;

typedef struct {
    AfMailWorkspace mail;
    AfMailText letter;
    unsigned char wire[AF_MAIL_RECORD_BYTES];
} AfNoticeWorkspace;

/* Four complete initial bodies, immutable catalogue four. Profile one changes
 * only the source-bound C Stick instruction to C Buttons. All manual whitespace
 * remains. Other notices require their own semantic/field approvals.
 * Workspace is disposable and must be 16-byte aligned and disjoint from both
 * inputs and output. Output is unchanged on failure and may overlap input.
 * These APIs are not yet installed at the native creation/draw boundaries.
 */
int af_notice_initial_pack(unsigned char *output, unsigned int capacity,
                            unsigned int template_id, unsigned int capital);
int af_notice_initial_restore(AfNoticeText *output, const unsigned char *input,
                               unsigned int size, AfNoticeWorkspace *work);

#endif
