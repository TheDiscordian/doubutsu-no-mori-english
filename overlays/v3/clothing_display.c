/* Preserve native mannequin geometry while selecting the full garment index. */
#include "clothing_display.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern int af_v3_item_type(u32);
#ifdef __mips__
#define selected_display (((const u8 *)0x80460020u)[119] & 0x80)
#else
extern u8 af_v3_display_profile[192];
#define selected_display (af_v3_display_profile[119] & 0x80)
#endif

u32 af_v3_display_clothing_index(u32 argument) {
    u32 item = (u16)argument;
    if (item >= 0x17ACu && item < 0x1BA8u) return (item - 0x17ACu) >> 2;
    if ((item & 0xFFFCu) == AF_V3_CLOTHING_DISPLAY_ITEM && selected_display &&
            af_v3_item_type(0x34BFu) == 12) return 0x10BFu;
    return 0; /* Retain the original callback's unknown-item fallback. */
}
