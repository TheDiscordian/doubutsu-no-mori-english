#ifndef AF_MAIL_CATALOG_H
#define AF_MAIL_CATALOG_H

#include "format.h"

#define AF_MAIL_CATALOG_VROM 0x03000000u
#define AF_MAIL_CATALOG_ID 2u
#define AF_MAIL_CATALOG_BYTES 319344u
/* Three 1024-byte sections; two additional DMA alignment gaps in composite body. */
#define AF_MAIL_SOURCE_BYTES 3104u

typedef struct {
    AfMailRecord record;
    AfMailTemplates templates;
    unsigned char source[AF_MAIL_SOURCE_BYTES] __attribute__((aligned(16)));
} AfMailWorkspace;

int af_mail_catalog_header_valid(const unsigned int *header, unsigned int catalog);

/* Workspace is caller-owned, aligned, and must not overlap input or output.
 * Its contents are scratch, including on failure. Do not put it on a small
 * nested stack. Output and encoded snapshot remain unchanged on failure.
 * Success publishes a complete letter, never partial template text.
 */
int af_mail_restore(AfMailText *output, const unsigned char *wire, unsigned int size,
                    AfMailWorkspace *workspace);

#endif
