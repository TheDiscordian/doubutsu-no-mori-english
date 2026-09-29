#ifndef AF_V3_HOLIDAY_PLACEMENT_H
#define AF_V3_HOLIDAY_PLACEMENT_H
#include "holiday_events.h"

/* Preserve the actual N64 coordinate order, including parameters passed by
 * value to mEv_use_block_by_other_event. Donor structs are not cast onto it. */
typedef struct { int z,x; } AFHolidayBlock;
typedef struct {
    AFHolidayBlock block,unit;
    unsigned short name,flags;
} AFHolidayPlace;
typedef struct {
    AFHolidayBlock maximum,next,shrine,excluded[5];
    unsigned int exclusions,month,day,hour,second;
} AFHolidayField;
typedef struct {
    void *context;
    int (*outdoors)(void *);
    int (*busy)(void *,int,int);
    int (*other)(void *,unsigned int,AFHolidayBlock);
    int (*unit)(void *,int *,int *,int,int);
    /* Donor check_fgcol AND no current/default terrain-height gap. */
    int (*height)(void *,int,int,int,int);
    AFHolidayPlace *(*get)(void *,unsigned int,unsigned int);
    AFHolidayPlace *(*reserve)(void *,unsigned int,unsigned int);
    int (*forward)(void *,int *,int *);
    void (*flatten)(void *,AFHolidayPlace *);
    int (*spawn)(void *,AFHolidayPlace *);
    void (*error)(void *,unsigned int);
} AFHolidayPlacementOps;

/* Decode the native manager, whose landmark order is pool/station/shrine/home. */
int af_holiday_placement_field(const void *,const unsigned char rtc[8],AFHolidayField *);

/* type/name are destination identities; source_seed preserves the donor's
 * deterministic free-acre selection despite additive IDs. */
int af_holiday_placement_make(const AFHolidayField *,const AFHolidayPlacementOps *,
    unsigned int type,unsigned int name,unsigned int id,unsigned int kind,int source_seed,
    AFHolidayPlace **);
/* Source owners have different edge margins. Share the complete search rather
 * than silently substituting the ordinary wandering owner's one-unit margin. */
int af_holiday_placement_make_adjust(const AFHolidayField *,const AFHolidayPlacementOps *,
    unsigned int,unsigned int,unsigned int,unsigned int,int,int,AFHolidayPlace **);
/* 0: actual failed spawn; 1: appeared; 2: no appearance in this acre. */
int af_holiday_placement_show(const AFHolidayField *,const AFHolidayPlacementOps *,
    unsigned int type,unsigned int id,AFHolidayBlock *forward_block);
/* Native adapters resolve only a currently loaded, checked event owner. */
int af_holiday_placement_native_make(void *manager,unsigned int donor,unsigned int native_name,
    unsigned int donor_name,AFHolidayPlace **);
int af_holiday_placement_native_show(void *manager,unsigned int donor,AFHolidayBlock *);
int af_holiday_placement_native_show_id(void *manager,unsigned int donor,unsigned int id,AFHolidayBlock *);
int af_holiday_placement_native_cull(unsigned int donor);
int af_holiday_placement_native_free(void *,unsigned int,unsigned int,unsigned int,int,int,AFHolidayPlace **);
int af_holiday_placement_native_show_type(void *,unsigned int,unsigned int,AFHolidayBlock *);
#endif
