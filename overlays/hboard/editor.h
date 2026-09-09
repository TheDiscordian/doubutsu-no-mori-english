#ifndef AF_HBOARD_OVERLAY_H
#define AF_HBOARD_OVERLAY_H
#include "../../runtime/hboard_editor.h"

typedef void (*af_hboard_draw_fn)(void *, void *, void *, float, float);
typedef void (*af_hboard_mark_fn)(void *, void *, float, float);

struct af_hboard_native_editor {
    unsigned char prefix[0x11];
    unsigned char command, unused12, code, animation, processed;
    short index, columns, rows, length, exchange, column, row;
    unsigned char *input;
    af_hboard_mark_fn end_draw, cursor_draw;
    af_hboard_draw_fn hboard_draw;
};

struct af_hboard_context {
    struct af_hboard_draft draft;
    unsigned char widths[256];
    void *submenu;
    struct af_hboard_native_editor *editor;
    unsigned char *saved;
    int warning, active;
};

extern struct af_hboard_context af_hboard_context;
extern const unsigned char af_hboard_native_default[64], af_hboard_english_default[92];

void af_hboard_editor_init(void *, void *);
void af_hboard_editor_command(void *, void *);
void af_hboard_editor_cursor(struct af_hboard_native_editor *, short *, short *, int);
void af_hboard_editor_destruct(void *);
void af_hboard_editor_draw(void *, void *, void *, float, float);

/* The real definitions are bound by linker symbols or absolute native calls.
 * Host fixtures implement these contracts without executing game code. */
extern void af_hboard_original_init(void *, void *);
extern void af_hboard_original_cursor(struct af_hboard_native_editor *, short *, short *, int);
extern void af_hboard_original_done(void *, void *);
extern void af_hboard_original_destruct(void *);
extern int af_hboard_code_width(unsigned int, int);
extern void af_hboard_font_line(void *, const unsigned char *, int, float, float,
                                int, int, int, int, int, int, float, float, int);

#ifdef __mips__
typedef char af_hboard_pointer_size[(sizeof(void *) == 4) ? 1 : -1];
typedef char af_hboard_editor_size[(sizeof(struct af_hboard_native_editor) == 0x34) ? 1 : -1];
typedef char af_hboard_context_size[(sizeof(struct af_hboard_context) == 472) ? 1 : -1];
/* A packed pointer accessor preserves the real submenu +2C offset on both the
 * N64 ABI and host test builds, without host misaligned pointer accesses. */
#endif
struct af_hboard_submenu_pointer { unsigned char pad[0x2C]; void *overlay; } __attribute__((packed));
struct af_hboard_matrix_pointer { void (*function)(void *); } __attribute__((packed));

#ifndef __mips__
extern unsigned char *af_hboard_test_saved(int);
#endif
#endif
