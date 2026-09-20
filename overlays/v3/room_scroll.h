#ifndef AF_V3_ROOM_SCROLL_H
#define AF_V3_ROOM_SCROLL_H
#include "room_materials.h"
#define ROOM_SCROLL_MAGIC 0x41464331u
#define ROOM_SCROLL_CAPACITY 64u
typedef struct {
    u16 index,bytes;
    u8 models,segment,tiles,colour_mode;
    u16 model_offsets[4];
    u8 dimensions[2][2];
    signed char rates[2][2];
    u32 colour_a,colour_b;
    u16 state_offset;
    u8 preview,reserved;
} RoomScrollRecord;
typedef struct {
    u32 magic,count,stride,reserved;
    RoomScrollRecord rows[ROOM_SCROLL_CAPACITY];
} RoomScrollTable;
_Static_assert(sizeof(RoomScrollRecord)==36,"Scroll record size");
#ifdef __mips__
#define room_scroll_table ((const RoomScrollTable *)0x804BB000u)
#else
extern RoomScrollTable af_v3_test_room_scroll;
#define room_scroll_table (&af_v3_test_room_scroll)
#endif
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);
#endif
