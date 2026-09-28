#ifndef AF_V3_DIARY_DRAW_H
#define AF_V3_DIARY_DRAW_H
#include "diary_menu.h"
/* The native owner supplies animation positions and actual native event data.
 * Source day types/attendance are not inferred from English event labels. */
typedef struct {
    const void *art;
    float x,y,scale,answer_scale,arrow_x;
    unsigned int alpha,answers_visible,event_attended;
    unsigned int editing,read_controls,prompt_state;
    float control_y;
    int stick_direction;
    const unsigned char *event_label;
    unsigned int event_length;
    unsigned char day_types[37];
} AFDiaryDraw;
int af_diary_draw_calendar(void *,void *,const AFDiaryMenu *,const AFDiary *,AFDiaryDates,const AFDiaryDraw *);
int af_diary_draw_page(void *,void *,const AFDiaryMenu *,const unsigned char *,const AFDiaryDraw *);
int af_diary_draw_prompt(void *,void *,const AFDiaryMenu *,const AFDiaryDraw *);
#endif
