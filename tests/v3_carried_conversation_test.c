/* Execute the actual generated reward selection and conversation transactions.
 * Native transport/storage doubles are not native gameplay verification. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "carried-conversation-under-test.c"
typedef struct {u16 source,item;u8 quantity,pad[3];} Reward;
extern const Reward af_cw_rewards[];
extern const u32 af_cw_reward_count;
typedef struct {
    u32 birth,change_master,change_mode;
    u8 request_mode,player_after_mode;u16 item;ACTOR *master,*target;
    u8 present,changed,pad[2];ACTOR *actor;u32 rebuild;
} NativeHandover;
static NativeHandover transport={.birth=1,.change_mode=2};
NativeHandover *volatile af_cw_native_handover=&transport;
static _Alignas(16) u8 player_actor[0xD20],private_data[0xBD0];
static EV_GHOST_ACTOR ghost;
static int player_index,request_ok,request_calls,give_ok,give_calls,deleted,locked;
static int collected,disable_untracked;
static u16 disabled,inserted,orders[10][16];
static float random_value;
static u8 window[0x300];
static int message,continued;
static u8 item_text[16];
static u16 named;
Private_c *af_cw_private(void) {return private_data;}
int af_cw_player(void) {return player_index;}
float fqrand(void) {return random_value;}
u16 af_cw_paper_stack(u16 paper,unsigned quantity) {
    if(paper==0x2043) {assert(quantity==1);return 0x2043;}
    assert(paper>=0x2000 && paper<=0x203F && quantity==4);
    /* This provider is still unimplemented in the cartridge. The double makes
     * its required four-sheet contract observable instead of discarding it. */
    return 0x7000+(paper-0x2000)*4+quantity-1;
}
int af_carried_type(u32 item) {
    if(!item || item==disabled)return 0;
    if(disable_untracked) {
        for(u32 i=0;i<af_cw_reward_count;i++)if(af_cw_rewards[i].item==item) {
            unsigned category=af_cw_rewards[i].source>>8;
            if(category==0x22 || category==0x24)return 0;
        }
    }
    return 12;
}
int af_carried_owned(const u8 *p,u32 item) {assert(p==private_data && item);return collected;}
u32 af_carried_quantity(u32 item) {return item==0x2D28?1:0;}
ACTOR *af_cw_native_player_actor(GAME *g) {assert(g==window);return (ACTOR *)player_actor;}
int af_hp_admit(ACTOR *a,GAME *g) {return a==(ACTOR *)&ghost && g==window;}
int af_cw_native_request_give(GAME *g,u16 item,int mode,int present,int surface) {
    assert(g==window && item==0x2D28 && mode==7 && !present && !surface);request_calls++;
    if(request_ok)transport.master=(ACTOR *)&ghost;
    return request_ok;
}
int af_cw_native_give(void *p,u16 item,int condition) {
    assert(p==private_data && item && !condition);give_calls++;
    if(give_ok)inserted=item;
    return give_ok;
}
u16 mDemo_Get_OrderValue(int type,int slot) {assert(type>=0 && type<10 && slot>=0 && slot<16);return orders[type][slot];}
void af_cw_native_order(int type,int slot,u16 value) {orders[type][slot]=value;}
void af_cw_native_message(int value) {message=value;}
void af_cw_native_continue(void *w,int value) {assert(w==window);continued=value;}
int af_cw_message(int source) {return source>=0x2ED3 && source<=0x2F02?source-0x2ED3+0x3320:-1;}
int af_cw_native_item_name(u8 *out,u32 length,u32 item) {
    assert(length==16);memset(out,'x',16);named=item;return 1;
}
void af_cw_native_item_string(void *w,int slot,const u8 *text,int length) {
    assert(w==window && slot==0 && length==16);memcpy(item_text,text,16);
}
mMsg_Window_c *mMsg_Get_base_window_p(void) {return window;}
void mMsg_Set_LockContinue(void *w) {assert(w==window);locked=1;}
void mMsg_Unset_LockContinue(void *w) {assert(w==window);locked=0;}
int mPr_GetPossessionItemIdxWithCond(void *p,u16 item,int condition) {
    assert(p==private_data && !condition);return !deleted && item==0x2D28?4:-1;
}
void mPr_SetPossessionItem(void *p,int slot,u16 item,int condition) {
    assert(p==private_data && slot==4 && !item && !condition);deleted++;
}

