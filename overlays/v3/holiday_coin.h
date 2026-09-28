#ifndef AF_V3_HOLIDAY_COIN_H
#define AF_V3_HOLIDAY_COIN_H
#include "holiday_sky.h"
enum { AF_COIN_ID=119 };
extern const u8 af_coin_art[];
extern const u32 af_coin_models[2],af_coin_palettes[2];
extern const u16 af_coin_sounds[2];
extern volatile const u8 af_hp_native_ticks;
extern volatile u32 af_hp_native_segments[16];
void af_hp_coin(xyz_t,int,s16,GAME *,u16,s16,s16);
RoomEffect *af_coin_create(s16,xyz_t,xyz_t *,GAME *,void *,u16,int,s16,s16);
void af_coin_request(int,xyz_t,int,s16,GAME *,u16,s16,s16);
void af_coin_sound(u32,xyz_t *);
void af_coin_draw(RoomEffect *,GAME *);
void xyz_t_add(xyz_t *,xyz_t *,xyz_t *);
float fqrand(void);
#define eEC_EFFECT_COIN AF_COIN_ID
#define eEC_EFFECT_TURI_MIZU 70
#define mRF_BLOCKKIND_SHRINE 4
#endif
