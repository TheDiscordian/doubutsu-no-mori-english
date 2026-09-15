#include "furniture_tables.h"
#ifdef AF_V3_CLOTHING_DISPLAY
#include "clothing_display.h"
#endif
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef AF_V3_SPARSE_FURNITURE
#include "sparse_furniture.h"
#include "speed_bag.h"
#ifdef __mips__
#define sparse_rows ((const u32 *)AF_V3_STATIC_IMPORT_RAM)
#else
extern u32 af_v3_sparse_rows[AF_V3_STATIC_IMPORT_COUNT * 20];
#define sparse_rows af_v3_sparse_rows
#endif
#endif
#ifdef __mips__
#define seed ((const u32 *)0x80465800u)
#define profiles ((u32 *)AF_V3_FURNITURE_PROFILES)
#define indices ((u8 *)AF_V3_FURNITURE_INDICES)
#define first ((u32 *)0x80470000u)
#define last ((u32 *)(AF_V3_FURNITURE_END-16))
#else
extern u32 af_v3_table_seed[1267], af_v3_table_profiles[AF_V3_FURNITURE_CAPACITY];
extern u8 af_v3_table_indices[AF_V3_FURNITURE_CAPACITY];
extern u32 af_v3_table_first[4], af_v3_table_last[4];
#define seed af_v3_table_seed
#define profiles af_v3_table_profiles
#define indices af_v3_table_indices
#define first af_v3_table_first
#define last af_v3_table_last
#endif

int af_v3_furniture_tables_init(void) {
    for (u32 i = 0; i < AF_V3_FURNITURE_CAPACITY; ++i) {
        /* The native prefix is always empty at startup. Its old storage now
           holds expanded helper code; only reviewed imported seed rows remain. */
#ifdef AF_V3_SPARSE_FURNITURE
        profiles[i] = 0;
        if (i >= AF_V3_SPARSE_FIRST && i < AF_V3_SPARSE_END) {
            u32 slot = i - AF_V3_SPARSE_FIRST;
            const u32 *row = sparse_rows + slot * 20u;
            if (row[0] == (i << 16 | (0x3000u + slot * 4u)) && row[1] == 1)
                profiles[i] = AF_V3_STATIC_IMPORT_RAM + slot * 80u + 8u;
        }
#else
        profiles[i] = i >= 947 && i < 1267 ? seed[i] : 0;
#endif
        indices[i] = 255;
    }
#ifdef AF_V3_SPARSE_FURNITURE
    /* Animated and clothing callback rows have their own stable owners. */
    profiles[AF_V3_SPEED_BAG_INDEX] = AF_V3_SPEED_BAG_PROFILE;
#endif
#ifdef AF_V3_CLOTHING_DISPLAY
    profiles[AF_V3_CLOTHING_DISPLAY_INDEX] = AF_V3_CLOTHING_DISPLAY_PROFILE;
#ifdef AF_V3_ALOHA_DISPLAY
    profiles[AF_V3_RED_DISPLAY_INDEX] = AF_V3_RED_DISPLAY_ROW+8u;
    profiles[AF_V3_BLUE_DISPLAY_INDEX] = AF_V3_BLUE_DISPLAY_ROW+8u;
#endif
#endif
    for (u32 i = 0; i < 4; ++i) first[i] = last[i] = AF_V3_FURNITURE_EDGE;
    return 1;
}
