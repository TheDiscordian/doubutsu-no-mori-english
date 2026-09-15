#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CONSTRUCTION_ITEMS 1
#define AF_V3_SPARSE_FURNITURE 1
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_MULTI_CELL_ITEMS 1
#define AF_V3_FOUR_CELL_ITEMS 1
#define find profile_find
#include "../overlays/v3/furniture.c"
#undef find
#include "../overlays/v3/items.c"

struct Import af_v3_furniture_imports[AF_V3_STATIC_IMPORT_COUNT];
u32 af_v3_furniture_profiles[CAPACITY], af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY];
volatile u32 af_v3_furniture_owner[8];
struct Item af_v3_test_items[ITEM_COUNT];
int af_v3_furniture_test_dma(void *p, u32 a, u32 n) {(void)p; (void)a; (void)n; assert(0); return 0;}
int af_v3_original_item_name(u8 *p, u32 n, u32 v) {(void)p; (void)n; assert(v == 0x1000); return 91;}
int af_v3_original_item_type(u32 v) {assert(v == 0x1000); return 92;}
int af_v3_original_item_size(u32 v) {assert(v == 0x1000); return 93;}
int af_v3_original_item_place(u32 v, int x, int z, struct Place *p) {
    assert(v == 0x1000 && x == 3 && z == 7 && p); return 94;
}
u32 af_v3_original_item_price(u32 v) {assert(v == 0x1000); return 95;}

int main(void) {
    struct Item rows[] = {
        {1239, 0x335C, 1360, 0, 1, {0}, {0}},
        {1240, 0x3360, 2240, 2, 1, {0}, {0}},
        {1243, 0x336C, 2550, 0, 1, {0}, {0}},
        {1241, 0x3364, 3460, 1, 1, {0}, {0}},
        {1024, 0x3000, 1000, 2, 1, {0}, {0}},
        {2047, 0x3FFC, 1000, 2, 1, {0}, {0}},
    };
    const char *names[] = {"campfire        ", "bonfire         ", "tent model      ",
                          "kayak           ", "boundary low    ", "boundary high   "};
    for (u32 k = 0; k < sizeof rows / sizeof rows[0]; ++k) memcpy(rows[k].name, names[k], 16);
    const int offsets[4][2] = {{0, 0}, {1, 0}, {1, 1}, {0, 1}};
    const int direction[4][2] = {{1, 0}, {0, -1}, {-1, 0}, {0, 1}};
    const int anchors[][2] = {{-4, 7}, {0, 0}, {15, 15}, {INT_MAX, INT_MAX}, {INT_MIN, INT_MIN}};
    struct { u32 before[4]; struct Place cells[4]; u32 after[4]; } place;
    u8 name[18];
    memset(&place, 0xA5, sizeof place);
    for (u32 k = 0; k < sizeof rows / sizeof rows[0]; ++k) {
        const struct Item *expected = rows + k;
        u32 slot = expected->index - 1024;
        struct Import *profile = af_v3_furniture_imports + slot;
        struct Item *row = af_v3_test_items + slot;
        *row = *expected;
        profile->index = row->index; profile->item = row->item; profile->enabled = 1;
        profiles[row->index] = AF_V3_STATIC_IMPORT_RAM + slot * 80 + 8;
        for (u32 rot = 0; rot < 4; ++rot) {
            u32 item = row->item | rot;
            assert(af_v3_item_type(item) == 10 && af_v3_item_price(item) == row->price);
            assert(af_v3_item_size(item) == row->size);
            memset(name, 0xA5, sizeof name);
            assert(af_v3_item_name(name + 1, 16, item) == 1);
            assert(!memcmp(name + 1, row->name, 16) && name[0] == 0xA5 && name[17] == 0xA5);
            for (u32 a = 0; a < sizeof anchors / sizeof anchors[0]; ++a) {
                int x = anchors[a][0], z = anchors[a][1];
                assert(af_v3_item_place(item, x, z, place.cells) == row->size);
                for (int i = 0; i < 4; ++i) {
                    const int *offset = row->size == 2 ? offsets[i] :
                                        row->size == 1 && i == 1 ? direction[rot] : offsets[0];
                    assert(place.cells[i].exists == (i < (1 << row->size)));
                    assert(place.cells[i].x == (int)((u32)x + (u32)offset[0]));
                    assert(place.cells[i].z == (int)((u32)z + (u32)offset[1]));
                }
            }
        }
        for (int invalid = 0; invalid < 8; ++invalid) {
            struct Import saved = *profile;
            u32 pointer = profiles[row->index];
            if (invalid == 0) row->enabled = 0;
            if (invalid == 1) row->size = 3;
            if (invalid == 2) row->size = 255;
            if (invalid == 3) profile->enabled = 0;
            if (invalid == 4) profiles[row->index] += 80;
            if (invalid == 5) profile->item ^= 4;
            if (invalid == 6) row->item ^= 4;
            if (invalid == 7) row->index++;
            assert(!af_v3_item_type(expected->item) && !af_v3_item_price(expected->item));
            assert(!af_v3_item_size(expected->item));
            memset(name, 0xA5, sizeof name);
            assert(!af_v3_item_name(name + 1, 16, expected->item));
            for (u32 i = 0; i < sizeof name; ++i) assert(name[i] == 0xA5);
            assert(af_v3_item_place(expected->item, 3, 7, place.cells) == 3);
            assert(!memcmp(place.cells, (u8[48]){0}, 48));
            *row = *expected; *profile = saved; profiles[row->index] = pointer;
        }
    }
    assert(af_v3_item_place(0x3360, 3, 7, 0) == 3);
    assert(af_v3_item_name(name, 16, 0x1000) == 91);
    assert(af_v3_item_type(0x1000) == 92 && af_v3_item_size(0x1000) == 93);
    assert(af_v3_item_place(0x1000, 3, 7, place.cells) == 94);
    assert(af_v3_item_price(0x1000) == 95);
    for (int i = 0; i < 4; ++i) assert(place.before[i] == 0xA5A5A5A5u && place.after[i] == 0xA5A5A5A5u);
    puts("Four-cell size, all rotations, sparse selection, signed boundaries, and original fallbacks pass");
}
