/* Complete generated Franklin actor and real shared adapters, with native
 * inventory/transport/event services doubled. This is not native gameplay. */
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "ev_turkey.c"
#include "holiday_hiding.h"
#include "harvest_manager.h"

typedef struct {
    u32 birth,change_master,change_mode;
    u8 request_mode,player_after_mode;u16 item;ACTOR *master,*target;
    u8 present,changed,pad[2];ACTOR *actor;u32 rebuild;
} NativeHandover;
static NativeHandover transport={.birth=1,.change_mode=2};
NativeHandover *volatile af_cw_native_handover=&transport;
static _Alignas(16) u8 player_actor[0x12D8],game[0x1EB0],private_data[0xBD0];
GAME *volatile af_hr_native_game=game;
static struct {u8 before[16];AFHarvestSaved data;u8 tail[18],after[16];} saved;
static struct {u8 before[16],data[40],after[16];} common;
AFHolidayNativeDay af_holiday_native_days[AF_HN_DAYS];
u8 af_holiday_native_index[128];
static EV_TURKEY_ACTOR turkey;
static u16 enabled=AF_HR_ALL,order[10][16];
static int cutlery=1,slot,save_exists,common_exists,fail_save,fail_common,reservations;
static int request_ok,request_count,give_ok,give_count,deleted,locked,unlocks;
static int constructors,deaths,continuing=1,current_message,last_message,continued_message;
static unsigned status_sets,force_calls,halt_calls;
static int expected_halt;
static jmp_buf failure;
static float random_value;
static u8 window[0x300];

void af_v3_save_halt(int error) {
    assert(error==-1 && expected_halt);halt_calls++;longjmp(failure,1);
}
int af_carried_type(u32 item) {
    if(item==0x2530)return cutlery?47:0;
    if(item==0x2D28)return 79;
    for(unsigned i=0;i<12;i++)if(item==af_hr_reward_items[i])return enabled&(1u<<i)?(i<10?10:12):0;
    return 0;
}
u32 af_carried_quantity(u32 item) {return item==0x2D28?1:0;}
void *af_cw_private(void) {return private_data;}
int af_cw_player(void) {return slot;}
static void args(int type,int id) {assert(type==AF_HR_NATIVE && id==0);}
void *af_cw_native_get_save(int type,int id) {args(type,id);return save_exists?&saved.data:0;}
void *af_cw_native_reserve_save(int type,int id) {
    args(type,id);if(fail_save)return 0;reservations++;save_exists=1;
    memset(&saved.data,0,40);return &saved.data;
}
void *af_cw_native_get_common(int type,int id) {args(type,id);return common_exists?common.data:0;}
void *af_cw_native_reserve_common(int type,int id) {
    args(type,id);if(fail_common)return 0;common_exists=1;memset(common.data,0,40);return common.data;
}
int af_hr_prior_calendar_before_cleanup(void) {return 19;}
int af_holiday_native_append(unsigned type,unsigned hours,unsigned begin,unsigned end) {
    assert(type==AF_HR_NATIVE);af_holiday_native_index[type]=1;
    af_holiday_native_days[1]=(AFHolidayNativeDay){type,hours,begin,end,AF_HE_EXIST,0};return 1;
}
void af_hr_native_set_status(int type,int status) {
    assert(type==AF_HR_NATIVE && status==mEv_STATUS_TALK);status_sets++;
    af_holiday_native_days[1].status|=(u16)status;
}
void af_holiday_native_death(int type,void *actor) {assert(type==AF_HR_NATIVE && actor==&turkey);deaths++;}
ACTOR *af_cw_native_player_actor(GAME *g) {assert(g==game);return (ACTOR *)player_actor;}
int af_hp_admit(ACTOR *a,GAME *g) {return a==(ACTOR *)&turkey && g==game;}
int af_cw_native_request_give(GAME *g,u16 item,int mode,int present,int surface) {
    assert(g==game && item==0x2530 && mode==7 && !present && !surface);request_count++;
    if(request_ok)transport.master=(ACTOR *)&turkey;
    return request_ok;
}
int af_cw_native_give(void *p,u16 item,int condition) {
    assert(p==private_data && item==af_hr_reward(turkey.present_idx) && !condition);
    give_count++;return give_ok;
}
int mPr_GetPossessionItemIdxWithCond(void *p,u16 item,int condition) {
    assert(p==private_data && item==0x2530 && !condition);return deleted?-1:4;
}
void mPr_SetPossessionItem(void *p,int index,u16 item,int condition) {
    assert(p==private_data && index==4 && !item && !condition);deleted++;
}
u16 mDemo_Get_OrderValue(int who,int index) {return order[who][index];}
void mDemo_Set_OrderValue(int who,int index,u16 value) {order[who][index]=value;}
void *mMsg_Get_base_window_p(void) {return window;}
int mMsg_Get_msg_num(void *w) {assert(w==window);return current_message;}
void mMsg_Set_LockContinue(void *w) {assert(w==window);locked=1;}
void mMsg_Unset_LockContinue(void *w) {assert(w==window);locked=0;unlocks++;}
void af_cw_native_message(int n) {last_message=n;}
void af_cw_native_continue(void *w,int n) {assert(w==window);continued_message=n;}
int af_hp_continue(void) {return continuing;}
void mIN_copy_name_str(u8 *out,u16 item) {assert(item==af_hr_reward(turkey.present_idx));memset(out,'x',16);}
int mIN_get_item_article(u16 item) {assert(item);return 0;}
void mMsg_Set_item_str_art(void *w,int which,const u8 *text,int size,int article) {
    assert(w==window && !which && text[0]=='x' && size==16 && !article);
}
u32 af_hp_frame(GAME *g) {assert(g==game);return *(u32 *)((u8 *)g+0x1EA0);}
void af_hr_test_force(GAME *g,const xyz_t *p,const s_xyz *angle,u8 flags) {
    assert(g==game && !p && angle && flags==32);force_calls++;
}
static int birth(ACTOR *a,GAME *g) {assert(a==(ACTOR *)&turkey && g==game);return 1;}
static void construct(ACTOR *a,GAME *g,const aNPC_ct_data_c *ct) {
    assert(a==(ACTOR *)&turkey && g==game && ct && ct->schedule==aNPC_CT_SCHED_TYPE_SPECIAL);constructors++;
}
static void lifecycle(ACTOR *a,GAME *g) {assert(a==(ACTOR *)&turkey && g==game);}
const AFHPNpcServices af_hp_npc_services={.birth_check_proc=birth,.ct_proc=construct,
    .dt_proc=lifecycle,.init_proc=lifecycle,.move_proc=lifecycle,.draw_proc=lifecycle};
