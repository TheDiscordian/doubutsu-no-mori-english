#define AF_V3_IMPORTED_OUTFIT_SOURCE 1
#define main retained_text_checks
#include "v3_villager_text_test.c"
#undef main
#include "../overlays/v3/clothing.c"

struct Clothing af_v3_clothing;
int af_v3_clothing_dma(void *destination, unsigned int source, unsigned int count) {
    (void)destination; (void)source; (void)count;
    assert(0 && "Defaults must not perform clothing DMA");
    return -1;
}

int main(void) {
    assert(retained_text_checks() == 0);
    reset();
    struct Villager *row = af_v3_villagers + 19;
    row->cloth = 0x24BF; row->native_cloth = 0x34BF; row->personality = 2;
    af_v3_clothing = (struct Clothing){.item=0x34BF, .index=0x10BF,
        .vrom=AF_V3_CLOTHING_VROM, .enabled=1};
    memcpy(af_v3_land_info, "Forest!!\x12\x34", 10);
    u8 expected[sizeof(animal)];
    memset(expected, 0xA5, sizeof(expected));
    expected[0] = 0xE0; expected[1] = 0xED; expected[11] = 2;
    memcpy(expected+2, "\x12\x34" "Forest", 8);
    memcpy(expected+0x4E5, "\xFE\xF3\xED ", 4);
    expected[0x520] = 0x34; expected[0x521] = 0xBF;
    for (int route=0; route<3; ++route) {
        memset(animal, 0xA5, sizeof(animal));
        if (route==0) af_v3_set_defaults(animal, 0xE0ED, NULL);
        if (route==1) af_v3_set_info(animal, 0xE0ED, 255, NULL);
        if (route==2) af_v3_set_index(animal, 237);
        assert(!memcmp(animal, expected, sizeof(animal)) && !calls);
    }
    struct Clothing valid = af_v3_clothing;
    for (int damage=0; damage<7; ++damage) {
        af_v3_clothing = valid;
        if (damage==0) af_v3_clothing.enabled=0;
        if (damage==1) af_v3_clothing.item=0x34BE;
        if (damage==2) af_v3_clothing.index=0x10BE;
        if (damage==3) af_v3_clothing.vrom++;
        if (damage==4) af_v3_clothing.reserved=1;
        if (damage==5) af_v3_clothing.padding=1;
        if (damage==6) row->native_cloth=0x34BE;
        memset(animal, 0xA5, sizeof(animal));
        af_v3_set_index(animal, 237);
        for (unsigned int i=0; i<sizeof(animal); ++i) assert(animal[i]==0xA5);
        row->native_cloth=0x34BF;
    }
    assert(!calls);
    puts("Punchy full defaults, actual garment checks, and no-write rejection pass");
    return 0;
}
