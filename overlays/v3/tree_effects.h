#ifndef AF_V3_TREE_EFFECTS_H
#define AF_V3_TREE_EFFECTS_H
#include "room_effects.h"
typedef float f32;
typedef EffectPosition xyz_t;
typedef struct { s16 x,y,z; } s_xyz;
typedef struct { s16 x,z; } s_xz;
typedef RoomCommand Gfx;
typedef struct __attribute__((aligned(8))) { u32 words[16]; } Mtx;
typedef RoomRigGraphics GRAPH;
typedef struct { GRAPH *graph;u8 pad[0xA0-sizeof(GRAPH *)];u32 frame_counter; } GAME;
typedef GAME GAME_PLAY;
typedef struct { u8 native[0x174]; } ACTOR;
typedef struct { u8 joints,shown,pad[2];void *rows; } cKF_Skeleton_R_c;
typedef struct { void *arrays[4];s16 unused,duration; } cKF_Animation_R_c;
typedef struct {
    struct { f32 start,end,duration,speed,current;int mode; } frame_control;
    cKF_Skeleton_R_c *skeleton;cKF_Animation_R_c *animation;f32 morph_counter;
    s_xyz *work,*morph,*diff;u8 movement[0x40];
} cKF_SkeletonInfo_R_c;
typedef int (*TreeDraw)(GAME *,cKF_SkeletonInfo_R_c *,int,Gfx **,u8 *,void *,s_xyz *,xyz_t *);
typedef RoomEffect eEC_Effect_c;
typedef struct { u16 *cedar_tree_pal,*palm_tree_pal,*golden_tree_pal; } mFM_field_pal_c;
typedef struct {
    void (*effect_make_proc)(int,xyz_t,int,s16,GAME *,u16,s16,s16);
    RoomEffect *(*make_effect_proc)(s16,xyz_t,xyz_t *,GAME *,void *,u16,int,s16,s16);
    void (*random_first_speed_proc)(xyz_t *,f32,f32,f32);
    f32 (*calc_adjust_proc)(s16,s16,s16,f32,f32);
} TreeEffectServices;
extern const TreeEffectServices af_tree_services;
extern void (*af_tree_make_clip)(GAME *,s16,s16,xyz_t *);
extern const u16 af_tree_palette_data[3][14][16];
extern const u8 af_tree_palette_terms[18];
extern const u32 af_tree_sprites[11];
extern const u8 af_tree_art[];
extern const xyz_t ZeroVec;
#define NULL ((void *)0)
#define TRUE 1
#define FALSE 0
#define MTX_LOAD 0
#define MTX_MULT 1
#define G_MTX_NOPUSH 0
#define G_MTX_LOAD 2
#define G_MTX_MODELVIEW 0
#define ANIME_1_TXT_SEG 8
#define ANIME_2_TXT_SEG 9
#define G_MWO_SEGMENT_8 8
#define G_TA_DOLPHIN 0
#define G_TA_N64 0
#define G_RM_FOG_SHADE_A 0xC8000000u
#define G_RM_AA_ZB_TEX_EDGE2 0x00113078u
#define G_RM_ZB_CLD_SURF2 0x00104B50u
#define mTM_SEASON_WINTER 3
#define mTM_TERM_4 4
#define mTM_TERM_15 15
#define mTM_TERM_16 16
#define eEC_EFFECT_BUSH_HAPPA 120
#define eEC_EFFECT_YOUNG_TREE 121
#define eEC_EFFECT_BUSH_YUKI 52
#define eEC_BUSH_HAPPA_PALM 0x2000
#define eEC_BUSH_HAPPA_CEDAR 0x4000
#define eEC_BUSH_HAPPA_GOLD 0x6000
#define RSV_NO 0xFFFF
#define NA_SE_61 0x61
#define NA_SE_63 0x63
#define NA_SE_65 0x65
#define NA_SE_67 0x67
#define NA_SE_108 0x108
#define ABS(v) ((v)<0?-(v):(v))
#define RANDOM_F(v) (fqrand()*(v))
#define RANDOM2_F(v) (fqrand2()*(v))
#define effect_specific specific
#define prio priority
#define item_name item
#define eEC_CLIP (&af_tree_services)
#define CLIP(member) af_tree_make_clip
#define GETREG(bank,index) af_tree_debug(index)
#define OPEN_DISP(g) { GRAPH *__tree_g=(g);
#define CLOSE_DISP(g) }
#define NEXT_POLY_OPA_DISP (__tree_g->head++)
#define NEXT_POLY_XLU_DISP (__tree_g->xlu_head++)
static inline void af_tree_command(Gfx *p,u32 a,u32 b) { *p=(Gfx){a,b}; }
#define gSPSegment(p,s,a) af_tree_command((p),0xDB060000u|((s)*4u),(u32)(uptr)(a))
#define gSPDisplayList(p,a) af_tree_command((p),0xDE000000u,(u32)(uptr)(a))
#define gSPMatrix(p,a,mode) af_tree_command((p),0xDA380001u|(mode),(u32)(uptr)(a))
#define gDPSetPrimColor(p,m,l,r,g,b,a) af_tree_command((p),0xFA000000u|((m)<<8)|(l),((u32)(r)<<24)|((u32)(g)<<16)|((u32)(b)<<8)|(a))
#define gDPSetRenderMode(p,a,b) af_tree_command((p),0xE200001Cu,(a)|(b))
/* GX's texture-adjust switch has no N64 command; the converter supplies native
 * texture coordinates and complete native load/tile commands instead. */
