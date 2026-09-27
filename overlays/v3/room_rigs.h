#ifndef AF_V3_ROOM_RIGS_H
#define AF_V3_ROOM_RIGS_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef union { float f; u32 bits; } FloatWord;
typedef struct {
    float amplitude,smoothed;
    s16 previous_state,rotation_ticks,phase;
    u16 reserved;
} RoomNeedle;
typedef struct {
    float start, end, duration;
    FloatWord speed, current;
    int mode;
    u8 rest[0x58];
} RoomKeyframe;
typedef struct {
    u16 index;
    s16 ctr_type;
    union { u8 before_position[4]; int id; };
    float position[3];
    union {
        u8 before_state[0x3C-20];
        struct {
            float previous_position[3],target_position[3];
            u8 before_angle[8];
            float angle_y,angle_y_target;
        };
    };
    s16 state;
    u8 shape_type,shape_padding;
    float base_position[3];
    u8 before_s_angle[0x124-0x4C];
    s16 s_angle_y;
    u8 angle_padding[6];
    u8 switched,changed;
    u8 before_keyframe[6];
    RoomKeyframe keyframe;
    s16 joint[9][3];
    /* Native capacity is eight joints plus root. Only six-joint behaviours
       may reuse the final two vectors as speed/previous-position work. */
    union __attribute__((packed,aligned(2))) {
        s16 morph[9][3];
        struct __attribute__((packed)) {
            s16 work_prefix[7][3];
            FloatWord speed,target;
            u8 unused_morph[4];
        };
    };
    union {
        u8 matrices[2][10][64];
        struct {
            u8 before_needle[9*64];
            RoomNeedle needle;
            u8 after_needle[20*64-9*64-sizeof(RoomNeedle)];
        };
        struct {
            /* The complete native recursive drawer consumes at most one matrix
               per shown joint (eight maximum). Slot nine is never submitted. */
            u8 before_motion[9*64];
            float motion_power,motion_phase;
            u8 after_motion[20*64-9*64-8];
        };
    };
    union {
        u8 tail[0x30];
        struct { u8 before_layer[0x28];s16 layer;u16 kept_item;u8 tail_end[4]; };
    };
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
#ifndef ROOM_RIG_TABLE_RAM
#define ROOM_RIG_TABLE_RAM 0x804B9000u
#endif
#define ROOM_RIG_SWITCH 0u
#define ROOM_RIG_CLOCK 1u
#define ROOM_RIG_STORAGE 2u
#define ROOM_RIG_HIT 3u
#define ROOM_RIG_BILLBOARD 4u
#define ROOM_RIG_ROLLING 5u
#define ROOM_RIG_JOINT 6u
#define ROOM_RIG_ROOF 7u
#define ROOM_RIG_MATERIAL 8u
#define ROOM_RIG_REVERSIBLE 9u
#define ROOM_RIG_EFFECT 10u
#ifdef AF_V3_ROOM_MATERIAL_RIG
/* Explicit big-endian halfwords keep immutable object data portable to the
   host checks as well as the native big-endian target. */
typedef struct {
    u8 segment,frames,sound,reserved;
    u8 divisor[2],frame_bytes[2],offsets[8][2],padding[8];
} RoomRigMaterial;
_Static_assert(sizeof(RoomRigMaterial)==32,"Rig material parameters");
extern void sAdo_OngenPos(u32,u8,float *);
#endif
#ifdef AF_V3_SELECTED_PALETTE
extern void af_v3_roof_ct(void *,u8 *);
extern void af_v3_roof_mv(void *,void *,void *,u8 *);
extern void af_v3_roof_dw(void *,void *,void *,u8 *);
#endif
#ifdef AF_V3_ROOM_JOINT
extern void af_v3_room_joint_ct(RoomRig *,const RoomRigRecord *);
extern void af_v3_room_joint_mv(RoomRig *,const RoomRigRecord *);
extern void af_v3_room_joint_dw(RoomRig *,RoomRigGame *,const RoomRigRecord *);
#endif
#ifdef AF_V3_ROOM_BILLBOARD
typedef struct {
    u32 flame;
    u8 dimensions[2][2];
    signed char rates[2][2];
    u8 sound,suppress_states,joint,reserved;
} RoomBillboard;
_Static_assert(sizeof(RoomBillboard)==16,"Billboard parameter size");
extern void sAdo_OngenPos(u32,u8,float *);
extern void af_v3_room_billboard_dw(RoomRig *,void *,RoomRigGame *,const RoomRigRecord *,const RoomBillboard *);
#endif
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
#ifdef AF_V3_ROOM_TRIGGER_SOUND
typedef struct {
    u16 index;
    u8 before_position[6];
    float position[3];
    u8 before_state[0x3C-20];
    s16 state;
    u8 before_changed[0x12D-0x3E];
    u8 changed;
} RoomSoundActor;
typedef struct {
    u16 index,word;
    union { u32 reserved;struct { u8 wall,effect;u16 system; }; };
} RoomSoundRecord;
typedef struct { u16 word;u8 rest[30]; } RoomNativeTrigger;
#define ROOM_SOUND_MAGIC 0x41465331u
#define ROOM_SOUND_CAPACITY 64u
typedef struct { u32 magic,count,stride,reserved; RoomSoundRecord rows[ROOM_SOUND_CAPACITY]; } RoomSoundTable;
#ifdef __mips__
#ifndef ROOM_SOUND_TABLE_RAM
#define ROOM_SOUND_TABLE_RAM 0x804B9C10u
#endif
#define room_sound_table ((const RoomSoundTable *)ROOM_SOUND_TABLE_RAM)
#define room_native_triggers ((const volatile RoomNativeTrigger *)0x80113C34u)
#else
extern RoomSoundTable af_v3_test_room_sounds;
extern RoomNativeTrigger af_v3_test_room_triggers[6];
#define room_sound_table (&af_v3_test_room_sounds)
#define room_native_triggers af_v3_test_room_triggers
#endif
ROOM_CHECK(RoomSoundActor,position,8); ROOM_CHECK(RoomSoundActor,state,0x3C);
ROOM_CHECK(RoomSoundActor,changed,0x12D);
_Static_assert(sizeof(RoomSoundRecord)==8,"Room sound record stride");
extern void sAdo_OngenTrgStart(u32,float *);
extern void sAdo_SysTrgStart(u32);
#endif
ROOM_CHECK(RoomRig,position,8); ROOM_CHECK(RoomRig,state,0x3C);
ROOM_CHECK(RoomRig,id,4); ROOM_CHECK(RoomRig,previous_position,0x14);
ROOM_CHECK(RoomRig,target_position,0x20); ROOM_CHECK(RoomRig,angle_y,0x34);
ROOM_CHECK(RoomRig,angle_y_target,0x38); ROOM_CHECK(RoomRig,shape_type,0x3E);
ROOM_CHECK(RoomRig,base_position,0x40); ROOM_CHECK(RoomRig,s_angle_y,0x124);
ROOM_CHECK(RoomRig,layer,0x738); ROOM_CHECK(RoomRig,kept_item,0x73A);
ROOM_CHECK(RoomRig,changed,0x12D); ROOM_CHECK(RoomRig,keyframe,0x134);
ROOM_CHECK(RoomRig,joint,0x1A4); ROOM_CHECK(RoomRig,morph,0x1DA);
ROOM_CHECK(RoomRig,speed,0x204); ROOM_CHECK(RoomRig,target,0x208);
ROOM_CHECK(RoomRig,switched,0x12C); ROOM_CHECK(RoomRig,motion_power,0x450);
ROOM_CHECK(RoomRig,ctr_type,2);
ROOM_CHECK(RoomRig,motion_phase,0x454);
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
