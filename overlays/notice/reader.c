#include "reader.h"
#include "../../runtime/mail/view.h"
#include "../../runtime/dateformat.h"

AfNoticeCache af_notice_cache[2] __attribute__((aligned(16)));
static unsigned int replacement;

/* These three calls target retained code inside the same relocated overlay. */
extern void af_notice_original_construct(void *);
extern void af_notice_original_read(void *, void *, unsigned char *);
extern void af_notice_original_body(void *, void *, const unsigned char *, int,
                                      float, float, float *, float *);

#ifdef __mips__
static void *allocate(unsigned int size) { return ((void *(*)(unsigned int))0x8009BFC0u)(size); }
static void release(void *memory) { ((void (*)(void *))0x8009C040u)(memory); }
static unsigned int trigger(void) { return ((unsigned int (*)(void))0x80078DF4u)(); }
static unsigned char *post(unsigned int index) { return (unsigned char *)(0x80129E0Au+index*104u); }
static int string_width(const unsigned char *text, unsigned int length) {
    return ((int (*)(const unsigned char *, unsigned int, int))0x800902CCu)(text, length, 0);
}
static void label(void *game, const unsigned char *text, unsigned int length, float x, float y) {
    ((float (*)(void *, const unsigned char *, int, float, float,
                int, int, int, int, int, int, float, float, int))0x80090E98u)
        (game, text, length, x, y, 0, 0, 255, 255, 0, 0, 0.75f, 0.75f, 0);
}
#else
extern void *af_notice_test_allocate(unsigned int);
extern void af_notice_test_release(void *);
extern unsigned int af_notice_test_trigger(void);
extern unsigned char *af_notice_test_post(unsigned int);
extern int af_notice_test_width(const unsigned char *, unsigned int);
extern void af_notice_test_label(void *, const unsigned char *, unsigned int, float, float);
#define allocate af_notice_test_allocate
#define release af_notice_test_release
#define trigger af_notice_test_trigger
#define post af_notice_test_post
#define string_width af_notice_test_width
#define label af_notice_test_label
#endif

static int equal(const unsigned char *a, const unsigned char *b) {
    unsigned int i;
    for (i = 0; i < AF_NOTICE_RECORD_BYTES; ++i)
        if (a[i] != b[i]) return 0;
    return 1;
}

static void error(AfNoticeCache *cache) {
    static const unsigned char message[] = "Unable to read this post.\xCD" "Close and reopen to retry.";
    unsigned int i;
    cache->status = 3u;
    cache->page = 0;
    cache->body.length = sizeof(message)-1u;
    for (i = 0; i < sizeof(message)-1u; ++i) cache->body.text[i] = message[i];
    af_notice_page(&cache->layout, cache->body.text, cache->body.length, 0);
}

static AfNoticeCache *cached(const unsigned char *source) {
    AfNoticeCache *cache;
    AfNoticeWorkspace *work;
    void *allocation;
    unsigned int i, result, length;
    for (i = 0; i < 2u; ++i)
        if (af_notice_cache[i].status && af_notice_cache[i].source == source
                && equal(af_notice_cache[i].saved, source))
            return &af_notice_cache[i];
    cache = &af_notice_cache[replacement++ & 1u];
    cache->source = source;
    cache->page = 0;
    cache->status = 1;
    for (i = 0; i < AF_NOTICE_RECORD_BYTES; ++i) cache->saved[i] = source[i];
    if (source[0] == 0x7Fu) {
        /* Reserved command-prefix records never enter the ordinary text path,
         * including damaged or future family/profile tags. */
        result = 0;
        allocation = allocate(sizeof(AfNoticeWorkspace)+15u);
        if (allocation) {
            work = (AfNoticeWorkspace *)(((__UINTPTR_TYPE__)allocation+15u) & ~(__UINTPTR_TYPE__)15u);
            result = af_notice_initial_restore(&cache->body, source, AF_NOTICE_RECORD_BYTES, work);
            release(allocation);
        }
        if (!result) { error(cache); return cache; }
        cache->status = 2;
    } else {
        length = AF_NOTICE_RECORD_BYTES;
        while (length && source[length-1u] == ' ') --length;
        cache->body.length = length;
        for (i = 0; i < length; ++i) cache->body.text[i] = source[i];
    }
    if (!af_notice_page(&cache->layout, cache->body.text, cache->body.length, 0)) error(cache);
    return cache;
}

void af_notice_construct(void *submenu) {
    unsigned int i;
    if (!submenu) return;
    for (i = 0; i < sizeof(af_notice_cache); ++i) ((unsigned char *)af_notice_cache)[i] = 0;
    replacement = 0;
    af_notice_original_construct(submenu);
}

