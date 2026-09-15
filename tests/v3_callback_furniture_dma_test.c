#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CONSTRUCTION_ITEMS 1
#define AF_V3_WESTERN_LARGE 1
#define AF_V3_SPARSE_FURNITURE 1
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_SPEED_BAG 1
#define AF_V3_EXPANDED_BANKS 1
#define AF_V3_TENT_MODEL 1
#include "../overlays/v3/furniture.c"

struct Import af_v3_furniture_imports[AF_V3_STATIC_IMPORT_COUNT];
struct Import af_v3_speed_bag_import;
u32 af_v3_furniture_profiles[CAPACITY], af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY];
volatile u32 af_v3_furniture_owner[8];
static u32 requests, expected_vrom, expected_bytes;
static int fail_dma;
int af_v3_furniture_test_dma(void *destination, u32 vrom, u32 size) {
    assert((uptr)destination == AF_V3_BANK_POOL_DATA);
    assert(vrom == expected_vrom && size == expected_bytes);
    ++requests;
    return fail_dma;
}

int main(void) {
    struct Import *row = &af_v3_furniture_imports[1243 - 1024];
    row->index = 1243; row->item = 0x336C; row->enabled = 1;
    row->profile[0] = 0x0244E000; row->profile[1] = 0x0244F0C0;
    row->profile[2] = 0x06000000; row->profile[3] = 0x060010C0;
    row->profile[16] = 0x80483700;
    af_v3_furniture_profiles[1243] = AF_V3_STATIC_IMPORT_RAM + (1243 - 1024) * 80 + 8;
    af_v3_furniture_owner[2] = 0x80936710;
    af_v3_furniture_owner[3] = 0x8094F610;
    af_v3_furniture_owner[4] = 0x80200000;
    af_v3_furniture_banks[0] = AF_V3_BANK_POOL_DATA;
    expected_vrom = 0x0244E000; expected_bytes = 4288;
    memset(indices, 255, sizeof af_v3_furniture_indices);
    for (u32 rotation = 0; rotation < 4; ++rotation) {
        assert(af_v3_furniture_import_dma(1243, 0x336C | rotation, AF_V3_BANK_POOL_DATA, 0));
        assert(indices[1243] == 0);
    }
    assert(af_v3_furniture_import_dma(1243, 0x336C, AF_V3_BANK_POOL_DATA, -1));
    for (int bad = 0; bad < 8; ++bad) {
        struct Import saved = *row;
        if (bad == 0) row->enabled = 0;
        if (bad == 1) row->index = 1242;
        if (bad == 2) row->item = 0x3368;
        if (bad == 3) row->profile[16] += 4;
        if (bad == 4) row->profile[16] = AF_V3_SPEED_BAG_VTABLE;
        if (bad == 5) row->profile[1] += 4;
        if (bad == 6) row->profile[3] = 0x06002401;
        if (bad == 7) af_v3_furniture_banks[0] += 16;
        indices[1243] = 255;
        assert(!af_v3_furniture_import_dma(1243, 0x336C, AF_V3_BANK_POOL_DATA, 0));
        assert(requests == 5 && indices[1243] == 255);
        *row = saved; af_v3_furniture_banks[0] = AF_V3_BANK_POOL_DATA;
    }
    fail_dma = 1;
    assert(!af_v3_furniture_import_dma(1243, 0x336C, AF_V3_BANK_POOL_DATA, 0));
    assert(requests == 6 && indices[1243] == 255);
    fail_dma = 0;
    /* A different selected item must not borrow tent's callback permission. */
    struct Import *neighbour = row - 1;
    *neighbour = *row; neighbour->index = 1242; neighbour->item = 0x3368;
    af_v3_furniture_profiles[1242] = af_v3_furniture_profiles[1243] - 80;
    assert(!af_v3_furniture_import_dma(1242, 0x3368, AF_V3_BANK_POOL_DATA, 0));
    assert(requests == 6);
    neighbour->profile[16] = 0;
    assert(af_v3_furniture_import_dma(1242, 0x3368, AF_V3_BANK_POOL_DATA, 0));
    /* The speed-bag path retains its separately checked identity and vtable. */
    af_v3_speed_bag_import = *row;
    af_v3_speed_bag_import.index = AF_V3_SPEED_BAG_INDEX;
    af_v3_speed_bag_import.item = AF_V3_SPEED_BAG_ITEM;
    af_v3_speed_bag_import.profile[16] = AF_V3_SPEED_BAG_VTABLE;
    af_v3_furniture_profiles[AF_V3_SPEED_BAG_INDEX] = AF_V3_SPEED_BAG_PROFILE;
    assert(af_v3_furniture_import_dma(AF_V3_SPEED_BAG_INDEX, AF_V3_SPEED_BAG_ITEM, AF_V3_BANK_POOL_DATA, 0));
    assert(requests == 8);
#ifdef AF_V3_FIRE
    for (u32 n = 0; n < 2; ++n) {
        u32 index = 1239 + n, item = 0x335C + n * 4;
        struct Import *fire = &af_v3_furniture_imports[index - 1024];
        *fire = *row; fire->index = index; fire->item = item;
        fire->profile[0] = expected_vrom = 0x2468000 + n * 0x2000;
        expected_bytes = n ? 6032 : 8000;
        fire->profile[1] = expected_vrom + expected_bytes;
        fire->profile[3] = 0x06000000 + expected_bytes;
        fire->profile[16] = 0x80483FC0 + n * 24;
        profiles[index] = AF_V3_STATIC_IMPORT_RAM + (index - 1024) * 80 + 8;
        for (u32 rotation = 0; rotation < 4; ++rotation)
            assert(af_v3_furniture_import_dma(index, item | rotation, AF_V3_BANK_POOL_DATA, 0));
        u32 previous = requests;
        fire->profile[16] = 0x80483FC0 + (1 - n) * 24;
        assert(!af_v3_furniture_import_dma(index, item, AF_V3_BANK_POOL_DATA, 0));
        assert(requests == previous);
    }
    puts("Both complete fire DMAs, rotations, and mismatched callback rejection pass");
#endif
    puts("tent complete-object DMA, reload, static/speed-bag retention, rejection, and failure handling pass");
}
