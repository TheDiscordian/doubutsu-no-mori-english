#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CLOTHING_PROFILE 1
#include "../../overlays/v3/items.c"
#include "../../overlays/v3/clothing.c"
struct Item af_v3_test_items[2];
struct Clothing af_v3_clothing;
u8 af_v3_clothing_profile[192];
int af_v3_furniture_import_profile(u32 i) { return i == 1161 || i == 1198; }
int af_v3_original_item_name(u8 *out, u32 size, u32 item) {
    assert(out && size >= 16 && item == 0x24BF); memcpy(out, "native garment  ", 16); return 1;
}
int af_v3_original_item_type(u32 item) { assert(item == 0x24BF); return 12; }
int af_v3_original_item_size(u32 item) { assert(item == 0x24BF); return 0; }
u32 af_v3_original_item_price(u32 item) { assert(item == 0x24BF); return 777; }
int af_v3_original_item_place(u32 item, int x, int z, struct Place *out) {
    assert(item == 0x24BF); (void)x; (void)z;
    memset(out, 0, 4*sizeof(*out));
    return 3;
}
int af_v3_clothing_dma(void *p, u32 source, u32 bytes) {
    (void)p; (void)source; (void)bytes; assert(0); return -1;
}
int main(void) {
    af_v3_clothing = (struct Clothing){0x34BF, 0x10BF, 0x3F0F000, 380, 1, 0, {0}, 0};
    memcpy(af_v3_clothing.name, "cherry shirt    ", 16);
    af_v3_clothing_profile[183] = 0x80;
    af_v3_test_items[0] = (struct Item){1161, 0x3224, 830, 0, 1, {0}, {0}};
    af_v3_test_items[1] = (struct Item){1198, 0x32B8, 840, 0, 1, {0}, {0}};
    memcpy(af_v3_test_items[0].name, "haz-mat barrel  ", 16);
    memcpy(af_v3_test_items[1].name, "oil drum        ", 16);
    u8 name[49]; memset(name, 0xA5, sizeof(name));
    struct { u32 left[4]; struct Place cells[4]; u32 right[4]; } place;
    memset(&place, 0xA5, sizeof(place));
    assert(af_v3_item_name(name+17, 16, 0x34BF));
    assert(!memcmp(name+17, "cherry shirt    ", 16));
    assert(af_v3_item_type(0x34BF) == 12 && af_v3_item_price(0x34BF) == 380);
    assert(af_v3_item_size(0x34BF) == 0 && af_v3_item_place(0x34BF, -4, 7, place.cells) == 3);
    for (u32 i = 0; i < 4; ++i) {
        assert(!place.cells[i].exists && !place.cells[i].x && !place.cells[i].z);
        assert(place.left[i] == 0xA5A5A5A5 && place.right[i] == 0xA5A5A5A5);
    }
    assert(!af_v3_item_name(name+17, 15, 0x34BF));
    assert(!af_v3_item_name(0, 16, 0x34BF));
    assert(!af_v3_item_name(name+17, 16, 0x134BF));
    assert(af_v3_item_place(0x34BF, 0, 0, 0) == 3);
    for (u32 item = 0x34BC; item < 0x34BF; ++item) {
        assert(!af_v3_item_name(name+17, 16, item));
        assert(!af_v3_item_type(item) && !af_v3_item_price(item));
    }
    for (u32 mode = 0; mode < 2; ++mode) {
        if (mode) af_v3_clothing.enabled = 0; else af_v3_clothing_profile[183] = 0;
        assert(!af_v3_item_name(name+17, 16, 0x34BF));
        assert(!af_v3_item_type(0x34BF) && !af_v3_item_price(0x34BF));
        assert(af_v3_item_place(0x34BF, -4, 7, place.cells) == 3);
        assert(!memcmp(place.cells, (u8[48]){0}, 48));
        af_v3_clothing.enabled = 1; af_v3_clothing_profile[183] = 0x80;
    }
    assert(!memcmp(name+17, "cherry shirt    ", 16));
    for (u32 i = 0; i < 17; ++i) assert(name[i] == 0xA5);
    for (u32 i = 33; i < sizeof(name); ++i) assert(name[i] == 0xA5);
    for (u32 i = 0; i < 2; ++i) for (u32 rotation = 0; rotation < 4; ++rotation) {
        struct Item *row = af_v3_test_items+i;
        assert(af_v3_item_name(name+17, 16, row->item+rotation));
        assert(!memcmp(name+17, row->name, 16));
        assert(af_v3_item_type(row->item+rotation) == 10);
        assert(af_v3_item_price(row->item+rotation) == row->price);
    }
    assert(af_v3_item_name(name+17, 16, 0x24BF) && !memcmp(name+17, "native garment  ", 16));
    assert(af_v3_item_type(0x24BF) == 12 && af_v3_item_price(0x24BF) == 777);
    assert(!af_v3_item_size(0x24BF) && af_v3_item_place(0x24BF, -4, 7, place.cells) == 3);
    puts("Selected clothing, furniture retention, original fallback, and guards pass");
    return 0;
}
