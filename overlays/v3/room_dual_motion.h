#ifndef AF_V3_ROOM_DUAL_MOTION_H
#define AF_V3_ROOM_DUAL_MOTION_H
#include "room_reversible.h"

/* Closed then open. Installed dispatch must resolve both actual object headers
   and bind the complete source sounds; this core never substitutes a motion. */
typedef struct {
    void *animation[2];
    float duration[2];
    u16 click[2];
    u8 loop;
} RoomDualMotion;
void af_v3_room_dual_ct(RoomRig *,void *,const RoomDualMotion *,int);
void af_v3_room_dual_step(RoomRig *,const RoomDualMotion *,int,int);
void af_v3_room_dual_dt(RoomRig *);
void af_v3_room_dual_dw(RoomRig *,RoomRigGame *,u32,int);
#endif
