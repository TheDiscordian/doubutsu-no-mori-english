/* Native drawing ABI for the complete source event-decoration controllers. */
#ifndef AF_DECORATION_DRAW_H
#define AF_DECORATION_DRAW_H
typedef unsigned char u8;
typedef unsigned short u16;
typedef signed short s16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef float f32;
typedef struct { float x,y,z; } xyz_t;
typedef struct { s16 x,y,z; } s_xyz;
typedef struct { u8 r,g,b,a; } rgba_t;
typedef struct { u32 a,b; } Gfx;
typedef struct { u32 words[16]; } Mtx;
typedef struct { u8 bytes[16]; } Vtx;
typedef struct { u8 num_joints,num_shown_joints;u16 padding;void *joint_table; } cKF_Skeleton_R_c;
typedef struct {
    struct { float start_frame,end_frame,max_frames,speed,current_frame;int mode; } frame_control;
    cKF_Skeleton_R_c *skeleton;
    u8 rest[0x70-0x18-sizeof(void*)];
} cKF_SkeletonInfo_R_c;
typedef struct { xyz_t position;s_xyz rotation;u16 padding; } AFDecorPosRot;
typedef struct {
    u8 prefix[6];u16 npc_id;u8 before_home[4];AFDecorPosRot home;
    u32 flags; s16 params,bank;AFDecorPosRot world;u8 rest[0x174-0x3C];
} ACTOR;
typedef struct {
    ACTOR actor_class;int keyframe_state;cKF_SkeletonInfo_R_c keyframe;
    int keyframe_saved_keyframe;s_xyz work_area[15],morph_area[15];
    u32 action_proc;int _2A4,structure_type,structure_pal,request_type,action;
    int arg0,arg1,arg2,arg3;float arg0_f,arg1_f,arg2_f,arg3_f;
} STRUCTURE_ACTOR;
typedef STRUCTURE_ACTOR HTABLE_ACTOR;
typedef STRUCTURE_ACTOR RADIO_ACTOR;
typedef struct { STRUCTURE_ACTOR structure_class; } MIKUJI_ACTOR,
    COUNT_ACTOR,TAMA_ACTOR,KAGO_ACTOR,TURI_ACTOR;
