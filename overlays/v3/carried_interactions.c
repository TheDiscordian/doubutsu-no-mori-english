/* Source carried-creature interactions share native menus, net animation,
 * inventory mutation, and release requests. No museum entry or cage is added. */
#include "carried_items.h"
typedef AFCarryByte u8;
typedef AFCarryHalf u16;
typedef AFCarryWord u32;
#define W(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define H(p,o) (*(u16 *)((u8 *)(p)+(o)))
#ifdef __mips__
#define P(p,o) (*(void **)((u8 *)(p)+(o)))
#define ACTIVE (*(u8 **)0x80136FD8u)
#define FIELD (*(u8 *)AF_CARRIED_FIELD_ADDRESS)
static void *native(u32 at) {
    if(at>=0x808B2D50u)at+=*(u32 *)0x80143900u-0x808DD748u;
    else if(at>=0x8086F310u)at+=W(*(void **)0x8010DCECu,0x2CC0)-0x808787A0u;
    return (void *)at;
}
#else
extern void *af_test_carried_interaction_pointer(void *,u32),*af_test_carried_interaction_function(u32);
extern u8 *af_test_carried_interaction_active,af_test_carried_interaction_field;
#define P af_test_carried_interaction_pointer
#define native af_test_carried_interaction_function
#define ACTIVE af_test_carried_interaction_active
#define FIELD af_test_carried_interaction_field
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
extern int af_carried_prior_action_menu(void *,u32,int);
extern void af_carried_prior_insect_message(u8 *,unsigned);
extern void af_carried_set_message(unsigned);
static unsigned spirit(u32 item) {
    return item-0x2D28u<5u ? af_carried_quantity(item) : 0;
}
static int ordinary(int slot) {
    return ACTIVE && (unsigned)slot<15u && !(W(ACTIVE,0x34)>>(slot*2)&3u);
}

int af_carried_interaction_menu(void *submenu,u32 item,int slot) {
    int original=af_carried_prior_action_menu(submenu,item,slot);
    /* Preserve multi-item marks and protected-present/quest actions. The
     * source uses the same release/catch menu for all five spirit counts. */
    if(ordinary(slot) && spirit(item) && (original==7 || original==8 || original==12))
        return FIELD==0 ? 7 : 8;
    return original;
}

void af_carried_release(void *submenu,void *menu) {
    if(!submenu || !menu || !ACTIVE)return;
    void *overlay=P(submenu,0x2C),*tag=overlay?P(overlay,0x106D0):0;
    if(!tag)return;
    int slot=FN(0x8086F910u,int,void *)((u8 *)tag+8);
    if((unsigned)slot>=15u)return;
    u32 item=H(ACTIVE,0x14+slot*2);
    if(item-0x2D28u>=5u) {
        FN(0x808739B0u,void,void *,void *)(submenu,menu);return;
    }
    unsigned count=spirit(item);
    if(!count || !ordinary(slot) || FIELD)return;
    ((u8 *)submenu)[0xDF]=(u8)slot;H(submenu,0xE0)=(u16)item;
    /* Both ordinary release and the full-pocket exchange route retain a
     * remaining stack, exactly as the donor's final Wisp branch does. */
    u16 rest=count>1 ? af_carried_with_quantity(item,count-1) : 0;
    FN(0x800B8B08u,void,void *,int,u32,int)(ACTIVE,slot,rest,0);
    FN(0x8086F4ACu,int,void *,int,int)(submenu,0,0);
    FN(0x80871760u,void,void *,void *,int)(submenu,menu,1);
    FN(0x800B20A8u,void,int)(40);
}

int af_carried_net_slot(void *player) {
    void *caught=player?P(player,0xE68):0;
    unsigned count=caught && W(player,0xF24)==40 ? spirit(H(caught,0x21C)) : 0;
    if(count && ACTIVE) {
        for(int i=0;i<15;i++) {
            unsigned held=spirit(H(ACTIVE,0x14+i*2));
            if(ordinary(i) && held && held+count<=5)return i;
        }
    }
    return FN(0x800B3780u,int,void)();
}

void af_carried_net_put(int slot,u32 item,void *position) {
    unsigned count=spirit(item);
    if(count) {
        if(!ordinary(slot))return;
        u32 held=H(ACTIVE,0x14+2*slot);
        unsigned previous=spirit(held);
        if(held && (!previous || previous+count>5))return;
        if(previous)item=af_carried_with_quantity(item,previous+count);
    }
    FN(0x808B5584u,void,int,u32,void *)(slot,item,position);
}

void af_carried_net_message(u8 *player,unsigned original) {
    if(player && P(player,0xE68) && W(player,0xF24)==40 && spirit(0x2D28)) {
        unsigned count=0;
        if(ACTIVE)for(int i=0;i<15;i++) {
            unsigned held=spirit(H(ACTIVE,0x14+i*2));
            if(ordinary(i) && held) {count=held;break;}
        }
        af_carried_set_message(AF_CARRIED_SPIRIT_MESSAGE_FIRST+count);
        return;
    }
    af_carried_prior_insect_message(player,original);
}
