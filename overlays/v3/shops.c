typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32);
extern int af_v3_original_shop_category(u32);

int af_v3_shop_category(u32 argument) {
    u32 item = (unsigned short)argument;
    if ((item >> 12) == 3)
        return af_v3_furniture_import_profile(1024u + ((item & 0xFFFu) >> 2)) ? 0 : -1;
    return af_v3_original_shop_category(argument);
}
