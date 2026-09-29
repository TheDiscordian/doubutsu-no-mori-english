/* Native insect ABI for the complete added-species behaviour category.
 * Donor C is compiled locally against this header, never against GC GAME/ACTOR.
 * The expanded controller owns nine native 0x280-byte objects. The guarded
 * installer extends all native allocations/loops; individual actors keep size.
 */
#ifndef AF_V3_CREATURE_INSECTS_H
#define AF_V3_CREATURE_INSECTS_H
#include <stddef.h>
#include <stdint.h>
typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef float f32;
typedef u16 mActor_name_t;
typedef struct { f32 x,y,z; } xyz_t;
typedef struct { s16 x,y,z; } s_xyz;
typedef struct { xyz_t position; s_xyz angle; s16 padding; } PositionAngle;
typedef struct GAME GAME;
typedef GAME GAME_PLAY;
typedef struct ACTOR ACTOR;
typedef void (*mActor_proc)(ACTOR *,GAME *);
typedef struct { s16 angleY,type; } mCoBG_WallInfo_c;
typedef struct {
    u32 on_ground:1,hit_attribute_wall:5,hit_wall:5,hit_wall_count:3,jump_flag:1,
        unit_attribute:6,is_on_move_bg_obj:1,is_in_water:1,remaining:9;
} AfInsectCollisionResult;
typedef struct {
    u8 units[0x14];
    AfInsectCollisionResult result;
    f32 wall_top_y,wall_bottom_y,ground_y;
    mCoBG_WallInfo_c wall_info[2];
    s16 in_front_wall_angle_y,padding;
} AfInsectCollision;
typedef struct {
    s_xyz rotation;
    s16 padding;
    f32 ofs_y;
    void (*shadow_proc)(void);
    f32 shadow_size_x,shadow_size_z,shadow_size_change_rate,shadow_alpha_change_rate;
    u8 opaque[0xC];
    u8 draw_shadow,unk_2D,force_shadow_position,unused[0x19];
} AfInsectShape;
struct ACTOR {
    s16 id;
    u8 part,restore_fg;
    s16 scene_id;
    u16 npc_id;
    s8 block_x,block_z;
    s16 move_actor_list_idx;
    PositionAngle home;
    u32 state_bitfield;
    s16 actor_specific,data_bank_id;
    PositionAngle world;
    xyz_t last_world_position;
    PositionAngle eye;
    xyz_t scale,position_speed;
    f32 speed,gravity,max_velocity_y,ground_y;
    AfInsectCollision bg_collision_check;
    u8 unknown_b4,drawn;
    s16 player_angle_y;
    f32 player_distance,player_distance_xz,player_distance_y;
    struct { xyz_t displacement; u8 tail[0xC]; } status_data;
    AfInsectShape shape_info;
    xyz_t camera_position;
    f32 camera_w,cull_width,cull_height,cull_distance,cull_radius,talk_distance;
    u8 cull_while_talking,skip_drawing,padding[2];
    ACTOR *parent_actor,*child_actor,*prev_actor,*next_actor;
    mActor_proc ct_proc,dt_proc,mv_proc,dw_proc,sv_proc;
    void *dlftbl;
};
typedef struct { ACTOR actor_class; } PLAYER_ACTOR;
typedef void (*aINS_MOVE_PROC)(ACTOR *);
typedef void (*aINS_ACTION_PROC)(ACTOR *,GAME *);
typedef struct {
    u8 type,padding;
    s16 x,y,z;
    u8 red,green,blue,glow;
    s16 radius;
} AfInsectPointLight;
typedef struct aINS_INSECT_ACTOR {
    struct { ACTOR actor_class; u8 work[0x44]; int init_matrix; u8 tail[0xC]; } tools_actor;
    int exist_flag,type;
    aINS_MOVE_PROC move_proc;
    int action;
    aINS_ACTION_PROC action_proc;
    f32 _1E0,_1E4; /* donor names; native animation fields are 1DC/1E0 */
    int native_1E4;
    f32 speed_step,target_speed,native_1F0,patience;
    u8 col_pipe[0x1C];
    f32 bg_height;
    int bg_type;
    mActor_name_t item;
    struct { u8 destruct:1,bit_1:1,bit_2:1,bit_3:1,bit_4:1,bit_5:1,bit_6:1,bit_7:1; } insect_flags;
    u8 padding;
    int life_time,alpha_time,timer,continue_timer,flag;
    int s32_work0,s32_work1,s32_work2,s32_work3;
    f32 f32_work0,f32_work1,f32_work2,f32_work3;
    void *native_program;
    int alpha0,alpha1,alpha2;
    AfInsectPointLight point_light;
    void *light_list;
    int light_flag;
    s16 light_counter,light_step;
} aINS_INSECT_ACTOR;

