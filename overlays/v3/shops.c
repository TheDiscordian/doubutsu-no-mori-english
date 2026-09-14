typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);
extern int af_v3_original_shop_category(u32);
#ifdef AF_V3_CLOTHING_PROFILE
extern int af_v3_item_type(u32);
#endif

int af_v3_shop_category(u32 argument) {
    u32 item = (unsigned short)argument;
#ifdef AF_V3_CLOTHING_PROFILE
    /* Shop category two is clothing, distinct from shared item category twelve.
       The shared query checks the selected profile and complete garment record. */
    if ((item >> 8) == 0x34) return af_v3_item_type(item) == 12 ? 2 : -1;
#endif
    if ((item >> 12) == 3)
        return af_v3_furniture_import_profile(1024u + ((item & 0xFFFu) >> 2)) ? 0 : -1;
    return af_v3_original_shop_category(argument);
}
