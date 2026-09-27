/* Verified native game fields used by the insect adapter. Not a GC GAME cast. */
#ifndef AF_V3_CREATURE_INSECT_ENGINE_H
#define AF_V3_CREATURE_INSECT_ENGINE_H
#include "creature_insects.h"
typedef struct { int count; ACTOR *head; } AfInsectActorList;
typedef struct {
    u8 prefix[0xE4];
    s8 acre_x,acre_z;
    u8 before_nature[0x1C58-0xE6];
    void (*nature)(ACTOR *);
    u8 before_lists[0x1C7C-0x1C58-sizeof(void (*)(ACTOR *))];
    AfInsectActorList lists[8];
    u8 before_projection[0x1E1C-0x1C7C-sizeof(AfInsectActorList)*8];
    f32 projection[16];
    u8 before_frame[0x1EA0-0x1E5C];
    u32 frame;
} AfInsectGameView;

extern GAME *af_insect_game;
extern PLAYER_ACTOR *af_insect_native_player(GAME *);
extern f32 af_insect_distance(const xyz_t *,const xyz_t *);
extern f32 af_insect_distance_xz(const xyz_t *,const xyz_t *);
extern s16 af_insect_angle(const xyz_t *,const xyz_t *);
extern void af_insect_native_bg(xyz_t *,ACTOR *,f32,f32,int,int,int);
extern void af_insect_project(const f32 *,const xyz_t *,xyz_t *,f32 *);
extern int af_insect_visible(const ACTOR *);
extern int af_insect_pipe_destroy(GAME *,void *);
extern void af_insect_world_to_eye(ACTOR *,f32);
extern const u32 *af_insect_unit(xyz_t);
/* These require actual collision integration; never aliases to ordinary BG. */
extern void af_insect_directed_bg(ACTOR *,f32,f32,int,int,int);
extern void af_insect_acre_wall(ACTOR *,f32);
extern void af_insect_register_catch(PLAYER_ACTOR *,GAME *,ACTOR *,f32);
void af_insect_begin_step(unsigned);
unsigned af_insect_step(void);
int af_v3_insect_slot(aINS_INSECT_ACTOR *,GAME *);

#ifdef __mips__
_Static_assert(offsetof(AfInsectGameView,nature)==0x1C58,"native nature callback");
_Static_assert(offsetof(AfInsectGameView,lists)==0x1C7C,"native actor lists");
_Static_assert(offsetof(AfInsectGameView,projection)==0x1E1C,"native projection");
_Static_assert(offsetof(AfInsectGameView,frame)==0x1EA0,"native frame counter");
#endif
#endif
