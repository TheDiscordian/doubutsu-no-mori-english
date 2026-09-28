#ifndef AF_V3_DIARY_SCREEN_H
#define AF_V3_DIARY_SCREEN_H
#include "diary_editor.h"
#include "diary_draw.h"

enum {
    AF_DIARY_SCREEN_MAGIC=0x41464459, AF_DIARY_HBOARD=2, AF_DIARY_KEYBOARD=10,
    AF_DIARY_VIEW_CALENDAR, AF_DIARY_VIEW_PAGE_IN, AF_DIARY_VIEW_READ,
    AF_DIARY_VIEW_TO_EDITOR, AF_DIARY_VIEW_EDITOR, AF_DIARY_VIEW_TO_CONFIRM,
    AF_DIARY_VIEW_PROMPT, AF_DIARY_VIEW_PROMPT_OUT, AF_DIARY_VIEW_PAGE_OUT
};
/* One resident owner for the existing HBOARD slot. No saved record or native
 * menu table grows. The real date/event provider must fill the selected event,
 * attendance, and all day types; a missing provider is not an empty calendar. */
typedef struct {
    unsigned int magic;
    void *submenu;
    AFDiaryMenu menu;
    AFDiaryMenuAccess access;
    AFDiaryEditorSession editor;
    AFDiaryDates dates;
    AFDiaryDraw draw;
    int (*calendar)(void *,const AFDiaryMenu *,AFDiaryDraw *);
    unsigned short phase,shown_state,pending_state,clock;
    unsigned short editor_requested,edited,page_visible,repeat_button,repeat_wait,repeat_fast;
    unsigned short scroll_mode,hint_tick;
    float page_x,page_y,page_speed,slide_speed,hint_y,prompt_scale,answer_scale;
    unsigned int answers;
    int fault;
} AFDiaryScreen;

int af_diary_screen_open(AFDiaryScreen *,void *submenu,const AFDiaryMenuAccess *,
    unsigned int viewer,unsigned int owner,AFDiaryDate,AFDiaryDates,const void *art,
    int (*calendar)(void *,const AFDiaryMenu *,AFDiaryDraw *));
AFDiaryScreen *af_diary_screen_owned(void *);
int af_diary_screen_init(void *);
int af_diary_screen_set_proc(void *);
void af_diary_screen_move(void *);
void af_diary_screen_draw(void *,void *);
void af_diary_screen_destruct(void *);

/* The installer binds these to the existing native functions. */
extern void af_diary_submenu_open(void *,int,int,int,void *,void *);
extern unsigned short af_diary_screen_trigger(void),af_diary_screen_button(void);
extern int af_diary_screen_y(void);
extern void af_diary_screen_sound(unsigned int);
#ifndef __mips__
extern void *af_diary_screen_test_pointer(void *,unsigned int);
extern void af_diary_screen_test_set_pointer(void *,unsigned int,void *);
#endif
#endif
