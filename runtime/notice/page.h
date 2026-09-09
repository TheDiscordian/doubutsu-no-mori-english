#ifndef AF_NOTICE_PAGE_H
#define AF_NOTICE_PAGE_H

#define AF_NOTICE_PAGE_LINES 6u

typedef struct {
    unsigned int offset, length, width;
} AfNoticeLine;

typedef struct {
    unsigned int total, count;
    AfNoticeLine lines[AF_NOTICE_PAGE_LINES];
} AfNoticePage;

/* Complete 192-pixel, six-line pages. Explicit blank lines and all spaces
 * remain; a trailing newline closes its line without inventing another page.
 * Registered glyph pairs stay together. The entire body is checked before
 * publication, including portions beyond the requested page. No draw or input
 * hook is installed here. Failure leaves the caller's result unchanged.
 */
int af_notice_page(AfNoticePage *output, const unsigned char *text,
                     unsigned int length, unsigned int requested);

#endif
