/* Choose late-December furniture from the four independently enabled items. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern const u16 af_seasonal_items[4]; /* candle, flag, kadomatsu, kagamimochi */
extern volatile u8 af_seasonal_rtc[8];
extern int af_v3_furniture_import_profile(u32);
extern float af_seasonal_random(void);
extern void af_seasonal_original(u16 *, int);
/* Bit 0 disables kadomatsu; bit 1 disables kagamimochi. */
u32 af_v3_seasonal_stock_mode __attribute__((section(".seasonal_choice"))) = 0;

void af_v3_seasonal_stock(u16 *items, int count) {
    if (!items || count <= 0) return;
    if (af_seasonal_rtc[5] != 12 || af_seasonal_rtc[3] < 26 ||
            af_seasonal_rtc[3] > 31 || af_v3_seasonal_stock_mode > 3) {
        af_seasonal_original(items, count);
        return;
    }
    u32 first = af_seasonal_items[0], second = af_seasonal_items[1];
    int a = af_v3_furniture_import_profile(1024u + ((first & 0xFFFu) >> 2));
    int b = af_v3_furniture_import_profile(1024u + ((second & 0xFFFu) >> 2));
    if (!a && !b && !af_v3_seasonal_stock_mode) {
        af_seasonal_original(items, count);
        return;
    }
    u16 choices[4];
    u32 n = 0;
    if (!(af_v3_seasonal_stock_mode & 1)) choices[n++] = af_seasonal_items[2];
    if (!(af_v3_seasonal_stock_mode & 2)) choices[n++] = af_seasonal_items[3];
    if (a) choices[n++] = first;
    if (b) choices[n++] = second;
    /* Retain the original maximum of two seasonal slots. With zero enabled
       decorations leave ordinary furniture untouched; with one use one slot.
       Draw without replacement so a two-slot shop never duplicates an item. */
    for (u32 slot = 0; slot < 2 && slot < (u32)count && n; ++slot) {
        u32 pick = n > 1 ? (u32)(af_seasonal_random() * (float)n) : 0;
        if (pick >= n) pick = n - 1;
        items[slot] = choices[pick];
        choices[pick] = choices[--n];
    }
}
