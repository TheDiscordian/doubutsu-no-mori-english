#ifndef AF_V3_DIARY_NATIVE_H
#define AF_V3_DIARY_NATIVE_H
#include "diary_events.h"
#include "diary_screen.h"
typedef struct {
    AFDiary *live;
    AFDiaryEventMonth calendar;
    unsigned char widths[256];
    int calendar_error;
} AFDiaryNative;
extern AFDiaryNative af_diary_native_context;
extern AFDiaryScreen af_diary_native_screen;
extern AFDiary af_diary_native_candidate;
extern unsigned int af_diary_native_candidate_guard[4];
extern const unsigned char af_diary_native_art[];
extern const unsigned char af_diary_native_rtc[8],af_diary_native_player;
extern const unsigned char af_diary_native_players[4][0xBD0];
extern const unsigned char af_diary_native_profiles[][80];
extern AFDiary *af_v3_diary_data(void);
extern int af_v3_diary_preflight(const AFDiary *);
extern int af_diary_native_width(unsigned int,int);
extern int af_diary_native_live_check(int);
unsigned short af_diary_native_selected(void);
int af_diary_native_open(void *game,int owner);
int af_diary_native_visit(void);
int af_diary_native_live_player(int);
/* Call only from a confirmed player participation path, with the native event
 * ID. Native IDs must never index the donor's different special-event bitset. */
int af_diary_native_attend(unsigned int native_event);
#endif
