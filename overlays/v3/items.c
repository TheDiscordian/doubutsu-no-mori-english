/* Selected furniture metadata; all original item paths retain their bodies. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Item { u16 index, item, price; u8 size, enabled; u8 name[16], reserved[8]; };
struct Place { int exists, x, z; };
_Static_assert(sizeof(struct Item) == 32, "Imported item metadata width");
_Static_assert(sizeof(struct Place) == 12, "Native placement cell width");
#ifdef __mips__
#define items ((const struct Item *)0x804672A0u)
#else
extern struct Item af_v3_test_items[2];
#define items af_v3_test_items
#endif
extern int af_v3_furniture_import_profile(u32);
extern int af_v3_original_item_name(u8 *, u32, u32);
extern int af_v3_original_item_type(u32);
extern int af_v3_original_item_size(u32);
extern int af_v3_original_item_place(u32, int, int, struct Place *);
extern u32 af_v3_original_item_price(u32);
#ifdef AF_V3_CLOTHING_PROFILE
#include "clothing.h"
#ifdef __mips__
#define clothing ((const struct Clothing *)0x80462820u)
#define selected_clothing (((const u8 *)0x80460020u)[183] & 0x80)
#else
extern struct Clothing af_v3_clothing;
extern u8 af_v3_clothing_profile[192];
#define clothing (&af_v3_clothing)
#define selected_clothing (af_v3_clothing_profile[183] & 0x80)
#endif
static const struct Clothing *find_clothing(u32 item) {
    return item == 0x34BF && selected_clothing && af_v3_clothing_source(0x10BF, 0) ? clothing : 0;
}
#endif

static const struct Item *find(u32 value) {
    u32 i, item = (u16)value & 0xFFFCu;
    for (i = 0; i < 2; ++i) {
        const struct Item *row = items + i;
        if (row->enabled == 1 && row->item == item && row->size == 0 &&
                af_v3_furniture_import_profile(row->index)) return row;
    }
    return 0;
}

int af_v3_item_name(u8 *destination, u32 capacity, u32 item) {
    const struct Item *row;
    u32 i;
    if (item > 65535u) return 0;
    if ((item >> 12) != 3u) return af_v3_original_item_name(destination, capacity, item);
#ifdef AF_V3_CLOTHING_PROFILE
    const struct Clothing *garment = find_clothing(item);
    if (garment && destination && capacity >= 16) {
        for (i = 0; i < 16; ++i) destination[i] = garment->name[i];
        return 1;
    }
#endif
    row = find(item);
    if (!destination || capacity < 16 || !row) return 0;
    for (i = 0; i < 16; ++i) destination[i] = row->name[i];
    return 1;
}

int af_v3_item_type(u32 argument) {
    u32 item = (u16)argument;
    if ((item >> 12) != 3u) return af_v3_original_item_type(argument);
#ifdef AF_V3_CLOTHING_PROFILE
    if (find_clothing(item)) return 12;
#endif
    return find(item) ? 10 : 0; /* Native furniture-leaf item category. */
}

int af_v3_item_size(u32 argument) {
    u32 item = (u16)argument;
    if ((item >> 12) != 3u) return af_v3_original_item_size(argument);
    /* Both selected profiles have the actual donor 1x1 shape. Missing items
     * retain the native size-query fallback; placement itself rejects them. */
    return 0;
}

int af_v3_item_place(u32 argument, int x, int z, struct Place *destination) {
    const struct Item *row;
    u32 item = (u16)argument, i;
    if ((item >> 12) != 3u) return af_v3_original_item_place(argument, x, z, destination);
    if (!destination) return 3;
    /* This is the furniture-only footprint query. Garments must retain the
       native non-furniture result (3, cleared cells), not become furniture. */
    row = find(item);
    for (i = 0; i < 4; ++i) {
        destination[i].exists = row && i == 0;
        destination[i].x = row ? x : 0;
        destination[i].z = row ? z : 0;
    }
    return row ? 0 : 3;
}

u32 af_v3_item_price(u32 argument) {
    const struct Item *row;
    u32 item = (u16)argument;
    if ((item >> 12) != 3u) return af_v3_original_item_price(argument);
#ifdef AF_V3_CLOTHING_PROFILE
    const struct Clothing *garment = find_clothing(item);
    if (garment) return garment->price;
#endif
    row = find(item);
    return row ? row->price : 0;
}
