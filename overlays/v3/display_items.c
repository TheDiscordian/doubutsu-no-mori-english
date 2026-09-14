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

u32 af_v3_display_pocket_item(u32 item) {
    if (item <= 65535u && (item & 0xFFFCu) == AF_V3_CLOTHING_DISPLAY_ITEM &&
            af_v3_furniture_import_profile(AF_V3_CLOTHING_DISPLAY_INDEX)) return 0x34BFu;
    return item;
}

int af_v3_display_item_name(u8 *destination, u32 capacity, u32 item) {
    return af_v3_base_item_name(destination, capacity, af_v3_display_pocket_item(item));
}

int af_v3_display_item_type(u32 argument) {
    u32 item = (u16)argument;
    if (af_v3_display_pocket_item(item) != item) return 10; /* Placed furniture, not pocket clothing. */
    return af_v3_base_item_type(argument);
}

int af_v3_display_item_place(u32 argument, int x, int z, void *destination) {
    u32 item = (u16)argument;
    /* Reuse all four native mannequin footprint cells, including their offsets. */
    if (af_v3_display_pocket_item(item) != item) argument = 0x17ACu | (item & 3u);
    return af_v3_base_item_place(argument, x, z, destination);
}

u32 af_v3_display_item_price(u32 argument) {
    u32 item = (u16)argument, canonical = af_v3_display_pocket_item(item);
    return af_v3_base_item_price(canonical != item ? canonical : argument);
}

void af_v3_display_catalogue_record(u32 argument) {
    u32 item = (u16)argument, canonical = af_v3_display_pocket_item(item);
    af_v3_prior_catalogue_record(canonical != item ? canonical : argument);
}

int af_v3_display_catalogue_owned(const u8 *private, u32 item) {
    return af_v3_prior_catalogue_owned(private, af_v3_display_pocket_item(item));
}
