#ifndef AF_V3_HOLIDAY_RESERVED_H
#define AF_V3_HOLIDAY_RESERVED_H
#include "holiday_placement.h"
typedef struct {
    unsigned int event,selection,normal_npcs,variants,count,npc_flags,source_cloth,kind;
    unsigned int source_name,x,z;
} AFHolidayMap;
/* Lookup retains source identities. Only a checked resolver may turn a source
 * actor, decoration, or uniform into an installed destination identity. */
int af_holiday_map_get(const unsigned char *,unsigned int bytes,unsigned int donor,
    unsigned int pool_variant,unsigned int index,AFHolidayMap *);
typedef struct {
    void *context;
    int (*outdoors)(void *);
    int (*landmark)(void *,unsigned int kind,AFHolidayBlock *);
    unsigned int (*resolve)(void *,unsigned int source_name);
    AFHolidayPlace *(*get)(void *,unsigned int native,unsigned int id);
    AFHolidayPlace *(*reserve)(void *,unsigned int native,unsigned int id);
    int (*set_foreground)(void *,const AFHolidayPlace *);
    void (*error)(void *,unsigned int native);
} AFHolidayReservedOps;
/* Shared complete make_actor/make_FG_in_reserved_block path. Existing placement
 * is retained; foreground placement is applied on every call, as in the donor.
 * A source name is never written to a native reservation without resolution. */
AFHolidayPlace *af_holiday_reserved_make(const unsigned char *,unsigned int bytes,
    const AFHolidayReservedOps *,unsigned int donor,unsigned int native,
    unsigned int variant,unsigned int index,unsigned int id,int foreground);
#endif
