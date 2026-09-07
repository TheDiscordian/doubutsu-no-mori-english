#ifndef AF_MAIL_GENERATE_H
#define AF_MAIL_GENERATE_H

#include "../../runtime/mail/catalog.h"

/* Caller-owned transient state, never a saved structure. No native generation
 * hook is installed by this implementation. The caller must supply approved
 * template identities and complete English field values before generation.
 */
typedef struct {
    unsigned int valid;
    unsigned int capital;
    AfMailField fields[AF_MAIL_FIELD_COUNT];
} AfMailCapture;

typedef struct {
    unsigned short catalog;
    unsigned char kind;
    unsigned char reserved;
    unsigned short templates[5];
} AfMailSelection;

typedef struct {
    AfMailWorkspace catalog;
    AfMailText text;
    unsigned char wire[128] __attribute__((aligned(16)));
} AfMailGenerateWork;

void af_mail_capture_reset(AfMailCapture *capture);

/* Copy a stable value now, including trailing spaces and article. Invalid data
 * invalidates this slot, so a rejected replacement cannot reuse an older value.
 * Other slots remain unchanged. The caller must check the return value.
 */
int af_mail_capture_set(AfMailCapture *capture, unsigned int slot,
                        const unsigned char *text, unsigned int length, unsigned int article);

/* Exact 164-byte whole-record transaction. On success only split/text and the
 * transient capital flag change. On failure mail and capture remain unchanged;
 * workspace is scratch. All structures require their natural alignment, work
 * requires 16-byte alignment, and work/mail/capture/selection must not overlap.
 * Full formatting and every selected cartridge part validate before publishing.
 * Native metadata, delivery, and template semantic approval belong to the caller.
 */
int af_mail_generate(unsigned char *mail, unsigned int mail_size, AfMailCapture *capture,
                      const AfMailSelection *selection, AfMailGenerateWork *work);

#endif
