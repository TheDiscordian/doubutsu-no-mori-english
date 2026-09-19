/* Parent names/prices share the equipment selector's profile and readiness.
   Catalogue representations are not separate inventory items. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef struct { u16 item, price, display; u8 kind, source_type; u8 name[16]; } HeldItem;
_Static_assert(sizeof(HeldItem)==24, "Held parent metadata stride");
#ifdef __mips__
#define header ((const u32 *)0x804A87F0u)
#define selected ((int (*)(u32))AF_V3_HELD_SELECTED)
#else
extern u32 af_test_held_items[340];
extern int af_test_held_selected(u32);
#define header af_test_held_items
#define selected af_test_held_selected
#endif

static const HeldItem *find(u32 item) {
    u32 index=item-0x2224u;
    if (index>=56u || header[0]!=0x41464849u || header[1]!=1u ||
            header[2]!=56u || header[3]!=sizeof(HeldItem)) return 0;
    const HeldItem *row=(const HeldItem *)(header+4)+index;
    if (row->item!=item || row->kind<36u || row->kind>=115u ||
            row->display<0x3000u || row->display>=0x4000u || (row->display&3u) ||
            selected(item)!=(int)row->kind) return 0;
    return row;
}

int af_v3_held_item_name(u8 *destination, u32 capacity, u32 item) {
    const HeldItem *row=find(item);
    if (!destination || capacity<16u || !row) return 0;
    for (u32 i=0;i<16u;++i) destination[i]=row->name[i];
    return 1;
}

u32 af_v3_held_item_price(u32 item) {
    const HeldItem *row=find((u16)item);
    return row ? row->price : 0;
}

#ifdef AF_V3_POCKET_ICONS
#ifdef __mips__
#define icons ((const u32 *)0x804A6800u)
#else
extern u32 af_test_pocket_icons[512];
#define icons af_test_pocket_icons
#endif

const u32 *af_v3_held_item_icon(u32 item) {
    if (!find(item) || icons[0]!=0x41464943u || icons[1]!=1u ||
            icons[2]!=56u || icons[3]!=8u) return 0;
    const u32 *row=icons+4+2*(item-0x2224u);
    if (row[0]<0x804A69D0u || row[0]>0x804A6FE0u || (row[0]&7u) ||
        row[1]<0x804A69D0u || row[1]>0x804A6E00u || (row[1]&7u)) return 0;
    return row;
}
#endif
