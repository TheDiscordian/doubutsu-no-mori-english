/* Apology-only adapter appended after the unchanged complete owner editor. */
#include "edit.h"
#include "../hboard/editor.h"

extern void af_apology_original_command(void *, void *);
extern int af_apology_original_exchange(struct af_hboard_native_editor *);

static struct {
    void *submenu, *menu;
    struct af_hboard_native_editor *editor;
    unsigned char *input;
} context;

static unsigned char *overlay(void *submenu) {
    return submenu ? ((struct af_hboard_submenu_pointer *)submenu)->overlay : (void *)0;
}

static struct af_hboard_native_editor *current(void *submenu) {
    unsigned char *ovl=overlay(submenu);
    return ovl ? *(struct af_hboard_native_editor **)(ovl+0x106E0) : (void *)0;
}

static int owns(struct af_hboard_native_editor *ed) {
    unsigned char *ovl=overlay(context.submenu);
    return context.editor && ed==context.editor && ovl && context.menu &&
        current(context.submenu)==ed && ed->input && ed->input==context.input &&
        ed->columns==10 && ed->rows==1 &&
        *(int *)((unsigned char *)context.menu+0x38)==3 &&
        *(int *)(ovl+0x101E0)==3 &&
        *(unsigned char **)(ovl+0x101E8)==ed->input;
}

static void clear(void) {
    context.submenu=context.menu=(void *)0;
    context.editor=(void *)0;
    context.input=(void *)0;
}

static void load(struct af_apology_draft *draft, const struct af_hboard_native_editor *ed) {
    unsigned int i;
    for (i=0;i<AF_APOLOGY_BYTES;++i) draft->text[i]=ed->input[i];
    draft->length=(unsigned char)ed->length;
    draft->cursor=(unsigned char)ed->index;
}

static int valid_editor(const struct af_hboard_native_editor *ed) {
    struct af_apology_draft draft;
    if (ed->length<0 || ed->length>10 || ed->index<0 || ed->index>ed->length) return 0;
    load(&draft,ed);
    return af_apology_valid(&draft);
}

/* These are key identities in the native symbol page, not stored aliases.
 * Three Japanese punctuation keys become Sun, Skull, and = in apology mode. */
static int key_code(const struct af_hboard_native_editor *ed, unsigned int code) {
    if (ed->prefix[4]==1) {
        if (code==0x84) return AF_APOLOGY_SUN;
        if (code==0x81) return AF_APOLOGY_SKULL;
        if (code==0x85) return '=';
    }
    return (int)code;
}

void af_apology_editor_init(void *submenu, void *menu) {
    unsigned char *ovl;
    struct af_hboard_native_editor *ed;
    clear();
    af_hboard_editor_init(submenu,menu);
    ovl=overlay(submenu);ed=current(submenu);
    if (!ovl || !ed || !menu || *(int *)((unsigned char *)menu+0x38)!=3 ||
            *(int *)(ovl+0x101E0)!=3 || ed->columns!=10 || ed->rows!=1 || !ed->input ||
            *(unsigned char **)(ovl+0x101E8)!=ed->input) return;
    context.submenu=submenu;context.menu=menu;context.editor=ed;context.input=ed->input;
}

void af_apology_editor_destruct(void *submenu) {
    clear();
    af_hboard_editor_destruct(submenu);
}

void af_apology_editor_command(void *submenu, void *menu) {
    struct af_hboard_native_editor *ed=current(submenu);
    struct af_apology_draft draft;
    int result, command, end;
    unsigned int i;
    if (!context.editor || submenu!=context.submenu || menu!=context.menu || ed!=context.editor) {
        af_apology_original_command(submenu,menu);
        return;
    }
    ed->processed=0;
    if (!owns(ed) || !valid_editor(ed)) return;
    load(&draft,ed);command=ed->command;end=draft.cursor==draft.length;
    result=af_apology_edit(&draft,command,
        command==AF_APOLOGY_EXCHANGE ? ed->exchange : key_code(ed,ed->code));
    if (result==AF_APOLOGY_FINISHED) {
        /* The original empty-input check, Done callback, and retry logic stay. */
        af_apology_original_command(submenu,menu);
    } else if (result==AF_APOLOGY_CHANGED) {
        for (i=0;i<AF_APOLOGY_BYTES;++i) ed->input[i]=draft.text[i];
        ed->length=draft.length;ed->index=draft.cursor;ed->column=draft.cursor;ed->row=0;
        ed->exchange=-1;ed->processed=1;
        if (command==AF_APOLOGY_RIGHT && end) {ed->command=AF_APOLOGY_INSERT;ed->code=' ';}
    }
}

int af_apology_editor_exchange(struct af_hboard_native_editor *ed) {
    if (context.editor && ed==context.editor) {
        if (!owns(ed) || !valid_editor(ed)) return -1;
        if (ed->index>=2 && ed->input[ed->index-2]==0x80) return -1;
    }
    return af_apology_original_exchange(ed);
}

void af_apology_editor_cursor(struct af_hboard_native_editor *ed, short *column, short *row, int index) {
    if (context.editor && ed==context.editor) {
        struct af_apology_draft draft;
        if (!column || !row) return;
        *column=*row=0;
        if (!owns(ed) || !valid_editor(ed) || index<0 || index>ed->length) return;
        load(&draft,ed);draft.cursor=(unsigned char)index;
        if (af_apology_valid(&draft)) *column=(short)index;
    } else af_hboard_editor_cursor(ed,column,row,index);
}

void af_apology_editor_key_draw(void *game, const unsigned char *text, int length, float x, float y,
        int r, int g, int b, int alpha, int polygon, int proportional, float sx, float sy, int mode) {
    unsigned char pair[2];
    int code;
    if (context.editor && owns(context.editor) && text && length==1) {
        code=key_code(context.editor,text[0]);
        if (code==AF_APOLOGY_SUN || code==AF_APOLOGY_SKULL) {
            pair[0]=0x80;pair[1]=(unsigned char)code;text=pair;length=2;
        } else if (code=='=' && text[0]==0x85) {pair[0]='=';text=pair;}
    }
    af_hboard_font_line(game,text,length,x,y,r,g,b,alpha,polygon,proportional,sx,sy,mode);
}
