/* Display-only recovery: never widen or modify a saved PersonalID. */
typedef unsigned char u8;
extern const u8 af_fishing_aliases[6368];
extern void af_fishing_native_set(void *, int, const u8 *, int);

const u8 *af_fishing_resolve(const u8 *id, const u8 *rows, int count) {
    int lo = 0, hi = count, i;
    if (!id || !rows || count < 1 || count > 394) return 0;
    /* Native NPC initializer: dummy town plus both reserved numeric IDs. */
    if (id[6] != 0x98 || id[7] != 0xA6 || id[8] != 0x8F || id[9] != 0xA1 ||
        id[10] != 0x20 || id[11] != 0x20 || id[12] != 0xFF || id[13] != 0xFF ||
        id[14] != 0xFF || id[15] != 0xFF) return 0;
    while (lo < hi) {
        int mid = lo + (hi - lo) / 2;
        const u8 *row = rows + mid * 16;
        for (i = 0; i < 6 && id[i] == row[i]; ++i) {}
        if (i == 6) return row + 8;
        if (id[i] < row[i]) hi = mid;
        else lo = mid + 1;
    }
    return 0;
}

void af_fishing_name(void *window, int slot, const u8 *id, int length) {
    const u8 *name = length == 6 ? af_fishing_resolve(id, af_fishing_aliases + 64, 394) : 0;
    af_fishing_native_set(window, slot, name ? name : id, name ? 8 : length);
}