void af_notice_read_control(void *submenu, void *menu, unsigned char *state) {
    unsigned int before, buttons, requested;
    AfNoticeCache *cache;
    if (!submenu || !menu || !state) return;
    before = state[4];
    buttons = trigger();
    af_notice_original_read(submenu, menu, state);
    /* Native post navigation, writing, and closing always take precedence. */
    if (before >= 15u || state[4] != before || state[0]
            || *(unsigned int *)((unsigned char *)menu+4) != 1u
            || (buttons & 0xD00Fu) || (buttons & 0x30u) == 0x30u)
        return;
    if (!(buttons & 0x30u)) return;
    cache = cached(post(before));
    requested = cache->page;
    if ((buttons & 0x20u) && requested) --requested;
    else if ((buttons & 0x10u) && requested+1u < cache->layout.total) ++requested;
    if (requested != cache->page
            && af_notice_page(&cache->layout, cache->body.text, cache->body.length, requested))
        cache->page = requested;
}

void af_notice_draw_body(void *menu, void *game, const unsigned char *source,
                           int length, float x, float y, float *end_x, float *end_y) {
    static const unsigned char colour[4] = {30, 0, 0, 255};
    AfNoticeCache *cache = 0;
    AfNoticePage planned;
    const AfNoticePage *layout;
    const unsigned char *text = source;
    unsigned int i;
    if (!menu || !game || !source || !end_x || !end_y) return;
    if (*(unsigned int *)((unsigned char *)menu+4) == 2u) {
        af_notice_original_body(menu, game, source, length, x, y, end_x, end_y);
        return;
    }
    for (i = 0; i < 15u; ++i)
        if (source == post(i)) { cache = cached(source); break; }
    if (cache) {
        text = cache->body.text;
        layout = &cache->layout;
    } else {
        /* A draft shown during confirmation is not a persisted snapshot. */
        if (length < 0 || length > 96 || !af_notice_page(&planned, source, (unsigned int)length, 0)) return;
        layout = &planned;
    }
    *end_x = x-160.0f;
    *end_y = 120.0f-y;
    for (i = 0; i < layout->count; ++i) {
        const AfNoticeLine *line = &layout->lines[i];
        if (line->length) af_mail_draw(game, text+line->offset, line->length, x, y+(float)i*16.0f, colour);
        *end_x = x+(float)line->width-160.0f;
        *end_y = 120.0f-y-(float)i*16.0f;
    }
    if (cache && layout->total > 1u) {
        static const unsigned char prefix[] = "L/R: page ";
        unsigned char hint[18];
        unsigned int n = 10u, value = cache->page+1u;
        for (i = 0; i < 10u; ++i) hint[i] = prefix[i];
        if (value >= 100u) hint[n++] = (unsigned char)('0'+value/100u);
        if (value >= 10u) hint[n++] = (unsigned char)('0'+value/10u%10u);
        hint[n++] = (unsigned char)('0'+value%10u);
        hint[n++] = '/';
        value = layout->total;
        if (value >= 100u) hint[n++] = (unsigned char)('0'+value/100u);
        if (value >= 10u) hint[n++] = (unsigned char)('0'+value/10u%10u);
        hint[n++] = (unsigned char)('0'+value%10u);
        label(game, hint, n, x, y+100.0f);
    }
}

void af_notice_draw_entry(void *game, unsigned int entry, float x, float y) {
    unsigned char text[8] = "entry ";
    unsigned int length = 6u;
    if (entry > 15u) { text[length++] = '?'; }
    else {
        if (entry >= 10u) text[length++] = '1';
        text[length++] = (unsigned char)('0'+entry%10u);
    }
    label(game, text, length, x, y);
}

void af_notice_draw_date(void *game, const unsigned char *rtc, float x, float y) {
    unsigned char text[32];
    unsigned int i, length, day, year;
    if (!rtc) return;
    if (rtc[5] >= 1u && rtc[5] <= 12u) length = (unsigned int)af_format_month(text, rtc[5]);
    else { text[0] = text[1] = text[2] = '?'; length = 3u; }
    text[length++] = ' ';
    day = rtc[3];
    if (day < 1u || day > 31u) { text[length++] = '?'; text[length++] = '?'; }
    else {
        if (day >= 10u) text[length++] = (unsigned char)('0'+day/10u);
        text[length++] = (unsigned char)('0'+day%10u);
    }
    text[length++] = ',';
    text[length++] = ' ';
    year = ((unsigned int)rtc[6] << 8) | rtc[7];
    for (i = 1000u; i; i /= 10u)
        text[length++] = year <= 9999u ? (unsigned char)('0'+year/i%10u) : '?';
    label(game, text, length, x+194.0f-(float)string_width(text, length)*0.75f, y);
}
