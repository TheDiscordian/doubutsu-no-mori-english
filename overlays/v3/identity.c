/* Inlined room index conversions retain their unchecked native fallback. */
typedef unsigned int u32;
extern int af_v3_furniture_import_profile(u32 index);
extern u32 af_v3_furniture_item(u32 index, u32 rotation);

u32 af_v3_identity_item(u32 index, u32 unused) {
    (void)unused;
    if (af_v3_furniture_import_profile(index))
        return af_v3_furniture_item(index, 0);
    return index * 4u + 0x1000u;
}
