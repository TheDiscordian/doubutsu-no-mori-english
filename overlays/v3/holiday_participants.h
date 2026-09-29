#ifndef AF_V3_HOLIDAY_PARTICIPANTS_H
#define AF_V3_HOLIDAY_PARTICIPANTS_H
/* Native-layout adapter for complete generated event controllers and NPCs.
 * Service calls use donor identities until their explicit native binding.
 * These declarations alone do not authorise registering a playable actor. */
typedef unsigned char u8;
typedef signed char s8;
typedef unsigned short u16;
typedef short s16;
typedef unsigned int u32;
typedef int s32;
typedef float f32;
typedef u16 mActor_name_t;
typedef struct {f32 x,y,z;} xyz_t;
typedef struct {s16 x,y,z;} s_xyz;
typedef struct {u8 r,g,b,a;} rgba_t;
typedef union {u8 bytes[16];struct {s16 ob[3];u8 rest[10];} v;} __attribute__((aligned(8))) Vtx;
typedef void GAME;
typedef void GAME_PLAY;
typedef union AFHPActor ACTOR;
typedef union AFHPNpc NPC_ACTOR;
typedef void (*mActor_proc)(ACTOR *,GAME *);
typedef void (*aNPC_THINK_PROC)(NPC_ACTOR *,GAME_PLAY *,int);
typedef aNPC_THINK_PROC aNPC_SCHEDULE_PROC;
typedef mActor_proc aNPC_TALK_REQUEST_PROC;
typedef int (*aNPC_TALK_INIT_PROC)(ACTOR *,GAME *);
typedef aNPC_TALK_INIT_PROC aNPC_TALK_END_CHECK_PROC;
typedef struct {xyz_t position;s_xyz angle;u16 pad;} AFHPPos;
typedef struct {f32 start_frame,end_frame,max_frames,speed,current_frame;int mode;} AFHPFrame;

/* Sparse views leave every unaccessed native field untouched. The offsets are
 * checked against native code, not inferred from the larger donor NPC. */
