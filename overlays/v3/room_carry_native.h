#ifndef AF_V3_ROOM_CARRY_NATIVE_H
#define AF_V3_ROOM_CARRY_NATIVE_H
#include "room_carry.h"
#include "room_goods.h"
#include "furniture_tables.h"

#define ROOM_CARRY_NATIVE_MAGIC 0x41464331u
#define ROOM_CARRY_NATIVE_STATE 0x804DC400u
typedef RoomGoodsActor RoomCarryOwner;
typedef struct {RoomRig *actors;u8 *used;int count;} RoomCarryWork;
typedef struct {u8 prefix[0x30];float height;} RoomCarryProfile;
typedef struct {
    u32 magic;
    RoomCarryOwner *owner;
    u8 *base;
    RoomCarry carry;
    int motion,failed_restoration;
} RoomCarryNative;
#ifdef __mips__
#define carry_native ((RoomCarryNative *)ROOM_CARRY_NATIVE_STATE)
#define carry_profiles ((RoomCarryProfile **)AF_V3_FURNITURE_PROFILES)
_Static_assert(sizeof(RoomCarryNative)==172,"Native carrying state");
#else
extern RoomCarryNative af_test_carry_native;
extern RoomCarryProfile *af_test_carry_profiles[AF_V3_FURNITURE_CAPACITY];
extern RoomCarryWork af_test_carry_work;
extern void *af_test_carry_resolve(u32);
#define carry_native (&af_test_carry_native)
#define carry_profiles af_test_carry_profiles
#endif

void af_v3_carry_ctor(RoomCarryOwner *);
int af_v3_carry_blocked(const int *);
int af_v3_carry_permit_move(int,int,RoomRig *);
int af_v3_carry_permit_rotate_b(RoomRig *,void *,void *,int);
int af_v3_carry_permit_rotate_ac(RoomRig *);
int af_v3_carry_after_move(RoomRig *,RoomCarryOwner *);
void af_v3_carry_draw_rotation(s16,int,RoomRig *);
void af_v3_carry_draw(RoomRig *,RoomCarryOwner *,void *,RoomRigGame *);
void af_v3_carry_destruct(RoomCarryOwner *);
RoomRig *af_v3_carry_parent(RoomRig *);
s16 af_v3_carry_angle(RoomRig *);
#endif
