#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_CONSTRUCTION_ITEMS 1
#define AF_V3_SPARSE_FURNITURE 1
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_MULTI_CELL_ITEMS 1
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
int af_v3_original_item_name(u8 *p, u32 n, u32 v) {(void)p; (void)n; (void)v; return 91;}
int af_v3_original_item_type(u32 v) {(void)v; return 92;}
int af_v3_original_item_size(u32 v) {(void)v; return 93;}
int af_v3_original_item_place(u32 v, int x, int z, struct Place *p) {
    (void)v; (void)x; (void)z; (void)p; return 94;
}
u32 af_v3_original_item_price(u32 v) {(void)v; return 95;}

int main(void) {
    const u32 slots[] = {0, 177, 700, 1023};
    memset(indices, 255, sizeof af_v3_furniture_indices);
    for (u32 k = 0; k < sizeof slots / sizeof slots[0]; ++k) {
        u32 i = slots[k], n = 1024 + i, item = 0x3000 + i * 4;
        struct Import *r = af_v3_furniture_imports + i;
        struct Item *m = af_v3_test_items + i;
        r->index = n; r->item = item; r->enabled = 1;
        m->index = n; m->item = item; m->enabled = 1; m->size = 1; m->price = 3380;
        memset(m->name, 'A' + k, sizeof m->name);
        profiles[n] = AF_V3_STATIC_IMPORT_RAM + i * 80 + 8;
        assert(af_v3_furniture_import_profile(0xFFFF0000 | n));
        for (u32 rot = 0; rot < 4; ++rot) {
            u8 output[18]; memset(output, 0xA5, sizeof output);
            struct Place p[4];
            assert(af_v3_furniture_item(n, rot) == item + rot);
            assert(af_v3_item_name(output + 1, 16, item + rot) == 1);
            assert(output[0] == 0xA5 && output[17] == 0xA5 && !memcmp(output + 1, m->name, 16));
            assert(af_v3_item_type(item + rot) == 10 && af_v3_item_price(item + rot) == 3380);
            assert(af_v3_item_place(item + rot, -4, 7, p) == 1);
            assert(p[0].exists && p[1].exists && !p[2].exists && !p[3].exists);
            assert(p[1].x == -4 + (rot == 0 ? 1 : rot == 2 ? -1 : 0));
            assert(p[1].z == 7 + (rot == 1 ? -1 : rot == 3 ? 1 : 0));
        }
        for (int bad = 0; bad < 4; ++bad) {
            struct Import saved = *r; u32 pointer = profiles[n];
            if (bad == 0) r->enabled = 0;
            if (bad == 1) r->index++;
            if (bad == 2) r->item ^= 4;
            if (bad == 3) profiles[n] += 80;
            assert(!af_v3_furniture_import_profile(n) && !af_v3_item_type(item));
            *r = saved; profiles[n] = pointer;
        }
        m->index++; assert(!af_v3_item_type(item)); m->index--;
        m->enabled = 0; assert(!af_v3_item_type(item)); m->enabled = 1;
    }
    for (u32 n = 2048; n < 2051; ++n) {
        assert(!af_v3_furniture_import_profile(n));
        assert(af_v3_furniture_bank(n) == -1);
    }
    /* Display metadata keeps parent identity in the reserved tail, but needs
       its own enabled footprint as well as the selected furniture profile. */
    struct Import *room=af_v3_furniture_imports+768;
    struct Item *form=af_v3_test_items+768;
    *room=(struct Import){.index=1792,.item=0x3C00,.enabled=1};
    profiles[1792]=AF_V3_STATIC_IMPORT_RAM+768*80+8;
    *form=(struct Item){1792,0x3C00,0,0,1,{0},{0,0,0,0,0x22,0x44,0,0}};
    for (u32 rotation=0;rotation<4;++rotation) {
        struct Place cells[4];
        assert(af_v3_item_place(0x3C00|rotation,-4,7,cells)==0);
        for (u32 j=0;j<4;++j)assert(cells[j].exists==(j==0) && cells[j].x==-4 && cells[j].z==7);
        form->enabled=0;assert(af_v3_item_place(0x3C00|rotation,-4,7,cells)==3);
        form->enabled=1;room->enabled=0;assert(af_v3_item_place(0x3C00|rotation,-4,7,cells)==3);
        room->enabled=1;
    }
    assert(!af_v3_furniture_import_profile(1023) && !af_v3_furniture_import_profile(65535));
    assert(!af_v3_item_type(0x3004) && !af_v3_item_type(0x3FF8));
    assert(af_v3_item_type(0x1088) == 92 && af_v3_item_price(0x1088) == 95);
    assert(af_v3_item_size(0x1088) == 93);
    puts("sparse item/profile boundaries, selected identity, rotations, and native fallbacks pass");
}
