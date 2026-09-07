#ifndef AF_MAIL_READER_H
#define AF_MAIL_READER_H

#include "catalog.h"
#include "page.h"

/* Experimental marker used only by the separately enabled snapshot reader.
 * Generation and release/save compatibility are not enabled by this constant.
 */
#define AF_MAIL_SNAPSHOT_SPLIT 0x80u

typedef struct {
    void *owner;
    unsigned int status, page, total;
    unsigned int lengths[3];
    AfMailPage layout;
    unsigned char header[1032];
    AfMailText letter;
    AfMailWorkspace workspace;
} AfMailReader;

extern AfMailReader af_mail_reader;

void af_mail_reader_copy(unsigned char *destination, const unsigned char *source, void *menu);
unsigned int af_mail_reader_trigger(void *submenu, void *menu);
void af_mail_snapshot_header(void *submenu, void *game, void *menu, float x,
                             float y, const unsigned char *colour);
void af_mail_snapshot_body(void *submenu, void *menu, void *game, float x,
                           float *y, float *end_x, float *end_y, const unsigned char *colour);
void af_mail_snapshot_footer(void *submenu, void *game, float x, float y,
                             const unsigned char *colour);

#endif
