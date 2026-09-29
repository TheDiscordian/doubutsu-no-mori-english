/* One bounded reader/state path for complete carried families. Selection stays
 * off until all gameplay and persistence consumers are connected. */
#include "carried_items.h"
typedef AFCarryByte u8;
typedef AFCarryHalf u16;
typedef AFCarryWord u32;
#ifdef __mips__
#define header ((const u32 *)AF_CARRY_TABLE)
#else
extern u32 af_test_carried_header[8+8*AF_CARRY_COUNT];
#define header af_test_carried_header
#endif
extern int af_carried_prior_name(u8 *,u32,u32),af_carried_prior_type(u32);
extern u32 af_carried_prior_price(u32);
extern u16 af_carried_prior_display(u32),af_carried_prior_pocket(u32);
extern int af_carried_event_type(u32);

int af_carried_reserved(u32 item) {
    return item-0x2040u<4u || item==0x251Eu || item-0x2523u<14u ||
        item==0x2807u || item==0x290Au || item-0x2D28u<5u;
}
static const AFCarryItem *find(u32 item) {
    if(!af_carried_reserved(item) || header[0]!=0x41464350u || header[1]!=1u ||
       header[2]!=AF_CARRY_COUNT || header[3]!=sizeof(AFCarryItem) ||
       (header[4]|header[5])&~127u || header[6] || header[7])return 0;
    const AFCarryItem *rows=(const AFCarryItem *)(header+8);
    for(u32 i=0;i<AF_CARRY_COUNT;i++) {
        const AFCarryItem *r=rows+i;
        if(r->item!=item)continue;
        if(r->family>=7u || !(header[4]&header[5]&(1u<<r->family)) || r->reserved ||
           r->category<27u || r->category>=71u ||
           r->icon<AF_CARRY_ICON || r->icon>=AF_CARRY_ICON_END ||
           (r->icon-AF_CARRY_ICON)%576u)return 0;
        u32 count=r->family==0u ? 4u : r->family==2u ? 13u : r->family==6u ? 5u : 1u;
        if(r->state>=count || r->parent+r->state!=r->item || (r->source>>12)!=2u)return 0;
        /* Event controls share their existing readiness/selection field. */
        if(item-0x2523u<14u && af_carried_event_type(item)!=r->category)return 0;
        return r;
    }
    return 0;
}
int af_carried_name(u8 *out,u32 capacity,u32 item) {
    if(!af_carried_reserved(item))return af_carried_prior_name(out,capacity,item);
    const AFCarryItem *r=find(item);
    if(!out || capacity<16u || !r)return 0;
    for(u32 i=0;i<16u;i++)out[i]=r->name[i];
    return 1;
}
/* -1 means an unrelated identity; zero is a reserved but unavailable import. */
int af_carried_category(u32 item) {
    if(!af_carried_reserved(item))return -1;
    const AFCarryItem *r=find(item);return r ? r->category : 0;
}
int af_carried_type(u32 argument) {
    int type=af_carried_category((u16)argument);
    return type<0 ? af_carried_prior_type(argument) : type;
}
u32 af_carried_price(u32 argument) {
    u32 item=(u16)argument;
    if(!af_carried_reserved(item))return af_carried_prior_price(argument);
    const AFCarryItem *r=find(item);return r ? r->price : 0;
}
u16 af_carried_display(u32 argument) {
    u32 item=(u16)argument;
    if(!af_carried_reserved(item))return af_carried_prior_display(argument);
    return find(item) ? item : 0;
}
u16 af_carried_pocket(u32 argument) {
    u32 item=(u16)argument;
    if(!af_carried_reserved(item))return af_carried_prior_pocket(argument);
    return find(item) ? item : 0;
}
u32 af_carried_icon(u32 item) {
    const AFCarryItem *r=find(item);return r ? r->icon : 0;
}
u32 af_carried_quantity(u32 item) {
    const AFCarryItem *r=find(item);
    return r && (r->family==0u || r->family==6u) ? r->state+1u : 0;
}
u16 af_carried_with_quantity(u32 item,u32 quantity) {
    const AFCarryItem *r=find(item);
    if(!r || (r->family!=0u && r->family!=6u) || !quantity ||
       quantity>(r->family==0u ? 4u : 5u))return 0;
    const AFCarryItem *rows=(const AFCarryItem *)(header+8);
    for(u32 i=0;i<AF_CARRY_COUNT;i++) {
        const AFCarryItem *next=rows+i;
        if(next->family==r->family && next->parent==r->parent && next->state==quantity-1u &&
           find(next->item)==next)return next->item;
    }
    return 0;
}
