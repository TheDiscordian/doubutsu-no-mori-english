#ifndef AF_V3_CREATURE_INSECT_COLLISION_H
#define AF_V3_CREATURE_INSECT_COLLISION_H
#include "creature_insect_engine.h"
typedef struct {
    xyz_t position;
    f32 height,radius;
    s16 attribute,padding;
    int x,z;
} AfInsectColumn;
typedef struct {
    s16 actor;
    u8 check_type,old_ground,unused,old_water,padding[2];
    AfInsectCollisionResult *result;
    f32 speed[2],previous_speed[2];
    xyz_t centre,old_centre,reverse;
    f32 range,ground_distance,old_ground_y,ground_y,wall_heights[2];
    mCoBG_WallInfo_c walls[2];
    s16 unit_count,unused2;
    u32 stopped;
} AfInsectBgContext;
extern AfInsectBgContext af_insect_bg_context;
extern void af_insect_native_columns(AfInsectColumn *,int *,void *,int,int,u16,u16);
extern int af_insect_world_block(int *,int *,xyz_t);
extern void af_insect_ground_check(xyz_t *,AfInsectBgContext *,ACTOR *,f32,
                                  AfInsectCollisionResult *,s_xyz *,int);
extern void af_insect_apply_reverse(ACTOR *,xyz_t,int);
extern int af_insect_acre_inset(int,int);
void af_insect_columns(AfInsectColumn *,int *,void *,int,int,u16,u16);
#ifdef __mips__
_Static_assert(sizeof(AfInsectColumn)==0x20,"native collision column");
_Static_assert(sizeof(AfInsectBgContext)==0x68,"native collision context");
_Static_assert(offsetof(AfInsectBgContext,reverse)==0x34,"native collision reversal");
#endif
#endif
