/* Compilation adapter for generated, source-credited complete donor functions.
 * The generated function bodies remain under ignored build/, never committed. */
#include "holiday_dedicated.h"
#include "holiday_placement.h"
#define TRUE 1
#define FALSE 0
#define NULL ((void *)0)
typedef AFHolidayDedicated EVENT_MANAGER_ACTOR;
typedef struct {int type;} aEvMgr_event_ctrl_c;
typedef AFHolidayPlace mEv_place_data_c;
static inline mEv_place_data_c *af_hd_place(EVENT_MANAGER_ACTOR *e,unsigned int op,int type,int map,int kind,int id) {
    return (mEv_place_data_c *)e->call(e->context,op,type,map,kind,id);
}
#define aEvMgr_SHOW_ACTOR_RESULT_NOT_SHOWN ((mEv_place_data_c *)-1)
#define Common_Get(member) (*evmgr->common)
#define HD(op,type,a,b,c) evmgr->call(evmgr->context,op,type,a,b,c)
#define mEv_check_keep(t) HD(AF_HD_KEEP,t,0,0,0)
#define mEv_set_keep(t) ((void)HD(AF_HD_SET_KEEP,t,0,0,0))
#define mEv_clear_keep(t) ((void)HD(AF_HD_CLEAR_KEEP,t,0,0,0))
#define mEv_check_status(t,s) HD(AF_HD_STATUS,t,s,0,0)
#define mEv_set_status(t,s) ((void)HD(AF_HD_SET_STATUS,t,s,0,0))
#define mEv_clear_status(t,s) ((void)HD(AF_HD_CLEAR_STATUS,t,s,0,0))
#define title_fade(e,t,f,k) HD(AF_HD_FADE,t,f,k,0)
#define clean_FG(e,k) ((void)HD(AF_HD_CLEAN,ctrl->type,k,0,0))
#define make_FG_in_reserved_block(e,c,m,k,i) af_hd_place(e,AF_HD_FOREGROUND,(c)->type,m,k,i)
#define make_actor_in_reserved_block(e,c,m,k,i) af_hd_place(e,AF_HD_ACTOR,(c)->type,m,k,i)
#define delete_FG(c,i) ((void)HD(AF_HD_DELETE_FOREGROUND,(c)->type,i,0,0))
#define delete_FG2(t,i) ((void)HD(AF_HD_DELETE_FOREGROUND_UNCHECKED,t,i,0,0))
#define mEv_clear_common_place(t,i) ((void)HD(AF_HD_CLEAR_PLACE,t,i,0,0))
#define make_control_actor_without_indoor(p) HD(AF_HD_CONTROL,ctrl->type,p,0,0)
#define show_actor_at_wade_checkless(e,c,i) ((mEv_place_data_c *)HD(AF_HD_SHOW,(c)->type,i,0,0))
#define show_actor_at_wade_checkfgcol(e,c,i) ((mEv_place_data_c *)HD(AF_HD_SHOW,(c)->type,i,1,0))
#define make_effect(i) HD(AF_HD_EFFECT,ctrl->type,i,0,0)
#define delete_effect(i) HD(AF_HD_DELETE_EFFECT,ctrl->type,i,0,0)
#define mPlib_Set_unable_wade(v) ((void)HD(AF_HD_UNABLE_WADE,ctrl->type,v,0,0))
