#ifndef AF_V3_HOLIDAY_NATIVE_H
#define AF_V3_HOLIDAY_NATIVE_H
#include "holiday_events.h"

enum { AF_HN_DAYS=64, AF_HN_REFERENCES=80, AF_HN_FIRST=71, AF_HN_END=115 };
/* Native event rows have a different layout from AFHolidayDay. */
typedef struct {
    unsigned int type,hours;
    unsigned short begin,end,status,reserved;
} AFHolidayNativeDay;
extern AFHolidayNativeDay af_holiday_native_days[AF_HN_DAYS];
extern unsigned char af_holiday_native_index[128];
extern unsigned int af_holiday_native_count;
extern const unsigned char af_holiday_native_ids[128],af_holiday_source_ids[128];
extern const unsigned char af_holiday_event_data[812];
extern void af_holiday_native_death(int,void *);

/* Native 0..69 and camper 70 are never donor IDs. */
int af_holiday_native_type(unsigned int donor);
/* Called between native daily reset and cleanup. Validate the whole insertion
 * before writing anything. ACTIVE is deliberately left to the native hourly/
 * acre update; planning cannot manufacture RUN, SHOW, or attendance. */
int af_holiday_native_merge(const AFHolidayDay *,unsigned int);
int af_holiday_native_schedule(const AFHolidayClock *);
int af_holiday_native_snapshot(AFHolidayDay *,unsigned int capacity);
unsigned int af_holiday_native_current(void);
unsigned int af_holiday_native_field(void);
/* The caller owns the special New Year Miko deletion (-2). */
int af_holiday_native_cleanup(void);
int af_holiday_native_notify(unsigned int donor,void *actor);
#endif
