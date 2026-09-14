#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/furniture.c"

struct Import af_v3_furniture_imports[2];
u32 af_v3_furniture_profiles[CAPACITY], af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY];
volatile u32 af_v3_furniture_owner[8];
static int requests, failed;

int af_v3_furniture_test_dma(void *destination, u32 vrom, u32 size) {
    assert((uptr)destination == 0x80300000u && vrom == 0x03F08000u && size == 0xC90);
    ++requests;
    return failed;
}

int main(void) {
    struct Import *row = imports;
    memset(indices, 255, sizeof(af_v3_furniture_indices));
    row->index = 1161; row->item = 0x3224; row->enabled = 1;
    row->profile[0] = 0x03F08000; row->profile[1] = 0x03F08C90;
    row->profile[2] = 0x06000000; row->profile[3] = 0x06000C90;
    af_v3_furniture_profiles[1161] = 0x80467208;
    af_v3_furniture_imports[1].index = 1198;
    af_v3_furniture_imports[1].item = 0x32B8;
    af_v3_furniture_imports[1].enabled = 1;
    af_v3_furniture_profiles[1198] = 0x80467258;
    assert(af_v3_furniture_import_profile(1161));
    assert(af_v3_furniture_import_profile(0xFFFF0000u | 1198));
    for (u32 i = 947; i < 65536; ++i) {
        if (i == 1161 || i == 1198) continue;
        assert(!af_v3_furniture_import_profile(i));
        assert(af_v3_furniture_bank(i) == -1);
    }
    for (u32 r = 0; r < 4; ++r) {
        assert(af_v3_furniture_item(1161, r) == 0x3224 + r);
        assert(af_v3_furniture_item(1198, r) == 0x32B8 + r);
        assert(af_v3_furniture_item(947, r) == 0x1ECC + r);
        assert(af_v3_furniture_item(946, r) == 0x1EC8 + r);
    }
    assert(af_v3_furniture_item(1267, 3) == 0x1088);
    indices[0] = 0; assert(af_v3_furniture_has_bank(0));
    indices[946] = 99; assert(af_v3_furniture_bank(946) == 99);
    indices[946] = 100; assert(af_v3_furniture_bank(946) == -1);
    assert(!af_v3_furniture_import_dma(1161, 0x3224, 0x80300000, 0));
    assert(!requests && indices[1161] == 255);
    af_v3_furniture_owner[2] = 0x80936710;
    af_v3_furniture_owner[3] = 0x8094F610;
    af_v3_furniture_owner[4] = 0x80200000;
    af_v3_furniture_banks[0] = 0x80300000;
    assert(af_v3_furniture_bank_address(0) == 0x80300000);
    assert(!af_v3_furniture_bank_address(-1) && !af_v3_furniture_bank_address(100));
    assert(af_v3_furniture_import_dma(1161, 0x3224, 0x80300000, 0));
    assert(requests == 1 && indices[1161] == 0);
    assert(af_v3_furniture_import_dma(1161, 0x2224, 0x80300000, -1));
    assert(requests == 2);
    indices[1161] = 255; failed = 1;
    assert(!af_v3_furniture_import_dma(1161, 0x3224, 0x80300000, 0));
    assert(requests == 3 && indices[1161] == 255);
    failed = 0;
    for (int which = 0; which < 7; ++which) {
        struct Import saved = *row;
        if (which == 0) row->enabled = 0;
        if (which == 1) row->profile[1]++;
        if (which == 2) row->profile[3] = 0x06001401;
        if (which == 3) row->profile[16] = 1;
        if (which == 4) row->index = 65535;
        if (which == 5) row->profile[2] = 0;
        if (which == 6) row->profile[0] = 0xFFFFFFFF;
        assert(!af_v3_furniture_import_dma(1161, 0x3224, 0x80300000, 0));
        assert(requests == 3 && indices[1161] == 255);
        *row = saved;
    }
    assert(!af_v3_furniture_import_dma(1161, 0x3224, 0x80300008, 0));
    assert(!af_v3_furniture_import_dma(1161, 0x3224, 0x80300000, 100));
    assert(!af_v3_furniture_import_dma(1161, 0x3224, 0x80300000, -1));
    assert(requests == 3);
    puts("Furniture selection, index bounds, bank ownership, DMA rejection, and item rotations pass");
    return 0;
}
