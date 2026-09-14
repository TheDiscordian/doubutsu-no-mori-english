/* Additive HRA metadata uses stable room indices, not catalogue bit numbers. */
typedef unsigned int u32;
#ifdef AF_V3_FURNITURE_TABLES
#include "furniture_tables.h"
#define HRA_COUNT AF_V3_FURNITURE_CAPACITY
#define ITEM_END 2048u
#else
#define HRA_COUNT 1267u
#define ITEM_END 1266u
#endif
extern u32 af_v3_hra_table[HRA_COUNT];
extern int af_v3_furniture_import_profile(unsigned int runtime_index);

unsigned int af_v3_hra_remaining(int group, int series) {
    unsigned int i;
    if (series < 0 || series >= 55 || group < 0 || group >= 1024)
        return 0;
    for (i = 0; i < HRA_COUNT; ++i) {
        u32 metadata = af_v3_hra_table[i];
        if ((int)(metadata >> 26) == series && (int)((metadata >> 16) & 1023) == group) {
            if (i < 947)
                return 0x1000 + i * 4;
            if (i >= 1024 && i < ITEM_END) {
                unsigned int item = 0x3000 + (i - 1024) * 4;
                if (af_v3_furniture_import_profile(i))
                    return item;
            }
        }
    }
    return 0;
}
