#ifndef AF_V3_ROOM_EFFECTS_H
#define AF_V3_ROOM_EFFECTS_H
#include "room_rigs.h"
typedef struct { float x,y,z; } EffectPosition;
typedef struct { u8 r,g,b,a; } EffectColour;
typedef struct {
    s16 timer,name,program,arg0,arg1,waiting;
    u16 item;
    u8 priority,state;
    EffectPosition position,velocity,acceleration,scale,offset;
    s16 specific[6];
} RoomEffect;
typedef struct {
    void (*request)(int,EffectPosition,int,s16,void *,u16,s16,s16);
    void *unused[4];
    float (*adjust)(s16,s16,s16,float,float);
    void *unused2[4];
    RoomEffect *(*create)(s16,EffectPosition,EffectPosition *,void *,void *,u16,int,s16,s16);
    void *morph;
    void (*light)(EffectColour,s16,s16,int);
} RoomEffectClip;
#define ROOM_EFFECT_FLASH 111
#define ROOM_EFFECT_FLASH_CONTROLLER 112
#ifdef __mips__
#define room_effect_clip (*(RoomEffectClip *volatile *)0x80136F3Cu)
#define room_effect_scene (*(volatile u32 *)0x80126EB4u)
#else
extern RoomEffectClip *af_test_effect_clip;
extern u32 af_test_effect_scene;
#define room_effect_clip af_test_effect_clip
#define room_effect_scene af_test_effect_scene
#endif
ROOM_CHECK(RoomEffect,position,0x10); ROOM_CHECK(RoomEffect,acceleration,0x28);
ROOM_CHECK(RoomEffect,scale,0x34); ROOM_CHECK(RoomEffect,specific,0x4C);
_Static_assert(sizeof(RoomEffect)==0x58,"Native effect pool stride");
#ifdef __mips__
ROOM_CHECK(RoomEffectClip,adjust,0x14); ROOM_CHECK(RoomEffectClip,create,0x28);
ROOM_CHECK(RoomEffectClip,light,0x30);
#endif
extern float af_effect_random(void);
#endif
