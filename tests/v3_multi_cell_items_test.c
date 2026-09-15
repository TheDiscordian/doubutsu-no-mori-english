#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_MULTI_CELL_ITEMS 1
#include "../overlays/v3/items.c"
#ifdef AF_V3_ROSTER_CLOTHING
#include "../overlays/v3/clothing_roster.c"
struct Clothing af_v3_roster_clothing[3];
u8 af_v3_roster_profile[192];
#endif

struct Item af_v3_test_items[ITEM_COUNT];
static int missing, fallback;
int af_v3_furniture_import_profile(u32 n) { return !missing && (n == 1201 || n == 1161); }
int af_v3_original_item_name(u8 *d, u32 c, u32 n) { (void)d; (void)c; assert(n == 0x1000); ++fallback; return 91; }
int af_v3_original_item_type(u32 n) { assert(n == 0x1000); ++fallback; return 92; }
int af_v3_original_item_size(u32 n) { assert(n == 0x1000); ++fallback; return 93; }
int af_v3_original_item_place(u32 n, int x, int z, struct Place *d) {
    assert(n == 0x1000 && x == 3 && z == 7 && d); ++fallback; return 94;
}
u32 af_v3_original_item_price(u32 n) { assert(n == 0x1000); ++fallback; return 95; }

int main(void) {
    af_v3_test_items[0] = (struct Item){1201, 0x32C4, 1100, 1, 1, {0}, {0}};
    af_v3_test_items[1] = (struct Item){1161, 0x3224, 830, 0, 1, {0}, {0}};
    memcpy(af_v3_test_items[0].name, "watering trough ", 16);
    memcpy(af_v3_test_items[1].name, "haz-mat barrel  ", 16);
    struct { u32 before[4]; struct Place cells[4]; u32 after[4]; } place;
    u8 text[32];
    const int dx[] = {1, 0, -1, 0}, dz[] = {0, -1, 0, 1};
    memset(&place, 0xA5, sizeof(place));
    for (int slot = 0; slot < 2; ++slot) {
        struct Item *row = af_v3_test_items + slot;
        for (int rotation = 0; rotation < 4; ++rotation) {
            u32 item = row->item | rotation;
            memset(text, 0xA5, sizeof(text));
            assert(af_v3_item_name(text + 1, 16, item) == 1);
            assert(!memcmp(text + 1, row->name, 16) && text[0] == 0xA5 && text[17] == 0xA5);
            assert(af_v3_item_type(item) == 10 && af_v3_item_price(item) == row->price);
            assert(af_v3_item_size(item) == row->size);
            assert(af_v3_item_place(item, -4, 7, place.cells) == row->size);
            for (int cell = 0; cell < 4; ++cell) {
                int second = row->size == 1 && cell == 1;
                assert(place.cells[cell].exists == (cell <= row->size));
                assert(place.cells[cell].x == -4 + (second ? dx[rotation] : 0));
                assert(place.cells[cell].z == 7 + (second ? dz[rotation] : 0));
            }
        }
    }
    assert(af_v3_item_place(0x32C4, INT_MAX, 0, place.cells) == 1);
    assert(place.cells[1].x == INT_MIN);
    for (int invalid = 0; invalid < 3; ++invalid) {
        if (invalid == 0) missing = 1;
        if (invalid == 1) af_v3_test_items[0].enabled = 0;
        if (invalid == 2) af_v3_test_items[0].size = 2;
        memset(text, 0xA5, sizeof(text));
        assert(!af_v3_item_name(text, 16, 0x32C4));
        assert(!af_v3_item_size(0x32C4) && !af_v3_item_type(0x32C4) && !af_v3_item_price(0x32C4));
        assert(af_v3_item_place(0x32C4, 3, 7, place.cells) == 3);
        assert(!memcmp(place.cells, (u8[48]){0}, 48));
        for (int j = 0; j < 32; ++j) assert(text[j] == 0xA5);
        missing = 0; af_v3_test_items[0].enabled = 1; af_v3_test_items[0].size = 1;
    }
    assert(af_v3_item_place(0x32C4, 3, 7, 0) == 3);
    assert(af_v3_item_name(text, 16, 0x1000) == 91);
    assert(af_v3_item_type(0x1000) == 92 && af_v3_item_size(0x1000) == 93);
    assert(af_v3_item_place(0x1000, 3, 7, place.cells) == 94);
    assert(af_v3_item_price(0x1000) == 95 && fallback == 5);
    for (int i = 0; i < 4; ++i) assert(place.before[i] == 0xA5A5A5A5u && place.after[i] == 0xA5A5A5A5u);
#ifdef AF_V3_ROSTER_CLOTHING
    const u16 garments[] = {0x34BF, 0x341A, 0x341B};
    const u32 sources[] = {0x0220F000, 0x022E2000, 0x022E2400};
    for (int slot = 0; slot < 3; ++slot) {
        struct Clothing *row = af_v3_roster_clothing + slot;
        u32 item = garments[slot], bit = item & 255;
        *row = (struct Clothing){item, item - 0x2400, sources[slot], 380 + slot * 20, 1, 0, {0}, 0};
        memset(row->name, 'A' + slot, 16);
        for (int enabled = 0; enabled < 2; ++enabled) {
            if (enabled) af_v3_roster_profile[160 + (bit >> 3)] |= 1u << (bit & 7);
            assert(af_v3_item_name(text, 16, item) == enabled);
            if (enabled) assert(!memcmp(text, row->name, 16));
            assert(af_v3_item_price(item) == (enabled ? row->price : 0));
            assert(af_v3_item_type(item) == (enabled ? 12 : 0));
            assert(af_v3_item_size(item) == 0);
            assert(af_v3_item_place(item, 3, 7, place.cells) == 3);
            assert(!memcmp(place.cells, (u8[48]){0}, 48));
        }
    }
    puts("All three dynamic clothing records retain names, prices, and non-furniture footprints");
#endif
    puts("Two-cell rotations, guards, rejection, and original fallbacks pass");
    return 0;
}
