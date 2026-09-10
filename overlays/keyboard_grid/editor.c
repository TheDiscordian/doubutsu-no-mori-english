/* Select commands only. Existing native/English handlers own all text writes. */
#include "editor.h"

struct af_grid_context af_grid_context;

static unsigned char *overlay(void *submenu) {
    return submenu ? ((struct af_hboard_submenu_pointer *)submenu)->overlay : (void *)0;
}

static struct af_hboard_native_editor *current(void *submenu) {
    unsigned char *ovl=overlay(submenu);
    return ovl ? *(struct af_hboard_native_editor **)(ovl+0x106E0) : (void *)0;
}

int af_grid_owned(void *submenu) {
    struct af_grid_context *ctx=&af_grid_context;
    return submenu && submenu==ctx->submenu && ctx->menu && ctx->editor &&
        current(submenu)==ctx->editor && ctx->input && ctx->editor->input==ctx->input;
}

int af_grid_apology(void *submenu) {
    struct af_grid_context *ctx=&af_grid_context;
    unsigned char *ovl=overlay(submenu);
    return af_grid_owned(submenu) && ovl &&
        *(int *)((unsigned char *)ctx->menu+0x38)==3 && *(int *)(ovl+0x101E0)==3 &&
        ctx->editor->columns==10 && ctx->editor->rows==1 &&
        *(unsigned char **)(ovl+0x101E8)==ctx->input;
}

static void clear(void) {
    unsigned int i;
    for (i=0;i<sizeof(af_grid_context);++i) ((unsigned char *)&af_grid_context)[i]=0;
}

void af_grid_editor_prepare(void *submenu) {
    struct af_hboard_native_editor *ed=current(submenu);
    if (!ed) return;
    /* Suppress radial scrolling without touching cursor blink or edit fields. */
    ed->prefix[0]=ed->prefix[1]=8;
    ed->prefix[2]=ed->prefix[3]=ed->prefix[5]=0;
    ed->prefix[6]=ed->prefix[7]=255;
}

void af_grid_editor_init(void *submenu, void *menu) {
    struct af_grid_context *ctx=&af_grid_context;
    clear();
    af_apology_editor_init(submenu,menu);
    ctx->editor=current(submenu);
    if (!ctx->editor || !ctx->editor->input || !menu) { clear(); return; }
    ctx->submenu=submenu;ctx->menu=menu;ctx->input=ctx->editor->input;
    af_grid_reset(&ctx->state);
    ctx->state.upper=1; /* Names open with the complete English capitals/digits. */
    af_grid_editor_prepare(submenu);
}

void af_grid_editor_destruct(void *submenu) {
    clear();
    af_apology_editor_destruct(submenu);
}

void af_grid_editor_input(void *submenu) {
    struct af_grid_context *ctx=&af_grid_context;
    struct af_hboard_native_editor *ed=current(submenu);
    unsigned short key=AF_GRID_DISABLED;
    int command;
    if (!ed) return;
    ed->command=AF_GRID_NONE;
    if (!af_grid_owned(submenu)) { ctx->error=1;return; }
    command=af_grid_update(&ctx->state,af_grid_tables,af_grid_get_button(),af_grid_get_trigger(),
        af_grid_get_x(),af_grid_get_y(),ed->rows>1,af_grid_apology(submenu),&key);
    ed->prefix[4]=3;
    if (command==AF_GRID_INSERT) {
        if (key==AF_GRID_SUN || key==AF_GRID_SKULL) {
            /* The installed apology adapter owns validation and two-byte writes. */
            ed->prefix[4]=1;key=key==AF_GRID_SUN ? 0x84 : 0x81;
        }
        ed->code=(unsigned char)key;
    }
    ed->command=(unsigned char)command;
}
