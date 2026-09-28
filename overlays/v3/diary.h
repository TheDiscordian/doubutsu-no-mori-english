#ifndef AF_V3_DIARY_H
#define AF_V3_DIARY_H

/* GAFE01 has one 992-byte page per month/player, shared by all sixteen covers.
 * The serialized bytes are independent of host alignment and endianness. */
enum {
    AF_DIARY_PLAYERS=4, AF_DIARY_MONTHS=12, AF_DIARY_PAGE=992,
    AF_DIARY_CALENDAR=104, AF_DIARY_HEADER=16,
    AF_DIARY_PLAYER=AF_DIARY_CALENDAR+AF_DIARY_MONTHS*AF_DIARY_PAGE,
    AF_DIARY_BYTES=AF_DIARY_HEADER+AF_DIARY_PLAYERS*AF_DIARY_PLAYER,
    AF_DIARY_ROWS=31, AF_DIARY_WIDTH=192, AF_DIARY_VISIBLE=7,
    AF_DIARY_OK=1, AF_DIARY_UNCHANGED=0, AF_DIARY_ARGUMENT=-1,
    AF_DIARY_LOCKED=-2, AF_DIARY_READONLY=-3, AF_DIARY_FULL=-4,
    AF_DIARY_CHANGED=-5, AF_DIARY_CAPACITY=-6
};
typedef unsigned char af_diary_u8;
typedef unsigned int af_diary_u32;
typedef struct { af_diary_u8 bytes[AF_DIARY_BYTES]; } AFDiary;
typedef struct { unsigned short year; af_diary_u8 month,day; } AFDiaryDate;
/* Special dates come from the game's existing date/event calculations. */
typedef struct { af_diary_u8 town_day,harvest_month,harvest_day; } AFDiaryDates;
typedef struct {
    af_diary_u8 text[AF_DIARY_PAGE], original[AF_DIARY_PAGE];
    unsigned short length,cursor,player,month,readonly,scroll;
} AFDiaryDraft;
typedef struct { unsigned short start,length,width; } AFDiaryLine;
typedef struct { unsigned short row,column,x; } AFDiaryPoint;
typedef struct {
    AFDiaryLine lines[AF_DIARY_ROWS];
    AFDiaryPoint cursor,end;
    unsigned short rows;
} AFDiaryLayout;

void af_diary_reset(AFDiary *);
int af_diary_valid(const AFDiary *);
int af_diary_player_clear(AFDiary *,unsigned int player);
int af_diary_lock(AFDiary *,unsigned int viewer,unsigned int owner,int locked);
/* Months are zero-based, matching the donor's actual page consumer. */
const af_diary_u8 *af_diary_page(const AFDiary *,unsigned int viewer,
    unsigned int owner,unsigned int month);
int af_diary_begin(AFDiaryDraft *,const AFDiary *,unsigned int viewer,
    unsigned int owner,unsigned int month,const af_diary_u8 *widths);
int af_diary_layout(const af_diary_u8 *,unsigned int length,unsigned int cursor,
    const af_diary_u8 *widths,AFDiaryLayout *);
/* Same 1..8 command values as the accepted native English keyboard. */
int af_diary_command(AFDiaryDraft *,unsigned int command,int code,
    const af_diary_u8 *widths);
int af_diary_scroll(AFDiaryDraft *,int delta,const af_diary_u8 *widths);
/* The callback measures the COMPLETE candidate town/console/diary save without
 * flash writes. Missing callback, capacity failure, changed source, or invalid
 * layout leaves live data unchanged. Scratch must be disjoint and caller-owned. */
typedef int (*AFDiaryCapacity)(void *,const AFDiary *);
int af_diary_commit(AFDiary *,AFDiaryDraft *,AFDiary *scratch,
    const af_diary_u8 *widths,AFDiaryCapacity,void *);
/* Atomically admit both the edited page and its privacy choice. */
int af_diary_commit_locked(AFDiary *,AFDiaryDraft *,AFDiary *scratch,
    const af_diary_u8 *widths,AFDiaryCapacity,void *,int locked);
unsigned int af_diary_days(unsigned int year,unsigned int month);
int af_diary_weekday(AFDiaryDate);
int af_diary_calendar_refresh(AFDiary *,unsigned int player,AFDiaryDate,AFDiaryDates);
int af_diary_calendar_visit(AFDiary *,unsigned int player,AFDiaryDate,AFDiaryDates);
int af_diary_calendar_event(AFDiary *,unsigned int player,AFDiaryDate,AFDiaryDates,unsigned int event);
/* 0: no mark, 1: played, 2: event attended; only the current twelve-month
 * interval is eligible. This never erases or changes a monthly text page. */
int af_diary_calendar_mark(const AFDiary *,unsigned int player,AFDiaryDate today,
    AFDiaryDate selected,AFDiaryDates);
#endif