#define gDPSetTextureAdjustMode(p,m) ((void)0)
extern f32 fqrand(void),fqrand2(void),sin_s(s16),cos_s(s16),sqrtf(f32);
extern u32 qrand(void);
extern void xyz_t_add(xyz_t *,xyz_t *,xyz_t *),xyz_t_sub(xyz_t *,xyz_t *,xyz_t *);
extern void xyz_t_mult_v(xyz_t *,f32);
extern f32 search_position_distance(xyz_t *,xyz_t *);
extern void add_calc_short_angle2(s16 *,s16,f32,s16,s16);
extern u16 *mFI_GetUnitFG(xyz_t);
extern f32 mCoBG_GetBgY_AngleS_FromWpos(void *,xyz_t,f32);
extern int mFI_Wpos2UtNum_inBlock(int *,int *,xyz_t);
extern void sAdo_OngenTrgStart(u32,xyz_t *);
#define cKF_SkeletonInfo_R_ct af_tree_keyframe_ct
#define cKF_SkeletonInfo_R_init_standard_stop af_tree_keyframe_stop
#define cKF_SkeletonInfo_R_play af_tree_keyframe_play
#define cKF_Si3_draw_R_SV af_tree_keyframe_draw
extern void cKF_SkeletonInfo_R_ct(cKF_SkeletonInfo_R_c *,cKF_Skeleton_R_c *,cKF_Animation_R_c *,s_xyz *,s_xyz *);
extern void cKF_SkeletonInfo_R_init_standard_stop(cKF_SkeletonInfo_R_c *,cKF_Animation_R_c *,s_xyz *);
extern int cKF_SkeletonInfo_R_play(cKF_SkeletonInfo_R_c *);
extern void cKF_Si3_draw_R_SV(GAME *,cKF_SkeletonInfo_R_c *,Mtx *,TreeDraw,TreeDraw,void *);
extern void Matrix_translate(f32,f32,f32,u8),Matrix_scale(f32,f32,f32,u8);
extern void Matrix_Position_VecX(f32,xyz_t *),Matrix_RotateVector(s16,xyz_t *,int);
extern void suMtxMakeSRT_ZXY(Mtx *,f32,f32,f32,s16,s16,s16,f32,f32,f32);
extern void _texture_z_light_fog_prim(GRAPH *),_texture_z_light_fog_prim_xlu(GRAPH *);
extern void osWritebackDCache(void *,int);
int af_tree_resources(void),af_tree_ready(GAME *),af_tree_term(void),af_tree_season(void);
u32 af_tree_frame(GAME *);
s16 af_tree_debug(unsigned int);
mFM_field_pal_c *af_tree_palettes(void);
int af_tree_collision(xyz_t),af_tree_admit(s16);
void af_tree_camera(GAME *,xyz_t *);
void af_tree_leaf_draw(RoomEffect *,GAME *),af_tree_young_draw(RoomEffect *,GAME *);
int af_tree_draw_space(GAME *);
Mtx *af_tree_alloc(GRAPH *);
#define GRAPH_ALLOC_TYPE(g,type,n) af_tree_alloc(g)
#ifdef __mips__
_Static_assert(sizeof(cKF_SkeletonInfo_R_c)==0x70,"Native keyframe workspace");
ROOM_CHECK(GAME,frame_counter,0xA0);
#endif
#endif
