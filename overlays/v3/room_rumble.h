#ifndef AF_V3_ROOM_RUMBLE_H
#define AF_V3_ROOM_RUMBLE_H
#include "room_rigs.h"

/* Immutable, source-extracted wave bank; offsets are relative to this header. */
#define ROOM_RUMBLE_WAVES 16u
#define ROOM_RUMBLE_ELEMENTS 4u
#define ROOM_RUMBLE_MAGIC 0x41465642u
typedef struct { u16 offset, count; } RoomRumbleWave;
typedef struct {
    u32 magic, bytes, count, reserved;
    RoomRumbleWave waves[ROOM_RUMBLE_WAVES];
} RoomRumbleBank;
typedef struct { int wave, frames; float step; } RoomRumblePhase;
typedef struct {
    RoomRumblePhase phases[3];
    float attenuation, intensity;
    int phase, cursor;
    float strength;
    int frame;
    float accumulated;
    int command;
} RoomRumbleElement;
typedef struct {
    RoomRumbleElement elements[ROOM_RUMBLE_ELEMENTS];
    u32 count;
} RoomRumbleEnvelope;
/* Independent OSPfs, never a player's Controller Pak/save-system instance.
   Only the controller thread reads/writes this transport state. */
typedef struct {
    u32 pfs[26];
    u32 ready, on, retry;
} RoomRumbleMotor;
_Static_assert(sizeof(RoomRumbleElement)==68,"Complete vibration element");
_Static_assert(sizeof(RoomRumbleMotor)==116,"Private motor state");

int af_v3_rumble_entry(RoomRumbleEnvelope *,const RoomRumbleBank *,
    int,int,int,int,int,int,int,float);
u32 af_v3_rumble_step(RoomRumbleEnvelope *,const RoomRumbleBank *);
void af_v3_rumble_clear(RoomRumbleEnvelope *);
void af_v3_rumble_motor(RoomRumbleMotor *,void *,u32,u32,u32);
/* Native bindings: called only after completed SI transfers, while padmgr
   owns its serial queue. They must never run in rumbleRetraceCallback. */
extern int af_rumble_motor_init(void *,void *,int);
extern int af_rumble_motor_access(void *,int);
#endif
