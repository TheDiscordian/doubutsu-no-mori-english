#ifndef AF_MAIL_VIEW_H
#define AF_MAIL_VIEW_H

typedef struct {
    unsigned int consumed, drawn, width, newline;
} AfMailLine;

/* One reference-style 192-pixel line. Explicit newlines consume one byte;
 * they are never submitted as glyphs in read mode. No spaces are removed and
 * no words or saved bytes are rearranged. The caller retains any remainder.
 */
int af_mail_next_line(AfMailLine *line, const unsigned char *text, unsigned int length);

/* Native board read-mode consumers. Editor paths retain their original code.
 * These consumers still read the native 96/16-byte fields, not snapshots.
 */
void af_mail_read_body(void *submenu, void *menu, void *game, float x,
                       float *y, float *end_x, float *end_y, const unsigned char *colour);
void af_mail_read_footer(void *submenu, void *game, float x, float y,
                         const unsigned char *colour);

#endif
