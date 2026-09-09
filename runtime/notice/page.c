#include "page.h"
#include "../mail/view.h"

int af_notice_page(AfNoticePage *output, const unsigned char *text,
                     unsigned int length, unsigned int requested) {
    AfNoticePage result;
    AfMailLine line;
    unsigned int i, offset = 0, rows = 0;
    if (!output || (!text && length) || length > 1024u)
        return 0;
    for (i = 0; i < sizeof(result); ++i)
        ((unsigned char *)&result)[i] = 0;
    while (offset < length) {
        if (!af_mail_next_line(&line, text+offset, length-offset) || !line.consumed)
            return 0;
        if (rows/AF_NOTICE_PAGE_LINES == requested) {
            AfNoticeLine *span = &result.lines[result.count++];
            span->offset = offset;
            span->length = line.drawn;
            span->width = line.width;
        }
        offset += line.consumed;
        ++rows;
    }
    result.total = rows ? (rows+AF_NOTICE_PAGE_LINES-1u)/AF_NOTICE_PAGE_LINES : 1u;
    if (requested >= result.total)
        return 0;
    for (i = 0; i < sizeof(result); ++i)
        ((unsigned char *)output)[i] = ((unsigned char *)&result)[i];
    return 1;
}
