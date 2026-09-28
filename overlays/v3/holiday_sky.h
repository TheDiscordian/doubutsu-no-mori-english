#ifndef AF_V3_HOLIDAY_SKY_H
#define AF_V3_HOLIDAY_SKY_H
#include "room_effects.h"
enum { AF_SKY_MOON=115,AF_SKY_SET,AF_SKY_SHOOTING,AF_SKY_KIRA };
typedef struct { u8 sec,min,hour,day,weekday,month;u16 year; } AFSkyClock;
typedef struct { struct { u8 prefix[0x28];struct { EffectPosition position; } world; } actor_class; } AFSkyPlayer;
typedef struct {
    void (*request)(int,EffectPosition,int,s16,void *,u16,s16,s16);
    void *kill,*rotate,*speed;
    void (*continuous)(RoomEffect *,s16,s16);
    float (*adjust)(s16,s16,s16,float,float);
    void *matrix,*offset,*unused20,*unused24;
    RoomEffect *(*create)(s16,EffectPosition,EffectPosition *,void *,void *,u16,int,s16,s16);
    void *morph,*light,*decide;
    int (*lookat)(EffectPosition);
    void *status,*center,*kill_all;
} AFSkyClip;
typedef struct {
    u32 moon,shooting,kira,kira_mode;
    u16 moon_width[2],moon_height[2];
    s16 moon_x[2],moon_y[2];
} AFSkyArt;
extern const AFSkyArt af_sky_art;
extern AFSkyClip *af_sky_native_clip;
extern const AFSkyClock af_sky_native_rtc;
extern u8 *af_sky_native_debug;
extern void *af_sky_native_npc_clip;
AFSkyPlayer *af_sky_player(void *);
int af_sky_ready(void *);
AFSkyClock af_sky_clock(void);
int af_sky_seconds(void);
s16 af_sky_debug(unsigned int);
float af_effect_random(void),sin_s(s16),cos_s(s16);
int mFI_BlockKind2BkNum(int *,int *,u32);
int mFI_BkNum2WposXZ(float *,float *,int,int);
float mFI_BkNum2BaseHeight(int,int);
int af_sky_title_demo(void);
void af_sky_attention(int,void *,EffectPosition *);
void af_sky_request(int,EffectPosition,int,s16,void *,u16,s16,s16);
RoomEffect *af_sky_create(s16,EffectPosition,EffectPosition *,void *,void *,u16,int,s16,s16);
void af_sky_continuous(RoomEffect *,s16,s16);
float af_sky_adjust(s16,s16,s16,float,float);
int af_sky_lookat(EffectPosition);
void af_sky_moon_draw(RoomEffect *,void *);
void af_sky_shooting_draw(RoomEffect *,void *);
void af_sky_kira_draw(RoomEffect *,void *);
/* Source spellings describe compatible records, not GameCube actor offsets. */
typedef EffectPosition xyz_t;
typedef RoomEffect eEC_Effect_c;
typedef AFSkyClock lbRTC_time_c;
typedef AFSkyPlayer PLAYER_ACTOR;
typedef void GAME;
typedef float f32;
#ifndef NULL
#define NULL ((void *)0)
#endif
#define TRUE 1
#define FALSE 0
#define effect_specific specific
#define prio priority
#define item_name item
#define RANDOM_F(maximum) (af_effect_random()*(maximum))
#define RANDOM(maximum) ((int)RANDOM_F(maximum))
#define DEG2SHORT_ANGLE(deg) ((s16)(int)((deg)*(65536.0f/360.0f)))
#define eEC_EFFECT_NIGHT13_MOON AF_SKY_MOON
#define eEC_EFFECT_SHOOTING_SET AF_SKY_SET
#define eEC_EFFECT_SHOOTING AF_SKY_SHOOTING
#define eEC_EFFECT_SHOOTING_KIRA AF_SKY_KIRA
#define mRF_BLOCKKIND_POOL (1u<<15)
#define mFI_BK_WORLDSIZE_HALF_X_F 320.0f
#define mFI_BK_WORLDSIZE_HALF_Z_F 320.0f
#define mEv_TITLEDEMO_STAFFROLL (-9)
#define aNPC_ATTENTION_TYPE_POSITION 2
#ifdef __mips__
ROOM_CHECK(AFSkyClip,continuous,0x10);ROOM_CHECK(AFSkyClip,create,0x28);
ROOM_CHECK(AFSkyClip,lookat,0x38);
#endif
ROOM_CHECK(AFSkyPlayer,actor_class.world.position,0x28);
#endif
