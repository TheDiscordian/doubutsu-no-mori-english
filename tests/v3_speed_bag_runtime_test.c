#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_SPEED_BAG 1
#include "../overlays/v3/furniture.c"
#include "../overlays/v3/storage.h"

struct Import af_v3_furniture_imports[2], af_v3_speed_bag_import;
u32 af_v3_furniture_profiles[CAPACITY], af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY];
volatile u32 af_v3_furniture_owner[8];
static int requests, failed;

int af_v3_furniture_test_dma(void* destination, u32 vrom, u32 size) {
    assert((uptr)destination == 0x80300000u);
    assert(vrom == AF_V3_STORAGE_VROM+0x10000 && size == 0xE90);
    ++requests;
    return failed;
}

int main(void) {
    struct Import* row = &af_v3_speed_bag_import;
    memset(indices, 255, sizeof(af_v3_furniture_indices));
    *row = (struct Import){.index=1236, .item=0x3350,
        .profile={AF_V3_STORAGE_VROM+0x10000, AF_V3_STORAGE_VROM+0x10E90,
                  0x06000000, 0x06000E90}};
    row->profile[16] = AF_V3_SPEED_BAG_VTABLE;
    af_v3_furniture_profiles[1236] = AF_V3_SPEED_BAG_PROFILE;
    af_v3_furniture_owner[2] = 0x80936710;
    af_v3_furniture_owner[3] = 0x8094F610;
    af_v3_furniture_owner[4] = 0x80200000;
    af_v3_furniture_banks[0] = 0x80300000;
    assert(!af_v3_furniture_import_profile(1236));
    assert(!af_v3_furniture_import_dma(1236, 0x3350, 0x80300000, 0));
    assert(!requests);
    row->enabled = 1;
    assert(af_v3_furniture_import_profile(1236));
    for (u32 r=0; r<4; ++r) {
        assert(af_v3_furniture_item(1236, r) == 0x3350+r);
        assert(af_v3_furniture_import_dma(1236, 0x3350+r, 0x80300000, 0));
        assert(af_v3_furniture_bank(1236) == 0);
    }
    for (int which=0; which<6; ++which) {
        struct Import original=*row;
        if (which==0) row->profile[16]+=4;
        if (which==1) row->profile[3]=0x06001401;
        if (which==2) row->profile[1]++;
        if (which==3) row->enabled=2;
        if (which==4) row->index++;
        if (which==5) row->item++;
        assert(!af_v3_furniture_import_dma(1236, 0x3350, 0x80300000, 0));
        *row=original;
    }
    assert(requests==4);
    failed=1;
    indices[1236]=255;
    assert(!af_v3_furniture_import_dma(1236, 0x3350, 0x80300000, 0));
    assert(requests==5 && indices[1236]==255);
    assert(!af_v3_furniture_import_dma(1236, 0x3350, 0x80300008, 0));
    assert(!af_v3_furniture_import_dma(1236, 0x3350, 0x80300000, 100));
    af_v3_furniture_profiles[1236]=0;
    assert(!af_v3_furniture_import_profile(1236));
    assert(requests==5);
    puts("Animated profile, enable/identity/vtable bounds, real object DMA, and rotations pass");
    return 0;
}