int main(void) {
    u16 *lists[]={ftr_listA,ftr_listB,ftr_listC,ftr_listEvent,ftr_listLottery,
        carpet_listA,carpet_listB,carpet_listC,carpet_listEvent,
        wall_listA,wall_listB,wall_listC,wall_listEvent,
        cloth_listA,cloth_listB,cloth_listC,cloth_listEvent,
        binsen_listA,binsen_listB,binsen_listC,list_haniwa,umbrella_list};
    assert(sizeof lists/sizeof *lists==22 && af_cw_reward_count==1000);
    unsigned count=0;
    for(unsigned i=0;i<22;i++)for(u16 *p=lists[i];*p;p++) {
        assert(af_cw_reward_supported(*p));count++;
    }
    assert(count==998);
    /* Every weighted candidate remains reachable in the actual donor chooser. */
    unsigned index=0;
    for(unsigned i=0;i<22;i++)for(u16 *p=lists[i];*p;p++,index++) {
        random_value=((float)index+0.5f)/(float)count;
        assert(aEGH_not_collect_get()==af_cw_reward_native(*p));
    }
    disabled=af_cw_reward_native(ftr_listA[0]);
    int all,uncollected;aEGH_check_collect_num(&all,&uncollected,ftr_listA);
    assert(all==uncollected && all>0 && af_cw_reward_at(0,ftr_listA)==ftr_listA[1]);
    assert(aEGH_get_collect(0,ftr_listA)==ftr_listA[1]);
    collected=1;disable_untracked=1;
    /* Exercise the source all-collected fallback with disabled holes in the
     * list. It must index the available entries, not the raw array. */
    count=0;
    for(unsigned i=0;i<22;i++) {
        aEGH_check_collect_num(&all,&uncollected,lists[i]);assert(!uncollected);count+=(unsigned)all;
    }
    index=0;
    for(unsigned i=0;i<22;i++)for(u16 *p=lists[i];*p;p++)if(af_cw_reward_supported(*p)) {
        random_value=((float)index++ +0.5f)/(float)count;
        assert(aEGH_not_collect_get()==af_cw_reward_native(*p));
    }
    assert(!af_cw_reward_native(0xFFFF) && !af_cw_reward_at(-1,ftr_listA));
    assert(!mRmTp_FtrItemNo2Item1ItemNo(ftr_listA[1],0));
    disabled=0;disable_untracked=0;
    assert(af_cw_reward_native(0x20C0)==af_cw_paper_stack(0x2000,4));
    assert(af_cw_reward_native(0x20C3)==0x2043);

    ghost.npc_class.actor_class.npc_id=0xD0CD;
    transport.actor=(ACTOR *)&ghost;
    *(int *)(player_actor+0xCF0)=0x40;
    *(ACTOR **)(player_actor+0xD10)=(ACTOR *)&ghost;
    orders[mDemo_ORDER_NPC0][9]=1;
    aEGH_give_me_wait(&ghost,window);
    assert(request_calls==1 && !deleted && !locked && orders[mDemo_ORDER_NPC0][9]==1);
    request_ok=1;aEGH_give_me_wait(&ghost,window);
    assert(request_calls==2 && deleted==1 && locked && orders[mDemo_ORDER_NPC0][9]==2);
    aEGH_give_me_wait(&ghost,window);assert(locked);
    af_cw_native_handover=0;aEGH_give_me_wait(&ghost,window);assert(locked);
    af_cw_native_handover=&transport;transport.master=0;
    aEGH_give_me_wait(&ghost,window);
    assert(!locked && ghost.talk_act==aEGH_TALK_SELECT_WAIT && !orders[mDemo_ORDER_NPC0][9]);
    ghost.give_item=af_cw_reward_native(ftr_listA[0]);
    ghost.talk_act=aEGH_TALK_GIVE_YOU_WAIT;orders[mDemo_ORDER_NPC0][1]=2;
    aEGH_give_you_wait(&ghost,window);
    assert(give_calls==1 && !inserted && !orders[mDemo_ORDER_NPC1][0] && ghost.talk_act==aEGH_TALK_GIVE_YOU_WAIT);
    give_ok=1;aEGH_give_you_wait(&ghost,window);
    assert(inserted==ghost.give_item && orders[mDemo_ORDER_NPC1][0]==inserted && ghost.talk_act==aEGH_TALK_END_WAIT);
    player_index=4;assert(!mPr_SetFreePossessionItem(private_data,inserted,0));player_index=0;
    assert(!mPr_SetFreePossessionItem(window,inserted,0));
    assert(!mPr_SetFreePossessionItem(private_data,inserted,1));
    disabled=inserted;assert(!mPr_SetFreePossessionItem(private_data,inserted,0));disabled=0;
    mDemo_Set_msg_num(0x2EE4);assert(message==0x3331);
    mDemo_Set_msg_num(-1);assert(message==0x3331);
    mMsg_Set_continue_msg_num(window,0x2F02);assert(continued==0x334F);
    u8 name[16];mIN_copy_name_str(name,inserted);assert(named==inserted);
    mMsg_Set_item_str_art(window,0,name,16,mIN_get_item_article(inserted));assert(!memcmp(name,item_text,16));
    for(int i=0;i<32;i++) {mString_Load_StringFromRom(name,16,0x62E + i);assert(name[0]!='\0');}
    puts("complete reward selection, mapped names/messages, and refused/successful handovers pass");
    return 0;
}
