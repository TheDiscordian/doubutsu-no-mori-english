#ifndef AF_LEAFLET_H
#define AF_LEAFLET_H

#include "generate.h"

/* Values selected by the original caller, never selected again by this API.
 * Renewal uses the planned reopening date, not the native formatted date.
 * Sale and Redd use their original scheduled start date/time.
 */
typedef struct {
    unsigned short template_id;
    unsigned short year;
    unsigned char month, day, hour, item_count;
    unsigned short items[3];
} AfLeafletChoice;

/* Complete, source-resolved names captured before the native ten-byte clamp.
 * The native adapter must bind each value to its selected item identity.
 * A matching numeric ID alone does not approve an arbitrary supplied name.
 */
typedef struct {
    unsigned short item;
    AfMailField name;
} AfLeafletItem;

typedef struct {
    AfMailCapture capture;
    AfMailSelection selection;
    unsigned char mail[164];
    AfMailGenerateWork generation __attribute__((aligned(16)));
} AfLeafletWork;

/* Complete received-letter transaction for 0018..001A renewal, 0002..0011
 * sale, and 0031..0033 Redd templates. Renewal wording names the closed day,
 * so only its captured text date is one day before the supplied reopening date.
 * World clocks, schedules, native choices, and input objects remain unchanged.
 * Items are an exact item_count-element array, or NULL for non-sale letters.
 * Work requires sixteen-byte alignment. Rejection retains mail and capital.
 * Delivery, allocation, and pending ownership belong to the native adapter.
 */
int af_leaflet_create(unsigned char *mail, unsigned int size,
    const AfLeafletChoice *choice, const AfLeafletItem *items,
    unsigned int *capital, AfLeafletWork *work);

#endif
