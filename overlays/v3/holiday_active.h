#ifndef AF_V3_HOLIDAY_ACTIVE_H
#define AF_V3_HOLIDAY_ACTIVE_H
#include "holiday_dedicated_native.h"
/* Transient event state survives manager/scene changes. Both native common
 * initialization and ClearEventInfo reset it; it is not a new saved field. */
extern AFHolidayDedicatedCommon af_holiday_dedicated_common;
/* Exact prefix of the native Event object, not the donor Event layout. */
typedef struct {
    unsigned char prefix[6];
    short changed_num;
    int block_z,block_x;
} AFHolidayActiveEvent;
void af_holiday_active_update(AFHolidayActiveEvent *);
int af_holiday_dedicated_current(void *,AFHolidayControl *,
    const AFHolidayDedicatedServices *,unsigned int phase);
#endif