void af_rw_npc_save(ACTOR *a,GAME *g) {lifecycle(a,g);}
void Actor_delete(ACTOR *a) {assert(a==(ACTOR *)&turkey);deaths++;}
void bzero(void *p,unsigned size) {memset(p,0,size);}
void none_proc1(void) {}
float fqrand(void) {return random_value;}
int mDemo_Check(int type,ACTOR *a) {(void)type;(void)a;return 0;}
int mDemo_Check_ListenAble(void) {return 0;}
void mDemo_Set_ListenAble(void) {}
int mDemo_Request(int type,ACTOR *a,void (*callback)(ACTOR *)) {
    (void)type;(void)a;(void)callback;assert(0);return 0;
}
void add_calc(float *p,float a,float b,float c,float d) {(void)p;(void)a;(void)b;(void)c;(void)d;assert(0);}
void add_calc_short_angle2(s16 *p,s16 a,float b,s16 c,s16 d) {(void)p;(void)a;(void)b;(void)c;(void)d;assert(0);}

static void guards(void) {
    for(unsigned i=0;i<16;i++)assert(saved.before[i]==0xA5 && saved.after[i]==0xA5 &&
        common.before[i]==0xA5 && common.after[i]==0xA5);
}
/* Extend the existing complete-actor fixture for the changed placement risk.
 * Native world services are recording doubles, not an emulator harness. */
static struct {
    u16 fg[256];u32 col[256];
    struct {u32 before[4];AFHolidayPlace place;u32 after[4];} area;
    AFHolidayBlock ball,marine,forward;
    int present,indoors,busy,ball_valid,marine_valid,occupied,normal,free_ok,fail_reserve;
    int errors,spawns,flattens,units,seed;
} hide;
static AFHolidayField hide_field={.maximum={9,7},.next={-1,-1},.shrine={2,3},
    .excluded={{2,1},{2,2},{3,1},{2,3}},.exclusions=4,.month=11,.day=24,.hour=15,.second=7};
