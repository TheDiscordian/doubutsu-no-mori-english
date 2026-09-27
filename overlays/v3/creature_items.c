/* Source-derived creature parents; room forms are not independent items. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct {u16 item,display,price;u8 type,source;u32 ready;u8 name[16];} Creature;
_Static_assert(sizeof(Creature)==28,"Creature metadata stride");
#ifdef __mips__
#define header ((const u32 *)0x804FF900u)
#define af_creature_prior_name ((int (*)(u8 *,u32,u32))AF_CREATURE_PRIOR_NAME)
#define af_creature_prior_type ((int (*)(u32))AF_CREATURE_PRIOR_TYPE)
#define af_creature_prior_price ((u32 (*)(u32))AF_CREATURE_PRIOR_PRICE)
#define af_creature_prior_display ((u16 (*)(u32))AF_CREATURE_PRIOR_DISPLAY)
#define af_creature_prior_pocket ((u16 (*)(u32))AF_CREATURE_PRIOR_POCKET)
#else
extern u32 af_test_creature_items[128];
#define header af_test_creature_items
extern int af_creature_prior_name(u8 *,u32,u32);
extern int af_creature_prior_type(u32);
extern u32 af_creature_prior_price(u32);
extern u16 af_creature_prior_display(u32),af_creature_prior_pocket(u32);
#endif
extern int af_creature_profile(u32);

static int extended(u32 item) {
    return (((item>>8)==0x23u || (item>>8)==0x2Du) && (item&255u)>=32u) ||
        (item>=0x3C98u && item<0x3CDCu);
}

static const Creature *find(u32 item) {
    if (header[0]!=0x41464349u || header[1]!=1u || header[2]!=17u || header[3]!=28u) return 0;
    const Creature *rows=(const Creature *)(header+4);
    for (u32 i=0;i<17u;i++) {
        const Creature *r=rows+i;
        if (r->item!=item && r->display!=(item&0xFFFCu)) continue;
        if (r->ready!=1u || r->display<0x3C98u || r->display>=0x3CDCu || (r->display&3u) ||
                !((r->item>=0x2320u && r->item<=0x2328u && r->type==8u) ||
                  (r->item>=0x2D20u && r->item<=0x2D27u && r->type==18u)) ||
                !af_creature_profile(1024u+((r->display&0xFFFu)>>2))) return 0;
        return r;
    }
    return 0;
}

int af_v3_creature_item_name(u8 *target,u32 capacity,u32 item) {
    if (!extended(item)) return af_creature_prior_name(target,capacity,item);
    const Creature *r=find(item);
    if (!target || capacity<16u || !r) return 0;
    for (u32 i=0;i<16u;i++) target[i]=r->name[i];
    return 1;
}

int af_v3_creature_item_type(u32 argument) {
    u32 item=(u16)argument;
    if (!extended(item)) return af_creature_prior_type(argument);
    const Creature *r=find(item);
    return r ? (r->item==item ? r->type : 10) : 0;
}

u32 af_v3_creature_item_price(u32 argument) {
    u32 item=(u16)argument;
    if (!extended(item)) return af_creature_prior_price(argument);
    const Creature *r=find(item);
    return r ? r->price : 0;
}

u16 af_v3_creature_room_display(u32 argument) {
    u32 item=(u16)argument;
    if (!extended(item)) return af_creature_prior_display(argument);
    const Creature *r=find(item);
    return r ? (r->item==item ? r->display : item) : 0;
}

u16 af_v3_creature_room_pocket(u32 argument) {
    u32 item=(u16)argument;
    if (!extended(item)) return af_creature_prior_pocket(argument);
    const Creature *r=find(item);
    return r ? r->item : 0;
}