union AFHPActor {
    u8 native[0x174];
    struct {u8 p_id[6];u16 npc_id;};
    struct {u8 p_block[8];s8 block_x,block_z;};
    struct {u8 p_home[0xC];AFHPPos home;u32 state_bitfield;};
    struct {u8 p_world[0x28];AFHPPos world;};
    struct {u8 p_speed[0x68];xyz_t position_speed;f32 speed,gravity,max_velocity_y;};
    struct {u8 p_bg[0x98];struct {struct {u32 before:15,unit_attribute:6,after:11;} result;} bg_collision_check;};
    struct {u8 p_player[0xB6];s16 player_angle_y;f32 player_distance_xz_sq,player_distance_xz,player_distance_y;};
    struct {u8 p_weight[0xD6];struct {u8 weight;} status_data;};
    struct {u8 p_shape[0xDC];struct {s_xyz rotation;} shape_info;};
    struct {u8 p_cull[0x140];f32 cull_radius,talk_distance;};
};
union AFHPNpc {
    ACTOR actor_class;
    u8 native[0x93C];
    struct {u8 p_draw[0x184];struct {
        u32 main_animation_frame;int main_animation_state;u8 pre_animation[12];
        struct {struct {AFHPFrame frame_control;u8 pointers[8];f32 morph_counter;} keyframe;} main_animation;
        u8 pad[0x704-0x198-sizeof(AFHPFrame)-12];int animation_id;
        u8 pre_speed[0x72A-0x708];u8 anim_speed_type,loop_flag;
        s16 effect_pattern,effect_type;u8 pre_frame_speed[12];f32 frame_speed;
    } draw;};
    struct {u8 p_think[0x7A4];struct {aNPC_THINK_PROC think_proc;u32 interrupt_flags;} think;};
    struct {u8 p_sched[0x7C0];struct {aNPC_SCHEDULE_PROC schedule_proc;} schedule;};
    struct {u8 p_action[0x7C4];struct {
        u8 priority,idx,step,type,previous,act_obj;u8 pad[6];aNPC_THINK_PROC act_proc;
    } action;};
    struct {u8 p_request[0x7D4];struct {u8 act_priority,act_idx,act_type,pad;u16 act_args[6];} request;};
    struct {u8 p_cond[0x7FD];struct {u8 hide_request,pad[14];u32 demo_flg;} __attribute__((packed)) condition_info;};
    struct {u8 p_hand[0x860];struct {ACTOR *item_actor_p;xyz_t pos;} right_hand;};
    struct {u8 p_head[0x876];struct {u8 lock_flag;} head;};
    struct {u8 p_ignore[0x8AC];int palActorIgnoreTimer;struct {
        struct {f32 max_speed,acceleration,deceleration;} speed;
        f32 dst_pos_x,dst_pos_z;u8 pad[24];s16 mv_angl,mv_add_angl;
    } movement;};
    struct {u8 p_collision[0x8F0];struct {
        struct {u8 pad[14];struct {struct {s16 radius;u8 tail[10];} pipe;} attribute;u8 alignment[2];} pipe;
        f32 radius;u8 flag,check_kind,turn_flag;
    } collision;};
    struct {u8 p_talk[0x91C];struct {
        aNPC_TALK_REQUEST_PROC talk_request_proc;
        aNPC_TALK_INIT_PROC talk_init_proc;
        aNPC_TALK_END_CHECK_PROC talk_end_check_proc;
        u8 type,default_act,demo_code,turn;s16 default_animation;
    } talk_info;};
};
#ifdef __mips__
_Static_assert(sizeof(ACTOR)==0x174,"Native actor prefix");
_Static_assert(sizeof(NPC_ACTOR)==0x93C,"Native NPC prefix");
#define AF_HP_OFFSET(member,offset) _Static_assert(__builtin_offsetof(NPC_ACTOR,member)==offset,"Native " #member)
AF_HP_OFFSET(draw.main_animation.keyframe.frame_control.mode,0x1AC);
AF_HP_OFFSET(draw.animation_id,0x704);
AF_HP_OFFSET(draw.main_animation_state,0x188);
AF_HP_OFFSET(draw.main_animation.keyframe.morph_counter,0x1B8);
AF_HP_OFFSET(draw.anim_speed_type,0x72A);
AF_HP_OFFSET(draw.effect_pattern,0x72C);
AF_HP_OFFSET(draw.effect_type,0x72E);
AF_HP_OFFSET(draw.frame_speed,0x73C);
AF_HP_OFFSET(action.act_obj,0x7C9);
AF_HP_OFFSET(action.act_proc,0x7D0);
AF_HP_OFFSET(think.think_proc,0x7A4);
AF_HP_OFFSET(schedule.schedule_proc,0x7C0);
AF_HP_OFFSET(request.act_args,0x7D8);
AF_HP_OFFSET(condition_info.demo_flg,0x80C);
AF_HP_OFFSET(right_hand.item_actor_p,0x860);
AF_HP_OFFSET(right_hand.pos,0x864);
AF_HP_OFFSET(movement.dst_pos_x,0x8BC);
AF_HP_OFFSET(movement.mv_add_angl,0x8DE);
AF_HP_OFFSET(collision.check_kind,0x911);
AF_HP_OFFSET(talk_info.default_animation,0x92C);
#undef AF_HP_OFFSET
#endif
typedef struct {
    mActor_proc move,draw;int schedule;
    aNPC_TALK_REQUEST_PROC request;
    aNPC_TALK_INIT_PROC start;
    aNPC_TALK_END_CHECK_PROC end;
    int extra;
} aNPC_ct_data_c;
typedef struct {
    s16 source_profile;u8 part;u32 flags;u16 source_name;s16 object;
    u32 actor_bytes;mActor_proc ctor,dtor,move,draw,save;
} ACTOR_PROFILE;
typedef struct {
    int (*birth_check_proc)(ACTOR *,GAME *);
    void (*ct_proc)(ACTOR *,GAME *,const aNPC_ct_data_c *);
    mActor_proc dt_proc,init_proc,move_proc,draw_proc;
    void (*animation_init_proc)(ACTOR *,int,int);
    int (*think_proc)(NPC_ACTOR *,GAME_PLAY *,int,int);
    void (*set_dst_pos_proc)(NPC_ACTOR *,f32,f32);
} AFHPNpcServices;
typedef struct {ACTOR *(*aTOL_birth_proc)(int,int,ACTOR *,GAME *,int,void *);} AFHPTools;
typedef struct {
    void (*effect_make_proc)(int,xyz_t,int,s16,GAME *,u16,s16,s16);
    void (*effect_kill_proc)(int,u16);
} AFHPEffects;
typedef struct {void (*anime_play_proc)(void);} AFHPShrine;
extern const AFHPNpcServices af_hp_npc_services;
extern const AFHPTools af_hp_tools_services;
extern const AFHPEffects af_hp_effect_services;
AFHPShrine *af_hp_shrine(void);
#define NPC_CLIP (&af_hp_npc_services)
#define eEC_CLIP (&af_hp_effect_services)
#define aSHR_GET_CLIP() af_hp_shrine()
#define CLIP(name) (af_hp_##name)
#define af_hp_npc_clip NPC_CLIP
#define af_hp_tools_clip (&af_hp_tools_services)

/* Donor-numbered services: adapters must map IDs, player states, animation,
 * text, tools, sounds, and profiles rather than call same-number native APIs. */
