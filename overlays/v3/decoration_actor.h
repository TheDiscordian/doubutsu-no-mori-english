/* Complete donor actor controllers use the native actor prefix and explicit
   providers for source-only interactions; never cast GC saved data to N64. */
#ifndef AF_DECORATION_ACTOR_H
#define AF_DECORATION_ACTOR_H
#include "decoration_draw.h"
typedef u16 mActor_name_t;
typedef u8 lbRTC_hour_t;
typedef struct { u8 sec,min,hour,day,weekday,month;u16 year; } lbRTC_time_c;
typedef struct { ACTOR actor_class; } PLAYER_ACTOR;
typedef struct { u8 bytes[20]; } cKF_Animation_R_c;
typedef void (*aSTR_MOVE_PROC)(STRUCTURE_ACTOR*,GAME_PLAY*);
typedef void (*RADIO_PROC)(RADIO_ACTOR*,GAME_PLAY*);
typedef struct { void (*anime_play_proc)(void);int anime_play_flag; } aCOU_Clip_c;
typedef struct {
    int (*get_msgno_proc)(mActor_name_t);
    void (*random_topsize_proc)(void),(*set_topname_proc)(void);
    int (*fish_rndsize_proc)(int);
} aTRC_clip_c;
typedef struct {
    mActor_name_t (*search_pick_up_item_layer2_proc)(GAME*);
    xyz_t pickup_pos;s16 pickup_counter;
} aHTBL_Clip_c;
typedef struct {
    u8 player_name[8],land_name[8];u16 player_id,land_id;
} PersonalID_c;
typedef struct { PersonalID_c player_ID; } Private_c;
typedef struct { int size;PersonalID_c pID;s16 pos[2];u8 talk_flag,flag; } aEANG_event_data_c;
typedef void mMsg_Window_c;
typedef struct {
    void (*effect_make_proc)(int,xyz_t,int,s16,GAME*,mActor_name_t,int,int);
} AFDecorEffectClip;
typedef struct {
    aCOU_Clip_c *countdown_clip;aTRC_clip_c *turi_clip;aHTBL_Clip_c *htbl_clip;
    AFDecorEffectClip *effect_clip;
} AFDecorActorClips;
typedef struct {
    struct { lbRTC_time_c rtc_time;int now_sec; } time;
    AFDecorActorClips clip;Private_c private_view;
    aCOU_Clip_c countdown;aTRC_clip_c fishing;
} AFDecorActorContext;
extern AFDecorActorContext af_decor_actor_context;
typedef struct {
    u16 source_name,native_name,profile,owner;
    u16 source_dummy,native_dummy;u32 dependencies;
    AFDecorDraw ctor,dtor,init,move;
} AFDecorActorRecord;
extern const AFDecorActorRecord af_decor_actor_records[18];
extern u8 af_decor_actor_descriptors[11][32];
void *af_decor_actor_descriptor(int);
ACTOR *af_decor_actor_setup(GAME*,u16,float,float,s16);
void af_decor_actor_free(ACTOR*);
extern void *af_decor_previous_descriptor(int);
extern ACTOR *af_decor_previous_setup(GAME*,u16,float,float,s16);
extern ACTOR *af_decor_native_make(void*,GAME*,s16,float,float,float,s16,s16,s16,
    signed char,signed char,s16,u16,s16,signed char,int);
extern float af_decor_native_ground(xyz_t,float);
extern void *af_decor_native_structure_clip;
typedef struct {
    u32 ready; /* Installed providers, never a per-frame fabricated success. */
    int (*demo)(int,ACTOR*);
    int (*resolve)(u16);
    void (*effect)(int,xyz_t,int,s16,GAME*,mActor_name_t,int,int);
    int (*pocket)(mActor_name_t,int);
    aEANG_event_data_c *(*fish_save)(int,int);
    int (*fish_size)(int),(*fish_npc_size)(int),(*event_npc)(u16*);
    void (*npc_name)(u8*,u16),(*random_name)(u8*),(*fish_record)(PersonalID_c*,int);
    mMsg_Window_c *(*message)(void);
    int (*number)(u8*,int,int);
    void (*string)(mMsg_Window_c*,int,const u8*,int);
} AFDecorActorServices;
extern const AFDecorActorServices af_decor_actor_services;
enum { AF_DECOR_DEMO=1,AF_DECOR_IDENTITIES=2,AF_DECOR_EFFECT=4,
       AF_DECOR_FISH=8,AF_DECOR_HARVEST=16 };
