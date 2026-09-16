/* The same garment keeps one name, price, and collected bit when displayed. */
#include "clothing_display.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);
extern int af_v3_base_item_name(u8 *, u32, u32);
extern int af_v3_base_item_type(u32);
extern int af_v3_base_item_place(u32, int, int, void *);
extern u32 af_v3_base_item_price(u32);
extern void af_v3_prior_catalogue_record(u32);
extern int af_v3_prior_catalogue_owned(const u8 *, u32);
#ifdef AF_V3_HELD_ITEMS
extern int af_v3_held_item_name(u8 *, u32, u32);
extern u32 af_v3_held_item_price(u32);
#endif
#ifdef AF_V3_DISPLAY_ALIASES
#include "display_aliases.h"
#endif

u32 af_v3_display_pocket_item(u32 item) {
#ifdef AF_V3_DISPLAY_ALIASES
    const u16 *alias=af_v3_raw_display_alias(item);
    if (alias && af_v3_furniture_import_profile(1024u+((item&0xFFFu)>>2))) return alias[0];
#elif defined(AF_V3_ALOHA_DISPLAY)
    u32 base=item&0xFFFCu;
    if (item<=65535u && (base==AF_V3_CLOTHING_DISPLAY_ITEM ||
            base==AF_V3_RED_DISPLAY_ITEM || base==AF_V3_BLUE_DISPLAY_ITEM) &&
            af_v3_furniture_import_profile(1024u+((base&0xFFFu)>>2)))
        return 0x3400u+((base-0x3800u)>>2);
#else
    if (item <= 65535u && (item & 0xFFFCu) == AF_V3_CLOTHING_DISPLAY_ITEM &&
            af_v3_furniture_import_profile(AF_V3_CLOTHING_DISPLAY_INDEX)) return 0x34BFu;
#endif
    return item;
}

int af_v3_display_item_name(u8 *destination, u32 capacity, u32 item) {
    item=af_v3_display_pocket_item(item);
#ifdef AF_V3_HELD_ITEMS
    if (item-0x2224u<56u) return af_v3_held_item_name(destination,capacity,item);
#endif
    return af_v3_base_item_name(destination, capacity, item);
}

int af_v3_display_item_type(u32 argument) {
    u32 item = (u16)argument;
    if (af_v3_display_pocket_item(item) != item) return 10; /* Placed furniture, not pocket clothing. */
    return af_v3_base_item_type(argument);
}

int af_v3_display_item_place(u32 argument, int x, int z, void *destination) {
    u32 item = (u16)argument;
    /* Reuse all four native mannequin footprint cells, including their offsets. */
    if (af_v3_display_pocket_item(item) != item) {
#ifdef AF_V3_DISPLAY_ALIASES
        u32 footprint=af_v3_raw_display_alias(item)[1];
        /* Zero retains the display's own generated footprint. Only categories
         * with a checked native equivalent use the recorded replacement. */
        if (footprint) argument=footprint | (item & 3u);
#else
        argument = 0x17ACu | (item & 3u);
#endif
    }
    return af_v3_base_item_place(argument, x, z, destination);
}

u32 af_v3_display_item_price(u32 argument) {
    u32 item = (u16)argument, canonical = af_v3_display_pocket_item(item);
#ifdef AF_V3_HELD_ITEMS
    if (canonical-0x2224u<56u) return af_v3_held_item_price(canonical);
#endif
    return af_v3_base_item_price(canonical != item ? canonical : argument);
}

void af_v3_display_catalogue_record(u32 argument) {
    u32 item = (u16)argument, canonical = af_v3_display_pocket_item(item);
    af_v3_prior_catalogue_record(canonical != item ? canonical : argument);
}

int af_v3_display_catalogue_owned(const u8 *private, u32 item) {
    return af_v3_prior_catalogue_owned(private, af_v3_display_pocket_item(item));
}
