#ifndef AF_V3_ROOM_REACTIONS_H
#define AF_V3_ROOM_REACTIONS_H
#include "room_rumble.h"
#define ROOM_REACTION_STATE_RAM 0x804CD000u
#define ROOM_REACTION_STATE_BYTES 1024u
#define ROOM_REACTION_STATE_MAGIC 0x41465258u
typedef struct {
    u32 magic,tick,heartbeat;
    RoomRumbleEnvelope envelope;
    RoomRumbleMotor motor;
    uptr owner;
    u32 pending;
    s16 angle;
} RoomReactionState;
_Static_assert(sizeof(RoomReactionState)<=ROOM_REACTION_STATE_BYTES,"Reaction state reservation");
#ifdef __mips__
#define room_reaction_state ((RoomReactionState *)ROOM_REACTION_STATE_RAM)
extern const RoomRumbleBank af_v3_rumble_waves;
#else
extern RoomReactionState af_v3_test_reaction_state;
#define room_reaction_state (&af_v3_test_reaction_state)
extern const RoomRumbleBank *af_v3_test_rumble_waves;
#define af_v3_rumble_waves (*af_v3_test_rumble_waves)
#endif
extern u32 af_rumble_mask(u32);
extern u8 *af_reaction_player(void *);
extern int af_reaction_shock(void *,float,s16,int);
void af_v3_room_reaction_ct(RoomRig *);
void af_v3_room_reaction_mv(RoomRig *,void *,RoomRigGame *);
void af_v3_room_rumble_retrace(void *,const u8 *);
#endif
