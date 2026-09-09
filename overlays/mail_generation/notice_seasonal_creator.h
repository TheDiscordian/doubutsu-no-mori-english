#ifndef AF_NOTICE_SEASONAL_CREATOR_H
#define AF_NOTICE_SEASONAL_CREATOR_H

#include "notice_owner.h"

/* First dispatcher, using the unchanged synchronous creator loader:
 * animal: AFNS | BE16 native template | BE16 posting year | 0 | 0 | 0 | 243.
 * player: any aligned readable sixteen-byte caller-owned identity/scratch.
 * remail, condition, and foreign are zero. Native IDs remain 01A4..01CC.
 * The caller selects the original year/template; this code captures only the
 * required town/shop/calendar field, without editing global free strings.
 * Success writes 96 notice bytes followed by 68 zero staging bytes, never a
 * timestamp, saved board, or scheduling state. The owner must publish/retry.
 */
int af_notice_seasonal_create(AfNpcMailCreateWork *, unsigned char *, AfNpcMailSession **,
                                unsigned int *);

#endif
