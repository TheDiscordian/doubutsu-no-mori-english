/* Added floor/wall items keep their own identities and complete official names. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct {u16 item,price;u32 enabled;u8 name[16];} SurfaceItem;
_Static_assert(sizeof(SurfaceItem)==24,"Surface item metadata stride");
#ifdef __mips__
#define header ((const u32 *)0x804BC800u)
#else
extern u32 af_test_surface_items[64];
#define header af_test_surface_items
#endif
extern int af_surface_prior_name(u8 *,u32,u32);
extern int af_surface_prior_type(u32);
extern u32 af_surface_prior_price(u32);

static int extended(u32 item) {
    return (item>>8)-0x26u<2u && (item&255u)>=64u;
}

static const SurfaceItem *find(u32 item) {
    u32 kind=(item>>8)-0x26u,index=(item&255u)-73u;
    if (kind>=2u || index>=5u || header[0]!=0x41465349u || header[1]!=1u ||
            header[2]!=10u || header[3]!=sizeof(SurfaceItem)) return 0;
    const SurfaceItem *row=(const SurfaceItem *)(header+4)+kind*5u+index;
    return row->item==item && row->enabled==1u ? row : 0;
}

int af_v3_surface_item_name(u8 *target,u32 capacity,u32 item) {
    if (!extended(item)) return af_surface_prior_name(target,capacity,item);
    const SurfaceItem *row=find(item);
    if (!target || capacity<16u || !row) return 0;
    for (u32 i=0;i<16u;i++) target[i]=row->name[i];
    return 1;
}

int af_v3_surface_item_type(u32 argument) {
    u32 item=(u16)argument;
    if (!extended(item)) return af_surface_prior_type(argument);
    return find(item) ? 12 : 0;
}

u32 af_v3_surface_item_price(u32 argument) {
    u32 item=(u16)argument;
    if (!extended(item)) return af_surface_prior_price(argument);
    const SurfaceItem *row=find(item);
    return row ? row->price : 0;
}
