/* Selected furniture metadata; all original item paths retain their bodies. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Item { u16 index, item, price; u8 size, enabled; u8 name[16], reserved[8]; };
struct Place { int exists, x, z; };
#if defined(AF_V3_FOUR_CELL_ITEMS) && !defined(AF_V3_MULTI_CELL_ITEMS)
#error Four-cell furniture requires multi-cell item readers
#endif
#ifdef AF_V3_CONSTRUCTION_ITEMS
#include "construction.h"
#define ITEM_COUNT AF_V3_ITEM_TABLE_COUNT
#define ITEM_RAM AF_V3_ITEM_TABLE_RAM
#else
#define ITEM_RAM 0x804672A0u
#ifdef AF_V3_SPEED_BAG
#define ITEM_COUNT 3
#else
#define ITEM_COUNT 2
#endif
#endif
_Static_assert(sizeof(struct Item) == 32, "Imported item metadata width");
_Static_assert(sizeof(struct Place) == 12, "Native placement cell width");
#ifdef __mips__
#define items ((const struct Item *)ITEM_RAM)
#else
extern struct Item af_v3_test_items[ITEM_COUNT];
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
#ifdef AF_V3_ROSTER_CLOTHING
extern const struct Clothing *af_v3_roster_clothing_record(u32);
#define find_clothing af_v3_roster_clothing_record
#else
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
#endif

static const struct Item *find(u32 value) {
    u32 item = (u16)value & 0xFFFCu;
#ifdef AF_V3_SPARSE_FURNITURE
    if ((item >> 12) != 3u) return 0;
    u32 i = (item - 0x3000u) >> 2;
    {
#else
    for (u32 i = 0; i < ITEM_COUNT; ++i) {
#endif
        const struct Item *row = items + i;
        if (row->enabled == 1 && row->item == item &&
#ifdef AF_V3_SPARSE_FURNITURE
                row->index == AF_V3_SPARSE_FIRST + i &&
#endif
#ifdef AF_V3_FOUR_CELL_ITEMS
                row->size <= 2 &&
#elif defined(AF_V3_MULTI_CELL_ITEMS)
                row->size <= 1 &&
#else
                row->size == 0 &&
#endif
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
#ifdef AF_V3_MULTI_CELL_ITEMS
    const struct Item *row = find(item);
    return row ? row->size : 0;
#else
    /* Both selected profiles have the actual donor 1x1 shape. Missing items
     * retain the native size-query fallback; placement itself rejects them. */
    return 0;
#endif
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
#ifdef AF_V3_MULTI_CELL_ITEMS
        /* Native 1x2 directions: south +x, east -z, north -x, west +z.
         * Inactive cells retain the anchor coordinates, just like the native
         * placement table. Unsigned addition preserves MIPS wrapping. */
        int dx = 0, dz = 0;
        if (row && row->size == 1 && i == 1) {
            u32 direction = item & 3u;
            dx = direction == 0 ? 1 : direction == 2 ? -1 : 0;
            dz = direction == 1 ? -1 : direction == 3 ? 1 : 0;
        }
#ifdef AF_V3_FOUR_CELL_ITEMS
        /* Both games anchor 2x2 furniture at the upper-left cell for every
         * rotation. Keep the native clockwise order; size 2 means four cells,
         * not three. It is independent of the profile's shape/collision 5. */
        if (row && row->size == 2) {
            dx = i == 1 || i == 2;
            dz = i >= 2;
        }
        destination[i].exists = row && (row->size == 2 || i <= row->size);
#else
        destination[i].exists = row && i <= row->size;
#endif
        destination[i].x = row ? (int)((u32)x + (u32)dx) : 0;
        destination[i].z = row ? (int)((u32)z + (u32)dz) : 0;
#else
        destination[i].exists = row && i == 0;
        destination[i].x = row ? x : 0;
        destination[i].z = row ? z : 0;
#endif
    }
#ifdef AF_V3_MULTI_CELL_ITEMS
    return row ? row->size : 3;
#else
    return row ? 0 : 3;
#endif
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
