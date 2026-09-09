#ifndef AF_MAIL_CATALOG_H
#define AF_MAIL_CATALOG_H

#include "format.h"
#include "glyph.h"

#define AF_MAIL_CATALOG_VROM 0x03000000u
#define AF_MAIL_CATALOG_ID 2u
#define AF_MAIL_CATALOG_BYTES 319344u
#define AF_MAIL_FORTUNE_CATALOG_ID 3u
#define AF_MAIL_FORTUNE_CATALOG_VROM 0x03050000u
#define AF_MAIL_FORTUNE_CATALOG_BYTES 319392u
#define AF_MAIL_GLYPH_CATALOG_VROM 0x030A0000u
#define AF_MAIL_GLYPH_CATALOG_BYTES 326288u

/* Catalog two stays at its original address with its frozen contents. The
 * optional second resource is independently identified and validated. Unknown
 * IDs never fall back to a newer interpretation of an old saved letter.
 */
static inline unsigned int af_mail_catalog_vrom(unsigned int catalog) {
    return catalog == AF_MAIL_CATALOG_ID ? AF_MAIL_CATALOG_VROM :
        catalog == AF_MAIL_FORTUNE_CATALOG_ID ? AF_MAIL_FORTUNE_CATALOG_VROM :
        catalog == AF_MAIL_GLYPH_CATALOG_ID ? AF_MAIL_GLYPH_CATALOG_VROM : 0u;
}
static inline unsigned int af_mail_catalog_bytes(unsigned int catalog) {
    return catalog == AF_MAIL_CATALOG_ID ? AF_MAIL_CATALOG_BYTES :
        catalog == AF_MAIL_FORTUNE_CATALOG_ID ? AF_MAIL_FORTUNE_CATALOG_BYTES :
        catalog == AF_MAIL_GLYPH_CATALOG_ID ? AF_MAIL_GLYPH_CATALOG_BYTES : 0u;
}
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
