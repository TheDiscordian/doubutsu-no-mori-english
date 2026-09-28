#ifndef AF_V3_DIARY_EVENTS_H
#define AF_V3_DIARY_EVENTS_H
#include "diary_draw.h"
enum {AF_DIARY_EVENT_MAX=6,AF_DIARY_EVENT_BIRTHDAY=19,AF_DIARY_EVENT_COUNT=20};
/* These source-bound rules describe calendar events, not every actor, weather,
 * rumour, or crowd spawned by the event scheduler. The native master supplies
 * the actual dates. Each event appears once even if it has several actors. */
typedef struct {unsigned char row,type,single,reserved;} AFDiaryEventRule;
typedef struct {const unsigned char *text;unsigned int size;} AFDiaryEventLabel;
typedef struct {
    unsigned short year;
    unsigned char month,birthday_month,birthday_day,valid;
    unsigned char counts[31],events[31][AF_DIARY_EVENT_MAX];
} AFDiaryEventMonth;
extern const AFDiaryEventRule af_diary_event_rules[AF_DIARY_EVENT_BIRTHDAY];
extern const AFDiaryEventLabel af_diary_event_labels[AF_DIARY_EVENT_COUNT];
extern const unsigned int af_diary_event_master[81][3];
/* Actual native conversion, with the year passed explicitly. Never temporarily
 * change the live clock to browse a calendar. */
extern int af_diary_native_lunar(AFDiaryDate *,const AFDiaryDate *);
int af_diary_events_month(AFDiaryEventMonth *,unsigned int year,unsigned int month,
    unsigned int birthday_month,unsigned int birthday_day);
int af_diary_events_draw(const AFDiaryEventMonth *,const AFDiaryMenu *,
    const AFDiary *,AFDiaryDraw *);
#endif
