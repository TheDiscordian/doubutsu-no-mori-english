#ifndef AF_ACCENT_MAIL_H
#define AF_ACCENT_MAIL_H

#include "../../runtime/mail/catalog.h"
#include "../../runtime/mail/view.h"
#include "../mail_generation/generate.h"

#define AF_ACCENT_CATALOG_ID 5u
#define AF_ACCENT_CATALOG_VROM 0x03100000u
#define AF_ACCENT_CATALOG_BYTES AF_MAIL_GLYPH_CATALOG_BYTES

static inline unsigned int af_accent_catalog_vrom(unsigned int id) {
    return id==AF_ACCENT_CATALOG_ID ? AF_ACCENT_CATALOG_VROM : af_mail_catalog_vrom(id);
}
static inline unsigned int af_accent_catalog_bytes(unsigned int id) {
    return id==AF_ACCENT_CATALOG_ID ? AF_ACCENT_CATALOG_BYTES : af_mail_catalog_bytes(id);
}
static inline unsigned int af_accent_glyph_width(unsigned int code,unsigned int catalog) {
    return catalog==AF_ACCENT_CATALOG_ID && (code==0x87u || code==0x12u) ? 6u : af_mail_glyph_width(code);
}
static inline unsigned int af_accent_glyph_upper(unsigned int code) {
    return code==0x87u ? 0x12u : af_mail_glyph_upper(code);
}

int af_accent_item_literal(const unsigned char *,unsigned int);
int af_accent_mail_format(AfMailText *,const AfMailRecord *,const AfMailTemplates *);
int af_accent_catalog_header_valid(const unsigned int *,unsigned int);
int af_accent_mail_restore(AfMailText *,const unsigned char *,unsigned int,AfMailWorkspace *);
void af_accent_capture_reset(AfMailCapture *);
int af_accent_capture_set(AfMailCapture *,unsigned int,const unsigned char *,unsigned int,unsigned int);
int af_accent_mail_generate(unsigned char *,unsigned int,AfMailCapture *,const AfMailSelection *,AfMailGenerateWork *);
int af_accent_next_line(AfMailLine *,const unsigned char *,unsigned int);

#endif
