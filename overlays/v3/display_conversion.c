/* Preserve native pocket/display conversions around the selected new garment. */
#include "clothing_display.h"
typedef unsigned short u16;
typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);
extern u32 af_v3_display_pocket_item(u32);
extern u16 af_v3_prior_display_item(u32);
extern u16 af_v3_prior_pocket_item(u32);
#ifdef AF_V3_DISPLAY_ALIASES
#include "display_aliases.h"
#endif

u16 af_v3_room_display_item(u32 argument) {
#ifdef AF_V3_DISPLAY_ALIASES
    u32 item=(u16)argument;
    if (display_alias_index->magic == AF_V3_DISPLAY_ALIAS_MAGIC &&
            display_alias_index->count <= AF_V3_DISPLAY_ALIAS_CAPACITY) {
        for (u32 i=0; i<display_alias_index->count; ++i) {
            u32 parent=display_alias_index->rows[i].parent;
            if (parent>item) break;
            if (parent==item) {
                u32 display=display_alias_index->rows[i].display;
                if (af_v3_display_pocket_item(display)==item) return (u16)display;
                break;
            }
        }
    }
#elif defined(AF_V3_ALOHA_DISPLAY)
    u32 item=(u16)argument;
    if ((item==0x34BFu || item==0x341Au || item==0x341Bu) &&
            af_v3_furniture_import_profile(1536u+item-0x3400u))
        return (u16)(0x3800u+(item-0x3400u)*4u);
#else
    if ((u16)argument == 0x34BFu &&
            af_v3_furniture_import_profile(AF_V3_CLOTHING_DISPLAY_INDEX))
        return AF_V3_CLOTHING_DISPLAY_ITEM;
#endif
    return af_v3_prior_display_item(argument);
}

u16 af_v3_room_pocket_item(u32 argument) {
    u32 item = (u16)argument, pocket = af_v3_display_pocket_item(item);
    if (pocket != item) return (u16)pocket;
    return af_v3_prior_pocket_item(argument);
}
