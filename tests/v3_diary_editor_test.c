#include "../overlays/v3/diary_editor.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>

static unsigned char ovl[0x10750] __attribute__((aligned(16))),sub[64];
static AFDiary live,scratch;
static AFDiaryMenu menu;
static unsigned char widths[256];
static AFDiaryMenuAccess access;
static AFDiaryEditorSession owned;
static struct af_hboard_native_editor editor;
struct af_grid_context af_grid_context;
static void *session_arg,*input_arg;
static unsigned int initialized,updated,feedback,finished,rejected,command,code;
static int exchange;
#define WORD(p,o) (*(unsigned int *)((unsigned char *)(p)+(o)))
static void *native_menu(void) {return ovl+0x10358;}
void *af_diary_editor_test_pointer(void *p,unsigned int at) {
    if(p==sub && at==0x2C)return ovl;
    assert(p==native_menu());
    if(at==0x40)return input_arg;
    assert(at==0x44);return session_arg;
}
void af_diary_editor_test_set_pointer(void *p,unsigned int at,void *value) {
    assert(p==native_menu() && at==0x44);session_arg=value;
}
int af_grid_owned(void *s) {
    return s==sub && af_grid_context.submenu==s && af_grid_context.menu==native_menu() &&
        af_grid_context.editor==&editor && af_grid_context.input==input_arg && editor.input==input_arg;
}
void af_grid_editor_prepare(void *s) {assert(s==sub);}
void af_diary_keyboard_init(void *s,void *m) {
    initialized++;
    if(owned.magic!=AF_DIARY_SESSION_MAGIC)return;
    assert(s==sub && m==native_menu() && WORD(m,0x38)==4 && WORD(m,0x3C)==32 && !session_arg);
    af_grid_context.submenu=s;af_grid_context.menu=m;af_grid_context.input=input_arg;
    af_grid_context.editor=&editor;editor.input=input_arg;
    editor.length=32;editor.index=0;
}
void af_diary_keyboard_update(void *s,void *m) {(void)s;(void)m;updated++;}
void af_diary_keyboard_input(void *s) {
    assert(s==sub);editor.command=command;editor.code=code;editor.exchange=exchange;
}
void af_diary_keyboard_feedback(void *s) {assert(s==sub);feedback++;}
void af_diary_keyboard_done(void *s,void *m) {assert(s==sub && m==native_menu());finished++;}
void af_diary_keyboard_sound(unsigned int id) {assert(id==0x1003);rejected++;}
static void key(unsigned int c,int ch) {
    command=c;code=ch;exchange=ch;
    af_diary_editor_update(sub,native_menu());
}
int main(void) {
    void *m=native_menu();
    for(unsigned int mode=0;mode<6;mode++) {
        WORD(m,0x38)=mode;af_diary_editor_init(sub,m);af_diary_editor_update(sub,m);
    }
    assert(initialized==6 && updated==6);
    memset(widths,6,sizeof(widths));widths['i']=2;widths['W']=10;
    af_diary_reset(&live);
    access=(AFDiaryMenuAccess){.live=&live,.scratch=&scratch,.widths=widths};
    AFDiaryDate today={2026,9,12};AFDiaryDates dates={23,9,29};
    assert(af_diary_menu_open(&menu,&access,2,2,today,dates)==AF_DIARY_OK);
    assert(af_diary_menu_input(&menu,&access,AF_DIARY_A,0,0)==AF_DIARY_OK);
    assert(af_diary_menu_input(&menu,&access,AF_DIARY_A,0,0)==AF_DIARY_OK);
    assert(af_diary_menu_input(&menu,&access,AF_DIARY_A,0,0)==AF_DIARY_OK);
    assert(menu.state==AF_DIARY_EDIT);
    owned=(AFDiaryEditorSession){AF_DIARY_SESSION_MAGIC,sub,&menu,&access};
    session_arg=&owned;input_arg=menu.draft.text;WORD(m,0x38)=6;WORD(m,0x3C)=992;
    af_diary_editor_init(sub,m);
    assert(af_diary_editor_active(sub) && WORD(m,0x38)==6 && WORD(m,0x3C)==992 && session_arg==&owned);
    assert(editor.rows==31 && editor.columns==32 && editor.length==0 && editor.index==0);
    key(0,0);assert(!feedback && !rejected);
    key(8,'W');key(8,'i');key(8,'i');key(8,0xCD);key(8,'a');
    assert(menu.draft.length==5 && editor.row==1 && editor.column==1 && editor.index==5);
    key(7,'A');assert(menu.draft.text[4]=='A');
    key(1,0);assert(editor.index==4 && !editor.column);
    key(4,0);key(4,0);assert(menu.draft.length==6 && menu.draft.text[5]==' ' && editor.command==8);
    key(6,0);assert(menu.draft.length==5);
    key(5,0);assert(finished==1 && menu.state==AF_DIARY_CONFIRM);
    const unsigned char *page=af_diary_page(&live,2,2,8);
    for(unsigned int i=0;i<992;i++)assert(page[i]==' '); /* Done is not a commit. */
    key(8,'Z');assert(menu.draft.length==5 && finished==1);
    assert(af_diary_menu_input(&menu,&access,AF_DIARY_B,0,0)==AF_DIARY_OK);
    af_diary_editor_init(sub,m);assert(editor.index==5 && menu.draft.text[4]=='A');
    for(unsigned int i=0;i<992;i++)menu.draft.text[i]='a';
    menu.draft.length=menu.draft.cursor=992;
    af_diary_editor_init(sub,m);assert(editor.index==992 && editor.row==30 && menu.draft.scroll==24);
    key(8,'W');assert(rejected==1 && menu.draft.length==992 && editor.index==992);
    key(6,0);assert(menu.draft.length==991);key(8,'a');assert(menu.draft.length==992);
    menu.draft.readonly=1;key(6,0);assert(menu.draft.length==992 && !af_diary_editor_active(sub));
    menu.draft.readonly=0;owned.magic=0;key(6,0);assert(menu.draft.length==992);
    owned.magic=AF_DIARY_SESSION_MAGIC;input_arg=live.bytes;key(6,0);assert(menu.draft.length==992);
    input_arg=menu.draft.text;assert(af_diary_editor_active(sub));
    menu.draft.text[0]=1;af_diary_editor_init(sub,m);
    assert(menu.state==AF_DIARY_ERROR && menu.error==AF_DIARY_ARGUMENT);
    puts("diary keyboard: complete page, proportional rows, Rewrite, ownership, and unchanged native modes pass");
    return 0;
}
