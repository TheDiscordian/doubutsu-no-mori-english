/* Complete carried exercise-card and Harvest-cutlery records, gated together
 * with their event/player/profile consumers. No native short-table indexing. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u16 item,price; u8 category,group; u16 reserved; u32 icon; u8 name[16]; } Item;
_Static_assert(sizeof(Item)==28,"Event item record size");
#ifdef __mips__
#define header ((const u32 *)0x80705E00u)
#else
extern u32 af_test_holiday_items[102];
#define header af_test_holiday_items
#endif
extern int af_holiday_prior_name(u8 *,u32,u32),af_holiday_prior_type(u32);
extern u32 af_holiday_prior_price(u32);
extern u16 af_holiday_prior_display(u32),af_holiday_prior_pocket(u32);

static int extended(u32 item) {return item-0x2523u<14u;}
static const Item *find(u32 item) {
    if(!extended(item) || header[0]!=0x41464849u || header[1]!=2u || header[2]!=14u || header[3]&~3u)return 0;
    u32 index=item-0x2523u;const Item *row=(const Item *)(header+4)+index;
    u32 group=index==13u ? 2u : 1u;
    if(!(header[3]&group) || row->item!=item || row->group!=group || row->price || row->reserved ||
       row->category!=(index==13u ? 47u : 45u) || row->icon!=(index==13u ? 0x80706240u : 0x80706000u))return 0;
    return row;
}
int af_holiday_item_name(u8 *out,u32 capacity,u32 item) {
    if(!extended(item))return af_holiday_prior_name(out,capacity,item);
    const Item *row=find(item);if(!out || capacity<16u || !row)return 0;
    for(u32 i=0;i<16u;i++)out[i]=row->name[i];
    return 1;
}
int af_holiday_item_type(u32 argument) {
    u32 item=(u16)argument;if(!extended(item))return af_holiday_prior_type(argument);
    const Item *row=find(item);return row ? row->category : 0;
}
u32 af_holiday_item_price(u32 argument) {
    u32 item=(u16)argument;if(!extended(item))return af_holiday_prior_price(argument);
    return 0; /* The donor miscellaneous category has no price table. */
}
u16 af_holiday_item_display(u32 argument) {
    u32 item=(u16)argument;if(!extended(item))return af_holiday_prior_display(argument);
    return find(item) ? item : 0;
}
u16 af_holiday_item_pocket(u32 argument) {
    u32 item=(u16)argument;if(!extended(item))return af_holiday_prior_pocket(argument);
    return find(item) ? item : 0;
}
u32 af_holiday_item_icon(u32 item) {const Item *row=find(item);return row ? row->icon : 0;}