/* Source-only fields do not occupy native collider/object/light storage. */
typedef struct { s16 ut_x,ut_z; f32 bg_range; } AfInsectExtra;
enum { AF_INSECT_WILD_SLOTS=8,AF_INSECT_RELEASE_SLOT=8,AF_INSECT_SLOTS=9 };
typedef struct {
    ACTOR actor_class;
    aINS_INSECT_ACTOR insects[AF_INSECT_SLOTS];
    int native_bank;
} AfInsectController;
typedef struct {
    int pl_action,pl_action_ut_x,pl_action_ut_z;
    aINS_MOVE_PROC position_move_proc;
} AfInsectEvents;
AfInsectExtra *af_insect_extra(aINS_INSECT_ACTOR *);
const AfInsectEvents *af_insect_events(void);
void af_v3_insect_bind_controller(AfInsectController *);
void af_v3_insect_unbind_controller(AfInsectController *);
int af_v3_insect_event(int,int,int);
void af_v3_insect_events_reset(void);
float af_v3_insect_catch_range(const aINS_INSECT_ACTOR *);
const xyz_t *af_insect_ball_position(void);
int af_insect_demo_active(void);
int af_insect_same_block(const ACTOR *,const GAME *);
u32 af_insect_source_frame(const GAME *);
PLAYER_ACTOR *af_insect_player(GAME *);
int af_insect_is_flower(mActor_name_t),af_insect_is_stump(mActor_name_t);
int af_insect_putting_net_away(GAME *);
void af_insect_effect(int,xyz_t,int,s16,GAME *,mActor_name_t,int,int);

/* These are adapter imports, not assumed GC-to-native symbol equivalences. */
f32 fqrand(void),sin_s(s16),cos_s(s16);
s16 atans_table(f32,f32);
int chase_f(f32 *,f32,f32),chase_angle(s16 *,s16,s16);
void xyz_t_move(xyz_t *,const xyz_t *);
void none_proc1(void);
int mFI_Wpos2UtNum(int *,int *,xyz_t);
int mFI_BkNum2WposXZ(f32 *,f32 *,int,int);
mActor_name_t *mFI_GetUnitFG(xyz_t);
f32 mCoBG_GetBgY_OnlyCenter_FromWpos(xyz_t,f32);
f32 mCoBG_GetBgY_OnlyCenter_FromWpos2(xyz_t,f32);
f32 mCoBG_GetBgY_AngleS_FromWpos(s_xyz *,xyz_t,f32);
f32 mCoBG_GetWaterHeight_File(xyz_t,const char *,int);
int mCoBG_GetWaterFlow(xyz_t *,u32);
u32 mCoBG_Wpos2BgAttribute_Original(xyz_t),mCoBG_Wpos2Attribute(xyz_t,s8 *);
int mCoBG_CheckWaterAttribute(u32),mCoBG_CheckHole_OrgAttr(u32);
int mPlib_Check_StopNet(xyz_t *),mPlib_Check_DigScoop(xyz_t *),mPlib_Check_HitAxe(xyz_t *);
uintptr_t mPlib_Get_item_net_catch_label(void);
int mPlib_Check_stung_mosquito(void *),mPlib_request_main_stung_mosquito_type1(void *);
void sAdo_OngenPos(u32,u32,xyz_t *),sAdo_OngenTrgStart(u32,xyz_t *);

