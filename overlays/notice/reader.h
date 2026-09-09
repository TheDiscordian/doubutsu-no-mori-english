#ifndef AF_NOTICE_READER_H
#define AF_NOTICE_READER_H

#include "../../runtime/notice/initial.h"
#include "../../runtime/notice/page.h"

typedef struct {
    const unsigned char *source;
    unsigned int status, page;
    unsigned char saved[AF_NOTICE_RECORD_BYTES];
    AfNoticeText body;
    AfNoticePage layout;
} AfNoticeCache;

extern AfNoticeCache af_notice_cache[2];

void af_notice_construct(void *submenu);
void af_notice_read_control(void *submenu, void *menu, unsigned char *state);
void af_notice_draw_body(void *menu, void *game, const unsigned char *source,
                           int length, float x, float y, float *end_x, float *end_y);
void af_notice_draw_entry(void *game, unsigned int entry, float x, float y);
void af_notice_draw_date(void *game, const unsigned char *rtc, float x, float y);

#endif
