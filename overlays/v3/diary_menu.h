#ifndef AF_V3_DIARY_MENU_H
#define AF_V3_DIARY_MENU_H
#include "diary.h"

enum {
    AF_DIARY_CLOSED, AF_DIARY_MONTH, AF_DIARY_DAY, AF_DIARY_READ,
    AF_DIARY_EDIT, AF_DIARY_CONFIRM, AF_DIARY_PRIVACY, AF_DIARY_WARNING,
    AF_DIARY_ERROR,
    AF_DIARY_A=0x8000, AF_DIARY_B=0x4000, AF_DIARY_START=0x1000,
    AF_DIARY_UP=8, AF_DIARY_DOWN=4, AF_DIARY_LEFT=2, AF_DIARY_RIGHT=1
};
/* The renderer/native adapter owns this transient state. It never goes in a
 * player record and holds no pointer into a relocatable overlay. */
typedef struct {
    AFDiaryDraft draft;
    AFDiaryDate today,selected;
    unsigned short viewer,owner,state,event_index,events,choice;
    short month_delta,error;
} AFDiaryMenu;
typedef struct {
    AFDiary *live,*scratch;
    const af_diary_u8 *widths;
    AFDiaryCapacity capacity;
    void *context;
    /* Calendar events must come from the actual native event schedule. */
    unsigned int (*event_count)(void *,AFDiaryDate,unsigned int owner);
} AFDiaryMenuAccess;

int af_diary_menu_open(AFDiaryMenu *,const AFDiaryMenuAccess *,unsigned int viewer,
    unsigned int owner,AFDiaryDate today,AFDiaryDates);
/* repeat_x is the native menu's debounced -1/0/+1 horizontal stick command.
 * scroll is the source reading scroll command, including ten-line jumps. */
int af_diary_menu_input(AFDiaryMenu *,const AFDiaryMenuAccess *,unsigned int trigger,
    int repeat_x,int scroll);
int af_diary_menu_edit(AFDiaryMenu *,const AFDiaryMenuAccess *,unsigned int command,int code);
int af_diary_menu_grid(const AFDiaryMenu *,const AFDiary *,AFDiaryDates,
    af_diary_u8 days[37],af_diary_u8 marks[37]);
#endif
