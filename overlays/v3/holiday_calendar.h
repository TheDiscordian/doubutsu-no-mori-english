#ifndef AF_V3_HOLIDAY_CALENDAR_H
#define AF_V3_HOLIDAY_CALENDAR_H
#include "holiday_native.h"
#include "diary_events.h"
enum {AF_HCAL_ORIGINAL=0,AF_HCAL_N64=1,AF_HCAL_GC=2};
/* One choice controls corresponding native events and imported owners. New
 * GC-only holidays supplement either calendar; N64-only events remain intact. */
extern const unsigned int af_holiday_calendar_choice;
extern const unsigned char af_holiday_calendar_native_sources[81][12];
extern const unsigned char af_holiday_calendar_donor_rows[49];
unsigned int af_holiday_calendar_mode(void);
int af_holiday_calendar_dates(const AFDiary *,unsigned int,AFDiaryDates *);
int af_holiday_calendar_clock(AFDiaryDate,AFHolidayClock *);
void *af_holiday_calendar_copy(void *,const void *,unsigned int);
int af_holiday_calendar_schedule(const AFHolidayClock *);
int af_holiday_calendar_status(int,int);
int af_holiday_calendar_today(int);
int af_holiday_calendar_run_today(int);
int af_holiday_calendar_owner_today(int);
int af_holiday_diary_month(AFDiaryEventMonth *,unsigned int,unsigned int,unsigned int,unsigned int);
int af_holiday_diary_draw(const AFDiaryEventMonth *,const AFDiaryMenu *,const AFDiary *,AFDiaryDraw *);
int af_holiday_diary_dates(AFDiaryDate,AFDiaryDates *);
#endif
