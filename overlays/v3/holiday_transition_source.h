/* Normalized ABI for complete generated donor collision/search/fade functions. */
#include "holiday_transition.h"
typedef unsigned int u32;
typedef unsigned short mActor_name_t;
typedef unsigned char u8;
typedef short s16;
typedef float f32;
typedef AFHolidayPosition xyz_t;
typedef AFHolidayShortPosition s_xyz;
typedef AFHolidayBlock BlockOrUnit_c;
typedef AFHolidayDoor Door_data_c;
typedef AFHolidayTransition EVENT_MANAGER_ACTOR;
typedef __typeof__(((AFHolidayTransition *)0)->play) GAME_PLAY;
typedef __typeof__(((AFHolidayTransition *)0)->player) ACTOR;
typedef __typeof__(((AFHolidayTransition *)0)->groundhog_save) aGHC_save_c;
#define TRUE 1
#define FALSE 0
#define NULL ((void *)0)
#define Common_Get(n) (evmgr->common.n)
#define Common_Set(n,v) ((void)(evmgr->common.n=(v)))
#define Save_Get(n) (evmgr->n)
#define gamePT (&evmgr->play)
#define GET_PLAYER_ACTOR_NOW_ACTOR() (&evmgr->player)
#define CLIP(n) (evmgr->groundhog_present?&evmgr->groundhog:NULL)
#define mDemo_CheckDemo4Event() (evmgr->demo_busy)
#define mEv_PlayerOK() (evmgr->player_ok)
#define mEv_LiveSonchoPresent() (evmgr->present_busy)
#define mPlib_Check_CorrectPlayerPos_forEvent() evmgr->ops->correct(evmgr->context)
#define mEv_get_common_area(t,i) (evmgr->groundhog_save_present?&evmgr->groundhog_save:NULL)
#define mEvMN_GetEventTypeMap() af_holiday_transition_map(evmgr)
#define mEvMN_GetMapIdx(t) af_holiday_transition_index(evmgr,t)
#define mEvMN_GetJointAllNpcMax(i) af_holiday_transition_count(evmgr,i)
#define mEvMN_GetEventSetUtInBlock(n,x,z,t,i) af_holiday_transition_unit(evmgr,n,x,z,t,i)
#define mFI_CheckStructureArea(x,z,n,ux,uz) af_holiday_transition_structure(evmgr,x,z,n,ux,uz)
#define mFI_Wpos2BkandUtNuminBlock(bx,bz,ux,uz,p) evmgr->ops->grid(evmgr->context,bx,bz,ux,uz,p)
#define mFI_BkandUtNum2CenterWpos(p,bx,bz,ux,uz) evmgr->ops->position(evmgr->context,p,bx,bz,ux,uz)
#define mFI_CheckLapPolice(bx,bz,ux,uz) evmgr->ops->police(evmgr->context,bx,bz,ux,uz)
#define mNpc_CheckNpcSet(bx,bz,ux,uz) evmgr->ops->npc_space(evmgr->context,bx,bz,ux,uz)
#define mFI_BlockKind2BkNum(x,z,k) evmgr->ops->landmark(evmgr->context,x,z,k)
#define mNpcW_GetNearGate(x,z,bx,bz,ux,uz) evmgr->ops->near_gate(evmgr->context,x,z,bx,bz,ux,uz)
#define mFI_BkNum2WposXZ(x,z,bx,bz) evmgr->ops->block_origin(evmgr->context,x,z,bx,bz)
#define goto_other_scene(p,d,f) evmgr->ops->go(evmgr->context,evmgr,d,f)
#define mFI_SetClimate(v) evmgr->ops->climate(evmgr->context,v)
#define aMR_SaveWaltzTempo2() evmgr->ops->tempo(evmgr->context)
#define mPlib_request_player_warp_forEvent() evmgr->ops->warp(evmgr->context,evmgr)
#define mBGMForce_inform_start() evmgr->ops->bgm(evmgr->context)
