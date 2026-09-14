/* Additive HRA metadata uses stable room indices, not catalogue bit numbers. */
typedef unsigned int u32;
extern u32 af_v3_hra_table[1267];
extern int af_v3_furniture_import_profile(unsigned int runtime_index);

unsigned int af_v3_hra_remaining(int group, int series) {
    unsigned int i;
    if (series < 0 || series >= 55 || group < 0 || group >= 1024)
        return 0;
    for (i = 0; i < 1267; ++i) {
        u32 metadata = af_v3_hra_table[i];
        if ((int)(metadata >> 26) == series && (int)((metadata >> 16) & 1023) == group) {
            if (i < 947)
                return 0x1000 + i * 4;
            if (i >= 1024 && i < 1266) {
                unsigned int item = 0x3000 + (i - 1024) * 4;
                if (af_v3_furniture_import_profile(i))
                    return item;
            }
        }
    }
    return 0;
}
