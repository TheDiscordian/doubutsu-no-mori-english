#ifndef AF_GRID_EDITOR_H
#define AF_GRID_EDITOR_H
#include "core.h"
#include "../hboard/editor.h"

struct af_grid_context {
    struct af_grid_state state;
    void *submenu, *menu;
    struct af_hboard_native_editor *editor;
    unsigned char *input;
    unsigned int draws, error;
};
extern struct af_grid_context af_grid_context;
extern const unsigned short af_grid_tables[240];
extern const unsigned char af_grid_keycap[128];
void af_grid_editor_init(void *, void *);
void af_grid_editor_destruct(void *);
void af_grid_editor_prepare(void *);
void af_grid_editor_input(void *);
void af_grid_editor_draw(void *, void *, void *);
int af_grid_owned(void *);
int af_grid_apology(void *);
extern void af_apology_editor_init(void *, void *);
extern void af_apology_editor_destruct(void *);
extern unsigned short af_grid_get_button(void), af_grid_get_trigger(void);
extern int af_grid_get_x(void), af_grid_get_y(void);
#endif
