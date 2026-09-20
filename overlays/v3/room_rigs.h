#ifndef AF_V3_ROOM_RIGS_H
#define AF_V3_ROOM_RIGS_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef union { float f; u32 bits; } FloatWord;
typedef struct {
    float start, end, duration;
    FloatWord speed, current;
    int mode;
    u8 rest[0x58];
} RoomKeyframe;
typedef struct {
    u16 index;
    u8 prefix[0x12D-2];
    u8 changed;
    u8 before_keyframe[6];
    RoomKeyframe keyframe;
    s16 joint[9][3];
    /* Six joints plus root use seven morph vectors. The remaining twelve
       bytes belong to this callback category, not the native engine. */
    s16 morph[7][3];
    FloatWord speed, target;
    u8 unused_morph[4];
    u8 matrices[2][10][64];
    u8 tail[0x30];
} RoomRig;
typedef struct { u32 a,b; } RoomCommand;
typedef struct {
    u8 before_head[0x298];
    RoomCommand *head;
    u8 *tail;
    u8 before_translucent[8];
    RoomCommand *xlu_head;
    u8 *xlu_tail;
} RoomRigGraphics;
typedef struct {
    RoomRigGraphics *gfx;
    u8 before_frame[0xA0-sizeof(RoomRigGraphics*)];
    u32 frame;
} RoomRigGame;
#ifdef AF_V3_ROOM_RIG_PACKET
typedef struct {
    u16 index, bytes; u32 skeleton, animation;
    u8 joints, shown, mode, reserved;
    FloatWord first, last;
} RoomRigRecord;
#define ROOM_RIG_MAGIC 0x41465232u
#define ROOM_RIG_CAPACITY 128u
#define ROOM_RIG_TABLE_RAM 0x804B9000u
#define ROOM_RIG_SWITCH 0u
#define ROOM_RIG_CLOCK 1u
#define ROOM_RIG_STORAGE 2u
typedef struct {
    u8 prefix[0x34];
    void (*open_close)(RoomRig *,void *,RoomRigGame *,float,float);
} RoomRigClip;
#ifdef __mips__
#define room_rig_clip (*(RoomRigClip *volatile *)0x80136F2Cu)
#define room_rig_hour (*(volatile u16 *)0x80136FC6u)
#define room_rig_minute (*(volatile u16 *)0x80136FC4u)
#else
extern RoomRigClip *af_v3_test_room_clip;
extern u16 af_v3_test_room_hour,af_v3_test_room_minute;
#define room_rig_clip af_v3_test_room_clip
#define room_rig_hour af_v3_test_room_hour
#define room_rig_minute af_v3_test_room_minute
#endif
#else
typedef struct { u16 index, bytes; u32 skeleton, animation; u16 joints, shown; } RoomRigRecord;
#define ROOM_RIG_MAGIC 0x41465231u
#define ROOM_RIG_CAPACITY 24u
#define ROOM_RIG_TABLE_RAM 0x804B1E00u
#endif
typedef struct { u32 magic,count,stride,reserved; RoomRigRecord rows[ROOM_RIG_CAPACITY]; } RoomRigTable;
#ifdef __mips__
#define room_rig_table ((const RoomRigTable *)ROOM_RIG_TABLE_RAM)
#else
extern RoomRigTable af_v3_test_room_rigs;
#define room_rig_table (&af_v3_test_room_rigs)
#endif
#define ROOM_CHECK(type,field,at) _Static_assert(__builtin_offsetof(type,field)==(at),#type "." #field)
ROOM_CHECK(RoomRig,changed,0x12D); ROOM_CHECK(RoomRig,keyframe,0x134);
ROOM_CHECK(RoomRig,joint,0x1A4); ROOM_CHECK(RoomRig,morph,0x1DA);
ROOM_CHECK(RoomRig,speed,0x204); ROOM_CHECK(RoomRig,target,0x208);
ROOM_CHECK(RoomRig,matrices,0x210); ROOM_CHECK(RoomRigGame,frame,0xA0);
_Static_assert(sizeof(RoomRig)==0x740,"Native furniture stride");
#ifdef AF_V3_ROOM_RIG_PACKET
_Static_assert(sizeof(RoomRigRecord)==24,"Room rig record stride");
#ifdef __mips__
ROOM_CHECK(RoomRigClip,open_close,0x34);
#endif
#else
_Static_assert(sizeof(RoomRigRecord)==16,"Room rig record stride");
#endif
_Static_assert(sizeof(RoomKeyframe)==0x70,"Native keyframe size");
#ifdef __mips__
ROOM_CHECK(RoomRigGraphics,head,0x298); ROOM_CHECK(RoomRigGraphics,tail,0x29C);
ROOM_CHECK(RoomRigGraphics,xlu_head,0x2A8); ROOM_CHECK(RoomRigGraphics,xlu_tail,0x2AC);
#endif
extern void cKF_SkeletonInfo_R_ct(RoomKeyframe*,void*,void*,void*,void*);
extern void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe*,void*,void*);
extern void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe*,void*,void*);
extern int cKF_SkeletonInfo_R_play(RoomKeyframe*);
extern void cKF_Si3_draw_R_SV(void*,RoomKeyframe*,void*,void*,void*,void*);
extern void *Lib_SegmentedToVirtual(void*);
extern void *_Matrix_to_Mtx_new(void*);
#endif
