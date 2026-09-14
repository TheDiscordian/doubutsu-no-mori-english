#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/items.c"

struct Item af_v3_test_items[2];
static u32 missing, names, types, sizes, places, prices;
int af_v3_furniture_import_profile(u32 n) { return !missing && (n == 1161 || n == 1198); }
int af_v3_original_item_name(u8 *d, u32 c, u32 n) {
    assert(d && c == 16 && n == 0x1000); ++names; return 91;
}
int af_v3_original_item_type(u32 n) { assert(n == 0x1000); ++types; return 92; }
int af_v3_original_item_size(u32 n) { assert(n == 0x1000); ++sizes; return 93; }
int af_v3_original_item_place(u32 n, int x, int z, struct Place *d) {
    assert(n == 0x1000 && x == -4 && z == 7 && d); ++places; return 94;
}
u32 af_v3_original_item_price(u32 n) { assert(n == 0x1000); ++prices; return 95; }

int main(void) {
    struct { u8 before[16], text[32], after[16]; } name;
    struct { u32 before[4]; struct Place cells[4]; u32 after[4]; } place;
    memset(&name, 0xA5, sizeof(name)); memset(&place, 0xA5, sizeof(place));
    af_v3_test_items[0] = (struct Item){1161, 0x3224, 830, 0, 1, {0}, {0}};
    af_v3_test_items[1] = (struct Item){1198, 0x32B8, 840, 0, 1, {0}, {0}};
    memcpy(af_v3_test_items[0].name, "haz-mat barrel  ", 16);
    memcpy(af_v3_test_items[1].name, "oil drum        ", 16);
    for (u32 i = 0; i < 2; ++i) {
        struct Item *row = af_v3_test_items + i;
        for (u32 r = 0; r < 4; ++r) {
            assert(af_v3_item_name(name.text + 1, 17, row->item + r) == 1);
            assert(!memcmp(name.text + 1, row->name, 16));
            assert(af_v3_item_type(row->item + r) == 10);
            assert(af_v3_item_price(row->item + r) == row->price);
            assert(af_v3_item_size(row->item + r) == 0);
            assert(af_v3_item_place(row->item + r, -4, 7, place.cells) == 0);
            for (u32 j = 0; j < 4; ++j) {
                assert(place.cells[j].exists == (j == 0));
                assert(place.cells[j].x == -4 && place.cells[j].z == 7);
            }
        }
    }
    u8 saved[sizeof(name)]; memcpy(saved, &name, sizeof(name));
    assert(!af_v3_item_name(name.text, 15, 0x3224));
    assert(!af_v3_item_name(0, 16, 0x3224));
    assert(!af_v3_item_name(name.text, 16, 0x13224u));
    assert(!af_v3_item_name(name.text, 16, 0x3000));
    assert(!memcmp(saved, &name, sizeof(name)));
    for (u32 invalid = 0; invalid < 3; ++invalid) {
        struct Item row = af_v3_test_items[0];
        if (invalid == 0) missing = 1;
        if (invalid == 1) af_v3_test_items[0].enabled = 0;
        if (invalid == 2) af_v3_test_items[0].size = 2;
        assert(!af_v3_item_name(name.text, 16, 0x3224));
        assert(!af_v3_item_type(0x3224)); assert(!af_v3_item_price(0x3224));
        assert(af_v3_item_place(0x3224, -4, 7, place.cells) == 3);
        assert(!memcmp(place.cells, (u8[48]){0}, 48));
        assert(!memcmp(saved, &name, sizeof(name)));
        af_v3_test_items[0] = row; missing = 0;
    }
    assert(af_v3_item_place(0x3224, -4, 7, 0) == 3);
    assert(af_v3_item_name(name.text, 16, 0x1000) == 91 && names == 1);
    assert(af_v3_item_type(0x1000) == 92 && types == 1);
    assert(af_v3_item_size(0x1000) == 93 && sizes == 1);
    assert(af_v3_item_place(0x1000, -4, 7, place.cells) == 94 && places == 1);
    assert(af_v3_item_price(0x1000) == 95 && prices == 1);
    for (u32 i = 0; i < 4; ++i)
        assert(place.before[i] == 0xA5A5A5A5u && place.after[i] == 0xA5A5A5A5u);
    assert(name.text[0] == 0xA5 && name.text[17] == 0xA5);
    puts("Selected full names, prices, footprints, no-write rejection, and original fallbacks pass");
    return 0;
}
