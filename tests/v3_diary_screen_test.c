/* Native ownership/callback contracts on host, not native execution evidence. */
#include "../overlays/v3/diary_screen.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define W(p,o) (*(unsigned int *)((unsigned char *)(p)+(o)))
#define F(p,o) (*(float *)((unsigned char *)(p)+(o)))
static unsigned char sub[0x100] __attribute__((aligned(16))),ovl[0x10740] __attribute__((aligned(16)));
static unsigned char widths[256],art[16] __attribute__((aligned(16)));
static AFDiary live,scratch;
static AFDiaryScreen screen;
static struct af_hboard_native_editor editor;
struct af_grid_context af_grid_context;
static struct {void *address,*value;} pointers[40];
static unsigned int pointer_count,trigger,button,command,code,opening,ended,capacity_calls;
static unsigned int cal_draws,page_draws,prompt_draws,base_moves,base_draws,old_init,old_proc,old_destruct;
static int y,capacity_ok=1;
static AFDiaryDraw last_page,last_prompt;
static void *m(void) {return ovl+0x10118;}
static void *e(void) {return ovl+0x10358;}
void *af_diary_screen_test_pointer(void *p,unsigned int offset) {
    void *address=(unsigned char *)p+offset;
    for(unsigned int i=0;i<pointer_count;i++)if(pointers[i].address==address)return pointers[i].value;
    return 0;
}
void af_diary_screen_test_set_pointer(void *p,unsigned int offset,void *value) {
    void *address=(unsigned char *)p+offset;
    for(unsigned int i=0;i<pointer_count;i++)if(pointers[i].address==address) {pointers[i].value=value;return;}
    assert(pointer_count<40);pointers[pointer_count].address=address;pointers[pointer_count++].value=value;
}
#define P(p,o,v) af_diary_screen_test_set_pointer(p,o,(void *)(v))
void *af_diary_editor_test_pointer(void *p,unsigned int o) {return af_diary_screen_test_pointer(p,o);}
void af_diary_editor_test_set_pointer(void *p,unsigned int o,void *v) {P(p,o,v);}
unsigned short af_diary_screen_trigger(void) {return trigger;}
unsigned short af_diary_screen_button(void) {return button;}
int af_diary_screen_y(void) {return y;}
void af_diary_screen_sound(unsigned int sound) {assert(sound==0x1003 || sound==0x105F || sound==0x1035);}
void af_diary_keyboard_sound(unsigned int sound) {assert(sound==0x1003);}
static void base_move(void *s) {assert(s==sub);base_moves++;}
static void base_draw(void *s,void *g) {assert(s==sub && g==art);base_draws++;}
static void change(void *menu,unsigned int direction) {W(menu,4)=0;W(menu,0x30)=direction&1?1:4;W(menu,0x34)=direction;}
static void move(void *s,void *menu) {
    assert(s==sub);W(menu,4)=W(menu,0x30);F(menu,0x1C)=0;
}
void af_diary_hboard_previous_init(void *s) {assert(s==sub);old_init++;}
void af_diary_hboard_previous_proc(void *s) {assert(s==sub);old_proc++;}
void af_diary_hboard_previous_destruct(void *s) {assert(s==sub);old_destruct++;}
extern void af_diary_hboard_init(void *),af_diary_hboard_proc(void *),af_diary_hboard_destruct(void *);
static void end(void *s,void *menu) {
    assert(s==sub && menu==m());af_diary_hboard_destruct(s);W(sub,4)=W(sub,8)=0;ended++;
}
void af_diary_submenu_open(void *s,int program,int data0,int data1,void *data2,void *data3) {
    assert(s==sub && (program==2 || program==10));assert(!opening);opening=program;
    W(sub,4)=program;W(sub,0x10)=data0;W(sub,0x14)=data1;P(sub,0x18,data2);P(sub,0x1C,data3);
}
int af_grid_owned(void *s) {
    return s==sub && af_grid_context.submenu==sub && af_grid_context.menu==e() &&
        af_grid_context.input==screen.menu.draft.text && editor.input==af_grid_context.input;
}
void af_grid_editor_prepare(void *s) {assert(s==sub);}
void af_diary_keyboard_init(void *s,void *menu) {
    assert(s==sub && menu==e() && W(menu,0x38)==4 && W(menu,0x3C)==32);
    assert(!af_diary_editor_test_pointer(menu,0x44));
    editor.input=screen.menu.draft.text;
    af_grid_context.submenu=s;af_grid_context.menu=menu;af_grid_context.editor=&editor;
    af_grid_context.input=editor.input;
}
void af_diary_keyboard_update(void *s,void *menu) {(void)s;(void)menu;assert(0);}
void af_diary_keyboard_input(void *s) {assert(s==sub);editor.command=command;editor.code=code;}
void af_diary_keyboard_feedback(void *s) {assert(s==sub);}
int af_diary_keyboard_exchange(struct af_hboard_native_editor *ed) {
    if(!ed->index)return -1;
    int ch=ed->input[ed->index-1];
    return ch>='a' && ch<='z'?ch-32:ch>='A' && ch<='Z'?ch+32:-1;
}
void af_diary_keyboard_done(void *s,void *menu) {assert(s==sub && menu==e());change(menu,6);}
static unsigned int events(void *ctx,AFDiaryDate date,unsigned int owner) {(void)ctx;(void)date;(void)owner;return 2;}
static int calendar(void *ctx,const AFDiaryMenu *menu,AFDiaryDraw *draw) {
    (void)ctx;assert(menu->owner<4);
    memset(draw->day_types,0,37);draw->event_label=(const unsigned char *)"Event";draw->event_length=5;
    return AF_DIARY_OK;
}
static int capacity(void *ctx,const AFDiary *candidate) {
    (void)ctx;assert(candidate==&scratch);capacity_calls++;return capacity_ok?AF_DIARY_OK:AF_DIARY_CAPACITY;
}
int af_diary_draw_calendar(void *s,void *g,const AFDiaryMenu *menu,const AFDiary *data,AFDiaryDates dates,const AFDiaryDraw *d) {
    assert(s==sub && g==art && menu==&screen.menu && data==&live && dates.town_day==23 && d->art==art);
    cal_draws++;return AF_DIARY_OK;
}
int af_diary_draw_page(void *s,void *g,const AFDiaryMenu *menu,const unsigned char *w,const AFDiaryDraw *d) {
    assert(s==sub && g==art && menu==&screen.menu && w==widths);page_draws++;last_page=*d;return AF_DIARY_OK;
}
int af_diary_draw_prompt(void *s,void *g,const AFDiaryMenu *menu,const AFDiaryDraw *d) {
    assert(s==sub && g==art && menu==&screen.menu);prompt_draws++;last_prompt=*d;return AF_DIARY_OK;
}
static void tick(unsigned int input) {
    trigger=input;W(ovl,0x1068C)=input;
    if(opening) {
        unsigned int id=opening;opening=0;void *menu=id==2?m():e();
        W(menu,0x38)=W(sub,0x10);W(menu,0x3C)=W(sub,0x14);
        P(menu,0x40,af_diary_screen_test_pointer(sub,0x18));P(menu,0x44,af_diary_screen_test_pointer(sub,0x1C));
        W(sub,8)=id;W(menu,4)=0;W(menu,0x30)=1;
        if(id==2) {af_diary_hboard_init(sub);af_diary_hboard_proc(sub);}
        else {
            W(m(),0x14)=10;P(menu,0xC,af_diary_screen_move);P(menu,0x10,af_diary_screen_draw);
            af_diary_editor_init(sub,menu);
        }
    }
    if(W(sub,8)==10) {
        af_diary_screen_move(sub);
        if(W(e(),4)==0)move(sub,e());
        else if(W(e(),4)==4) {
            W(sub,4)=W(sub,8)=2;W(m(),0x14)=0;af_diary_hboard_proc(sub);
        } else af_diary_editor_update(sub,e());
    } else af_diary_screen_move(sub);
    if(af_diary_screen_owned(sub))af_diary_screen_draw(sub,art);
    trigger=0;command=0;
}
static void settle(unsigned int phase) {
    unsigned int i;
    for(i=0;i<500 && (screen.phase!=phase || opening);i++)tick(0);
    if(i==500)fprintf(stderr,"phase %u expected %u, state %u, fault %d, child %u\n",screen.phase,phase,screen.menu.state,screen.fault,W(sub,8));
    assert(i<500 && !screen.fault);
}
static void begin(unsigned int viewer,unsigned int owner) {
    memset(sub,0,sizeof(sub));memset(ovl,0,sizeof(ovl));pointer_count=0;
    P(sub,0x2C,ovl);P(m(),0xC,base_move);P(m(),0x10,base_draw);
    P(ovl,0x106A8,move);P(ovl,0x106AC,end);P(ovl,0x106B0,change);
    AFDiaryMenuAccess a={&live,&scratch,widths,capacity,0,events};
    assert(af_diary_screen_open(&screen,sub,&a,viewer,owner,(AFDiaryDate){2026,9,12},(AFDiaryDates){23,9,29},art,calendar));
    assert(!af_diary_screen_open(&screen,sub,&a,viewer,owner,(AFDiaryDate){2026,9,12},(AFDiaryDates){23,9,29},art,calendar));
    tick(0);assert(af_diary_screen_owned(sub)==&screen && W(m(),4)==1);
    assert(af_diary_screen_test_pointer(ovl,0x10670)==af_diary_screen_move);
    tick(AF_DIARY_A);assert(screen.menu.state==AF_DIARY_DAY);
    tick(AF_DIARY_A);
}
static void edit(void) {
    settle(AF_DIARY_VIEW_READ);tick(AF_DIARY_A);settle(AF_DIARY_VIEW_EDITOR);
    tick(0);tick(0);assert(af_diary_editor_active(sub));
}
static void done(void) {
    command=5;tick(0);assert(screen.menu.state==AF_DIARY_CONFIRM);
    settle(AF_DIARY_VIEW_PROMPT);assert(W(sub,8)==2 && !screen.editor_requested);
}
static void finish(void) {
    tick(AF_DIARY_A);assert(screen.menu.state==AF_DIARY_CONFIRM && screen.answers);
    for(int i=0;i<3;i++)tick(0);
    assert(screen.answer_scale==1);tick(AF_DIARY_A);
    assert(screen.menu.state==AF_DIARY_PRIVACY);settle(AF_DIARY_VIEW_PROMPT);
    for(int i=0;i<3;i++)tick(0);
}
int main(void) {
    memset(widths,6,256);widths['i']=2;widths['W']=10;af_diary_reset(&live);
    P(sub,0x2C,ovl);af_diary_hboard_init(sub);af_diary_hboard_proc(sub);af_diary_hboard_destruct(sub);
    assert(old_init==1 && old_proc==1 && old_destruct==1);
    begin(2,2);edit();command=8;code='W';tick(0);command=8;code='i';tick(0);
    assert(screen.menu.draft.length==2);done();assert(!capacity_calls);
    /* The same A that reveals the answers must not also accept Yes. */
    tick(AF_DIARY_A);assert(screen.menu.state==AF_DIARY_CONFIRM && screen.answers);
    tick(AF_DIARY_B);assert(screen.menu.state==AF_DIARY_EDIT);settle(AF_DIARY_VIEW_EDITOR);
    tick(0);tick(0);assert(editor.index==2 && screen.menu.draft.text[1]=='i');
    done();finish();capacity_ok=0;tick(AF_DIARY_A);
    assert(screen.menu.state==AF_DIARY_ERROR && screen.menu.error==AF_DIARY_CAPACITY);
    assert(af_diary_page(&live,2,2,8)[0]==' ' && screen.menu.draft.text[0]=='W');
    settle(AF_DIARY_VIEW_PROMPT);for(int i=0;i<3;i++)tick(0);
    tick(AF_DIARY_A);settle(AF_DIARY_VIEW_EDITOR);tick(0);tick(0);
    assert(editor.index==2);done();finish();capacity_ok=1;tick(AF_DIARY_RIGHT);tick(AF_DIARY_A);
    assert(screen.menu.state==AF_DIARY_DAY && af_diary_page(&live,2,2,8)[0]=='W');
    settle(AF_DIARY_VIEW_CALENDAR);tick(AF_DIARY_B);tick(AF_DIARY_B);tick(0);tick(0);
    assert(ended==1 && !screen.magic && !screen.editor.magic && !af_diary_screen_owned(sub));
    assert(old_init==1 && old_proc==1 && old_destruct==2);
    assert(cal_draws && page_draws && prompt_draws && base_moves && base_draws);
    /* Another player cannot enter the editor, including after a locked warning. */
    begin(0,2);assert(screen.menu.state==AF_DIARY_WARNING);settle(AF_DIARY_VIEW_PROMPT);
    for(int i=0;i<3;i++)tick(0);
    unsigned int previous_pages=page_draws;
    tick(AF_DIARY_B);settle(AF_DIARY_VIEW_CALENDAR);assert(page_draws==previous_pages);
    assert(af_diary_lock(&live,2,2,0)==AF_DIARY_OK);tick(AF_DIARY_A);settle(AF_DIARY_VIEW_READ);
    assert(screen.menu.draft.readonly);tick(AF_DIARY_A);settle(AF_DIARY_VIEW_CALENDAR);
    assert(!opening && W(sub,8)==2 && screen.menu.state==AF_DIARY_DAY);
    /* A damaged diary session must close, not fall through into writing the
     * house message belonging to the numerically matching resident. */
    screen.magic=0;af_diary_hboard_init(sub);af_diary_hboard_proc(sub);tick(0);
    assert(ended==2 && old_init==1 && old_proc==1);
    puts("diary screen: native ownership contracts, child return, first-A, Rewrite, rejection, commit, read-only and cleanup pass");
    return 0;
}
