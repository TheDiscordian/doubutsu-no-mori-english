#ifndef AF_V3_ROOM_REVERSIBLE_H
#define AF_V3_ROOM_REVERSIBLE_H
#include "room_rigs.h"

/* Six shown matrices leave four slots in buffer zero unused. Larger skeletons
   keep every hidden joint in this region, instead of overflowing native vectors.
   The complete no-callback drawer must be bound before using this layout. */
typedef struct {
    s16 joint[17][3],morph[17][3];
    s16 state,reserved;
} RoomReversible;
_Static_assert(sizeof(RoomReversible)==208,"Complete reversible joint work");
_Static_assert(sizeof(RoomReversible)<=4*64,"Unused matrix-slot capacity");
_Static_assert(__builtin_offsetof(RoomRig,matrices)+6*64==0x390,"Extended rig work offset");

void af_v3_room_reverse_ct(RoomRig *,void *,void *,float);
void af_v3_room_reverse_step(RoomRig *,float,u32,int);
void af_v3_room_reverse_dt(RoomRig *);
#endif