#define TRUE 1
#define FALSE 0
#define SQ(x) ((x)*(x))
#define ABS(x) ((x)<0?-(x):(x))
#define F32_IS_ZERO(x) (ABS(x)<0.008f)
#define DEG2SHORT_ANGLE2(x) ((int)((x)*(65536.0f/360.0f)))
#define DEG2SHORT_ANGLE3(x) ((x)*(65536.0f/360.0f))
#define RANDOM_F(x) (fqrand()*(x))
#define RANDOM(x) ((int)RANDOM_F(x))
#define RANDOM_CENTER_F(x) ((fqrand()-0.5f)*(x))
#define GET_PLAYER_ACTOR(g) af_insect_player((GAME *)(g))
#define GET_PLAYER_ACTOR_GAME_ACTOR(g) ((ACTOR *)af_insect_player((GAME *)(g)))
#define get_player_actor_withoutCheck(g) af_insect_player((GAME *)(g))
#define IS_ITEM_FLOWER(x) af_insect_is_flower(x)
#define IS_ITEM_TREE_STUMP(x) af_insect_is_stump(x)
#define aINS_CLIP af_insect_events()
#define CLIP(x) af_insect_events()
#define mFI_UNIT_BASE_SIZE_F 40.0f
#define mFI_BK_WORLDSIZE_HALF_X_F 320.0f
#define mFI_BK_WORLDSIZE_HALF_Z_F 320.0f
#define mCoBG_HIT_WALL_FRONT 2
#define mCoBG_HIT_WALL_BACK 16
#define mCoBG_WALL_TYPE0 0

/* Donor constants. Sound/effect and item queries pass through native adapters. */
#define VERSION 0
#define VER_GAFU01_00 1
#define EMPTY_NO 0
#define RSV_NO 0xFFFF
enum { aINS_INIT_NORMAL,aINS_INIT_RELEASE };
enum { aINS_BG_CHECK_TYPE_NONE,aINS_BG_CHECK_TYPE_REG_ATTR,aINS_BG_CHECK_TYPE_REG_NO_ATTR,
       aINS_BG_CHECK_TYPE_NO_UNIT_COLUMN_ATTR,aINS_BG_CHECK_TYPE_NO_UNIT_COLUMN_NO_ATTR };
enum { aINS_PL_ACT_NONE,aINS_PL_ACT_REFLECT_AXE,aINS_PL_ACT_REFLECT_SCOOP,
       aINS_PL_ACT_DIG_SCOOP,aINS_PL_ACT_SHAKE_TREE };
enum { aINS_INSECT_TYPE_LADYBUG=24,aINS_INSECT_TYPE_SPOTTED_LADYBUG,aINS_INSECT_TYPE_MANTIS,
       aINS_INSECT_TYPE_SNAIL=32,aINS_INSECT_TYPE_MOLE_CRICKET,aINS_INSECT_TYPE_POND_SKATER,
       aINS_INSECT_TYPE_BAGWORM,aINS_INSECT_TYPE_PILL_BUG,aINS_INSECT_TYPE_SPIDER,
       aINS_INSECT_TYPE_ANT,aINS_INSECT_TYPE_MOSQUITO,aINS_INSECT_TYPE_SPIRIT };
enum { ITM_INSECT24=0x2D18,ITM_INSECT25,ITM_INSECT26,
       ITM_INSECT32=0x2D20,ITM_INSECT33,ITM_INSECT34,ITM_INSECT35,
       ITM_INSECT36,ITM_INSECT37,ITM_INSECT38,ITM_INSECT39,ITM_SPIRIT0 };
#ifdef AF_INSECT_CARRIED
#define AF_IMPORTED_INSECT_COUNT 9u
void aIHD_actor_init(ACTOR *,GAME *);
int af_carried_creature_enabled(int);
void af_carried_insect_light_delete(aINS_INSECT_ACTOR *,GAME *);
#else
#define AF_IMPORTED_INSECT_COUNT 8u
#endif
enum { NA_SE_25=0x25,NA_SE_26=0x26,NA_SE_MOLE_CRICKET_HIDE=0x44,
       NA_SE_MOLE_CRICKET_OUT=0x45,NA_SE_6A=0x6A,NA_SE_KA_BUZZ=0xCF,NA_SE_438=0x438 };