typedef struct {
    u8 before_opa[0x298];Gfx *opa;u8 *tail;
    u8 before_xlu[8];Gfx *xlu;u8 *xlu_tail;
    u8 before_shadow[0x2C8-0x2A8-2*sizeof(void*)];Gfx *shadow;u8 *shadow_tail;
} GRAPH;
typedef struct { GRAPH *graph; } GAME;
typedef struct { u32 count;u8 *flags;float size;Vtx *vertices;Gfx *model; } bIT_ShadowData_c;
typedef int (*AFDecorBefore)(GAME*,cKF_SkeletonInfo_R_c*,int,Gfx**,u8*,void*,s_xyz*,xyz_t*);
typedef void (*AFDecorDraw)(ACTOR*,GAME*);
typedef struct { u8 attribute; signed char a,b,c,d,e;u8 flags; } mCoBG_OffsetTable_c;
extern void mCoBG_SetPlussOffset(xyz_t,int,int);
extern void mCoBG_SetPluss5PointOffset_file(xyz_t,mCoBG_OffsetTable_c,const char*,int);
typedef struct {
    u16 source_name,owner;u32 rig_base,skeleton,animation;
    AFDecorDraw draw;
    void (*collision)(ACTOR*);
} AFDecorRecord;
extern const AFDecorRecord af_decor_records[18];
extern volatile u32 af_decor_segments[16];
extern void native_decor_matrix(void*);
extern void native_decor_writeback(void*,int);
extern void native_decor_rig_draw(GAME*,cKF_SkeletonInfo_R_c*,Mtx*,AFDecorBefore,void*,void*);
extern void Matrix_push(void),Matrix_pull(void);
extern void Matrix_translate(float,float,float,int);
extern void Matrix_RotateZ(s16,int);
extern void _texture_z_light_fog_prim(GRAPH*);
extern void _texture_z_light_fog_prim_npc(GRAPH*);
extern void _texture_z_light_fog_prim_shadow(GRAPH*);
extern void _texture_z_light_fog_prim_xlu(GRAPH*);
void *af_decor_alloc(GRAPH*,u32);
Mtx *af_decor_matrix(GRAPH*);
Gfx *af_decor_scroll(GRAPH*,int,u32,u32,int,int,int,u32,u32,int,int);
void af_decor_shadow(GAME*,bIT_ShadowData_c*,int);
void af_decor_rig_draw(GAME*,cKF_SkeletonInfo_R_c*,Mtx*,AFDecorBefore,void*,void*);
u16 *af_decor_palette(int);
int af_decor_draw(ACTOR*,GAME*,u16);
int af_decor_collision(ACTOR*,u16);
int af_decor_valid(const STRUCTURE_ACTOR*,u16);
typedef struct { u16 *(*get_pal_segment_proc)(int); } AFDecorStructureClip;
typedef struct { void (*draw_shadow_proc)(GAME*,bIT_ShadowData_c*,int); } AFDecorShadowClip;
typedef struct { const AFDecorStructureClip *structure_clip;const AFDecorShadowClip *bg_item_clip; } AFDecorClip;
extern const struct { AFDecorClip clip; } af_decor_common;
#ifdef __mips__
_Static_assert(sizeof(STRUCTURE_ACTOR)==0x2D8,"Native structure pool stride");
_Static_assert(__builtin_offsetof(STRUCTURE_ACTOR,arg0)==0x2B8,"Native structure arguments");
_Static_assert(__builtin_offsetof(GRAPH,xlu)==0x2A8,"Native translucent arena");
_Static_assert(__builtin_offsetof(GRAPH,shadow)==0x2C8,"Native shadow arena");
_Static_assert(sizeof(AFDecorRecord)==24,"Decoration directory stride");
_Static_assert(sizeof(ACTOR)==0x174,"Native actor prefix");
_Static_assert(__builtin_offsetof(ACTOR,world)==0x28,"Native actor world position");
#endif
#define NULL ((void*)0)
#define TRUE 1
#define FALSE 0
#define MTX_MULT 1
#define mCoBG_ATTRIBUTE_NONE 100
#define mFI_UT_WORLDSIZE_X_F 40.0f
#define mFI_UT_WORLDSIZE_Z_F 40.0f
#define mFI_UNIT_BASE_SIZE_F 40.0f
#define G_MTX_NOPUSH 0
#define G_MTX_LOAD 2
#define G_MTX_MODELVIEW 0
#define G_MWO_SEGMENT_8 8
#define ANIME_1_TXT_SEG 8
#define ANIME_2_TXT_SEG 9
#define ANIME_3_TXT_SEG 10
#define aCOU_ACT_HAPPY_NEW_YEAR 2
#define mTM_SECONDS_IN_MINUTE 60
#define mTM_MINUTES_IN_HOUR 60
#define Common_Get(x) (af_decor_common.x)
#define CLIP(x) (af_decor_common.clip.x)
#define GRAPH_ALLOC_TYPE(g,t,n) ((t*)af_decor_alloc(g,sizeof(t)*(n)))
#define _Matrix_to_Mtx_new af_decor_matrix
#define two_tex_scroll af_decor_scroll
#define cKF_Si3_draw_R_SV af_decor_rig_draw
#define OPEN_DISP(g) ((void)(g))
#define CLOSE_DISP(g) ((void)(g))
#define NOW_POLY_OPA_DISP (graph->opa)
#define NOW_POLY_XLU_DISP (graph->xlu)
#define NEXT_POLY_OPA_DISP (graph->opa++)
#define NEXT_POLY_XLU_DISP (graph->xlu++)
#define SET_POLY_OPA_DISP(p) (graph->opa=(p))
#define SET_POLY_XLU_DISP(p) (graph->xlu=(p))
#define OPEN_POLY_OPA_DISP(g) { GRAPH *af_graph=(g);Gfx *af_poly=af_graph->opa;
#define CLOSE_POLY_OPA_DISP(g) af_graph->opa=af_poly; }
#define OPEN_POLY_XLU_DISP(g) { GRAPH *af_graph=(g);Gfx *af_poly=af_graph->xlu;
#define CLOSE_POLY_XLU_DISP(g) af_graph->xlu=af_poly; }
#define POLY_OPA_DISP af_poly
#define POLY_XLU_DISP af_poly
#define AF_CMD(p,x,y) do { Gfx *af_p=(p);*af_p=(Gfx){(x),(y)}; } while(0)
#define gSPMatrix(p,m,f) AF_CMD(p,0xDA380003u,(u32)(uptr)(m))
#define gSPDisplayList(p,d) AF_CMD(p,0xDE000000u,(u32)(uptr)(d))
#define gSPSegment(p,s,d) AF_CMD(p,0xDB060000u+4u*(s),(u32)(uptr)(d)&0x1FFFFFFFu)
#define gDPPipeSync(p) AF_CMD(p,0xE7000000u,0)
#define AF_RGBA(r,g,b,a) ((u32)(r)<<24|(u32)(g)<<16|(u32)(b)<<8|(u32)(a))
#define gDPSetEnvColor(p,r,g,b,a) AF_CMD(p,0xFB000000u,AF_RGBA(r,g,b,a))
#define gDPSetPrimColor(p,m,l,r,g,b,a) AF_CMD(p,0xFA000000u|((u32)(m)<<8)|(l),AF_RGBA(r,g,b,a))
#endif
