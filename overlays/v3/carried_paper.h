#ifndef AF_V3_CARRIED_PAPER_H
#define AF_V3_CARRIED_PAPER_H
#include "carried_items.h"
/* Native singles and the existing orange-paper states keep their identities.
 * Three additional quantities for each of the 64 native styles use a separate
 * reserved range, not the donor bits that collide with native/orange items. */
#define AF_PAPER_PACK_FIRST 0x2E40u
#define AF_PAPER_PACK_COUNT 192u
extern const AFCarryWord af_carried_paper_mode;
int af_carried_paper_packs_enabled(void);
int af_carried_paper_style(AFCarryWord);
AFCarryWord af_carried_paper_quantity(AFCarryWord);
AFCarryHalf af_carried_paper_with_quantity(AFCarryWord,AFCarryWord);
AFCarryHalf af_carried_paper_obtain(AFCarryWord);
AFCarryHalf af_cw_paper_stack(AFCarryHalf,unsigned);
int af_carried_paper_reserved(AFCarryWord);
#endif
