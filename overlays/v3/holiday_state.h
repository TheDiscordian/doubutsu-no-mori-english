#ifndef AF_V3_HOLIDAY_STATE_H
#define AF_V3_HOLIDAY_STATE_H
#include "holiday_events.h"
#include "holiday_npc.h"
enum { AF_HOLIDAY_DAY_ZERO=0,AF_HOLIDAY_WEEK=1,AF_HOLIDAY_AFTER=2,AF_HOLIDAY_NONE=3 };
/* Serialized AFDY-v2 header: town day 6; lighthouse year 8/9, month 10,
 * day 11, daily lights 12, started/contributed players 13, completed 14.
 * Bytes 7/15 stay zero. All four diary page/calendar records retain offsets. */
int af_holiday_state_init(AFDiary *,unsigned int random_thirty);
int af_holiday_state_period(const AFDiary *,AFDiaryDate);
int af_holiday_state_day(const AFDiary *,AFDiaryDate);
int af_holiday_state_available(AFDiary *,AFDiaryDate);
int af_holiday_state_after(const AFDiary *,AFDiaryDate);
int af_holiday_state_start(AFDiary *,AFDiaryDate,unsigned int player);
int af_holiday_state_check(const AFDiary *,AFDiaryDate,unsigned int player);
int af_holiday_state_complete(AFDiary *,AFDiaryDate,unsigned int player);
int af_holiday_state_switch_check(const AFDiary *,AFDiaryDate,unsigned int hour);
int af_holiday_state_enter(const AFDiary *,AFDiaryDate,unsigned int hour,unsigned int player,int working);
int af_holiday_state_switch_on(AFDiary *,AFDiaryDate,unsigned int player);
int af_holiday_state_dates(const AFDiary *,unsigned int year,AFDiaryDates *);
int af_holiday_state_clock(AFDiary *,const unsigned char rtc[8],unsigned int working,AFHolidayClock *);
/* Called inside the native non-working-player gate, before old-event cleanup.
 * The complete actor selection stays off until all required owners are bound. */
int af_holiday_calendar_update(void);
int af_holiday_calendar_before_cleanup(void);
extern int af_holiday_calendar_previous(void);
extern const unsigned char af_holiday_harvest_days[58];
extern int af_holiday_state_lunar(AFDiaryDate *,const AFDiaryDate *);
extern float af_holiday_random_native(void);
#endif
