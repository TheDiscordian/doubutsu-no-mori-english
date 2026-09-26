#ifndef AF_V3_ROOM_STATIC_H
#define AF_V3_ROOM_STATIC_H
#include "room_rigs.h"
typedef struct { u16 index; u8 mode,parameter; u16 sound,reserved; } RoomStaticRecord;
typedef struct { u32 magic,count,stride,reserved; RoomStaticRecord rows[128]; } RoomStaticTable;
typedef struct { u8 prefix[0x38]; u32 wallet; } RoomPrivateWallet;
typedef struct {
    u8 prefix[0x64];
    void (*melody)(RoomSoundActor *,void *,u32);
} RoomStaticClip;
extern const RoomStaticTable af_v3_room_static_table;
#ifdef __mips__
#define room_static_private (*(RoomPrivateWallet *volatile *)0x80136FD8u)
#define room_static_clip (*(RoomStaticClip *volatile *)0x80136F2Cu)
#else
extern RoomPrivateWallet *af_v3_test_static_private;
extern RoomStaticClip *af_v3_test_static_clip;
#define room_static_private af_v3_test_static_private
#define room_static_clip af_v3_test_static_clip
#endif
_Static_assert(sizeof(RoomStaticRecord)==8,"Static record stride");
_Static_assert(__builtin_offsetof(RoomPrivateWallet,wallet)==0x38,"Native wallet");
#ifdef __mips__
_Static_assert(__builtin_offsetof(RoomStaticClip,melody)==0x64,"Native melody callback");
#endif
int af_v3_room_static_mv(RoomSoundActor *,void *);
#endif
