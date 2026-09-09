#include "editor.h"

struct af_hboard_context af_hboard_context;

static void *overlay(void *submenu) {
    return submenu ? ((struct af_hboard_submenu_pointer *)submenu)->overlay : (void *)0;
}

static struct af_hboard_native_editor *editor(void *submenu) {
    unsigned char *ovl = overlay(submenu);
    return ovl ? *(struct af_hboard_native_editor **)(ovl + 0x106E0) : (void *)0;
}

static unsigned char *home_message(int home) {
    if (home < 0 || home >= 4) return (void *)0;
#ifdef __mips__
    return (unsigned char *)(0x80126EA0u + 0x4080u + (unsigned int)home * 0xB48u);
#else
    return af_hboard_test_saved(home);
#endif
}

static int owned(void *submenu, struct af_hboard_native_editor *ed) {
    struct af_hboard_context *ctx = &af_hboard_context;
    return ctx->active && submenu == ctx->submenu && ed && ed == ctx->editor &&
           ed->input == ctx->draft.text && ed->hboard_draw == af_hboard_editor_draw &&
           ed->index == ctx->draft.cursor && ed->length == ctx->draft.length;
}

static void sync_editor(struct af_hboard_native_editor *ed) {
    ed->index = (short)af_hboard_context.draft.cursor;
    ed->length = (short)af_hboard_context.draft.length;
}

void af_hboard_editor_init(void *submenu, void *menu) {
    struct af_hboard_context *ctx = &af_hboard_context;
    struct af_hboard_native_editor *ed;
    unsigned char *ovl = overlay(submenu), *saved;
    int i, width;
    ctx->active = 0;
    ctx->submenu = submenu;
    ctx->saved = (void *)0;
    ctx->editor = (void *)0;
    ctx->warning = 0;
    af_hboard_original_init(submenu, menu);
    ed = editor(submenu);
    if (!ed) return;
    ed->hboard_draw = (void *)0;
    if (!ovl || !menu || *(int *)((unsigned char *)menu + 0x38) != 1) return;
    ed->hboard_draw = af_hboard_editor_draw;
    ctx->editor = ed;
    saved = home_message(*(int *)(ovl + 0x10154));
    if (!saved || ed->input != saved) { ctx->warning = AF_HBOARD_ARGUMENT; return; }
    if (af_hboard_begin(&ctx->draft, saved, af_hboard_native_default, af_hboard_english_default) != AF_HBOARD_OK) {
        ctx->warning = AF_HBOARD_ARGUMENT;
        return;
    }
    for (i = 0; i < 256; ++i) {
        width = af_hboard_code_width((unsigned int)i, 1);
        if (width < 1 || width > 12) { ctx->warning = AF_HBOARD_BAD_WIDTH; return; }
        ctx->widths[i] = (unsigned char)width;
    }
    ctx->saved = saved;
    ctx->active = 1;
    ed->input = ctx->draft.text;
    ed->columns = 32;
    ed->rows = 4;
    ed->column = ed->row = 0;
    ed->exchange = -1;
    sync_editor(ed);
}

void af_hboard_editor_command(void *submenu, void *menu) {
    struct af_hboard_context *ctx = &af_hboard_context;
    struct af_hboard_native_editor *ed = editor(submenu);
    int result, command, at_end;
    if (!ed) return;
    ed->processed = 0;
    command = ed->command;
    if (!owned(submenu, ed)) {
        ctx->warning = AF_HBOARD_ARGUMENT;
        /* A bad editor cannot write to the save, but Done still permits a
         * safe exit. The draw bridge explains that nothing will be saved. */
        if (command == AF_HBOARD_DONE) af_hboard_original_done(submenu, menu);
        return;
    }
    if (!command) return;
    if (command == AF_HBOARD_DONE) {
        if (ctx->warning == AF_HBOARD_SAVE_CHANGED) {
            af_hboard_original_done(submenu, menu);
            return;
        }
        result = af_hboard_commit(&ctx->draft, af_hboard_native_default, af_hboard_english_default, ctx->saved);
        if (result == AF_HBOARD_OK) af_hboard_original_done(submenu, menu);
        else ctx->warning = result;
        return;
    }
    at_end = ctx->draft.cursor == ctx->draft.length;
    result = af_hboard_command(&ctx->draft, command,
                               command == AF_HBOARD_EXCHANGE ? ed->exchange : ed->code, ctx->widths);
    if (result == AF_HBOARD_OK) {
        sync_editor(ed);
        ed->processed = 1;
        ctx->warning = 0;
        if (at_end && (command == AF_HBOARD_RIGHT || command == AF_HBOARD_DOWN)) {
            ed->command = AF_HBOARD_INSERT;
            ed->code = command == AF_HBOARD_RIGHT ? ' ' : 0xCD;
        }
    } else if (result < 0) ctx->warning = result;
}

