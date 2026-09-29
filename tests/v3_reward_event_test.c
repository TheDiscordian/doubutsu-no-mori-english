/* Complete generated gift NPC, exercised through its real talk callbacks.
 * Native inventory, message, and handover services are recording doubles. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "present_npc.c"

mDemo_Clip_c *af_rw_demo_clip;
static unsigned inserts,locks,unlocks,orders;
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
    if(slot==2)assert(!value);
    orders++;
}
int mPr_SetFreePossessionItem(void *p,u16 item,int condition) {
    assert(p==&private_data && item==last_item && condition==mPr_ITEM_COND_NORMAL);
    inserts++;return 0;
}
void *mMsg_Get_base_window_p(void) {return &window;}
void mMsg_Set_LockContinue(void *p) {assert(p==&window);locks++;}
void mMsg_Unset_LockContinue(void *p) {assert(p==&window);unlocks++;}
void mIN_copy_name_str(u8 *s,u16 item) {(void)s;(void)item;assert(0);}
int mIN_get_item_article(u16 item) {(void)item;assert(0);return 0;}
void mMsg_Set_item_str_art(void *p,int n,const u8 *s,int size,int article) {
    (void)p;(void)n;(void)s;(void)size;(void)article;assert(0);
}
u8 *af_rw_first_present(void) {return &first_present;}
/* ASan retains the complete exported actor profile, including unrelated
 * callbacks. Any accidental call outside this handover test must fail. */
const AFHPNpcServices af_hp_npc_services={0};
const AFHPTools af_rw_tools={0};
static int unexpected(void) {assert(0);return 0;}
void af_rw_npc_save(ACTOR *a,GAME *g) {unexpected();}
int mDemo_Request(int type,ACTOR *a,void (*f)(ACTOR *)) {return unexpected();}
int mDemo_Check(int type,ACTOR *a) {return unexpected();}
void mDemo_Set_ListenAble(void) {unexpected();}
int af_rw_player(void) {return unexpected();}
int mHS_get_arrange_idx(int p) {return unexpected();}
int af_rw_is_resident(NPC_ACTOR *a) {return unexpected();}
int af_rw_weather(void) {return unexpected();}
u8 *af_rw_menu_refuse(GAME *g) {unexpected();return NULL;}
void Actor_delete(ACTOR *a) {unexpected();}
u16 af_rw_umbrella(NPC_ACTOR *a) {return unexpected();}
int *af_rw_sub_animation(NPC_ACTOR *a) {unexpected();return NULL;}
int mNpc_GetNpcLooks(ACTOR *a) {return unexpected();}
void mDemo_Set_msg_num(int n) {unexpected();}
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
    puts("Both complete gift-NPC callbacks insert once, wait for handover, unlock once, and keep independent first-gift flags. Native services are doubled.");
}
