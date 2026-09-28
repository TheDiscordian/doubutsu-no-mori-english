/* Diary commands use the existing N64-style keyboard and shared diary draft.
 * Native mode tables never receive mode six. No copy can truncate a monthly
 * page to the native one-line editor's capacity. */
#include "diary_editor.h"

struct diary_pointer { void *value; } __attribute__((packed));
static void *pointer(void *p,unsigned int at) {
#ifndef __mips__
    return af_diary_editor_test_pointer(p,at);
#else
    return ((struct diary_pointer *)((unsigned char *)p+at))->value;
#endif
}
static void set_pointer(void *p,unsigned int at,void *value) {
#ifndef __mips__
    af_diary_editor_test_set_pointer(p,at,value);
#else
    ((struct diary_pointer *)((unsigned char *)p+at))->value=value;
#endif
}
static unsigned int *word(void *p,unsigned int at) {
    return (unsigned int *)((unsigned char *)p+at);
}
static int mode(void *menu) {return menu && *word(menu,0x38)==AF_DIARY_EDITOR_MODE;}

static AFDiaryEditorSession *session(void *submenu,void *menu) {
    unsigned char *ovl;
    AFDiaryEditorSession *s;
    if(!submenu || !mode(menu))return 0;
    ovl=pointer(submenu,0x2C);
    if(!ovl || menu!=ovl+0x10358 || *word(menu,0x3C)!=AF_DIARY_PAGE)return 0;
    s=pointer(menu,0x44);
#ifdef __mips__
    /* A caller-owned resident session must lie in Expansion Pak RAM, above
     * all installed world/save workspaces and below the framebuffer. */
    if((unsigned int)s<0x806A0000 || (unsigned int)s>0x807DA800-sizeof(*s) ||
       (unsigned int)s&3)return 0;
#endif
    if(!s || s->magic!=AF_DIARY_SESSION_MAGIC || s->submenu!=submenu ||
       !s->menu || !s->access || !s->access->widths ||
       s->menu->viewer!=s->menu->owner || s->menu->draft.readonly ||
       pointer(menu,0x40)!=s->menu->draft.text)return 0;
    return s;
}

int af_diary_editor_active(void *submenu) {
    struct af_grid_context *ctx=&af_grid_context;
    AFDiaryEditorSession *s=session(submenu,ctx->menu);
    return s && af_grid_owned(submenu) && ctx->input==s->menu->draft.text &&
        ctx->editor->input==ctx->input;
}

static int sync(AFDiaryEditorSession *s,struct af_hboard_native_editor *ed) {
    AFDiaryDraft *d=&s->menu->draft;
    AFDiaryLayout layout;
    int result=af_diary_layout(d->text,d->length,d->cursor,s->access->widths,&layout);
    if(result!=AF_DIARY_OK)return result;
    ed->columns=32;ed->rows=AF_DIARY_ROWS;ed->length=d->length;ed->index=d->cursor;
    ed->column=layout.cursor.column;ed->row=layout.cursor.row;
    /* Reopening Rewrite preserves the draft/cursor and reveals its actual
     * proportional row; reading's scroll is not used as a byte offset. */
    if(layout.cursor.row<d->scroll)d->scroll=layout.cursor.row;
    if(layout.cursor.row>=d->scroll+AF_DIARY_VISIBLE)
        d->scroll=layout.cursor.row-AF_DIARY_VISIBLE+1;
    return AF_DIARY_OK;
}

void af_diary_editor_init(void *submenu,void *menu) {
    AFDiaryEditorSession *s;
    void *saved;
    if(!mode(menu)) {af_diary_keyboard_init(submenu,menu);return;}
    s=session(submenu,menu);
    if(!s || s->menu->state!=AF_DIARY_EDIT)return;
    /* Mode four initializes caller-owned text without touching native letters
     * or the house message. Limit its initial scan to one ordinary row; the
     * shared draft below restores the full length and cursor immediately. */
    saved=pointer(menu,0x44);
    *word(menu,0x38)=4;*word(menu,0x3C)=32;set_pointer(menu,0x44,0);
    af_diary_keyboard_init(submenu,menu);
    *word(menu,0x38)=AF_DIARY_EDITOR_MODE;*word(menu,0x3C)=AF_DIARY_PAGE;set_pointer(menu,0x44,saved);
    if(!af_diary_editor_active(submenu)) {
        s->menu->error=AF_DIARY_ARGUMENT;s->menu->state=AF_DIARY_ERROR;return;
    }
    int result=sync(s,af_grid_context.editor);
    if(result<0) {s->menu->error=result;s->menu->state=AF_DIARY_ERROR;}
    else {
        af_grid_context.editor->exchange=af_diary_keyboard_exchange(af_grid_context.editor);
        *(short *)(void *)(af_grid_context.editor->prefix+0xC)=0;
    }
}

void af_diary_editor_update(void *submenu,void *menu) {
    AFDiaryEditorSession *s;
    struct af_hboard_native_editor *ed;
    int result,code,at_end;
    unsigned int command;
    if(!mode(menu)) {af_diary_keyboard_update(submenu,menu);return;}
    if(!af_diary_editor_active(submenu) || af_grid_context.menu!=menu)return;
    s=session(submenu,menu);ed=af_grid_context.editor;ed->processed=0;
    if(s->menu->state!=AF_DIARY_EDIT || s->menu->error<0)return;
    short *blink=(short *)(void *)(ed->prefix+0xC);
    *blink=(*blink+1)%20;
    af_grid_editor_prepare(submenu);
    if(ed->animation)ed->animation--;
    af_diary_keyboard_input(submenu); /* existing repeat, case, page, and sounds */
    command=ed->command;
    if(!command)return;
    code=command==7?ed->exchange:ed->code;
    at_end=s->menu->draft.cursor==s->menu->draft.length;
    result=af_diary_menu_edit(s->menu,s->access,command,code);
    if(result==AF_DIARY_OK) {
        result=sync(s,ed);
        if(result<0) {s->menu->error=result;s->menu->state=AF_DIARY_ERROR;return;}
        ed->processed=1;
        if(at_end && (command==4 || command==2)) {
            ed->command=8;ed->code=command==4?' ':0xCD;
        }
        af_diary_keyboard_feedback(submenu);
        ed->exchange=af_diary_keyboard_exchange(ed);
        if(command<=4 || command==6 || command==8)*blink=0;
        if(command==5)af_diary_keyboard_done(submenu,menu);
    } else if(result<0)af_diary_keyboard_sound(0x1003);
}
