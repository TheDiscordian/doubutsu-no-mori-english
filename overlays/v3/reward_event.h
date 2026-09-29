#ifndef AF_V3_REWARD_EVENT_H
#define AF_V3_REWARD_EVENT_H
/* Shared gift controller, gift NPC, and Shrine spirit use the native NPC
 * prefix. Source-only world/private/clip layouts never alias native memory.
 * Unbound providers remain link errors, not successful placeholder services. */
#include "carried_event.h"
typedef int BOOL;
typedef void (*aNPC_SUB_PROC)(NPC_ACTOR *,GAME_PLAY *);
typedef struct {void *demo_class;int type;} mDemo_Clip_c;
typedef void mNpc_MaskNpc_c;
typedef struct {void (*anime_play_proc)(void);int play_flag,hem_flag;} AFRewardShrine;
extern mDemo_Clip_c *af_rw_demo_clip;
AFRewardShrine *af_rw_shrine(void);
void *af_rw_private(void);
int af_rw_month(void),af_rw_day(void),af_rw_player(void),af_rw_weather(void);
int af_rw_birthday_month(void),af_rw_birthday_day(void);
u16 *af_rw_birthday_present(void);
u8 *af_rw_first_present(void);
int *af_rw_hem_visible(void);
int af_rw_block_x(GAME_PLAY *),af_rw_block_z(GAME_PLAY *);
u8 *af_rw_menu_refuse(GAME_PLAY *);
int *af_rw_sub_animation(NPC_ACTOR *);
u16 af_rw_umbrella(NPC_ACTOR *);
int af_rw_is_resident(NPC_ACTOR *);
void af_rw_npc_save(ACTOR *,GAME *);
typedef int (*AFRewardSetupNpc)(GAME_PLAY *,u16,int,int,int,int,int,int,int);
AFRewardSetupNpc af_rw_npc_setup(void);
const AFHPNpcServices *af_rw_npc_services(void);
extern const AFHPTools af_rw_tools;
extern const AFHPEffects af_rw_effects;
#undef CLIP
#define CLIP(name) (af_rw_##name)
#define af_rw_demo_clip2 af_rw_demo_clip
#define af_rw_npc_clip af_rw_npc_services()
#define af_rw_tools_clip (&af_rw_tools)
#undef eEC_CLIP
#define eEC_CLIP (&af_rw_effects)
#undef aSHR_GET_CLIP
#define aSHR_GET_CLIP() af_rw_shrine()
int mSC_LightHouse_Event_Check(int);
u16 mSC_LightHouse_Event_Present_Item(int);
void mSC_LightHouse_Event_Clear(int);
int mSC_trophy_get(int);
void mSC_trophy_set(int);
int mSM_CHECK_ALL_FISH_GET(void),mSM_CHECK_ALL_INSECT_GET(void);
mNpc_MaskNpc_c *mNpc_GetSameMaskNpc(u16);
int mNpc_RegistMaskNpc(u16,u16,u16);
ACTOR *Actor_info_fgName_search(void *,u16,int);
int mPlib_check_player_actor_main_index_OutDoorMove2(GAME *);
void mPlib_request_main_wait_type3(GAME *);
int mPlib_request_main_demo_get_golden_item2_type1(GAME *,int);
int mPr_GetPossessionItemIdx(void *,u16);
void mFAs_ClearGoodField(void);
void mDemo_Set_talk_return_get_golden_axe_demo(int);
#endif
