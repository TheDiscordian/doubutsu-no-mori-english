#ifndef AF_V3_HARVEST_EVENT_H
#define AF_V3_HARVEST_EVENT_H
/* Complete Harvest source actor uses the verified native NPC prefix. Source
 * personal/event layouts are owned views, never casts of native save padding.
 * Unbound state, selection, and world providers remain explicit link errors. */
#include "carried_event.h"
#include "harvest_state.h"
typedef AFHarvestPersonalID PersonalID_c;
typedef void (*aNPC_SUB_PROC)(NPC_ACTOR *,GAME_PLAY *);
_Static_assert(sizeof(PersonalID_c)==20,"Complete source personal identity");
void mEv_set_status(int,int);
void af_hr_begin_message(int),af_hr_continue_message(int);
int mMsg_Get_msg_num(mMsg_Window_c *);
int af_hr_message(int);
int mDemo_Check_ListenAble(void);
void af_rw_npc_save(ACTOR *,GAME *);
unsigned int af_hr_enabled_mask(void);
u16 af_hr_reward(unsigned int);
int af_hr_insert(void *,u16,int);
u32 af_hr_frame(void);
GAME *af_hr_game(void);
void af_hr_force_angle(GAME *,const xyz_t *,const s_xyz *,int);
f32 sqrtf(f32);
void add_calc(f32 *,f32,f32,f32,f32);
void add_calc_short_angle2(s16 *,s16,f32,s16,s16);
#endif
