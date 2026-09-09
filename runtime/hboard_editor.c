#include "hboard_editor.h"

#define NEWLINE 0xCDu
#define SPACE 32u

/* Struct assignments may generate libc calls even with -ffreestanding. Keep
 * these tiny overlay-owned copies explicit and independent of native imports. */
static void copy_bytes(void *out, const void *in, unsigned int length) {
    unsigned char *dst = out;
    const volatile unsigned char *src = in;
    unsigned int i;
    for (i = 0; i < length; ++i) dst[i] = src[i];
}

static void zero_bytes(void *out, unsigned int length) {
    volatile unsigned char *dst = out;
    unsigned int i;
    for (i = 0; i < length; ++i) dst[i] = 0;
}

static int equal(const unsigned char *a, const unsigned char *b, int length) {
    int i;
    for (i = 0; i < length; ++i)
        if (a[i] != b[i]) return 0;
    return 1;
}

static int valid(const struct af_hboard_draft *draft) {
    int i;
    if (!draft || draft->length > AF_HBOARD_DRAFT || draft->cursor > draft->length)
        return 0;
    for (i = draft->length; i < AF_HBOARD_DRAFT; ++i)
        if (draft->text[i] != SPACE) return 0;
    return 1;
}

int af_hboard_layout(const unsigned char *text, int length, int cursor,
                     const unsigned char *widths, struct af_hboard_layout *out) {
    struct af_hboard_layout result;
    struct af_hboard_point point = {0, 0, 0};
    int i, width;
    if (!text || !widths || !out || length < 0 || length > AF_HBOARD_DRAFT ||
        cursor < 0 || cursor > length)
        return AF_HBOARD_ARGUMENT;
    zero_bytes(&result, sizeof(result));
    for (i = 0; i < length; ++i) {
        unsigned char code = text[i];
        if (code != NEWLINE) {
            width = widths[code];
            if (width < 1 || width > 12) return AF_HBOARD_BAD_WIDTH;
            if (point.x + width > AF_HBOARD_WIDTH) {
                if (point.row + 1 >= AF_HBOARD_ROWS) return AF_HBOARD_TOO_MANY_ROWS;
                ++point.row;
                point.column = point.x = 0;
                result.lines[point.row].start = (unsigned short)i;
            }
        } else {
            width = 0;
        }
        /* Look ahead before recording a cursor: a wrapped glyph belongs to
         * the next row, as in GAFE01 mED_check_line_over. */
        if (i == cursor) result.cursor = point;
        ++result.lines[point.row].length;
        if (code == NEWLINE) {
            if (point.row + 1 >= AF_HBOARD_ROWS) return AF_HBOARD_TOO_MANY_ROWS;
            ++point.row;
            point.column = point.x = 0;
            result.lines[point.row].start = (unsigned short)(i + 1);
        } else {
            ++point.column;
            point.x = (unsigned short)(point.x + width);
            result.lines[point.row].width = point.x;
        }
    }
    width = widths[SPACE];
    if (width < 1 || width > 12) return AF_HBOARD_BAD_WIDTH;
    /* The native editor's unused tail is space padded. Do not read text[len]
     * when the draft is full; use the same next-space check without an overread. */
    if (point.row + 1 < AF_HBOARD_ROWS && point.x + width > AF_HBOARD_WIDTH) {
        ++point.row;
        point.column = point.x = 0;
        result.lines[point.row].start = (unsigned short)length;
    }
    if (cursor == length) result.cursor = point;
    result.end = point;
    result.rows = (unsigned short)(point.row + 1);
    copy_bytes(out, &result, sizeof(result));
    return AF_HBOARD_OK;
}

int af_hboard_begin(struct af_hboard_draft *draft, const unsigned char *saved,
                    const unsigned char *native_default, const unsigned char *english_default) {
    struct af_hboard_draft result;
    const unsigned char *source;
    int i, length;
    if (!draft || !saved || !native_default || !english_default) return AF_HBOARD_ARGUMENT;
    for (i = 0; i < AF_HBOARD_SAVED; ++i) result.original[i] = saved[i];
    if (equal(saved, native_default, AF_HBOARD_SAVED)) {
        source = english_default;
        length = AF_HBOARD_DEFAULT;
    } else {
        source = saved;
        length = AF_HBOARD_SAVED;
    }
    for (i = 0; i < AF_HBOARD_DRAFT; ++i) result.text[i] = i < length ? source[i] : SPACE;
    while (length && result.text[length - 1] == SPACE) --length;
    result.length = (unsigned short)length;
    result.cursor = 0;
    copy_bytes(draft, &result, sizeof(result));
    return AF_HBOARD_OK;
}

static int insert(struct af_hboard_draft *draft, int code, const unsigned char *widths) {
    struct af_hboard_layout layout;
    struct af_hboard_draft staged;
    int i, status;
    if (code < 0 || code > 255 || code == 0x7F || code == 0x80) return AF_HBOARD_ARGUMENT;
    if (draft->length == AF_HBOARD_DRAFT) return AF_HBOARD_DRAFT_FULL;
    copy_bytes(&staged, draft, sizeof(staged));
    for (i = staged.length; i > staged.cursor; --i) staged.text[i] = staged.text[i - 1];
    staged.text[staged.cursor++] = (unsigned char)code;
    ++staged.length;
    status = af_hboard_layout(staged.text, staged.length, staged.cursor, widths, &layout);
    if (status != AF_HBOARD_OK) return status;
    copy_bytes(draft, &staged, sizeof(staged));
    return AF_HBOARD_OK;
}

