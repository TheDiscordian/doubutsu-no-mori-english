#ifndef AF_V3_HOLIDAY_EVENTS_H
#define AF_V3_HOLIDAY_EVENTS_H
#include "diary.h"

enum {
    AF_HE_ACTIVE=1, AF_HE_STOP=2, AF_HE_SHOW=4, AF_HE_RUN=16,
    AF_HE_ERROR=32, AF_HE_EXIST=128, AF_HE_CAPACITY=48,
    AF_HE_NONE=0, AF_HE_SHRINE=1, AF_HE_WANDER=2,
    AF_HE_HALLOWEEN=3, AF_HE_DEDICATED=4,
    AF_HE_START=0, AF_HE_END=1, AF_HE_ENTER=2, AF_HE_LEAVE=3, AF_HE_BEHIND=4
};
typedef struct {
    AFDiaryDate date;
    AFDiaryDates special;
    unsigned int hour,working,vernal_day,autumnal_day;
    /* The actual lighthouse state decides this value, not the calendar. */
    unsigned int vacation_available;
} AFHolidayClock;
typedef struct {
    unsigned int hours;
    unsigned short begin,end,type,status;
} AFHolidayDay;
typedef struct {
    unsigned int type,kind,callbacks;
} AFHolidayOwner;
typedef struct {
    void *context;
    /* A dedicated owner must have all declared callbacks bound. A null donor
     * callback is not a failed implementation and is not invoked. */
    int (*dispatch)(void *,unsigned int type,unsigned int phase);
    int (*keep)(void *,unsigned int type);
    void (*set_keep)(void *,unsigned int type,int);
    /* Positive: retained placement. Zero: outside the field, without ERROR.
     * Negative: the actual search/reservation sets the event's ERROR state. */
    int (*place)(void *,unsigned int type,unsigned int kind,unsigned int id,int adjust);
    /* 0 failure; 1 appeared; 2 not in the entering acre. */
    int (*show)(void *,unsigned int type,unsigned int id);
    int (*cull)(void *,unsigned int type);
    void (*wandering_place)(void *,int present);
} AFHolidayOwnerOps;

/* Produce the complete source-ordered daily directory transactionally.
 * No active hour implies RUN/SHOW, and scheduling never marks attendance.
 * Output remains untouched for malformed input or insufficient capacity. */
int af_holiday_event_plan(const unsigned char *,unsigned int,const AFHolidayClock *,
    AFHolidayDay *,unsigned int capacity);
/* Same daily planner, with resolved start/end dates for selected source rows.
 * Zero pairs retain the donor rule. Nonzero pairs include the original hour
 * flags in the low byte and Gregorian month/day in the high halfword. */
int af_holiday_event_plan_dates(const unsigned char *,unsigned int,const AFHolidayClock *,
    AFHolidayDay *,unsigned int capacity,const unsigned int dates[49][2]);
/* One resolved range, zero for an unavailable lunar date in the adjacent
 * diary browsing years, or -1 for malformed inputs. */
int af_holiday_event_dates(const AFHolidayClock *,const unsigned char row[12],
    unsigned int dates[2]);
int af_holiday_event_owner(const unsigned char *,unsigned int,unsigned int,AFHolidayOwner *);
unsigned int af_holiday_event_current(const unsigned char *,unsigned int,const AFHolidayDay *,unsigned int);
unsigned int af_holiday_event_field(const AFHolidayDay *,unsigned int);
/* Returns -1 for no notification, -2 for the New Year's Miko owner, or a donor
 * event type. Sports cleanup follows SHOW, not the event's calendar date. */
int af_holiday_event_cleanup(const unsigned char *,unsigned int,const AFHolidayDay *,unsigned int);
int af_holiday_event_clock(AFHolidayDay *,const AFHolidayOwner *,const AFHolidayOwnerOps *);
int af_holiday_event_wade(AFHolidayDay *,const AFHolidayOwner *,const AFHolidayOwnerOps *,
    int skip,int player_wading,int fading);
#endif
