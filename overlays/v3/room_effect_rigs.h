#ifndef AF_V3_ROOM_EFFECT_RIGS_H
#define AF_V3_ROOM_EFFECT_RIGS_H
#include "room_reversible.h"

typedef struct {
    u8 duration[4],model[4],segment,frames,sound,joint;
    u8 delay[2],frame_bytes[2],offsets[5][2],padding[6];
} RoomEffectRigParams;
typedef struct {
    RoomReversible reverse;
    s16 delayed,steam,delay,reserved;
} RoomEffectRigState;
_Static_assert(sizeof(RoomEffectRigParams)==32,"Complete effect rig parameters");
_Static_assert(sizeof(RoomEffectRigState)<=4*64,"Effect rig fits unused matrices");

const RoomEffectRigParams *af_v3_room_effect_rig_params(const RoomRigRecord *,const u8 *);
void af_v3_room_effect_rig_ct(RoomRig *,void *,void *,const RoomEffectRigParams *);
void af_v3_room_effect_rig_step(RoomRig *,RoomRigGame *,const RoomEffectRigParams *,int);
void af_v3_room_effect_rig_dw(RoomRig *,RoomRigGame *,const RoomRigRecord *,const RoomEffectRigParams *,u8 *);
#endif