int af_hboard_command(struct af_hboard_draft *draft, int command, int code,
                      const unsigned char *widths) {
    struct af_hboard_layout layout;
    int i, target, distance, best = -1, best_distance = AF_HBOARD_WIDTH + 1, status;
    if (!valid(draft) || !widths) return AF_HBOARD_ARGUMENT;
    switch (command) {
    case AF_HBOARD_LEFT:
        if (!draft->cursor) return AF_HBOARD_UNCHANGED;
        --draft->cursor;
        return AF_HBOARD_OK;
    case AF_HBOARD_RIGHT:
        if (draft->cursor == draft->length) return insert(draft, SPACE, widths);
        ++draft->cursor;
        return AF_HBOARD_OK;
    case AF_HBOARD_BACKSPACE:
        if (!draft->cursor) return AF_HBOARD_UNCHANGED;
        --draft->cursor;
        --draft->length;
        for (i = draft->cursor; i < draft->length; ++i) draft->text[i] = draft->text[i + 1];
        draft->text[draft->length] = SPACE;
        return AF_HBOARD_OK;
    case AF_HBOARD_EXCHANGE: {
        unsigned char previous;
        if (!draft->cursor || code == -1) return AF_HBOARD_UNCHANGED;
        if (code < 0 || code > 255 || code == 0x7F || code == 0x80) return AF_HBOARD_ARGUMENT;
        previous = draft->text[draft->cursor - 1];
        draft->text[draft->cursor - 1] = (unsigned char)code;
        status = af_hboard_layout(draft->text, draft->length, draft->cursor, widths, &layout);
        if (status != AF_HBOARD_OK) draft->text[draft->cursor - 1] = previous;
        return status;
    }
    case AF_HBOARD_INSERT:
        return insert(draft, code, widths);
    case AF_HBOARD_UP:
    case AF_HBOARD_DOWN:
        status = af_hboard_layout(draft->text, draft->length, draft->cursor, widths, &layout);
        if (status != AF_HBOARD_OK) return status;
        target = layout.cursor.row + (command == AF_HBOARD_UP ? -1 : 1);
        if (target < 0) return AF_HBOARD_UNCHANGED;
        if (target > layout.end.row) {
            if (command == AF_HBOARD_DOWN && draft->cursor == draft->length)
                return insert(draft, NEWLINE, widths);
            return AF_HBOARD_UNCHANGED;
        }
        /* Choose the nearest insertion boundary in pixels, not glyph count.
         * Equal distances prefer the following boundary, matching GC intent. */
        distance = layout.cursor.x;
        status = 0; /* Pixel position within the chosen row. */
        for (i = layout.lines[target].start;
             i < layout.lines[target].start + layout.lines[target].length ||
             (i == draft->length && target == layout.end.row); ++i) {
            int delta = status - distance;
            if (delta < 0) delta = -delta;
            if (delta <= best_distance) { best = i; best_distance = delta; }
            if (i == draft->length) break;
            if (draft->text[i] != NEWLINE) status += widths[draft->text[i]];
        }
        if (best < 0) return AF_HBOARD_UNCHANGED;
        draft->cursor = (unsigned short)best;
        return AF_HBOARD_OK;
    default:
        return AF_HBOARD_ARGUMENT;
    }
}

int af_hboard_pack(const struct af_hboard_draft *draft, const unsigned char *native_default,
                   const unsigned char *english_default, unsigned char *out) {
    unsigned char staged[AF_HBOARD_SAVED];
    int i, length, is_default = 1;
    if (!valid(draft) || !native_default || !english_default || !out) return AF_HBOARD_ARGUMENT;
    for (i = 0; i < AF_HBOARD_DRAFT; ++i)
        if (draft->text[i] != (i < AF_HBOARD_DEFAULT ? english_default[i] : SPACE)) is_default = 0;
    length = draft->length;
    while (length && draft->text[length - 1] == SPACE) --length;
    if (!is_default && length > AF_HBOARD_SAVED) return AF_HBOARD_SAVE_FULL;
    for (i = 0; i < AF_HBOARD_SAVED; ++i)
        staged[i] = is_default ? native_default[i] : (i < length ? draft->text[i] : SPACE);
    for (i = 0; i < AF_HBOARD_SAVED; ++i) out[i] = staged[i];
    return AF_HBOARD_OK;
}

int af_hboard_commit(const struct af_hboard_draft *draft, const unsigned char *native_default,
                     const unsigned char *english_default, unsigned char *saved) {
    if (!valid(draft) || !saved) return AF_HBOARD_ARGUMENT;
    if (!equal(saved, draft->original, AF_HBOARD_SAVED)) return AF_HBOARD_SAVE_CHANGED;
    return af_hboard_pack(draft, native_default, english_default, saved);
}
