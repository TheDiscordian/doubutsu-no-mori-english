#ifndef AF_V3_HOLIDAY_DEDICATED_H
#define AF_V3_HOLIDAY_DEDICATED_H
/* Common interface for the complete source event-owner callbacks. All IDs and
 * effect/profile arguments here remain donor IDs until the native adapter maps
 * them. This interface never casts donor manager/common-data structures. */
enum {
    AF_HD_KEEP,AF_HD_SET_KEEP,AF_HD_CLEAR_KEEP,AF_HD_STATUS,AF_HD_SET_STATUS,AF_HD_CLEAR_STATUS,
    AF_HD_FADE,AF_HD_CLEAN,AF_HD_FOREGROUND,AF_HD_ACTOR,AF_HD_DELETE_FOREGROUND,
    AF_HD_CLEAR_PLACE,AF_HD_CONTROL,AF_HD_SHOW,AF_HD_EFFECT,AF_HD_DELETE_EFFECT,AF_HD_UNABLE_WADE,
    AF_HD_DELETE_FOREGROUND_UNCHECKED
};
typedef struct {short fieldday_event_id,fieldday_event_over_status;} AFHolidayDedicatedCommon;
typedef struct {
    void *context;
    /* Signed pointer-sized result; source show helpers use -1 for not in acre.
     * Native failures/status writes remain the adapter's responsibility. */
    __INTPTR_TYPE__ (*call)(void *,unsigned int op,int donor,int a,int b,int c);
    AFHolidayDedicatedCommon *common;
    int pool_block_exists,shrine_block_exists;
} AFHolidayDedicated;
/* Complete start/stop/in/out/behind dispatch; absent source callbacks return
 * zero. A nonexistent event/phase or missing adapter returns -1. */
int af_holiday_dedicated(AFHolidayDedicated *,unsigned int donor,unsigned int phase);
#endif
