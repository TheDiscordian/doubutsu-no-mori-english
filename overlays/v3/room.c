/* Values used by checked in-place room detours, never replacement item IDs. */
typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);
#ifdef AF_V3_CLOTHING_PROFILE
extern int af_v3_item_type(u32);
#endif

u32 af_v3_room_value(u32 value, u32 mode) {
    u32 item = value & 65535u;
    u32 index = 1024u + ((item & 4095u) >> 2);
#ifdef AF_V3_CLOTHING_PROFILE
    /* Player animation's item-to-cloth index conversion, with the original
       index-zero fallback for unknown items. Never mask imports to eight bits. */
    if (mode == 3)
        return value == item && ((item >> 8) == 0x24 ||
            ((item >> 8) == 0x34 && af_v3_item_type(item) == 12)) ? item-0x2400 : 0;
    /* Only category decisions see clothes as ordinary type-2 items. Never
       admit garments to furniture bounds or furniture index arithmetic. */
    if (value == item && mode > 1 && (item >> 12) == 3u && af_v3_item_type(item) == 12)
        return 2;
#endif
    int imported = value == item && (item >> 12) == 3u &&
                   af_v3_furniture_import_profile(index);
    if (mode == 0) return (int)value < 0x1ECD || imported;
    if (mode == 1) return imported ? index * 4u + (item & 3u) : value - 0x1000u;
    return imported ? 1u : (item >> 12);
}
