#ifndef AF_V3_HOLIDAY_DEDICATED_NATIVE_H
#define AF_V3_HOLIDAY_DEDICATED_NATIVE_H
#include "holiday_dedicated.h"
#include "holiday_owner.h"
enum {AF_HD_NAME,AF_HD_PROFILE,AF_HD_EFFECT_ID};
typedef struct {
    void *context;
    /* Checked source-to-installed identity, or -1 when not installed. No
     * same-number fallback for decorations, actors, profiles, or effects. */
    int (*resolve)(void *,unsigned int kind,unsigned int source);
    /* Imported event-title text/transition service. The original native fade
     * cannot consume additive event IDs without updating its title readers. */
    int (*fade)(void *,void *manager,unsigned int donor,unsigned int native,
        unsigned int title,unsigned int landmark);
    /* The donor sports closing ceremony locks acre transitions. Its player
     * consumer must be installed; an absent native equivalent is not a no-op. */
    void (*unable_wade)(void *,int);
    const unsigned char *maps;
    unsigned int map_bytes;
} AFHolidayDedicatedServices;
/* Common state belongs to the imported manager's lifetime, not a stack-local
 * reset on every event callback and not the differently indexed native state. */
int af_holiday_dedicated_native(void *,AFHolidayControl *,AFHolidayDedicatedCommon *,
    const AFHolidayDedicatedServices *,unsigned int phase);
#endif
