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

#ifdef AF_SURFACE_ROOM
extern int af_surface_prior_floor(void);
extern u32 af_surface_field(void);
extern int af_surface_npc_floor(void);
#ifdef __mips__
#define room_clip (*(u8 ***)0x80136F48u)
#define room_scene (*(const u32 *)0x80126EB4u)
#define home_bytes ((const u8 *)0x8012A428u)
#else
extern u8 **af_test_room_clip;
extern u32 af_test_room_scene;
extern u8 af_test_homes[4*0xB48];
#define room_clip af_test_room_clip
#define room_scene af_test_room_scene
#define home_bytes af_test_homes
#endif

/* Keep the native 0..67 application range. Added identities must be selected. */
int af_v3_surface_allowed(u32 item,u32 base) {
    return (base==0x2600u || base==0x2700u) &&
        (item-base<68u || (item>>8==base>>8 && find(item)));
}

static u32 reserve(u32 argument,u32 base,u32 identity,u32 pending) {
    u32 item=(u16)argument;
    u8 **clip=room_clip;
    if (!clip || !*clip || !af_v3_surface_allowed(item,base)) return 0;
    u8 *actor=*clip;
    if (*(u32 *)(actor+pending)) return 0;
    u32 old=(u16)(*(short *)(actor+identity)+base);
    *(u32 *)(actor+pending)=1;
    *(u16 *)(actor+pending+4)=(u16)item;
    return old;
}

u32 af_v3_surface_reserve_floor(u32 item) {return reserve(item,0x2600,0x174,0x1B0);}
u32 af_v3_surface_reserve_wall(u32 item) {return reserve(item,0x2700,0x176,0x1A8);}

int af_v3_surface_floor_index(void) {
    u32 index;
    if (room_scene-20u<3u) {
        u32 home=af_surface_field()-0x6000u;
        if (home>=4u) return -1;
        index=home_bytes[home*0xB48+0x14];
    } else if (room_scene==6u) index=(u32)af_surface_npc_floor();
    else return af_surface_prior_floor(); /* Includes the existing campsite. */
    return index>=73u && index<78u && find(0x2600u+index) ? (int)index : (int)(index&63u);
}
#endif
