#include "page.h"
#include "view.h"

static int scan(AfMailLine *line, const unsigned char *text, unsigned int length) {
    return af_mail_next_line(line, text, length > 1024u ? 1024u : length) && line->consumed;
}

static void span(AfMailPage *page, unsigned int section, unsigned int offset,
                  const AfMailLine *line, unsigned int y) {
    AfMailSpan *s = &page->spans[page->count++];
    s->section = section;
    s->offset = offset;
    s->length = line->drawn;
    s->y = y;
}

int af_mail_page(AfMailPage *out, const unsigned char *const sections[3],
                 const unsigned int lengths[3], unsigned int requested) {
    AfMailPage value, chosen;
    AfMailLine line, first = {0}, footer[7];
    unsigned int pos[3] = {0, 0, 0}, page = 0, row, fresh, i, n, used;
    int repeat = 0;
    if (!out || !sections || !lengths || requested > 1029u)
        return 0;
    for (i = 0; i < sizeof(value); ++i) {
        ((unsigned char *)&value)[i] = 0;
        ((unsigned char *)&chosen)[i] = 0;
    }
    for (i = 0; i < 3u; ++i)
        if ((!sections[i] && lengths[i]) || lengths[i] > (i ? 1024u : 1030u))
            return 0;
    if (lengths[0]) {
        if (!scan(&first, sections[0], lengths[0]))
            return 0;
        repeat = first.consumed == lengths[0];
    }
    do {
        value.count = 0;
        row = fresh = 0;
        while (pos[0] < lengths[0] && row < 7u) {
            if (!scan(&line, sections[0]+pos[0], lengths[0]-pos[0]))
                return 0;
            span(&value, 0, pos[0], &line, row ? 28u+(row-1u)*16u : 0u);
            pos[0] += line.consumed;
            ++row;
            fresh = 1;
        }
        if (!row) {
            if (repeat)
                span(&value, 0, 0, &first, 0);
            row = 1;
        }
        if (pos[0] == lengths[0]) {
            while (pos[1] < lengths[1] && row < 7u) {
                if (!scan(&line, sections[1]+pos[1], lengths[1]-pos[1]))
                    return 0;
                span(&value, 1, pos[1], &line, 28u+(row-1u)*16u);
                pos[1] += line.consumed;
                ++row;
                fresh = 1;
            }
        }
        if (pos[0] == lengths[0] && pos[1] == lengths[1]) {
            used = pos[2];
            n = 0;
            while (used < lengths[2] && n < 7u) {
                if (!scan(&footer[n], sections[2]+used, lengths[2]-used))
                    return 0;
                used += footer[n++].consumed;
            }
            /* Keep a footer together when it fits on its own page. Longer
             * footers continue across footer-only pages without losing bytes.
             */
            if (!fresh || (used == lengths[2] && n <= 8u-row)) {
                for (i = 0; i < n; ++i) {
                    span(&value, 2, pos[2], &footer[i], 136u-(n-1u-i)*16u);
                    pos[2] += footer[i].consumed;
                }
            }
        }
        if (page == requested)
            for (i = 0; i < sizeof(value); ++i)
                ((unsigned char *)&chosen)[i] = ((const unsigned char *)&value)[i];
        ++page;
    } while (pos[0] < lengths[0] || pos[1] < lengths[1] || pos[2] < lengths[2]);
    if (requested >= page)
        return 0;
    chosen.total = page;
    for (i = 0; i < sizeof(chosen); ++i)
        ((unsigned char *)out)[i] = ((const unsigned char *)&chosen)[i];
    return 1;
}
