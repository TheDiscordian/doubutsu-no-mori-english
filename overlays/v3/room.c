/* Values used by checked in-place room detours, never replacement item IDs. */
typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);

u32 af_v3_room_value(u32 value, u32 mode) {
    u32 item = value & 65535u;
    u32 index = 1024u + ((item & 4095u) >> 2);
    int imported = value == item && (item >> 12) == 3u &&
                   af_v3_furniture_import_profile(index);
    if (mode == 0) return (int)value < 0x1ECD || imported;
    if (mode == 1) return imported ? index * 4u + (item & 3u) : value - 0x1000u;
    return imported ? 1u : (item >> 12);
}
