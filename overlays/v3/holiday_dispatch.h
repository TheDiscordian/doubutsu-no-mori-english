#ifndef AF_V3_HOLIDAY_DISPATCH_H
#define AF_V3_HOLIDAY_DISPATCH_H
#include "holiday_dedicated_native.h"
typedef struct { unsigned short kind,source; } AFHolidayNeed;
typedef struct { unsigned short donor,first,count,phases; } AFHolidayNeeds;
/* Generated from all scheduled dedicated owners and their complete layouts. */
extern const AFHolidayNeeds af_holiday_owner_needs[14];
extern const AFHolidayNeed af_holiday_identity_needs[];
extern const unsigned int af_holiday_identity_need_count;
int af_holiday_dedicated_ready(unsigned int,const AFHolidayDedicatedServices *);
int af_holiday_dedicated_dispatch(void *,AFHolidayControl *,
    const AFHolidayDedicatedServices *,unsigned int);
int af_holiday_dedicated_bind(AFHolidayDedicatedServices *);
int af_holiday_dedicated_start(void *,AFHolidayControl *);
int af_holiday_dedicated_stop(void *,AFHolidayControl *);
int af_holiday_dedicated_in(void *,AFHolidayControl *);
int af_holiday_dedicated_out(void *,AFHolidayControl *);
int af_holiday_dedicated_behind(void *,AFHolidayControl *);
#endif
