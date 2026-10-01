#ifndef AF_V3_TRAVEL_COLLECTION_H
#define AF_V3_TRAVEL_COLLECTION_H
#include "travel_native.h"
/* Every added-item consumer uses the same identity-bound visitor record.
 * Invalid transport state is an error, never a resident-slot fallback. */
static inline int af_travel_collection(const af_save_u8 *private,
                                      unsigned item,unsigned mark) {
    int result=af_v3_travel_visitor_collect((af_save_u8 *)private,item,mark);
    if(result<0)af_v3_save_halt(result);
    return result;
}
static inline int af_travel_paper(const af_save_u8 *private,unsigned mark) {
    int result=af_v3_travel_visitor_paper((af_save_u8 *)private,mark);
    if(result<0)af_v3_save_halt(result);
    return result;
}
#endif
