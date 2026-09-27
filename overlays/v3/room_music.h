#ifndef AF_V3_ROOM_MUSIC_H
#define AF_V3_ROOM_MUSIC_H
#include "room_rigs.h"

/* Existing room-owner music fields; no additional save or resident state. */
typedef struct {
    int song,previous_song;
    u8 reserved,padding;
    s16 timer;
    RoomRig *reserved_actor,*active_actor;
    int active;
} RoomMusic;
#ifdef __mips__
ROOM_CHECK(RoomMusic,reserved,8); ROOM_CHECK(RoomMusic,timer,10);
ROOM_CHECK(RoomMusic,reserved_actor,12); ROOM_CHECK(RoomMusic,active_actor,16);
ROOM_CHECK(RoomMusic,active,20);
_Static_assert(sizeof(RoomMusic)==24,"Native room music state");
#endif

void af_v3_room_music_apply(RoomMusic *,RoomRig *,u8);
void af_v3_room_music_reserve(RoomMusic *,RoomRig *,int,s16);
void af_v3_room_music_disk_dt(RoomRig *,RoomMusic *,u8);
void af_v3_room_radio_ct(RoomRig *);
void af_v3_room_radio_dt(RoomRig *,RoomMusic *,u8);
void af_v3_room_radio_move(RoomRig *,RoomMusic *,u8,void (*)(RoomRig *));
void af_v3_room_radio_notes(RoomRig *,RoomRigGame *,u16);
void af_v3_room_radio_draw(RoomRig *,RoomRigGame *,u32,u32);
#endif
