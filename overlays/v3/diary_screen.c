/* Native HBOARD ownership with the GAFE01 diary transition sequence. The
 * existing editor is a real child menu: its saved pre-move/pre-draw callbacks
 * keep the paper alive, and native return restores this owner. */
#include "diary_screen.h"
const unsigned int af_diary_screen_bytes=sizeof(AFDiaryScreen);
typedef char diary_screen_reservation[(sizeof(AFDiaryScreen)<=0xFF0)?1:-1];
#define W(p,o) (*(unsigned int *)((unsigned char *)(p)+(o)))
#define F(p,o) (*(float *)((unsigned char *)(p)+(o)))
static void *ptr(void *p,unsigned int at) {
#ifdef __mips__
    return *(void **)((unsigned char *)p+at);
#else
    return af_diary_screen_test_pointer(p,at);
#endif
}
static void put(void *p,unsigned int at,void *value) {
#ifdef __mips__
    *(void **)((unsigned char *)p+at)=value;
#else
    af_diary_screen_test_set_pointer(p,at,value);
#endif
}
static unsigned char *overlay(void *sub) {return sub?ptr(sub,0x2C):0;}
static void *info(void *sub) {unsigned char *o=overlay(sub);return o?o+0x10118:0;}
static float absolute(float x) {return x<0?-x:x;}
static void copy(void *target,const void *source,unsigned int size) {
    volatile unsigned char *d=target;const unsigned char *s=source;
    for(unsigned int i=0;i<size;i++)d[i]=s[i];
}
static int approach(float *x,float target,float speed) {
    if(absolute(target-*x)<=speed) {*x=target;return 1;}
    *x+=target>*x?speed:-speed;return 0;
}
static int resident(const AFDiaryScreen *s) {
#ifdef __mips__
    if((unsigned int)s<0x806A0000 || (unsigned int)s>0x807DA800-sizeof(*s) ||
        (unsigned int)s&3)return 0;
#endif
    return s && s->magic==AF_DIARY_SCREEN_MAGIC;
}
AFDiaryScreen *af_diary_screen_owned(void *sub) {
    void *m=info(sub);
    if(!m || W(m,0x38)!=AF_DIARY_SCREEN_MAGIC)return 0;
    AFDiaryScreen *s=ptr(m,0x40);
    if(!resident(s) || s->submenu!=sub || W(m,0x3C)!=s->menu.owner)return 0;
    return s;
}
static int refresh(AFDiaryScreen *s) {
    s->draw.event_length=0;s->draw.event_label=0;s->draw.event_attended=0;
    int result=s->calendar(s->access.context,&s->menu,&s->draw);
    if(result!=AF_DIARY_OK) {s->fault=result<0?result:AF_DIARY_ARGUMENT;return 0;}
    if(s->draw.event_length>48 || (s->draw.event_length && !s->draw.event_label)) {
        s->fault=AF_DIARY_ARGUMENT;return 0;
    }
    for(unsigned int i=0;i<37;i++)if(s->draw.day_types[i]>4) {
        s->fault=AF_DIARY_ARGUMENT;return 0;
    }
    return 1;
}
int af_diary_screen_open(AFDiaryScreen *s,void *sub,const AFDiaryMenuAccess *a,
    unsigned int viewer,unsigned int owner,AFDiaryDate today,AFDiaryDates dates,
    const void *art,int (*calendar)(void *,const AFDiaryMenu *,AFDiaryDraw *)) {
    if(!s || !sub || !a || !a->live || !a->scratch || !a->widths || !a->capacity ||
        !a->event_count || !art || !calendar || viewer>=4 || owner>=4 || W(sub,4))return 0;
    /* Only a closed native submenu can acquire this resident draft. */
    volatile unsigned char *p=(volatile unsigned char *)s;
    for(unsigned int i=0;i<sizeof(*s);i++)p[i]=0;
    s->submenu=sub;copy(&s->access,a,sizeof(*a));s->dates=dates;s->calendar=calendar;
    if(af_diary_menu_open(&s->menu,&s->access,viewer,owner,today,dates)!=AF_DIARY_OK)return 0;
    s->draw.art=art;s->draw.scale=1;s->draw.alpha=255;
    if(!refresh(s))return 0;
    s->magic=AF_DIARY_SCREEN_MAGIC;s->phase=AF_DIARY_VIEW_CALENDAR;
    s->shown_state=s->menu.state;
    s->editor=(AFDiaryEditorSession){AF_DIARY_SESSION_MAGIC,sub,&s->menu,&s->access};
    af_diary_submenu_open(sub,AF_DIARY_HBOARD,AF_DIARY_SCREEN_MAGIC,owner,s,0);
    if(W(sub,4)!=AF_DIARY_HBOARD) {s->editor.magic=0;s->magic=0;return 0;}
    return 1;
}
int af_diary_screen_init(void *sub) {
    void *m=info(sub);unsigned char *o=overlay(sub);
    if(!m || W(m,0x38)!=AF_DIARY_SCREEN_MAGIC)return 0;
    AFDiaryScreen *s=af_diary_screen_owned(sub);
    if(!s) {W(m,4)=W(m,0x30)=4;return 1;}
    W(m,4)=0;W(m,0x30)=1;W(m,0x34)=5; /* native MOVE -> PLAY, IN_TOP */
    F(m,0x18)=0;F(m,0x1C)=300;F(m,0x20)=0;F(m,0x24)=75;
    W(o,0x106A0)=0;
    return 1;
}
int af_diary_screen_set_proc(void *sub) {
    void *m=info(sub);if(!m || W(m,0x38)!=AF_DIARY_SCREEN_MAGIC)return 0;
    unsigned char *o=overlay(sub);
    put(o,0x10670,af_diary_screen_move);put(o,0x10674,af_diary_screen_draw);
    return 1;
}
void af_diary_screen_destruct(void *sub) {
    AFDiaryScreen *s=af_diary_screen_owned(sub);if(!s)return;
    /* The native owner destroys its children first. Never retain their pointer
     * fields or a session that could be accepted by another keyboard opening. */
    s->editor.magic=0;s->editor.submenu=0;s->editor_requested=0;
    s->magic=0;s->submenu=0;s->menu.state=AF_DIARY_CLOSED;
    put(info(sub),0x40,0);
}
static void sound(int result,unsigned int old,const AFDiaryScreen *s) {
    if(result<0)af_diary_screen_sound(0x1003);
    else if(result>0)af_diary_screen_sound(old!=s->menu.state?0x105F:0x1035);
}
static int paper_scroll(AFDiaryScreen *s,float target,float limit) {
    float distance=absolute(target-s->page_y);
    if(distance<0.1f) {s->page_y=target;s->page_speed=0;return 1;}
    if(s->page_speed==0)s->page_speed=1;
    if(s->scroll_mode)s->page_speed=s->scroll_mode==2?16.0f/7.0f:16.0f/3.0f;
    else if(distance>9) {s->page_speed*=2;if(s->page_speed>limit)s->page_speed=limit;}
    else if(distance<7) {s->page_speed*=0.5f;if(s->page_speed<1)s->page_speed=1;}
    if(approach(&s->page_y,target,s->page_speed)) {s->page_speed=0;return 1;}
    return 0;
}
static unsigned int cursor_row(AFDiaryScreen *s) {
    AFDiaryLayout layout;
    int result=af_diary_layout(s->menu.draft.text,s->menu.draft.length,
        s->menu.draft.cursor,s->access.widths,&layout);
    if(result!=AF_DIARY_OK) {s->fault=result;return 0;}
    return layout.cursor.row;
}
static void prompt(AFDiaryScreen *s) {
    s->phase=AF_DIARY_VIEW_PROMPT;s->shown_state=s->menu.state;
    s->prompt_scale=s->menu.state==AF_DIARY_CONFIRM?1:0;
    s->answers=0;s->answer_scale=0;s->clock=0;
}
static void transition(AFDiaryScreen *s,unsigned int old) {
    if(old==s->menu.state)return;
    switch(s->menu.state) {
    case AF_DIARY_READ:
        s->page_x=-300;s->slide_speed=75;s->page_y=0;s->page_speed=0;
        s->hint_y=0;s->hint_tick=0;s->edited=0;s->phase=AF_DIARY_VIEW_PAGE_IN;
        s->page_visible=1;s->shown_state=AF_DIARY_READ;
        break;
    case AF_DIARY_EDIT:
        s->phase=AF_DIARY_VIEW_TO_EDITOR;s->scroll_mode=0;s->page_speed=0;
        break;
    case AF_DIARY_CONFIRM:
        s->phase=AF_DIARY_VIEW_TO_CONFIRM;s->scroll_mode=0;s->page_speed=0;
        break;
    case AF_DIARY_WARNING: case AF_DIARY_ERROR: case AF_DIARY_PRIVACY:
        if(s->menu.state==AF_DIARY_ERROR && s->editor_requested) {
            unsigned char *o=overlay(s->submenu);void *ed=o+0x10358;
            if(W(ed,0x38)==AF_DIARY_EDITOR_MODE && W(ed,0x30)!=4)
                ((void (*)(void *,unsigned int))ptr(o,0x106B0))(ed,6);
        }
        prompt(s);break;
    case AF_DIARY_DAY:
        if(old==AF_DIARY_READ || old==AF_DIARY_PRIVACY ||
           (old==AF_DIARY_ERROR && s->edited)) {
            s->phase=AF_DIARY_VIEW_PAGE_OUT;s->slide_speed=1;
        } else s->phase=AF_DIARY_VIEW_CALENDAR;
        break;
    default:break;
    }
}
static int active_child(AFDiaryScreen *s) {
    void *sub=s->submenu,*m=info(sub);
    return W(sub,4)==AF_DIARY_KEYBOARD || W(sub,8)==AF_DIARY_KEYBOARD || W(m,0x14);
}
static void open_editor(AFDiaryScreen *s) {
    if(s->editor_requested || active_child(s))return;
    s->editor.magic=AF_DIARY_SESSION_MAGIC;
    s->editor_requested=1;s->edited=1;
    af_diary_submenu_open(s->submenu,AF_DIARY_KEYBOARD,AF_DIARY_EDITOR_MODE,
        AF_DIARY_PAGE,s->menu.draft.text,&s->editor);
    if(W(s->submenu,4)!=AF_DIARY_KEYBOARD) {
        s->editor_requested=0;s->menu.error=AF_DIARY_ARGUMENT;s->menu.state=AF_DIARY_ERROR;
        prompt(s);return;
    }
    s->phase=AF_DIARY_VIEW_EDITOR;
}
static int read_command(AFDiaryScreen *s,unsigned int trigger) {
    int direction=af_diary_screen_y();unsigned int button=af_diary_screen_button();
    unsigned int held=direction>32 || (button&0x800)?1:direction<-32 || (button&0x400)?2:0;
    if(!held) {
        s->repeat_button=0;s->repeat_wait=s->repeat_fast=0;
        if(s->page_speed!=0)return 0;
        if(trigger&(AF_DIARY_UP|AF_DIARY_DOWN)) {s->scroll_mode=1;return trigger&AF_DIARY_UP?-10:10;}
        return 0;
    }
    if(held!=s->repeat_button) {
        s->repeat_button=held;s->repeat_wait=30;s->repeat_fast=26;
        if(s->page_speed!=0)return 0;
        s->scroll_mode=0;return held==1?-1:1;
    }
    if(s->repeat_wait) {s->repeat_wait--;return 0;}
    if(s->repeat_fast)s->repeat_fast--;
    if(s->page_speed!=0)return 0;
    s->scroll_mode=s->repeat_fast?2:3;
    return held==1?-1:1;
}
static void frame(AFDiaryScreen *s,unsigned int trigger,unsigned int native_trigger) {
    unsigned int old=s->menu.state;int result=AF_DIARY_UNCHANGED;
    switch(s->phase) {
    case AF_DIARY_VIEW_CALENDAR:
        result=af_diary_menu_input(&s->menu,&s->access,native_trigger,
            (native_trigger&AF_DIARY_LEFT)?-1:(native_trigger&AF_DIARY_RIGHT)?1:0,0);
        if(result!=AF_DIARY_UNCHANGED)refresh(s);
        transition(s,old);sound(result,old,s);break;
    case AF_DIARY_VIEW_PAGE_IN:
        if(s->page_x>-120) {s->slide_speed*=0.5f;if(s->slide_speed<1)s->slide_speed=1;}
        if(approach(&s->page_x,0,s->slide_speed))s->phase=AF_DIARY_VIEW_READ;
        break;
    case AF_DIARY_VIEW_READ: {
        int command=read_command(s,trigger);
        result=af_diary_menu_input(&s->menu,&s->access,trigger,0,command);
        paper_scroll(s,s->menu.draft.scroll*16,8);
        transition(s,old);sound(result,old,s);break;
    }
    case AF_DIARY_VIEW_TO_EDITOR: {
        int ready=paper_scroll(s,cursor_row(s)*16,8);
        if(!s->edited) {
            s->hint_y=-0.6f*s->hint_tick*s->hint_tick;
            if(s->hint_y<=-100)s->hint_y=-100;else s->hint_tick++;
        }
        if(ready && (s->edited || s->hint_y==-100))open_editor(s);
        break;
    }
    case AF_DIARY_VIEW_EDITOR:
        if(s->menu.state!=AF_DIARY_EDIT) {transition(s,AF_DIARY_EDIT);break;}
        paper_scroll(s,cursor_row(s)*16,2);break;
    case AF_DIARY_VIEW_TO_CONFIRM:
        if(paper_scroll(s,s->menu.draft.scroll*16,8) && !active_child(s)) {
            s->editor_requested=0;prompt(s);
        }
        break;
    case AF_DIARY_VIEW_PROMPT:
        if(active_child(s))break;
        if(s->prompt_scale<1) {approach(&s->prompt_scale,1,0.2f);break;}
        if(s->menu.state==AF_DIARY_CONFIRM) {
            if(trigger&AF_DIARY_B) { /* Rewrite is available before answers. */ }
            else if(!s->answers) {
                if(trigger&(AF_DIARY_A|AF_DIARY_START)) {s->answers=1;af_diary_screen_sound(0x105F);}
                break;
            } else if(s->answer_scale<1) {approach(&s->answer_scale,1,0.2f);break;}
        }
        result=af_diary_menu_input(&s->menu,&s->access,trigger|native_trigger,0,0);
        if(old!=s->menu.state) {
            s->pending_state=s->menu.state;s->phase=AF_DIARY_VIEW_PROMPT_OUT;
            /* Keep the exiting prompt's state for drawing without delaying the
             * atomic commit or temporarily changing the live controller. */
        }
        sound(result,old,s);break;
    case AF_DIARY_VIEW_PROMPT_OUT:
        if(approach(&s->prompt_scale,0,0.2f)) {
            if(s->shown_state==AF_DIARY_CONFIRM && s->menu.state==AF_DIARY_EDIT)s->editor_requested=0;
            transition(s,s->shown_state);refresh(s);
        }
        break;
    case AF_DIARY_VIEW_PAGE_OUT:
        s->slide_speed*=2;if(s->slide_speed>75)s->slide_speed=75;
        if(approach(&s->page_x,-300,s->slide_speed)) {
            s->phase=AF_DIARY_VIEW_CALENDAR;s->edited=0;s->page_visible=0;
        }
        break;
    default:s->fault=AF_DIARY_ARGUMENT;break;
    }
}
void af_diary_screen_move(void *sub) {
    void *m=info(sub);unsigned char *o=overlay(sub);
    AFDiaryScreen *s=af_diary_screen_owned(sub);
    if(!s) {
        if(m && W(m,0x38)==AF_DIARY_SCREEN_MAGIC)
            ((void (*)(void *,void *))ptr(o,0x106AC))(sub,m);
        return;
    }
    void (*before)(void *)=ptr(m,0xC);
    if(before && before!=af_diary_screen_move)before(sub);
    if(W(m,4)==0) {
        ((void (*)(void *,void *))ptr(o,0x106A8))(sub,m);return;
    }
    if(W(m,4)==4) {
        ((void (*)(void *,void *))ptr(o,0x106AC))(sub,m);return;
    }
    unsigned int trigger=af_diary_screen_trigger(),native_trigger=W(o,0x1068C);
    /* The native child owns all buttons, even while sliding in/out. */
    if(active_child(s))trigger=native_trigger=0;
    /* Source transitions run at 60 Hz; the N64 menu advances twice per 30 Hz
     * update. An A press is consumed once, never twice by adjacent states. */
    frame(s,trigger,native_trigger);
    frame(s,0,0);
    s->clock=(s->clock+2)%60;
    s->draw.alpha=s->clock<30?s->clock*255/30:(60-s->clock)*255/30;
    s->draw.arrow_x=(s->clock<30?s->clock:60-s->clock)*0.1f;
    if(s->fault && active_child(s)) {
        void *ed=o+0x10358;
        if(W(ed,0x30)!=4)((void (*)(void *,unsigned int))ptr(o,0x106B0))(ed,6);
    } else if(s->fault || s->menu.state==AF_DIARY_CLOSED) {
        ((void (*)(void *,unsigned int))ptr(o,0x106B0))(m,4);
    }
}
void af_diary_screen_draw(void *sub,void *game) {
    AFDiaryScreen *s=af_diary_screen_owned(sub);if(!s || !game)return;
    void *m=info(sub);void (*before)(void *,void *)=ptr(m,0x10);
    if(before && before!=af_diary_screen_draw)before(sub,game);
    AFDiaryDraw d;copy(&d,&s->draw,sizeof(d));
    d.x=F(m,0x18);d.y=F(m,0x1C);d.scale=1;d.answer_scale=1;
    int result=af_diary_draw_calendar(sub,game,&s->menu,s->access.live,s->dates,&d);
    if(result<0) {s->fault=result;return;}
    if(s->phase==AF_DIARY_VIEW_CALENDAR)return;
    if(s->page_visible) {
        d.x=s->page_x;d.y=s->page_y;
        d.read_controls=s->phase==AF_DIARY_VIEW_READ || s->phase==AF_DIARY_VIEW_PAGE_IN ||
            (s->phase==AF_DIARY_VIEW_TO_EDITOR && !s->edited);
        d.control_y=s->hint_y;
        d.editing=s->phase==AF_DIARY_VIEW_EDITOR && s->menu.state==AF_DIARY_EDIT;
        result=af_diary_draw_page(sub,game,&s->menu,s->access.widths,&d);
        if(result<0) {s->fault=result;return;}
    }
    if(s->phase==AF_DIARY_VIEW_PROMPT || s->phase==AF_DIARY_VIEW_PROMPT_OUT) {
        /* No 2 KiB menu copy on the native thread stack just for an exiting
         * prompt. Draw functions take the display state independently. */
        d.x=d.y=0;d.scale=s->prompt_scale;d.answer_scale=s->answer_scale*s->prompt_scale;
        d.answers_visible=s->answers;d.prompt_state=s->shown_state;
        result=af_diary_draw_prompt(sub,game,&s->menu,&d);
        if(result<0)s->fault=result;
    }
}
