/* Complete choice substitutions, staged before touching the twenty-byte row. */
#include "extension.h"

extern int af_text_fields_init(void);
extern int af_copy_item_string(void *, int, unsigned char *, int, int);
extern int af_copy_talk_name(const unsigned char *, unsigned char *, int, int);
extern int af_copy_catchphrase(const unsigned char *, unsigned char *, int, int);
extern void af_writeback(void *, unsigned int);
extern void af_invalidate(void *, unsigned int);

#ifdef __mips__
#define main_window() ((void *)0x80142410u)
#define word(at) (*(volatile af_u32 *)(at))
static int legacy(unsigned int command, unsigned char *data, const unsigned char *actor) {
    typedef int (*handler)(unsigned char *, int, int, const unsigned char *);
    handler fn = ((handler *)0x80102A80u)[command];
    return fn ? fn(data, 0, 2, actor) : -1;
}
static int selected(unsigned char *data) {
    unsigned int size = word(0x80142638u), i;
    const unsigned char *source = (const unsigned char *)0x8019A8C0u;
    if (size > 20) return -1;
    for (i=0; i<size; ++i) data[i] = source[i];
    return (int)size;
}
#else
extern void *af_choice_test_window(void);
extern af_u32 *af_choice_test_word(af_u32);
extern int af_choice_test_legacy(unsigned int, unsigned char *, const unsigned char *);
extern int af_choice_test_selected(unsigned char *);
#define main_window af_choice_test_window
#define word(at) (*af_choice_test_word(at))
#define legacy af_choice_test_legacy
#define selected af_choice_test_selected
#endif

/* Every approved command is two bytes. Legacy outputs are at most ten bytes;
 * selected answers use the explicitly bounded twenty-byte reader above. */
static int replacement(unsigned int code, unsigned char *text, const unsigned char *actor) {
    if (code == 0x1b) return af_copy_talk_name(actor, text, 0, 2);
    if (code == 0x1c) return af_copy_catchphrase(actor, text, 0, 2);
    if (code >= 0x24 && code <= 0x2d) return af_free_copy(main_window(), (int)code-0x24, text, 0, 2);
    if (code >= 0x36 && code <= 0x3f) return af_free_copy(main_window(), (int)code-0x36+10, text, 0, 2);
    if (code >= 0x31 && code <= 0x35) return af_copy_item_string(main_window(), (int)code-0x31, text, 0, 2);
    if (code == 0x2e) return selected(text);
    if (code == 0x1a || (code >= 0x1d && code <= 0x23) || code == 0x2f || code == 0x30)
        return legacy(code, text, actor);
    return -1;
}

int af_choice_expand(unsigned char *data, int capacity, const unsigned char *actor) {
    unsigned char output[20], text[32];
    int end, at, used=0, count, i, commands=0;
    if (!data || capacity < 0 || capacity > 20) return 0;
    /* The day command's argument is 0x20, also the padding byte. Identify
     * padding by complete tokens, never by trimming raw bytes backwards. */
    end = 0;
    for (at=0; at<capacity; ++at) {
        if (data[at] == 0x7f) {
            if (++at >= capacity) return 0;
            end = at+1;
        } else if (data[at] != ' ') end = at+1;
    }
    for (at=0; at<end; ++at) {
        if (data[at] != 0x7f) {
            if (used >= capacity) return 0;
            output[used++] = data[at];
            continue;
        }
        if (++at >= end) return 0;
        for (i=0; i<(int)sizeof(text); ++i) text[i] = ' ';
        text[0]=0x7f; text[1]=data[at];
        count = replacement(data[at], text, actor);
        if (count < 0 || count > 20 || used+count > capacity) return 0;
        /* Field values are plain text. Never recurse indefinitely into a field
         * containing the same command, or expose an unexpanded control byte. */
        for (i=0; i<count; ++i) {
            if (text[i] == 0x7f) return 0;
            output[used++] = text[i];
        }
        commands = 1;
    }
    if (!commands) return capacity; /* Plain GC choices retain all original bytes. */
    for (i=used; i<capacity; ++i) output[i] = ' ';
    for (i=0; i<capacity; ++i) data[i] = output[i];
    return used;
}

__attribute__((section(".text.entry")))
int af_text_extension_init(void) {
    /* Complete capacity/layout and source checks precede every installed hook. */
    if (word(0x80065cf8u) != 0x27bdffd0u || word(0x80065cfcu) != 0xafb50028u
            || word(0x80194908u) != 20 || word(0x8019490cu) != 32
            || word(0x80194910u) != 0x8019a840u || word(0x80194914u) != 0x8019a8c0u)
        return 0;
    if (!af_text_fields_init()) return 0;
    word(0x80065cf8u) = 0x08000000u | (((af_u32)(__UINTPTR_TYPE__)af_choice_expand >> 2) & 0x03ffffffu);
    word(0x80065cfcu) = 0;
    af_writeback((void *)0x80065cf8u, 8);
    af_invalidate((void *)0x80065cf8u, 8);
    return 1;
}
