#ifndef AF_V3_ROOM_COLOURS_H
#define AF_V3_ROOM_COLOURS_H
#include "room_rigs.h"
#define ROOM_COLOUR_RAM 0x804CD400u
#define ROOM_COLOUR_BYTES 256u
#define ROOM_COLOUR_MAGIC 0x4146434Cu
typedef struct {
    u32 magic,request,active;
    float timer;
    void *player;
    u8 rgb[3],reserved;
} RoomColourState;
typedef struct { u32 vrom_start,vrom_end,vram_start,vram_end;u8 *loaded; } RoomColourOverlay;
typedef struct { RoomRig *actors;u8 *used;int count; } RoomColourInstances;
#ifdef __mips__
#define room_colour_state ((RoomColourState *)ROOM_COLOUR_RAM)
#else
extern RoomColourState af_v3_test_room_colour;
#define room_colour_state (&af_v3_test_room_colour)
#endif
typedef void (*RoomColourOriginal)(void *,RoomRigGame *);
extern u8 *af_reaction_player(void *);
_Static_assert(sizeof(RoomColourState)<=ROOM_COLOUR_BYTES,"Colour state reservation");
#ifdef __mips__
ROOM_CHECK(RoomColourInstances,used,4);
ROOM_CHECK(RoomColourInstances,count,8);
ROOM_CHECK(RoomColourOverlay,loaded,0x10);
#endif
extern void sAdo_OngenPos(u32,u8,float *);
extern float sqrtf(float);
extern RoomCommand *gfx_set_fog_nosync(RoomCommand *,int,int,int,int,int,int);
extern void af_v3_room_colour_ct(RoomRig *);
extern void af_v3_room_colour_mv(RoomRig *,void *,RoomRigGame *,u8);
extern void af_v3_room_colour_update(void *,RoomRigGame *,RoomColourOriginal);
extern void af_v3_room_colour_draw(RoomRigGame *,RoomKeyframe *,void *,void *,void *,void *);
#endif
