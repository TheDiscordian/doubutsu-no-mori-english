#ifndef AF_V3_HOLIDAY_FESTIVAL_H
#define AF_V3_HOLIDAY_FESTIVAL_H
/* Complete ordinary festival participants share the existing native NPC and
 * exercise service types. Additional services must be linked, never stubbed. */
#include "holiday_exercise.h"
typedef int BOOL;
typedef void (*mDemo_REQUEST_PROC)(ACTOR *);
typedef struct {u8 before[0x1C4];int work2;} TOOLS_ACTOR;
typedef struct {u16 event_id,texture_id,npc_id,cloth;u8 exists,used;u16 pad;} mNpc_EventNpc_c;
extern GAME *gamePT;
int af_hg_seconds(void);
int af_hg_head(NPC_ACTOR *,u8,u8,ACTOR *,xyz_t *);
void af_hg_message(int),af_hg_continue_message(int);
int af_hg_event_status(int,int);
void af_hg_event_set(int,int);
mNpc_EventNpc_c *af_hg_event_resident(u16);
void af_hg_world_name(u8 *,ACTOR *);
void af_hg_free_string(mMsg_Window_c *,int,const u8 *,int);
extern const AFHPTools af_hg_tools_services;
extern const AFHPEffects af_hg_effect_services;
void af_hg_sound(u32,u32,xyz_t *);
ACTOR *Actor_info_fgName_search(void *,u16,int);
int mDemo_Check_SpeakerAble(void);
int mFI_BlockKind2BkNum(int *,int *,int),mFI_GetPuleIdx(void);
int mFI_Wpos2BlockNum(int *,int *,xyz_t);
void mFI_BkNum2WposXZ(f32 *,f32 *,int,int);
s16 search_position_angleY(xyz_t *,xyz_t *);
int chase_angle(s16 *,s16,s16);
_Static_assert(sizeof(mNpc_EventNpc_c)==12,"Native event resident layout");
#endif
