#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_SPARSE_FURNITURE 1
#define AF_V3_CLOTHING_DISPLAY 1
#define AF_V3_ALOHA_DISPLAY 1
#include "../overlays/v3/furniture_tables.c"
u32 af_v3_table_seed[1267], af_v3_table_profiles[AF_V3_FURNITURE_CAPACITY];
u8 af_v3_table_indices[AF_V3_FURNITURE_CAPACITY];
u32 af_v3_table_first[4], af_v3_table_last[4];
u32 af_v3_sparse_rows[AF_V3_STATIC_IMPORT_COUNT * 20];

int main(void) {
    const u32 slots[] = {0, 177, 700, 1023};
    for (u32 i = 0; i < 1267; ++i) af_v3_table_seed[i] = 0xDEADBEEF;
    for (u32 k = 0; k < sizeof slots / sizeof slots[0]; ++k) {
        u32 i = slots[k];
        sparse_rows[i * 20] = ((i + 1024) << 16) | (0x3000 + i * 4);
        sparse_rows[i * 20 + 1] = 1;
    }
    sparse_rows[20] = 0x04013004; /* Correct identity, disabled. */
    sparse_rows[40] = 0x04033008; sparse_rows[41] = 1; /* Wrong index. */
    sparse_rows[60] = 0x04033018; sparse_rows[61] = 1; /* Wrong item. */
    for (int repeat = 0; repeat < 2; ++repeat) {
        memset(af_v3_table_profiles, 0xA5, sizeof af_v3_table_profiles);
        memset(af_v3_table_indices, 0xA5, sizeof af_v3_table_indices);
        assert(af_v3_furniture_tables_init() == 1);
        for (u32 n = 0; n < AF_V3_FURNITURE_CAPACITY; ++n) {
            u32 expected = 0;
            for (u32 k = 0; k < sizeof slots / sizeof slots[0]; ++k)
                if (n == slots[k] + 1024) expected = AF_V3_STATIC_IMPORT_RAM + slots[k] * 80 + 8;
            if (n == AF_V3_SPEED_BAG_INDEX) expected = AF_V3_SPEED_BAG_PROFILE;
            if (n == AF_V3_CLOTHING_DISPLAY_INDEX) expected = AF_V3_CLOTHING_DISPLAY_PROFILE;
            if (n == AF_V3_RED_DISPLAY_INDEX) expected = AF_V3_RED_DISPLAY_ROW + 8;
            if (n == AF_V3_BLUE_DISPLAY_INDEX) expected = AF_V3_BLUE_DISPLAY_ROW + 8;
            assert(profiles[n] == expected && indices[n] == 255);
        }
        for (u32 i = 0; i < 4; ++i) assert(first[i] == AF_V3_FURNITURE_EDGE && last[i] == AF_V3_FURNITURE_EDGE);
    }
    puts("complete sparse initialization, disabled/malformed rows, padding, and guards pass");
}
