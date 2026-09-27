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
#ifdef AF_V3_ROOM_DUAL_MOTION
int af_v3_room_dual_resolve(const RoomRigRecord *,u8 *,RoomDualMotion *);
int af_v3_room_dual_front(void);
#ifdef __mips__
#define room_dual_scene (*(volatile u32 *)0x80126EB4u)
#else
extern u32 af_v3_test_dual_scene;
#define room_dual_scene af_v3_test_dual_scene
extern void *af_v3_test_dual_owner;
#endif
#endif
#endif
