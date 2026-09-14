#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/furniture_tables.c"

u32 af_v3_table_seed[1267], af_v3_table_profiles[AF_V3_FURNITURE_CAPACITY];
u8 af_v3_table_indices[AF_V3_FURNITURE_CAPACITY];
u32 af_v3_table_first[4], af_v3_table_last[4];

int main(void) {
    af_v3_table_seed[1161] = 0x80467208;
    af_v3_table_seed[1198] = 0x80467258;
    af_v3_table_seed[3] = 0xDEADBEEF; /* Retired native prefix can contain code. */
    memset(af_v3_table_profiles, 0xA5, sizeof af_v3_table_profiles);
    memset(af_v3_table_indices, 0xA5, sizeof af_v3_table_indices);
    assert(af_v3_furniture_tables_init() == 1);
    for (u32 i = 0; i < AF_V3_FURNITURE_CAPACITY; ++i) {
        assert(af_v3_table_profiles[i] == (i == 1161 ? 0x80467208u : i == 1198 ? 0x80467258u : 0));
        assert(af_v3_table_indices[i] == 255);
    }
    for (u32 i = 0; i < 4; ++i) {
        assert(af_v3_table_first[i] == AF_V3_FURNITURE_EDGE);
        assert(af_v3_table_last[i] == AF_V3_FURNITURE_EDGE);
    }
    assert(AF_V3_FURNITURE_CAPACITY % 4 == 3);
    assert(AF_V3_FURNITURE_PROFILES + 4*AF_V3_FURNITURE_CAPACITY <= AF_V3_FURNITURE_INDICES);
    assert(AF_V3_FURNITURE_INDICES + AF_V3_FURNITURE_CAPACITY <= AF_V3_FURNITURE_END-16);
    puts("expanded furniture table initialization and bounds pass");
    return 0;
}
