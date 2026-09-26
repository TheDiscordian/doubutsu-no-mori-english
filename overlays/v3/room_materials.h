#ifndef AF_V3_ROOM_MATERIALS_H
#define AF_V3_ROOM_MATERIALS_H
#include "room_rigs.h"
#define ROOM_MATERIAL_MAGIC 0x41464D31u
#define ROOM_MATERIAL_CAPACITY 11u
typedef struct {
    u16 index, bytes;
    u8 mode, segment, frames, models;
    u16 divisor, frame_bytes;
    u16 model_offsets[4], frame_offsets[8];
    u16 state_offset;
    u8 kind, reserved;
} RoomMaterialRecord;
typedef struct {
    u32 magic,count,stride,reserved;
    RoomMaterialRecord rows[ROOM_MATERIAL_CAPACITY];
} RoomMaterialTable;
typedef struct {
    RoomRigGame game;
    u8 before_play_frame[0x1EA0-sizeof(RoomRigGame)];
    u32 play_frame;
} RoomMaterialPlay;
_Static_assert(sizeof(RoomMaterialRecord)==40,"Material row size");
ROOM_CHECK(RoomMaterialPlay,play_frame,0x1EA0);
#ifdef __mips__
#ifndef ROOM_MATERIAL_TABLE_RAM
#define ROOM_MATERIAL_TABLE_RAM 0x804B9E20u
#endif
#define room_material_table ((const RoomMaterialTable *)ROOM_MATERIAL_TABLE_RAM)
#else
extern RoomMaterialTable af_v3_test_room_materials;
#define room_material_table (&af_v3_test_room_materials)
#endif
#endif
