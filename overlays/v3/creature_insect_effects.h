#ifndef AF_V3_INSECT_EFFECTS_H
#define AF_V3_INSECT_EFFECTS_H
#include "creature_insects.h"
typedef struct {
    s16 timer,name,program,arg0,arg1,waiting;
    u16 item;
    u8 priority,state;
    xyz_t position,velocity,acceleration,scale,offset;
    s16 specific[6];
} AfInsectEffect;
typedef struct {
    void (*request)(int,xyz_t,int,s16,GAME *,u16,s16,s16);
    void *unused[9];
    AfInsectEffect *(*create)(s16,xyz_t,xyz_t *,GAME *,void *,u16,int,s16,s16);
} AfInsectEffectClip;
extern AfInsectEffectClip *af_insect_effect_clip;
AfInsectEffect *af_insect_mud_create(s16,xyz_t,xyz_t *,GAME *,void *,u16,int,s16,s16);
_Static_assert(sizeof(AfInsectEffect)==0x58,"Native effect stride");
_Static_assert(offsetof(AfInsectEffect,scale)==0x34,"Native effect scale");
_Static_assert(offsetof(AfInsectEffect,specific)==0x4C,"Native effect work");
#ifdef __mips__
_Static_assert(offsetof(AfInsectEffectClip,create)==0x28,"Native effect constructor");
#endif
#endif
