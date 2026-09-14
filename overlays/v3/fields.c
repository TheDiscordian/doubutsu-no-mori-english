/* The installed donor proof requires shop groups A/C and no action sounds. */
typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);
extern int af_v3_original_shop_furniture(u32);

int af_v3_field_shop(u32 item) {
    if ((item >> 12) == 3u)
        return af_v3_furniture_import_profile(1024u + ((item & 4095u) >> 2)) != 0;
    return af_v3_original_shop_furniture(item);
}
