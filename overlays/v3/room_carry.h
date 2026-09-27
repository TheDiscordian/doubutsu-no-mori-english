#ifndef AF_V3_ROOM_CARRY_H
#define AF_V3_ROOM_CARRY_H
#include "room_rigs.h"

/* One moving parent and all four occupied tabletop cells, as in the donor.
   This is transient owner state, never a replacement for saved foreground. */
typedef struct {
    int active;
    float relative[3];
    int actor_id;
    u16 item;
    s16 angle;
    float world[3];
} RoomCarrySlot;
typedef struct {
    int parent_id;
    s16 angle;
    u16 reserved;
    RoomCarrySlot slots[4];
} RoomCarry;
_Static_assert(sizeof(RoomCarrySlot)==36,"Carried tabletop record");
_Static_assert(sizeof(RoomCarry)==152,"Moving-table owner state");

/* Native overlay addresses must be resolved by the owner adapter. Callbacks
   are complete native operations; null callbacks do not mean 'do nothing'.
   lookup returns an actor ID, or -1 for a missing furniture actor. */
typedef struct {
    void *opaque;
    RoomRig *actors;
    const u8 *used;
    int count;
    u16 *foreground;
    int (*lookup)(void *,int);
    float (*top_height)(void *,RoomRig *);
    void (*set_furniture)(void *,RoomRig *,int);
    void (*set_place)(void *,int,int);
    s16 (*get_angle)(void *,int);
    void (*set_angle)(void *,int,s16);
    void (*draw_item)(void *,RoomRigGame *,u16,const float *,float,s16);
} RoomCarryAccess;

void af_v3_room_carry_init(RoomCarry *);
int af_v3_room_carry_cells(int *,const float *,u8);
int af_v3_room_carry_request(RoomCarry *,const RoomCarryAccess *,RoomRig *);
int af_v3_room_carry_update(RoomCarry *,const RoomCarryAccess *,RoomRig *);
int af_v3_room_carry_release(RoomCarry *,const RoomCarryAccess *,RoomRig *);
RoomRig *af_v3_room_carry_parent(const RoomCarry *,const RoomCarryAccess *,const RoomRig *);
s16 af_v3_room_carry_angle(const RoomCarry *,const RoomCarryAccess *,const RoomRig *);
int af_v3_room_carry_draw(const RoomCarry *,const RoomCarryAccess *,RoomRig *,RoomRigGame *);
#endif
