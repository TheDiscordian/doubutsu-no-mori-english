#ifndef AF_V3_HOLIDAY_OWNER_H
#define AF_V3_HOLIDAY_OWNER_H
#include "holiday_placement.h"
/* Exact native manager directory: five callbacks followed by a z,x block. */
typedef struct {
    unsigned int type,callbacks[5];
    AFHolidayBlock block;
} AFHolidayControl;
int af_holiday_owner_start(void *,AFHolidayControl *);
int af_holiday_owner_stop(void *,AFHolidayControl *);
int af_holiday_owner_in(void *,AFHolidayControl *);
int af_holiday_owner_out(void *,AFHolidayControl *);
/* An explicitly unfinished dedicated callback fails; it is never a null
 * callback that the native manager would interpret as successful work. */
int af_holiday_owner_unbound(void *,AFHolidayControl *);
#endif
