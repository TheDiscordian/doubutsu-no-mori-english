#ifndef AF_V3_ROOM_MUSIC_NATIVE_H
#define AF_V3_ROOM_MUSIC_NATIVE_H
#include "room_music.h"
#include "room_goods.h"
#include "furniture_tables.h"

typedef struct {
    RoomGoodsActor actor;
    u8 before_music[0x45C-sizeof(RoomGoodsActor)];
    RoomMusic music;
} RoomMusicOwner;
typedef struct {RoomMusicOwner *owner;} RoomMusicClip;
typedef struct {u8 prefix[0x3E];u16 interaction;} RoomMusicProfile;
#ifdef __mips__
ROOM_CHECK(RoomMusicOwner,music,0x45C);
#define room_music_clip (*(RoomMusicClip *volatile *)0x80136F2Cu)
#define room_music_profiles ((RoomMusicProfile **)AF_V3_FURNITURE_PROFILES)
#else
extern RoomMusicClip *af_test_music_clip;
extern RoomMusicProfile *af_test_music_profiles[AF_V3_FURNITURE_CAPACITY];
extern void *af_test_music_resolve(u8 *,u32);
#define room_music_clip af_test_music_clip
#define room_music_profiles af_test_music_profiles
#endif

void af_v3_room_music_native_apply(RoomMusicOwner *,RoomRig *);
void af_v3_room_music_native_disk_dt(RoomRig *,RoomMusicOwner *);
void af_v3_room_music_native_move(RoomRig *,RoomMusicOwner *);
void af_v3_room_music_native_radio_dt(RoomRig *);
#endif
