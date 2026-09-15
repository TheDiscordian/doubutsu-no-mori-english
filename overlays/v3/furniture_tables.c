#include "furniture_tables.h"
#ifdef AF_V3_CLOTHING_DISPLAY
#include "clothing_display.h"
#endif
typedef unsigned char u8;
typedef unsigned int u32;
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
        profiles[i] = i >= 947 && i < 1267 ? seed[i] : 0;
        indices[i] = 255;
    }
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
