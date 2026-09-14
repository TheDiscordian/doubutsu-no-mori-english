#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_CLOTHING_DISPLAY 1
#include "../overlays/v3/furniture.c"
#include "../overlays/v3/clothing_display.c"

struct Import af_v3_furniture_imports[2], af_v3_display_import;
u32 af_v3_furniture_profiles[CAPACITY], af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY], af_v3_display_profile[192];
volatile u32 af_v3_furniture_owner[8];
static int available = 1, transfers;
static u32 last_item;

int af_v3_item_type(u32 item) { assert(item == 0x34BF); return available ? 12 : 0; }
int af_v3_furniture_test_dma(void *destination, u32 vrom, u32 size) {
    (void)destination; (void)vrom; (void)size;
    assert(0); return 1;
}
void af_v3_display_test_dma(u32 item, u32 bank) {
    assert((item & 0xFFFC) == 0x3AFC && bank == 0x80300000);
    last_item = item; ++transfers;
}

int main(void) {
    struct Import *row = &af_v3_display_import;
    row->index = 1727; row->item = 0x3AFC; row->enabled = 1;
    row->profile[16] = 0x80466150;
    af_v3_furniture_profiles[1727] = 0x80466608;
    memset(indices, 255, sizeof af_v3_furniture_indices);
    af_v3_display_profile[119] = 0x80;
    assert(af_v3_display_clothing_index(0x17AC) == 0);
    assert(af_v3_display_clothing_index(0x1BA7) == 254);
    assert(af_v3_display_clothing_index(0x1BA8) == 0);
    assert(af_v3_display_clothing_index(0x34BF) == 0);
    assert(af_v3_display_clothing_index(0xFFFF3AFC) == 0x10BF);
    assert(af_v3_furniture_import_profile(1727));
    assert(!af_v3_furniture_import_dma(1727, 0x3AFC, 0x80300000, 0));
    assert(!transfers);
    af_v3_furniture_owner[2] = 0x80936710;
    af_v3_furniture_owner[3] = 0x8094F610;
    af_v3_furniture_owner[4] = 0x80200000;
    af_v3_furniture_banks[0] = 0x80300000;
    for (u32 rotation = 0; rotation < 4; ++rotation) {
        assert(af_v3_display_clothing_index(0x3AFC | rotation) == 0x10BF);
        assert(af_v3_furniture_item(1727, rotation) == (0x3AFC | rotation));
        assert(af_v3_furniture_import_dma(1727, 0x3AFC | rotation, 0x80300000, 0));
        assert(last_item == (0x3AFC | rotation) && indices[1727] == 0);
    }
    assert(transfers == 4);
    assert(af_v3_furniture_import_dma(1727, 0x3AFE, 0x80300000, -1));
    assert(transfers == 5 && last_item == 0x3AFE);
    row->profile[16]++;
    assert(!af_v3_furniture_import_dma(1727, 0x3AFC, 0x80300000, 0));
    row->profile[16]--;
    assert(!af_v3_furniture_import_dma(1727, 0x3AFC, 0x80300008, 0));
    assert(!af_v3_furniture_import_dma(1727, 0x3AFC, 0x80300000, 100));
    af_v3_display_profile[119] = 0;
    assert(!af_v3_display_clothing_index(0x3AFC));
    assert(!af_v3_furniture_import_profile(1727));
    assert(af_v3_furniture_bank(1727) == -1);
    af_v3_display_profile[119] = 0x80; available = 0;
    assert(!af_v3_display_clothing_index(0x3AFC));
    assert(!af_v3_furniture_import_dma(1727, 0x3AFC, 0x80300000, 0));
    available = 1;
    for (int field = 0; field < 4; ++field) {
        struct Import saved = *row;
        if (field == 0) row->enabled = 0;
        if (field == 1) row->item = 0x3AF8;
        if (field == 2) row->index = 1728;
        if (field == 3) af_v3_furniture_profiles[1727] = 0;
        assert(!af_v3_furniture_import_profile(1727));
        assert(!af_v3_furniture_import_dma(1727, 0x3AFC, 0x80300000, 0));
        *row = saved;
    }
    assert(transfers == 5);
    assert(!af_v3_furniture_import_profile(1726));
    assert(!af_v3_furniture_import_profile(2051));
    assert(af_v3_furniture_item(491, 3) == 0x17AF);
    puts("clothing display selection, native indices, rotations, bank ownership, and rejection pass");
    return 0;
}
