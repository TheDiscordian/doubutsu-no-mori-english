#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/display_items.c"

static int selected = 1;
static u32 last_item;
static const u8 *last_private;
int af_v3_furniture_import_profile(u32 index) { assert(index == 1727); return selected; }
int af_v3_base_item_name(u8 *out, u32 capacity, u32 item) {
    last_item = item;
    if (!out || capacity < 16 || item != 0x34BF) return 0;
    memcpy(out, "cherry shirt    ", 16); return 1;
}
int af_v3_base_item_type(u32 item) { last_item = item; return (u16)item == 0x34BF ? 12 : 0; }
int af_v3_base_item_place(u32 item, int x, int z, void *out) {
    last_item = item;
    assert(x == -4 && z == 7 && out);
    return (item & 0xFFFC) == 0x17AC ? 0 : 3;
}
u32 af_v3_base_item_price(u32 item) { last_item = item; return (u16)item == 0x34BF ? 380 : 0; }
void af_v3_prior_catalogue_record(u32 item) { last_item = item; }
int af_v3_prior_catalogue_owned(const u8 *private, u32 item) {
    last_private = private; last_item = item; return item == 0x34BF;
}

int main(void) {
    u8 text[18], private[16];
    memset(text, 0xA5, sizeof text);
    for (u32 r = 0; r < 4; ++r) {
        u32 item = 0x3AFC | r;
        assert(af_v3_display_pocket_item(item) == 0x34BF);
        assert(af_v3_display_item_name(text+1, 16, item) == 1);
        assert(!memcmp(text+1, "cherry shirt    ", 16) && text[0] == 0xA5 && text[17] == 0xA5);
        assert(af_v3_display_item_type(item) == 10);
        assert(af_v3_display_item_type(0xFFFF0000u | item) == 10);
        assert(af_v3_display_item_price(item) == 380);
        assert(af_v3_display_item_place(item, -4, 7, text) == 0 && last_item == (0x17AC | r));
        af_v3_display_catalogue_record(item); assert(last_item == 0x34BF);
        af_v3_display_catalogue_record(0xFFFF0000u | item); assert(last_item == 0x34BF);
        assert(af_v3_display_catalogue_owned(private, item) == 1 && last_private == private);
    }
    assert(!af_v3_display_item_name(text+1, 15, 0x3AFC));
    assert(!af_v3_display_item_name(text+1, 16, 0x13AFC) && last_item == 0x13AFC);
    assert(!af_v3_display_catalogue_owned(private, 0x13AFC) && last_item == 0x13AFC);
    assert(af_v3_display_item_type(0x34BF) == 12);
    assert(af_v3_display_item_place(0x34BF, -4, 7, text) == 3 && last_item == 0x34BF);
    for (u32 item = 0x3AFB; item <= 0x3B00; ++item) {
        selected = 0;
        assert(af_v3_display_pocket_item(item) == item);
        assert(!af_v3_display_item_type(item));
        assert(!af_v3_display_item_price(item) && last_item == item);
        assert(af_v3_display_item_place(item, -4, 7, text) == 3 && last_item == item);
        af_v3_display_catalogue_record(item); assert(last_item == item);
        assert(!af_v3_display_catalogue_owned(private, item));
    }
    af_v3_display_catalogue_record(0xFFFF2401); assert(last_item == 0xFFFF2401);
    puts("display metadata, footprint delegation, collection aliases, strict names, and disabled imports pass");
    return 0;
}