void *mEv_get_save_area(int,int),*mEv_reserve_save_area(int,int);
void mEv_actor_dying_message(int,ACTOR *);
int mFI_SetOyasiroPos(s16 *);
void Actor_delete(ACTOR *);
ACTOR *Actor_info_make_actor(void *,GAME *,int,f32,f32,f32,int,int,int,int,int,int,u16,int,int,int);
void *af_hp_actor_info(GAME_PLAY *);
int mFI_Wpos2UtCenterWpos(xyz_t *,xyz_t);
void mCoBG_SetPlussOffset(xyz_t,int,int);
void af_hp_rope_draw(ACTOR *,GAME *,void (*)(Vtx *));
extern const u8 af_hp_rope_art[];
extern const u32 af_hp_rope_models[2];
u32 af_hp_frame(GAME_PLAY *);
float fqrand(void),sin_s(s16),cos_s(s16);
s16 atans_table(f32,f32);
void bzero(void *,unsigned int),mem_copy(u8 *,const u8 *,unsigned int);
void none_proc1(void);
int cKF_FrameControl_stop_proc(AFHPFrame *),cKF_FrameControl_passCheck_now(AFHPFrame *,f32);
int mNpc_GetNpcLooks(ACTOR *),mNpc_GetNpcSoundSpec(ACTOR *);
void mNpc_RenewalSetNpc(ACTOR *);
float mCoBG_GetBgY_OnlyCenter_FromWpos2(xyz_t,f32);
int mDemo_Check(int,ACTOR *),mDemo_Request(int,ACTOR *,void (*)(ACTOR *));
ACTOR *mDemo_Get_talk_actor(void);
void mDemo_Start(ACTOR *),mDemo_Set_camera(int),mDemo_Set_msg_num(int);
void mDemo_Set_talk_display_name(s8),mDemo_Set_ListenAble(void);
void mDemo_Set_talk_turn(int),mDemo_Set_talk_return_demo_wait(int),mDemo_Set_talk_window_color(rgba_t *);
int af_hp_continue(void),af_hp_choice(void);
void af_hp_continue_message(int);
#define mMsg_CHECK_MAINNORMALCONTINUE() af_hp_continue()
#define mChoice_GET_CHOSENUM() af_hp_choice()
#define mMsg_SET_CONTINUE_MSG_NUM(n) af_hp_continue_message(n)
int mSP_money_check(int);
void mSP_get_sell_price(int);
typedef struct {u8 prefix[0x38];struct {u32 wallet;} inventory;} AFHPPrivate;
AFHPPrivate *af_hp_private(void);
int mPr_GetPossessionItemSumWithCond(void *,u16,int);
int mPr_GetPossessionItemIdxWithCond(void *,u16,int);
void mPr_SetPossessionItem(void *,int,u16,int);
int mPlib_get_player_actor_main_index(GAME *),mPlib_Check_now_handin_item(void);
int mPlib_request_main_demo_wait_type1(GAME *,int,void *);
int mPlib_request_main_demo_walk_type1(GAME *,f32,f32,f32,int);
int mPlib_request_main_pray_type1(GAME *,xyz_t *,s16);
int mPlib_request_main_throw_money_type1(GAME *,xyz_t *,s16);
void sAdo_OngenTrgStart(u32,xyz_t *),sAdo_OngenPos(u32,u32,xyz_t *);
/* Called after the ordinary native animation entry, only for registered
 * imported participants. The native entry retains its three bank lifetimes. */
void af_hp_motion_override(ACTOR *);
/* Native registry uses complete generated callbacks and the ordinary NPC pool.
 * Descriptor/registration hooks must be installed together before activation. */
typedef struct {
    u16 source_name,name,profile,event;u8 save,count,part,pad;
    const ACTOR_PROFILE *source;
    u32 native_flags;
} AFHPRecord;
typedef struct {u16 event_name,texture,resident,cloth;u8 exists,used;u16 pad;} AFHPResident;
enum {AF_HP_OWNER_COUNT=9,AF_HP_RESIDENT_COUNT=14,AF_HP_LIVE_COUNT=18};
extern const AFHPRecord af_hp_records[AF_HP_OWNER_COUNT];
extern const u32 af_hp_available;
int af_hp_identity(unsigned int,unsigned int);
void *af_hp_descriptor(int);
AFHPResident *af_hp_event_lookup(u16);
int af_hp_resident_bind(u16,u16,u16);
void af_hp_event_unregister(u16),af_hp_events_clear(void);
int af_hp_name_profile(u16);
void af_hp_free(ACTOR *);
int af_hp_admit(ACTOR *,GAME *),af_hp_owned(const ACTOR *);
void af_hp_constructed(ACTOR *);
int af_hp_npc_callbacks(ACTOR *,aNPC_ct_data_c *);
void af_hp_ctor(ACTOR *,GAME *),af_hp_dtor(ACTOR *,GAME *);
void af_hp_step(ACTOR *,GAME *),af_hp_draw(ACTOR *,GAME *),af_hp_save(ACTOR *,GAME *);
int af_hp_countdown(int);
unsigned int af_hp_elapsed(void);
#endif
