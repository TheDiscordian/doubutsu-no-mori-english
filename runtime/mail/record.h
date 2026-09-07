#ifndef AF_MAIL_RECORD_H
#define AF_MAIL_RECORD_H

/* Standalone generated-mail prototype. Not linked into the resident module. */
#define AF_MAIL_RECORD_BYTES 122u
#define AF_MAIL_FIELD_COUNT 20u
#define AF_MAIL_FIELD_BYTES 16u

typedef struct {
    unsigned char length;
    unsigned char article;
    unsigned char text[AF_MAIL_FIELD_BYTES];
} AfMailField;

typedef struct {
    unsigned short catalog;
    unsigned char kind;
    unsigned char flags; /* Bit zero: initial sticky capitalization; others zero. */
    unsigned int field_mask;
    unsigned short templates[5];
    AfMailField fields[AF_MAIL_FIELD_COUNT];
} AfMailRecord;

/* Return one on success, zero without destination writes on invalid input.
 * Catalog identity names immutable text/resources, not a current build number.
 * These routines never auto-detect native text or change native mail metadata.
 */
int af_mail_record_pack(unsigned char *output, unsigned int capacity, const AfMailRecord *record);
int af_mail_record_unpack(AfMailRecord *record, const unsigned char *input,
                          unsigned int size, unsigned int expected_catalog);

#endif
