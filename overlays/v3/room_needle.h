#ifndef AF_V3_ROOM_NEEDLE_H
#define AF_V3_ROOM_NEEDLE_H
#include "room_rigs.h"

/* Transient state fits one unused matrix slot. No saved fields are involved.
   The owner adapter must supply the actual carried parent, when present. */
typedef struct {
    float amplitude,smoothed;
    s16 previous_state,rotation_ticks,phase;
    u16 reserved;
} RoomNeedle;
_Static_assert(sizeof(RoomNeedle)==16,"Needle work size");

void af_v3_room_needle_ct(RoomNeedle *,RoomKeyframe *,s16);
void af_v3_room_needle_step(RoomNeedle *,RoomKeyframe *,s16,const s16 *,s16,s16);
s16 af_v3_room_needle_angle(const RoomNeedle *,s16,s16,s16);
#endif
