/* Complete generated gift NPC, exercised through its real talk callbacks.
 * Native inventory, message, and handover services are recording doubles. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "present_npc.c"
#include "npc_hem.c"

mDemo_Clip_c *af_rw_demo_clip;
static unsigned inserts,locks,unlocks,orders,refuse,messages,marks,clears,returns;
static u16 last_item;
static void *handover;
static int window,private_data;
static u8 first_present;
void none_proc1(void) {}
void *af_rw_private(void) {return &private_data;}
void *af_cw_handover_master(void) {return handover;}
u16 mDemo_Get_OrderValue(int who,int slot) {
    assert(who==mDemo_ORDER_NPC0 && slot==1);return 2;
}
void mDemo_Set_OrderValue(int who,int slot,u16 value) {
    assert(who==mDemo_ORDER_NPC1 && slot>=0 && slot<=2);
    if(slot==0)last_item=value;
    if(slot==1)assert(value==aHOI_REQUEST_PUTAWAY);
    if(slot==2)assert(value==(last_item==ITM_GOLDEN_AXE?2:0));
    orders++;
}
int af_rw_insert(void *p,u16 item,int condition) {
    assert(p==&private_data && condition==mPr_ITEM_COND_NORMAL);
    if(refuse)return 0;
    last_item=item;inserts++;return 1;
}
int mPr_SetFreePossessionItem(void *p,u16 item,int condition) {return af_rw_insert(p,item,condition);}
void *mMsg_Get_base_window_p(void) {return &window;}
void mMsg_Set_LockContinue(void *p) {assert(p==&window);locks++;}
void mMsg_Unset_LockContinue(void *p) {assert(p==&window);unlocks++;}
void mIN_copy_name_str(u8 *s,u16 item) {(void)s;(void)item;assert(0);}
int mIN_get_item_article(u16 item) {(void)item;assert(0);return 0;}
void mMsg_Set_item_str_art(void *p,int n,const u8 *s,int size,int article) {
    (void)p;(void)n;(void)s;(void)size;(void)article;assert(0);
}
u8 *af_rw_first_present(void) {return &first_present;}
u8 af_rw_first_present_get(void) {return first_present;}
void af_rw_first_present_mark(u8 bits) {first_present|=bits;}
/* ASan retains the complete exported actor profile, including unrelated
 * callbacks. Any accidental call outside this handover test must fail. */
const AFHPNpcServices af_hp_npc_services={0};
const AFHPTools af_rw_tools={0};
const AFHPEffects af_rw_effects={0};
static AFRewardShrine shrine;
AFRewardShrine *af_rw_shrine(void) {return &shrine;}
static int visible;
int *af_rw_hem_visible(void) {return &visible;}
void af_rw_trophy_set(int trophy) {assert(trophy==mSC_TROPHY_GOLDEN_AXE);marks++;}
void mFAs_ClearGoodField(void) {clears++;}
void mDemo_Set_talk_return_get_golden_axe_demo(int yes) {assert(yes);returns++;}
static int unexpected(void) {assert(0);return 0;}
void af_rw_npc_save(ACTOR *a,GAME *g) {unexpected();}
int mDemo_Request(int type,ACTOR *a,void (*f)(ACTOR *)) {return unexpected();}
int mDemo_Check(int type,ACTOR *a) {return unexpected();}
void mDemo_Set_ListenAble(void) {}
int af_rw_player(void) {return unexpected();}
int mHS_get_arrange_idx(int p) {return unexpected();}
int af_rw_is_resident(NPC_ACTOR *a) {return unexpected();}
int af_rw_weather(void) {return unexpected();}
u8 *af_rw_menu_refuse(GAME *g) {unexpected();return NULL;}
void Actor_delete(ACTOR *a) {unexpected();}
u16 af_rw_umbrella(NPC_ACTOR *a) {return unexpected();}
int *af_rw_sub_animation(NPC_ACTOR *a) {unexpected();return NULL;}
int mNpc_GetNpcLooks(ACTOR *a) {return unexpected();}
void mDemo_Set_msg_num(int n) {assert(n==MSG_HEM_GOLD_AXE1);messages++;}
float fqrand(void) {return unexpected();}
int mPr_GetPossessionItemIdx(void *p,u16 item) {return unexpected();}
void mSC_LightHouse_Event_Clear(int p) {unexpected();}
void mem_copy(u8 *dst,const u8 *src,unsigned size) {memcpy(dst,src,size);}

