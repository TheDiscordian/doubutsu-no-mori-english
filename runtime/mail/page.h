#ifndef AF_MAIL_PAGE_H
#define AF_MAIL_PAGE_H

typedef struct {
    unsigned int section, offset, length, y;
} AfMailSpan;

typedef struct {
    unsigned int total, count;
    AfMailSpan spans[8];
} AfMailPage;

/* Complete sequential reading, with native paper geometry. All offsets and y
 * positions are relative to the supplied section and header origin. Explicit
 * newlines consume a row, including blank rows; no whitespace is discarded.
 * A one-line header repeats on continuation pages. Long headers continue before
 * the body. Footers retain right alignment and finish at the native baseline.
 * Failure leaves output unchanged. Input sections must remain stable.
 */
int af_mail_page(AfMailPage *out, const unsigned char *const sections[3],
                 const unsigned int lengths[3], unsigned int requested);

#endif