enum { eEC_EFFECT_TURI_HAMON=69,eEC_EFFECT_TURI_MIZU=70,eEC_EFFECT_DIG_MUD=84 };

void aITT_actor_init(ACTOR *,GAME *),aIKR_actor_init(ACTOR *,GAME *);
void aIAB_actor_init(ACTOR *,GAME *),aIMN_actor_init(ACTOR *,GAME *);
void aIDG_actor_init(ACTOR *,GAME *),aIKA_actor_init(ACTOR *,GAME *);
int af_v3_insect_init(aINS_INSECT_ACTOR *,GAME *);
void af_v3_insect_position(ACTOR *);
int af_v3_insect_tick(aINS_INSECT_ACTOR *,GAME *);
/* Called once per source half-step; adapter supplies player info, terrain,
 * collision, stress, and weather using native objects, not GC game offsets. */
void af_insect_environment(aINS_INSECT_ACTOR *,GAME *);
void af_insect_position_integrate(ACTOR *);

#ifdef __mips__
#define AF_OFFSET(t,f,n) _Static_assert(offsetof(t,f)==n,"insect ABI: " #f)
_Static_assert(sizeof(ACTOR)==0x174,"native actor size");
_Static_assert(sizeof(aINS_INSECT_ACTOR)==0x280,"native insect stride");
_Static_assert(sizeof(AfInsectController)==0x17F8,"expanded native insect controller size");
_Static_assert(offsetof(AfInsectController,native_bank)==0x17F4,"expanded graphics bank field");
AF_OFFSET(ACTOR,world,0x28);
AF_OFFSET(ACTOR,bg_collision_check.result,0x98);
AF_OFFSET(ACTOR,shape_info,0xDC);
AF_OFFSET(ACTOR,mv_proc,0x164);
AF_OFFSET(aINS_INSECT_ACTOR,exist_flag,0x1C8);
AF_OFFSET(aINS_INSECT_ACTOR,type,0x1CC);
AF_OFFSET(aINS_INSECT_ACTOR,move_proc,0x1D0);
AF_OFFSET(aINS_INSECT_ACTOR,_1E0,0x1DC);
AF_OFFSET(aINS_INSECT_ACTOR,speed_step,0x1E8);
AF_OFFSET(aINS_INSECT_ACTOR,target_speed,0x1EC);
AF_OFFSET(aINS_INSECT_ACTOR,patience,0x1F4);
AF_OFFSET(aINS_INSECT_ACTOR,col_pipe,0x1F8);
_Static_assert(sizeof(((aINS_INSECT_ACTOR *)0)->col_pipe)==0x1C,"native pipe size");
AF_OFFSET(aINS_INSECT_ACTOR,bg_height,0x214);
AF_OFFSET(aINS_INSECT_ACTOR,bg_type,0x218);
AF_OFFSET(aINS_INSECT_ACTOR,item,0x21C);
AF_OFFSET(aINS_INSECT_ACTOR,life_time,0x220);
AF_OFFSET(aINS_INSECT_ACTOR,flag,0x230);
AF_OFFSET(aINS_INSECT_ACTOR,s32_work0,0x234);
AF_OFFSET(aINS_INSECT_ACTOR,f32_work0,0x244);
AF_OFFSET(aINS_INSECT_ACTOR,native_program,0x254);
AF_OFFSET(aINS_INSECT_ACTOR,alpha0,0x258);
_Static_assert(sizeof(AfInsectPointLight)==14,"native point light size");
AF_OFFSET(aINS_INSECT_ACTOR,point_light,0x264);
AF_OFFSET(aINS_INSECT_ACTOR,light_list,0x274);
AF_OFFSET(aINS_INSECT_ACTOR,light_flag,0x278);
AF_OFFSET(aINS_INSECT_ACTOR,light_counter,0x27C);
AF_OFFSET(aINS_INSECT_ACTOR,light_step,0x27E);
#undef AF_OFFSET
#endif
#endif