static const u16 *hide_fg(void *c,int x,int z) {(void)c;(void)x;(void)z;return hide.fg;}
static const u32 *hide_col(void *c,int x,int z) {(void)c;(void)x;(void)z;return hide.col;}
static int hide_allowed(u16 fg,u32 attr) {return fg==0 && attr==1;}
static int hide_outdoors(void *c) {(void)c;return !hide.indoors;}
static int hide_busy(void *c,int x,int z) {(void)c;(void)x;(void)z;return hide.busy;}
static int hide_other(void *c,unsigned type,AFHolidayBlock b) {(void)c;(void)b;assert(type==116);return 0;}
static int hide_unit(void *c,int *x,int *z,int bx,int bz) {
    (void)c;(void)bx;(void)bz;hide.units++;if(!hide.normal)return 0;*x=6;*z=6;return 1;
}
static int hide_height(void *c,int bx,int bz,int x,int z) {(void)c;(void)bx;(void)bz;(void)x;(void)z;return 1;}
static AFHolidayPlace *hide_get(void *c,unsigned type,unsigned id) {
    (void)c;assert(type==116 && id==0x51);return hide.present?&hide.area.place:0;
}
static AFHolidayPlace *hide_reserve(void *c,unsigned type,unsigned id) {
    (void)c;assert(type==116 && id==0x51);
    if(hide.fail_reserve)return 0;
    hide.present=1;return &hide.area.place;
}
static int hide_forward(void *c,int *x,int *z) {(void)c;*x=hide.forward.x;*z=hide.forward.z;return 1;}
static void hide_flatten(void *c,AFHolidayPlace *p) {(void)c;assert(p==&hide.area.place);hide.flattens++;}
static int hide_spawn(void *c,AFHolidayPlace *p) {
    (void)c;assert(p==&hide.area.place && p->block.x==hide.forward.x && p->block.z==hide.forward.z);
    hide.spawns++;return 1;
}
static void hide_error(void *c,unsigned type) {(void)c;assert(type==116);hide.errors++;}
static int hide_ball(void *c,AFHolidayBlock *b) {(void)c;*b=hide.ball;return hide.ball_valid;}
static int hide_marine(void *c,AFHolidayBlock *b) {(void)c;*b=hide.marine;return hide.marine_valid;}
static int hide_occupied(void *c,const AFHolidayPlace *p) {(void)c;(void)p;return hide.occupied;}
static int hide_free(void *c,unsigned type,AFHolidayPlace *p,int seed) {
    (void)c;assert(type==116);hide.seed=seed;
    if(!hide.free_ok)return 0;
    p->block=(AFHolidayBlock){5,4};p->unit=(AFHolidayBlock){6,6};return 1;
}
static AFHolidayHiding hide_ops={
    {0,hide_outdoors,hide_busy,hide_other,hide_unit,hide_height,hide_get,hide_reserve,
        hide_forward,hide_flatten,hide_spawn,hide_error},
    hide_fg,hide_col,hide_allowed,hide_ball,hide_marine,hide_occupied,hide_free};
