#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CONSTRUCTION_ITEMS 1
#define AF_V3_WESTERN_LARGE 1
#define AF_V3_SPARSE_FURNITURE 1
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_EXPANDED_BANKS 1
#define AF_V3_LARGE_MODEL_BANKS 1
#include "../overlays/v3/furniture.c"

struct Import af_v3_furniture_imports[AF_V3_STATIC_IMPORT_COUNT];
u32 af_v3_furniture_profiles[CAPACITY], af_v3_furniture_banks[BANKS];
u8 af_v3_furniture_indices[CAPACITY];
volatile u32 af_v3_furniture_owner[8];
static u32 destination, bytes, requests;
static int fail;
int af_v3_furniture_test_dma(void *target, u32 vrom, u32 size) {
    assert((uptr)target == destination && vrom == 0x02600000 && size == bytes);
    ++requests;
    return fail;
}

int main(void) {
    enum { INDEX = 1137, ITEM = 0x31C4 };
    struct Import *row = &imports[INDEX - 1024];
    row->index = INDEX; row->item = ITEM; row->enabled = 1;
    row->profile[0] = 0x02600000;
    row->profile[2] = 0x06000000;
    profiles[INDEX] = AF_V3_STATIC_IMPORT_RAM + 8 + (INDEX - 1024) * 80;
    owner[2] = 0x80936710; owner[3] = 0x8094F610; owner[4] = 0x80200000;
    memset(indices, 255, sizeof af_v3_furniture_indices);
    assert(BANK_BYTES == 12288 && AF_V3_BANK_POOL_END == 0x8062C020);
    const u32 sizes[] = { 10448, BANK_BYTES };
    for (u32 s = 0; s < 2; ++s) {
        bytes = sizes[s];
        row->profile[1] = row->profile[0] + bytes;
        row->profile[3] = row->profile[2] + bytes;
        for (int i = 0; i < BANKS; ++i) {
            destination = af_v3_furniture_banks[i] = AF_V3_BANK_POOL_DATA + i * BANK_BYTES;
            assert(af_v3_furniture_import_dma(INDEX, ITEM, destination, i));
            assert(indices[INDEX] == i);
            assert(af_v3_furniture_import_dma(INDEX, ITEM, destination, -1));
        }
    }
    assert(requests == 400);
    const struct Import saved = *row;
    for (int bad = 0; bad < 9; ++bad) {
        *row = saved;
        destination = af_v3_furniture_banks[99] = AF_V3_BANK_POOL_DATA + 99 * BANK_BYTES;
        if (bad == 0) ++row->profile[3];
        if (bad == 1) ++row->profile[1];
        if (bad == 2) row->profile[16] = 0x80460000;
        if (bad == 3) row->enabled = 0;
        if (bad == 4) ++row->index;
        if (bad == 5) row->item += 4;
        if (bad == 6) destination += 8;
        if (bad == 7) destination = AF_V3_BANK_POOL_GUARD;
        if (bad == 8) af_v3_furniture_banks[99] -= BANK_BYTES;
        indices[INDEX] = 255;
        assert(!af_v3_furniture_import_dma(INDEX, ITEM, destination, 99));
        assert(indices[INDEX] == 255 && requests == 400);
    }
    *row = saved;
    destination = af_v3_furniture_banks[99] = AF_V3_BANK_POOL_DATA + 99 * BANK_BYTES;
    fail = 1;
    assert(!af_v3_furniture_import_dma(INDEX, ITEM, destination, 99));
    assert(indices[INDEX] == 255 && requests == 401);
    puts("complete models, all bank bounds, and failed-DMA state pass");
}
