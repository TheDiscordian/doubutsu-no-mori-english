/* Shared imported stacks use native hand movement, inventory refresh, and
 * letter confirmation. Existing paper, tickets, presents, and quests retain
 * their original paths. Source quantities are translated through the registry,
 * never through the donor's incompatible paper-ID arithmetic. */
#include "carried_items.h"
typedef AFCarryByte u8;
typedef AFCarryHalf u16;
typedef AFCarryWord u32;
#define W(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define H(p,o) (*(u16 *)((u8 *)(p)+(o)))
#ifdef __mips__
#define P(p,o) (*(void **)((u8 *)(p)+(o)))
#define ACTIVE (*(u8 **)0x80136FD8u)
static void *native(u32 at) {
    u8 *metadata=*(u8 **)0x8010DCECu;
    if(at>=0x8087A330u && at<0x8087CA30u)
        at=W(metadata,0x2CE0)-0x8087C360u+at;
    else if(at>=0x8086F310u && at<0x8087A330u)
        at=W(metadata,0x2CC0)-0x808787A0u+at;
    return (void *)at;
}
#else
extern void *af_test_carried_action_pointer(void *,u32),*af_test_carried_action_function(u32);
extern u8 *af_test_carried_action_active;
#define P af_test_carried_action_pointer
#define native af_test_carried_action_function
#define ACTIVE af_test_carried_action_active
#endif
#define FN(at,result,...) ((result (*)(__VA_ARGS__))native(at))
extern int af_carried_prior_menu(void *,u32,int);

static void *component(void *submenu,u32 offset) {
    void *overlay=submenu?P(submenu,0x2C):0;
    return overlay?P(overlay,offset):0;
}
static u32 condition(void *player,int slot) {
    return W(player,0x34)>>(2*slot)&3u;
}

/* Keep the preceding installed reader packet's final alignment padding. */
__attribute__((aligned(16))) int af_carried_menu_type(void *submenu,u32 item,int slot) {
    /* The predecessor includes presents/quests, room rules, burial eligibility,
     * existing event items, furniture, balloons, and creatures. */
    int result=af_carried_prior_menu(submenu,item,slot);
    if(!ACTIVE || (u32)slot>=15u || condition(ACTIVE,slot) ||
            item-0x2040u>=4u || af_carried_quantity(item)<2u)return result;
    switch(result) {
        case 3:return AF_CARRIED_PAPER_MENUS;
        case 4:return AF_CARRIED_PAPER_MENUS+1;
        case 15:return AF_CARRIED_PAPER_MENUS+2;
        case 17:return AF_CARRIED_PAPER_MENUS+3;
        default:return result;
    }
}

void af_carried_grab_one(void *submenu,void *menu) {
    (void)menu;
    u8 *tag=component(submenu,0x106D0),*hand=component(submenu,0x106D4);
    if(!tag || !hand || !ACTIVE)return;
    int slot=FN(0x8086F910u,int,void *)(tag+8);
    if((u32)slot>=15u || condition(ACTIVE,slot) || H(hand,0x23C))return;
    u32 item=H(ACTIVE,0x14+2*slot),quantity=af_carried_quantity(item);
    if(quantity<2u)return;
    u16 one=af_carried_with_quantity(item,1),rest=af_carried_with_quantity(item,quantity-1);
    if(!one || !rest)return;
    H(hand,0x23A)=2;H(hand,0x23C)=one;W(hand,0x2E4)=0;
    hand[0x2E8]=0;hand[0x2E9]=(u8)slot;hand[0x2EB]=0;
    H(ACTIVE,0x14+2*slot)=rest;
    FN(0x8086F4ACu,int,void *,int,int)(submenu,0,0);
    FN(0x8086FD3Cu,void,void *)(submenu);
    FN(0x800D1A9Cu,void,int)(0x33);
}

void af_carried_drop_stack(void *submenu,void *tag,u16 *target,int slot) {
    u8 *hand=component(submenu,0x106D4);
    if(hand && ACTIVE && (u32)slot<15u && target==(u16 *)(ACTIVE+0x14+2*slot) &&
            !W(hand,0x2E4) && !condition(ACTIVE,slot)) {
        u32 held=H(hand,0x23C),a=af_carried_quantity(held),b=af_carried_quantity(*target);
        u32 max=held-0x2040u<4u?4u:5u;
        if(a && b && a<max && b<max &&
                af_carried_with_quantity(held,1)==af_carried_with_quantity(*target,1)) {
            u32 total=a+b,overflow=total>max?total-max:0;
            u16 combined=af_carried_with_quantity(held,total>max?max:total);
            u16 remainder=overflow?af_carried_with_quantity(held,overflow):0;
            if(combined && (!overflow || remainder)) {
                /* The real native drop swaps these temporary values, leaving
                 * the full combined stack in the pocket and overflow in hand. */
                *target=remainder;H(hand,0x23C)=combined;
                FN(0x8087A94Cu,void,void *,void *,u16 *,void *)(submenu,tag,target,0);
                return;
            }
        }
    }
    FN(0x8087AC90u,void,void *,void *,u16 *,int)(submenu,tag,target,slot);
}

void af_carried_consume_paper(void *player,int slot,u32 replacement,int cond) {
    /* This call is only the confirmed write-letter branch. Cancel/rewrite never
     * comes here. Preserve all ordinary setter/ownership/condition behaviour. */
    if(player && (u32)slot<15u && !replacement && !cond && !condition(player,slot)) {
        u32 item=H(player,0x14+2*slot);
        if(item-0x2040u<4u) {
            u32 quantity=af_carried_quantity(item);
            if(!quantity)return;
            if(quantity>1) {
                replacement=af_carried_with_quantity(item,quantity-1);
                if(!replacement)return;
            }
        }
    }
    FN(0x800B8B08u,void,void *,int,u32,int)(player,slot,replacement,cond);
}
