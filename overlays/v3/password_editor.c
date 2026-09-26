/* Included after the accepted V2 renderer, with source-derived title/# assets. */
#include "password_editor.h"
#include "password_edit.c"

extern void af_pw_previous_init(void *, void *);
extern void af_pw_previous_update(void *, void *);
extern void af_pw_previous_input(void *);
extern void af_pw_done(void *, void *);
extern void af_pw_feedback(void *);
extern void af_pw_sound(unsigned int);
static struct {
    void *submenu, *menu;
    unsigned char *input;
    struct af_hboard_native_editor *editor;
    struct AfPasswordDraft draft;
} pw_editor;

static int mode(void *menu) { return menu && U32(menu,0x38)==AF_PW_EDITOR_MODE; }

int af_pw_editor_active(void *submenu) {
    unsigned char *ovl;
    if (!submenu || submenu!=pw_editor.submenu || !mode(pw_editor.menu) ||
        !af_grid_owned(submenu) || pw_editor.editor!=af_grid_context.editor ||
        af_grid_context.menu!=pw_editor.menu || pw_editor.editor->input!=pw_editor.input ||
        PTR(pw_editor.menu,0x40)!=pw_editor.input || U32(pw_editor.menu,0x3C)!=28)
        return 0;
    ovl=PTR(submenu,0x2C);
    return ovl && pw_editor.menu==ovl+0x10358;
}

void af_pw_editor_init(void *submenu, void *menu) {
    unsigned char *ovl=PTR(submenu,0x2C);
    unsigned int i;
    pw_editor.submenu=0;
    if (!mode(menu)) { af_pw_previous_init(submenu,menu); return; }
    /* Native mode four safely initializes a caller-owned single-line buffer.
     * The new mode must never index its five-entry dimensions/handler tables. */
    if (!ovl || menu!=ovl+0x10358 || U32(menu,0x3C)!=28 || !PTR(menu,0x40)) return;
    U32(menu,0x38)=4;
    af_pw_previous_init(submenu,menu);
    U32(menu,0x38)=AF_PW_EDITOR_MODE;
    if (!af_grid_owned(submenu)) return;
    pw_editor.menu=menu; pw_editor.submenu=submenu;
    pw_editor.editor=af_grid_context.editor; pw_editor.input=PTR(menu,0x40);
    for (i=0;i<28;++i) pw_editor.draft.text[i]=pw_editor.input[i];
    pw_editor.draft.line=pw_editor.draft.cursor=pw_editor.draft.finished=0;
    /* One logical row keeps the shared keyboard's Return key disabled. */
    pw_editor.editor->columns=14; pw_editor.editor->rows=1;
    pw_editor.editor->length=14; pw_editor.editor->index=0;
    pw_editor.editor->column=pw_editor.editor->row=0;
}

unsigned int af_pw_editor_key(const struct af_grid_state *state, const unsigned short *table,
                              int newline, int apology) {
    /* The first otherwise unused symbol cell is # only in code-entry mode.
     * The common table is never modified, including during drawing. */
    if (af_pw_editor_active(af_grid_context.submenu) && state->page &&
        state->column==AF_PW_HASH_COLUMN && state->row==AF_PW_HASH_ROW) return '#';
    return af_grid_key(state,table,newline,apology);
}

void af_pw_editor_update(void *submenu, void *menu) {
    struct af_hboard_native_editor *ed;
    int result;
    unsigned int i;
    if (!mode(menu)) { af_pw_previous_update(submenu,menu); return; }
    if (!af_pw_editor_active(submenu) || pw_editor.draft.finished) return;
    ed=pw_editor.editor; ed->processed=0;
    af_grid_editor_prepare(submenu);
    af_pw_previous_input(submenu); /* accepted repeat, page, case, and feedback */
    result=af_pw_edit(&pw_editor.draft,ed->command,ed->code);
    if (result==AF_PW_EDIT_CHANGED || result==AF_PW_EDIT_DONE) {
        for (i=0;i<28;++i) pw_editor.input[i]=pw_editor.draft.text[i];
        ed->processed=1;
        ed->index=ed->column=pw_editor.draft.cursor; ed->row=pw_editor.draft.line;
        ed->exchange=-1;
        af_pw_feedback(submenu);
        if (result==AF_PW_EDIT_DONE) af_pw_done(submenu,menu);
    } else if (result==AF_PW_EDIT_REJECT) af_pw_sound(0x1003);
}

static Gfx *rectangle(Gfx *g, int x, int y, int w, int h) {
    if (x>=0 && y>=0 && x+w<=320 && y+h<=240) gDPFillRectangle(g++,x,y,x+w-1,y+h-1);
    return g;
}

void af_pw_editor_draw(void *submenu, void *menu, void *game) {
    unsigned char *ovl;
    void *graph;
    unsigned int i;
    float dx,dy;
    Gfx *g;
    af_bg_editor_draw(submenu,menu,game);
    if (!game || !af_pw_editor_active(submenu)) return;
    graph=PTR(game,0); ovl=PTR(submenu,0x2C);
    if (!graph || !space(graph,14000)) return;
    dx=*(float *)((unsigned char *)menu+0x18); dy=*(float *)((unsigned char *)menu+0x1C);
    if (!(dx>=-320 && dx<=320 && dy>=-240 && dy<=240)) return;
    /* Fixed source row lengths: glyph widths do not move the code boundaries. */
    g=PTR(graph,0x298);
    gDPPipeSync(g++); gDPSetCycleType(g++,G_CYC_1CYCLE);
    gDPSetRenderMode(g++,G_RM_XLU_SURF,G_RM_XLU_SURF2);
    gDPSetCombineMode(g++,G_CC_PRIMITIVE,G_CC_PRIMITIVE);
    gDPSetPrimColor(g++,0,255,40,45,50,235);
    g=rectangle(g,(int)(62+dx),(int)(44-dy),196,64);
    gDPPipeSync(g++); PTR(graph,0x298)=g;
    ((struct af_hboard_matrix_pointer *)(ovl+0x106B4))->function(graph);
    text(graph,game,af_pw_title,sizeof(af_pw_title),94+dx,48-dy,1,0,0.75f);
    for (i=0;i<28;++i) {
        unsigned char ch=pw_editor.input[i];
        float x=76+12*(i%14)+dx, y=66+18*(i/14)-dy;
        if (ch!=' ') text(graph,game,&ch,1,x+(12-af_hboard_code_width(ch,1))*0.5f,y,1,0,1);
    }
    g=PTR(graph,0x298); gDPPipeSync(g++);
    gDPSetCombineMode(g++,G_CC_PRIMITIVE,G_CC_PRIMITIVE);
    gDPSetPrimColor(g++,0,255,245,220,65,255);
    g=rectangle(g,(int)(76+12*pw_editor.draft.cursor+dx),
        (int)(81+18*pw_editor.draft.line-dy),10,2);
    gDPPipeSync(g++); PTR(graph,0x298)=g;
}
