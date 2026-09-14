/* Preserve native pocket/display conversions around the selected new garment. */
#include "clothing_display.h"
typedef unsigned short u16;
typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);
extern u32 af_v3_display_pocket_item(u32);
extern u16 af_v3_prior_display_item(u32);
extern u16 af_v3_prior_pocket_item(u32);

u16 af_v3_room_display_item(u32 argument) {
    if ((u16)argument == 0x34BFu &&
            af_v3_furniture_import_profile(AF_V3_CLOTHING_DISPLAY_INDEX))
        return AF_V3_CLOTHING_DISPLAY_ITEM;
    return af_v3_prior_display_item(argument);
}

u16 af_v3_room_pocket_item(u32 argument) {
    u32 item = (u16)argument, pocket = af_v3_display_pocket_item(item);
    if (pocket != item) return (u16)pocket;
    return af_v3_prior_pocket_item(argument);
}
