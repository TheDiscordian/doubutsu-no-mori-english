#ifndef AF_V3_REWARD_EFFECTS_H
#define AF_V3_REWARD_EFFECTS_H
#include "holiday_sky.h"
#ifndef AF_RW_EFFECT_FIRST
#define AF_RW_EFFECT_FIRST 122
#endif
#define eEC_EFFECT_MAKE_HEM AF_RW_EFFECT_FIRST
#define eEC_EFFECT_MAKE_HEM_KIRA (AF_RW_EFFECT_FIRST+1)
#define eEC_EFFECT_MAKE_HEM_LIGHT (AF_RW_EFFECT_FIRST+2)
#define eEC_STATE_NORMAL 0
#define eEC_STATE_FINISHED 2
#define RSV_NO 0xFFFF
extern volatile const u8 af_hp_native_ticks;
extern int af_rw_effect_light_index;
extern const u32 af_rw_effect_models[3],af_rw_effect_kira_mode;
extern const u16 af_rw_effect_sounds[2];
int *af_rw_hem_visible(void);
int af_rw_effect_ready(void *);
void af_rw_effect_request(int,xyz_t,int,s16,void *,u16,s16,s16);
RoomEffect *af_rw_effect_create(s16,xyz_t,xyz_t *,void *,void *,u16,int,s16,s16);
void af_rw_effect_kill(int,u16);
void af_rw_effect_sound(u32,xyz_t *);
int af_rw_effect_light_reserve(void *,xyz_t *,u8,u8,u8,s16);
int af_rw_effect_light_cancel(int,void *);
void af_rw_effect_light_colour(int,u8,u8,u8);
void af_rw_effect_reset(void *);
void af_rw_effect_sphere_draw(RoomEffect *,void *);
void af_rw_effect_kira_draw(RoomEffect *,void *);
void af_rw_effect_light_draw(RoomEffect *,void *);
void xyz_t_add(xyz_t *,xyz_t *,xyz_t *);
void add_calc(float *,float,float,float,float);
float mCoBG_GetBgY_OnlyCenter_FromWpos2(xyz_t,float);
#endif