void af_hboard_editor_cursor(struct af_hboard_native_editor *ed, short *column, short *row, int index) {
    struct af_hboard_context *ctx = &af_hboard_context;
    struct af_hboard_layout layout;
    if (owned(ctx->submenu, ed)) {
        if (af_hboard_layout(ctx->draft.text, ctx->draft.length, index, ctx->widths, &layout) == AF_HBOARD_OK) {
            *column = (short)layout.cursor.column;
            *row = (short)layout.cursor.row;
        }
    } else af_hboard_original_cursor(ed, column, row, index);
}

void af_hboard_editor_destruct(void *submenu) {
    struct af_hboard_context *ctx = &af_hboard_context;
    struct af_hboard_native_editor *ed = editor(submenu);
    if (ed) ed->hboard_draw = (void *)0;
    ctx->active = 0;
    ctx->saved = (void *)0;
    ctx->editor = (void *)0;
    ctx->submenu = (void *)0;
    af_hboard_original_destruct(submenu);
}

static void label(void *game, float x, float y, const char *text) {
    int length = 0;
    while (text[length]) ++length;
    af_hboard_font_line(game, (const unsigned char *)text, length, x, y,
                        30, 0, 0, 255, 0, 1, 0.5f, 0.5f, 0);
}

void af_hboard_editor_draw(void *submenu, void *graph, void *game, float x, float y) {
    struct af_hboard_context *ctx = &af_hboard_context;
    struct af_hboard_native_editor *ed = editor(submenu);
    unsigned char *ovl = overlay(submenu);
    struct af_hboard_layout layout;
    const char *note = "Custom messages: 64 characters max.";
    int i, result;
    if (!ovl || !ed) return;
    ((struct af_hboard_matrix_pointer *)(ovl + 0x106B4))->function(graph);
    x += 46.0f;
    y = 54.0f - y;
    if (!owned(submenu, ed)) {
        label(game, x, y - 12.0f, "Editor unavailable. Done closes without saving.");
        return;
    }
    result = af_hboard_layout(ctx->draft.text, ctx->draft.length, ctx->draft.cursor, ctx->widths, &layout);
    if (result == AF_HBOARD_OK) {
        for (i = 0; i < AF_HBOARD_ROWS; ++i) {
            struct af_hboard_line *line = &layout.lines[i];
            if (line->length)
                af_hboard_font_line(game, ctx->draft.text + line->start, line->length, x, y + 16.0f * i,
                                    30, 0, 0, 255, 0, 1, 1.0f, 1.0f, 0);
        }
        if (ed->cursor_draw) ed->cursor_draw(submenu, game, x + layout.cursor.x - 7.0f, y + 16.0f * layout.cursor.row);
        if (ed->end_draw) ed->end_draw(submenu, game, x + layout.end.x + 1.0f - 160.0f,
                                      120.0f - y - 16.0f * layout.end.row);
    } else ctx->warning = result;
    if (ctx->warning == AF_HBOARD_SAVE_FULL) note = "Too long: shorten custom text to 64 characters.";
    else if (ctx->warning == AF_HBOARD_SAVE_CHANGED) note = "Changed elsewhere. Done closes without saving.";
    else if (ctx->warning == AF_HBOARD_TOO_MANY_ROWS) note = "Message must fit four lines. Delete to shorten.";
    else if (ctx->warning == AF_HBOARD_DRAFT_FULL) note = "Draft full. Delete text before adding more.";
    else if (ctx->warning < 0) note = "Cannot apply that edit. Your saved text is safe.";
    label(game, x, y - 12.0f, note);
}
