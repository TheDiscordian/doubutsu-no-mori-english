#ifndef AF_V3_ROOM_SCROLL_H
#define AF_V3_ROOM_SCROLL_H
#include "room_materials.h"
#define ROOM_SCROLL_MAGIC 0x41464332u
#define ROOM_SCROLL_CAPACITY 64u
typedef struct {
    u16 index,bytes;
    u8 models,segment,tiles,colour_mode;
    u16 model_offsets[4];
    u8 dimensions[2][2];
    signed char rates[2][2];
    u32 colour_a,colour_b;
    u16 state_offset;
    u8 preview,opaque_models;
    u32 colour2_a,colour2_b;
    u16 debug_offset,reserved;
} RoomScrollRecord;
typedef struct {
    u32 magic,count,stride,reserved;
    RoomScrollRecord rows[ROOM_SCROLL_CAPACITY];
} RoomScrollTable;
_Static_assert(sizeof(RoomScrollRecord)==48,"Scroll record size");
#ifdef __mips__
#define room_scroll_table ((const RoomScrollTable *)0x804BB000u)
#else
extern RoomScrollTable af_v3_test_room_scroll;
#define room_scroll_table (&af_v3_test_room_scroll)
#endif
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);
/* Existing native Debug_mode owner, not new shared writable renderer state. */
extern u8 *af_v3_room_debug;
#ifdef AF_V3_ROOM_SCROLL_LIFECYCLE
#define ROOM_SCROLL_LIFE_MAGIC 0x41464C31u
#define ROOM_SCROLL_LIFE_CAPACITY 64u
typedef struct {
    u16 index;
    u8 mode,flags;
    u16 sound,on,off;
    u8 maximum,step;
} RoomScrollLife;
typedef struct {
    u32 magic,count,stride,reserved;
    RoomScrollLife rows[ROOM_SCROLL_LIFE_CAPACITY];
} RoomScrollLives;
typedef struct {
    u16 index;
    u8 before_position[6];
    float position[3];
    u8 before_state[0x3C-20];
    s16 state;
    u8 before_switch[0x12C-0x3E];
    u8 saved_switch,changed;
    u8 before_private[0x1A4-0x12E];
    FloatWord colour;
    s16 private_switch;
} RoomScrollActor;
_Static_assert(sizeof(RoomScrollLife)==12,"Scroll lifecycle record size");
ROOM_CHECK(RoomScrollActor,position,8); ROOM_CHECK(RoomScrollActor,state,0x3C);
ROOM_CHECK(RoomScrollActor,saved_switch,0x12C); ROOM_CHECK(RoomScrollActor,changed,0x12D);
ROOM_CHECK(RoomScrollActor,colour,0x1A4); ROOM_CHECK(RoomScrollActor,private_switch,0x1A8);
#ifdef __mips__
#define room_scroll_lives ((const RoomScrollLives *)0x804BBC10u)
#else
extern RoomScrollLives af_v3_test_room_scroll_lives;
#define room_scroll_lives (&af_v3_test_room_scroll_lives)
#endif
extern void sAdo_OngenPos(u32,u8,float *);
extern void sAdo_OngenTrgStart(u32,float *);
#ifdef AF_V3_ROOM_CONTACT
/* The contact getter resolves the current room through the native clip. A
   null preview room argument is not evidence that this global owner exists. */
typedef struct { u8 before_direction[0x1A0]; int direction; } RoomContactOwner;
typedef struct { RoomContactOwner *owner; } RoomContactClip;
ROOM_CHECK(RoomContactOwner,direction,0x1A0);
#ifdef __mips__
#define room_contact_clip (*(RoomContactClip *volatile *)0x80136F2Cu)
#define room_contact_floor (*(volatile signed char *)0x80137655u)
#else
extern RoomContactClip *af_v3_test_contact_clip;
extern signed char af_v3_test_contact_floor;
#define room_contact_clip af_v3_test_contact_clip
#define room_contact_floor af_v3_test_contact_floor
#endif
extern float add_calc(float *,float,float,float,float);
#endif
#endif
#endif