static _Alignas(16) u8 manager_data[0x260];
static int hide_fluctuation=-0x7654321;
AFHolidayPlace *af_holiday_native_get_place(int type,u8 id) {return hide_get(0,type,id);}
int af_holiday_hide_native_fluctuation(void *m,int *seed) {
    assert(m==manager_data);*seed=hide_fluctuation;return 1;
}
int af_holiday_hide_native_make(void *m,u32 t,u32 name,u32 id,int seed,AFHolidayPlace **out) {
    assert(m==manager_data && name==0xD0D1 && seed==108+0xD08D+0x51);
    return af_holiday_hide_make(&hide_field,&hide_ops,t,name,id,seed,out);
}
int af_holiday_hide_native_walk(void *m,u32 t,u32 name,u32 id,int seed,AFHolidayPlace **out) {
    assert(m==manager_data && name==0xD08D && seed==(int)((u32)hide_fluctuation+108));
    return af_holiday_hide_walk(&hide_field,&hide_ops,t,name,id,seed,out);
}
int af_holiday_hide_native_show(void *m,u32 t,u32 id,int seed,AFHolidayBlock *b) {
    assert(m==manager_data && seed==(int)((u32)hide_fluctuation+108+0x51));
    return af_holiday_hide_show(&hide_field,&hide_ops,t,id,seed,b);
}
void af_hr_manager_native_set_status(int type,int bits) {assert(type==116);af_holiday_native_days[1].status|=bits;}
void af_hr_manager_native_clear_status(int type,int bits) {assert(type==116);af_holiday_native_days[1].status&=~bits;}
int af_hr_manager_native_check_status(int type,int bits) {assert(type==116);return af_holiday_native_days[1].status&bits;}
static void hiding_checks(void) {
    for(unsigned i=0;i<4;i++)hide.area.before[i]=hide.area.after[i]=0xA55AA55A;
    for(unsigned i=0;i<256;i++)hide.col[i]=1; /* All five zero-height corners, allowed terrain. */
    hide.fg[9*16+8]=0x804;
    int x=-1,z=-1;
    assert(af_holiday_hide_unit(&x,&z,1,3,2,&hide_ops) && x==8 && z==8);
    hide.col[8*16+8]|=1u<<11; /* A single raised corner rejects the apparently empty spot. */
    assert(!af_holiday_hide_unit(&x,&z,1,3,2,&hide_ops));hide.col[8*16+8]=1;
    assert(!af_holiday_hide_unit(&x,&z,1,3,9,&hide_ops));
    u16 mask[16];
    const u16 objects[]={0x5000,0xF200,0x5829,0x580C,0x5849,0x5804,0x5808,0x5805,0x5806,0x5807,0x5843,7,12,14};
    for(unsigned i=0;i<sizeof(objects)/sizeof(objects[0]);i++) {
        memset(hide.fg,0,sizeof hide.fg);memset(mask,0,sizeof mask);
        hide.fg[8*16+8]=objects[i];af_holiday_hide_mask(mask,hide.fg);
        int bits=0;for(unsigned row=0;row<16;row++)bits+=mask[row]!=0;
        assert(bits==1); /* Every supported building/board cover occupies its source row. */
    }
    for(unsigned i=0;i<2;i++) {
        memset(hide.fg,0,sizeof hide.fg);memset(mask,0,sizeof mask);
        hide.fg[8*16+8]=(u16)(i?0x584D:0x584A);af_holiday_hide_mask(mask,hide.fg);
        for(unsigned row=0;row<16;row++)assert(!mask[row]);
    }
    memset(hide.fg,0,sizeof hide.fg);hide.fg[9*16+8]=0x804;
    AFHolidayPlace *p=0,candidate={{0,0},{0,0},0xD0D1,1};
    assert(af_holiday_hide_search(&hide_field,&hide_ops,116,&candidate,108+0xD08D+0x51));
    hide.ball=candidate.block;hide.ball_valid=1;
    assert(af_holiday_hide_make(&hide_field,&hide_ops,116,0xD0D1,0x51,108+0xD08D+0x51,&p)==1);
    assert(p==&hide.area.place && (p->block.x!=hide.ball.x || p->block.z!=hide.ball.z));
    hide.ball_valid=0;hide.forward=p->block;
    assert(af_holiday_hide_show(&hide_field,&hide_ops,116,0x51,17,&candidate.block)==1 && hide.spawns==1);
    hide.occupied=1;hide.free_ok=1;
    assert(af_holiday_hide_show(&hide_field,&hide_ops,116,0x51,17,&candidate.block)==2 && hide.spawns==1);
    assert(p->block.x==4 && p->block.z==5 && hide.seed==17); /* Preserve the source-bug repair. */
    hide.forward=p->block;hide.normal=1;
    assert(af_holiday_hide_show(&hide_field,&hide_ops,116,0x51,17,&candidate.block)==1 && hide.spawns==2);
    assert(p->unit.x==6 && p->unit.z==6);hide.occupied=0;
    AFHolidayControl control={.type=116};
    *(int *)(manager_data+0x234)=0;
    assert(!af_hr_manager_start(manager_data,&control));
    assert((af_holiday_native_days[1].status&AF_HE_ERROR) && !(af_holiday_native_days[1].status&AF_HE_ACTIVE));
    af_holiday_native_days[1].status=AF_HE_EXIST|AF_HE_ACTIVE;*(int *)(manager_data+0x234)=1;
    hide.present=0;
    assert(af_hr_manager_start(manager_data,&control)==1 && af_hr_manager_check_keep(116));
    assert(af_hr_manager_start(manager_data,&control)==2);
    p=&hide.area.place;hide.forward=p->block;assert(af_hr_manager_in(manager_data,&control)==1);
    af_holiday_native_days[1].status|=64;hide.busy=1;
    AFHolidayPlace before=*p;
    assert(!af_hr_manager_behind(manager_data,&control) && !memcmp(p,&before,sizeof before));
    assert(af_holiday_native_days[1].status&64); /* Failed relocation does not consume TALK. */
    af_holiday_native_days[1].status&=~AF_HE_ERROR;hide.busy=0;
    assert(af_hr_manager_behind(manager_data,&control)==1 && !(af_holiday_native_days[1].status&64));
    assert(af_hr_manager_stop(manager_data,&control)==1 && af_hr_manager_stop(manager_data,&control)==2);
    assert(!af_hr_manager_check_keep(116));
    for(unsigned i=0;i<4;i++)assert(hide.area.before[i]==0xA55AA55A && hide.area.after[i]==0xA55AA55A);
    puts("Full cover/flat-unit search, actual ball exclusion, repaired arrival fallback, source manager callbacks, failed/successful relocation, and placement guards pass with world services doubled.");
}
int main(void) {
    memset(&saved,0xA5,sizeof saved);memset(&common,0xA5,sizeof common);
    memset(af_holiday_native_index,255,sizeof af_holiday_native_index);
    af_holiday_native_index[AF_HR_HARVEST_NATIVE]=0;
    af_holiday_native_days[0]=(AFHolidayNativeDay){AF_HR_HARVEST_NATIVE,0xFFF000,0x0B1C,0x0B1C,AF_HE_EXIST,0};
    assert(af_hr_calendar_before_cleanup()==19 && af_holiday_native_days[1].hours==0xFFF000);
    assert(af_holiday_native_days[1].status==AF_HE_EXIST); /* No invented ACTIVE/RUN. */
    assert(!af_hr_get_save(56,0) && !af_hr_reserve_save(AF_HR_SOURCE,1));
    assert(af_hr_enabled_mask()==AF_HR_ALL && !af_hr_reward(12));
    u16 bits=0;
    for(unsigned i=0;i<12;i++) {assert(aETKY_DecidePresent(&bits)==(int)i);aETKY_ReportPresent(&bits,i);}
    assert(bits==AF_HR_ALL && aETKY_DecidePresent(&bits)==0 && !bits);
    enabled=(1u<<2)|(1u<<10);bits=1u<<7;
    random_value=0.75f;assert(aETKY_DecidePresent(&bits)==10);aETKY_ReportPresent(&bits,10);
    assert(aETKY_DecidePresent(&bits)==2);aETKY_ReportPresent(&bits,2);
    assert(aETKY_DecidePresent(&bits)==10 && bits==(1u<<7));
    enabled=0;assert(aETKY_DecidePresent(&bits)==-1 && bits==(1u<<7));
    enabled=AF_HR_ALL;bits=0x8000;assert(aETKY_DecidePresent(&bits)==-1 && bits==0x8000);
    assert(aETKY_DecidePresent(NULL)==-1);random_value=0;
    fail_save=1;aETKY_actor_ct((ACTOR *)&turkey,game);assert(deaths==1);guards();
    fail_save=0;fail_common=1;aETKY_actor_ct((ACTOR *)&turkey,game);assert(deaths==2);guards();
    /* A shared registry pre-reservation must initialise the source PID and
     * subsequent reservations must preserve the existing reward history. */
    save_exists=0;assert(af_hr_reserve_save(AF_HR_SOURCE,0)==&saved.data);
    int count=reservations;saved.data.given_present_bitfield=1u<<7;
    assert(af_hr_reserve_save(AF_HR_SOURCE,0)==&saved.data && reservations==count);
    assert(saved.data.given_present_bitfield==(1u<<7));
    saved.data.given_present_bitfield=0;
    fail_common=0;aETKY_actor_ct((ACTOR *)&turkey,game);assert(constructors==3 && turkey.ev_save_p==&saved.data);
    assert(turkey.ev_common_p==(void *)common.data && !saved.data.given_present_bitfield);
    assert(saved.data.pid.player_id==65535 && saved.data.pid.land_id==65535);
    for(unsigned i=0;i<8;i++)assert(saved.data.pid.player_name[i]==32 && saved.data.pid.land_name[i]==32);
    turkey.npc_class.actor_class.npc_id=0xD0D1;transport.actor=(ACTOR *)&turkey;
    *(int *)(player_actor+0xCF0)=0x40;*(ACTOR **)(player_actor+0xD10)=(ACTOR *)&turkey;
    aETKY_SetTalkInfo((ACTOR *)&turkey);assert(status_sets==1 && last_message==af_hr_message(0x3BFE));
    for(int action=1;action<=4;action++) {
        turkey.talk_action=action;current_message=0x3BFD+action;continued_message=-1;
        aETKY_Explain_Env0123(&turkey,game);assert(continued_message==-1);
        current_message=af_hr_message(current_message);aETKY_Explain_Env0123(&turkey,game);
        assert(continued_message==af_hr_message(action==4?0x3C11:0x3BFE + action));
    }
    assert(turkey.talk_action==aETKY_TALK_GIVE_ME_FORK);order[mDemo_ORDER_NPC0][9]=1;
    turkey.talk_proc(&turkey,game);assert(request_count==1 && !deleted && !locked);
    request_ok=1;turkey.talk_proc(&turkey,game);
    assert(request_count==2 && deleted==1 && locked && order[mDemo_ORDER_NPC0][9]==2);
    for(unsigned i=0;i<20;i++)turkey.talk_proc(&turkey,game);
    assert(locked && !unlocks);
    af_cw_native_handover=0;turkey.talk_proc(&turkey,game);assert(locked);
    af_cw_native_handover=&transport;transport.master=0;turkey.talk_proc(&turkey,game);
    assert(!locked && unlocks==1 && turkey.talk_action==aETKY_TALK_GIVE_YOU_PRESENT);
    order[mDemo_ORDER_NPC0][1]=2;turkey.talk_proc(&turkey,game);
    assert(give_count==1 && !saved.data.given_present_bitfield && !order[mDemo_ORDER_NPC1][0]);
    give_ok=1;turkey.talk_proc(&turkey,game);
    assert(give_count==2 && saved.data.given_present_bitfield==1 && order[mDemo_ORDER_NPC1][0]==af_hr_reward(0));
    for(unsigned i=0;i<20;i++)turkey.talk_proc(&turkey,game);
    assert(give_count==2 && turkey.talk_action==aETKY_TALK_WAIT_END);guards();
    slot=4;assert(!af_hr_insert(private_data,af_hr_reward(0),0));slot=0;
    assert(!af_hr_insert(window,af_hr_reward(0),0) && !af_hr_insert(private_data,af_hr_reward(0),1));
    cutlery=0;assert(!af_hr_enabled_mask() && !af_hr_get_save(AF_HR_SOURCE,0));cutlery=1;
    s_xyz angle={1,2,3};af_hr_force_angle(game,NULL,&angle,32);assert(force_calls==1);
    af_hr_force_angle(game,NULL,&angle,16);af_hr_force_angle(window,NULL,&angle,32);assert(force_calls==1);
    *(u32 *)(game+0x1EA0)=123;assert(af_hr_frame()==123 && af_hr_game()==game);
    af_hr_dying(AF_HR_SOURCE,&turkey);assert(deaths==3);
    saved.data.given_present_bitfield=0x1000;expected_halt=1;
    if(!setjmp(failure)) {af_hr_get_save(AF_HR_SOURCE,0);assert(0);}
    assert(halt_calls==1);guards();
    puts("Complete Franklin selection, additive dialogue, refused/accepted cutlery, single reward insertion, native event-area guards, and force-angle routing pass; native services are doubled.");
    saved.data.given_present_bitfield=0;expected_halt=0;hiding_checks();
}