int main(void) {
    const int types[]={aPRD_TYPE_GOLDEN_NET,aPRD_TYPE_GOLDEN_ROD};
    const u16 items[]={ITM_GOLDEN_NET,ITM_GOLDEN_ROD};
    for(unsigned i=0;i<2;i++) {
        PRESENT_NPC_ACTOR actor={0};
        PRESENT_DEMO_ACTOR director={0};
        mDemo_Clip_c clip={&director,mDemo_CLIP_TYPE_PRESENT_DEMO};
        director.type=types[i];director.present=items[i];af_rw_demo_clip=&clip;
        inserts=locks=unlocks=orders=0;handover=&actor;
        aPST_change_talk_proc(&actor,aPST_TALK_PRESENT_SEND_START_WAIT);
        refuse=1;actor.talk_proc(&actor);
        assert(!inserts && !locks && !orders && actor.talk_proc==aPST_present_send_start_wait_talk_proc);
        refuse=0;
        actor.talk_proc(&actor);
        assert(inserts==1 && locks==1 && !unlocks && orders==3 && last_item==items[i]);
        assert(actor.talk_proc==aPST_present_send_end_wait_talk_proc);
        for(unsigned frame=0;frame<100;frame++)actor.talk_proc(&actor);
        assert(inserts==1 && locks==1 && !unlocks && orders==3);
        handover=NULL;actor.talk_proc(&actor);
        assert(inserts==1 && locks==1 && unlocks==1 && orders==3);
        actor.talk_proc(&actor);
        assert(inserts==1 && unlocks==1);
    }
    assert(aPST_check_first_present(aPST_PRESENT_TYPE_GOLDEN_NET));
    assert(!aPST_check_first_present(aPST_PRESENT_TYPE_GOLDEN_NET));
    assert(aPST_check_first_present(aPST_PRESENT_TYPE_GOLDEN_ROD));
    assert(!aPST_check_first_present(aPST_PRESENT_TYPE_GOLDEN_ROD));
    NPC_HEM_ACTOR hem={0};hem.talk_timer=90;
    inserts=locks=unlocks=orders=0;refuse=1;
    aNHM_set_force_talk_info_talk_request((ACTOR *)&hem);
    for(unsigned i=0;i<100;i++)assert(!aNHM_talk_init((ACTOR *)&hem,0));
    assert(!hem.reward_ready && hem.talk_timer==90 && !inserts && !messages && !marks && !clears && !returns && !orders);
    refuse=0;assert(!aNHM_talk_init((ACTOR *)&hem,0));
    assert(hem.reward_ready && hem.talk_timer==89 && inserts==1 && messages==1 && marks==1 && clears==1 && returns==1);
    for(unsigned i=0;i<88;i++)assert(!aNHM_talk_init((ACTOR *)&hem,0));
    assert(aNHM_talk_init((ACTOR *)&hem,0));
    assert(inserts==1 && !orders && hem.talk_proc==aNHM_trans_demo_start_wait_talk_proc);
    handover=&hem;hem.talk_proc(&hem,0);
    assert(orders==3 && hem.trans_flag && locks==1 && !unlocks);
    assert(hem.talk_proc==aNHM_trans_demo_end_wait_talk_proc);
    for(unsigned i=0;i<100;i++)hem.talk_proc(&hem,0);
    assert(inserts==1 && marks==1 && !unlocks);
    handover=0;hem.talk_proc(&hem,0);hem.talk_proc(&hem,0);
    assert(unlocks==1 && inserts==1 && marks==1);
    puts("Net, rod, and Shrine axe callbacks block refused insertion, retry safely, insert once, wait for handover, and unlock once. Native services are doubled.");
}
