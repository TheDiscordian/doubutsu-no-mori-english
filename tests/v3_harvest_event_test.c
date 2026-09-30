/* Complete generated Franklin actor and real shared adapters, with native
 * inventory/transport/event services doubled. This is not native gameplay. */
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "ev_turkey.c"

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
}
