#ifndef AF_NOTICE_SEASONAL_H
#define AF_NOTICE_SEASONAL_H

#include "initial.h"

/* Immutable, source-bound overlay-local English text. The saved IDs remain
 * native 01A4..01CC; catalogue four and prior notice records stay unchanged.
 * Invalid IDs return ~0u, since zero is a valid field mask for fixed notices.
 */
unsigned int af_notice_seasonal_mask(unsigned int);
int af_notice_seasonal_valid(const AfMailRecord *);
int af_notice_seasonal_pack(unsigned char *, unsigned int, const AfMailRecord *);
/* Exact supplied sixteen-byte shop field for the original tier 0..3. */
int af_notice_seasonal_shop(unsigned char *, unsigned int, unsigned int);

/* Aligned, pairwise-disjoint disposable scratch; no cartridge text reads or
 * allocation. The decoder publishes nothing outside scratch on failure.
 */
int af_notice_seasonal_decode_parts(AfMailWorkspace *, AfMailText *, unsigned char *,
                                     const unsigned char *, unsigned int);
int af_notice_seasonal_decode(AfNoticeWorkspace *, const unsigned char *, unsigned int);

/* Complete output only, unchanged on failure. Output can overlap input, but
 * neither may overlap workspace. All unused output bytes are cleared.
 */
int af_notice_seasonal_restore(AfNoticeText *, const unsigned char *, unsigned int,
                                AfNoticeWorkspace *);

#endif
