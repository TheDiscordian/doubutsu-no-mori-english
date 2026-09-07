#ifndef AF_MAIL_FORMAT_H
#define AF_MAIL_FORMAT_H

#include "record.h"

#define AF_MAIL_TEXT_BYTES 1024u

typedef struct {
    const unsigned char *text;
    unsigned int length;
    unsigned short id;
    unsigned short reserved;
} AfMailPart;

typedef struct {
    unsigned int catalog;
    unsigned int kind;
    /* Classic: header/body/footer. Composite: header/A/B/C/footer. */
    AfMailPart parts[5];
} AfMailTemplates;

typedef struct {
    /* Header/body/footer; offsets account for the reference processing order. */
    unsigned short offsets[3];
    unsigned short lengths[3];
    unsigned short header_split;
    unsigned char final_capital;
    unsigned char reserved;
    unsigned char text[AF_MAIL_TEXT_BYTES];
} AfMailText;

/* Inputs must be stable during this synchronous call. Aligned output may
 * overlap inputs: publication occurs only after complete successful assembly.
 * This routine does not acquire resources, assign mail tags, or modify saves.
 */
int af_mail_format(AfMailText *output, const AfMailRecord *record, const AfMailTemplates *templates);

#endif