int af_decor_actor_call(ACTOR*,GAME*,unsigned int);
void af_decor_actor_ctor(ACTOR*,GAME*),af_decor_actor_dtor(ACTOR*,GAME*);
void af_decor_actor_init(ACTOR*,GAME*),af_decor_actor_move(ACTOR*,GAME*);
void af_decor_actor_draw(ACTOR*,GAME*);
u16 af_decor_source_name(ACTOR*);
int af_decor_source_fg(u16,xyz_t,int);
int af_decor_source_demo(int,ACTOR*);
int af_decor_actor_demo(int,ACTOR*);
extern int af_decor_native_demo(int,ACTOR*);
void af_decor_source_collision(ACTOR*);
void af_decor_source_move_install(ACTOR*,AFDecorDraw);
void af_decor_source_rig_ct(cKF_SkeletonInfo_R_c*,cKF_Skeleton_R_c*,void*,s_xyz*,s_xyz*);
void af_decor_source_rig_init(cKF_SkeletonInfo_R_c*,cKF_Skeleton_R_c*,void*,float,float,float,float,float,int,void*);
int af_decor_source_rig_play(cKF_SkeletonInfo_R_c*);
int af_decor_source_status(int,int);
void af_decor_source_copy(void*,const void*,int);
void af_decor_source_zero(void*,unsigned int);
void af_decor_source_land(u8*);
void af_decor_source_personal(PersonalID_c*,const PersonalID_c*);
extern ACTOR *af_decor_native_player(void*);
extern void af_decor_native_delete(ACTOR*);
extern int mFI_Wpos2BlockNum(int*,int*,xyz_t);
extern int mFI_Wpos2UtNum(int*,int*,xyz_t);
extern int mFI_UtNum2CenterWpos(xyz_t*,int,int);
extern u16 *af_decor_native_fg(xyz_t);
extern int af_decor_native_fg_set(u16,xyz_t,int);
extern float mCoBG_GetBgY_OnlyCenter_FromWpos(xyz_t,float);
extern void *zelda_malloc(unsigned int);
extern void zelda_free(void*);
extern void Matrix_Position(const xyz_t*,xyz_t*);
extern void cKF_SkeletonInfo_R_dt(cKF_SkeletonInfo_R_c*);
extern const lbRTC_time_c af_decor_native_rtc;
extern int af_holiday_native_type(unsigned int);
extern int af_decor_native_status(int,int);
extern void af_decor_native_rig_ct(cKF_SkeletonInfo_R_c*,cKF_Skeleton_R_c*,void*,s_xyz*,s_xyz*);
extern void af_decor_native_rig_init(cKF_SkeletonInfo_R_c*,cKF_Skeleton_R_c*,void*,float,float,float,float,float,int,void*);
extern int af_decor_native_rig_play(cKF_SkeletonInfo_R_c*);
void af_decor_source_unit_set(u16,int,int,int);
void af_decor_noop(void*,void*);
#ifdef __mips__
_Static_assert(sizeof(AFDecorActorRecord)==32,"Actor registry stride");
_Static_assert(sizeof(PersonalID_c)==20,"Normalized donor personal identity");
_Static_assert(sizeof(aEANG_event_data_c)==32,"Normalized donor fishing record");
_Static_assert(sizeof(aHTBL_Clip_c)==20,"Harvest interaction storage");
_Static_assert(sizeof(AFDecorActorContext)<=0x100,"Owned controller context reservation");
_Static_assert(sizeof(AFDecorActorServices)<=0xF0,"Owned provider directory reservation");
#endif
#undef Common_Get
#undef CLIP
#undef aCOU_ACT_HAPPY_NEW_YEAR
#define Common_Get(x) (af_decor_actor_context.x)
#define Common_GetPointer(x) (&af_decor_actor_context.x)
#define CLIP(x) Common_Get(clip.x)
#define Now_Private (&af_decor_actor_context.private_view)
#define GET_PLAYER_ACTOR(g) ((PLAYER_ACTOR*)af_decor_native_player(g))
#define GET_PLAYER_ACTOR_ACTOR(g) af_decor_native_player(g)
#define GET_PLAYER_ACTOR_GAME_ACTOR(g) af_decor_native_player(g)
#define get_player_actor_withoutCheck(g) GET_PLAYER_ACTOR(g)
#define Actor_delete af_decor_native_delete
#define mDemo_Check af_decor_source_demo
#define mFI_SetFG_common af_decor_source_fg
#define cKF_SkeletonInfo_R_ct af_decor_source_rig_ct
#define cKF_SkeletonInfo_R_init af_decor_source_rig_init
#define cKF_SkeletonInfo_R_play af_decor_source_rig_play
#define mEv_check_status af_decor_source_status
#define none_proc1 af_decor_noop
#define MTX_LOAD 0
#define lbRTC_JUNE 6
#define lbRTC_DECEMBER 12
#define cKF_FRAMECONTROL_STOP 0
#define mFI_UT_WORLDSIZE_HALF_Z_F 20.0f
#define mTM_TIME2SEC(h,m,s) ((h)*3600+(m)*60+(s))
#define ARRAY_COUNT(a) ((int)(sizeof(a)/sizeof((a)[0])))
#define SQ(a) ((a)*(a))
#define PLAYER_NAME_LEN 8
#define ANIMAL_NAME_LEN 8
#define mString_DEFAULT_STR_SIZE 16
#define mPr_ITEM_COND_NORMAL 0
#define mMsg_FREE_STR0 0
#define mMsg_FREE_STR1 1
#define mPr_GetPossessionItemIdxWithCond(p,i,c) af_decor_actor_services.pocket(i,c)
#define mEv_get_save_area(e,n) af_decor_actor_services.fish_save(e,n)
#define mFR_fish_rndsize(r) af_decor_actor_services.fish_size(r)
#define mFR_make_NpcRecord(h) af_decor_actor_services.fish_npc_size(h)
#define mEvMN_GetJointEventRandomNpc(p) af_decor_actor_services.event_npc(p)
#define mNpc_GetNpcWorldNameTableNo(p,n) af_decor_actor_services.npc_name(p,n)
#define mNpc_GetRandomAnimalName(p) af_decor_actor_services.random_name(p)
#define mEv_fishRecord_set(p,s) af_decor_actor_services.fish_record(p,s)
#define mMsg_Get_base_window_p() af_decor_actor_services.message()
#define mString_Load_NumberStringAddUnitFromRom(p,n,u) af_decor_actor_services.number(p,n,u)
#define mMsg_Set_free_str(w,s,p,n) af_decor_actor_services.string(w,s,p,n)
#define mPr_CopyPersonalID af_decor_source_personal
#define mLd_ClearLandName af_decor_source_land
#define mem_copy af_decor_source_copy
#define bzero af_decor_source_zero
#define mFI_UtNumtoFGSet_common af_decor_source_unit_set
/* Pointer lifetime is confined to the immediate source comparison. */
u16 *af_decor_source_get_fg(xyz_t);
#define mFI_GetUnitFG af_decor_source_get_fg
#endif
