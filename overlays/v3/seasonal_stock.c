/* Extend existing late-December stock without changing seasonal allocations. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
extern const u16 af_seasonal_items[4]; /* donor pair, native fallback pair */
extern volatile u8 af_seasonal_rtc[8];
extern int af_v3_furniture_import_profile(u32);
extern float af_seasonal_random(void);
extern void af_seasonal_original(u16 *, int);
extern void af_seasonal_pair(u16 *, int, u32, u32);
u32 af_v3_seasonal_stock_mode __attribute__((section(".seasonal_choice"))) = 0;

void af_v3_seasonal_stock(u16 *items, int count) {
    if (!items || count <= 0) return;
    if (af_seasonal_rtc[5] != 12 || af_seasonal_rtc[3] < 26 || af_seasonal_rtc[3] > 31) {
        af_seasonal_original(items, count);
        return;
    }
    u32 first = af_seasonal_items[0], second = af_seasonal_items[1];
    int a = af_v3_furniture_import_profile(1024u + ((first & 0xFFFu) >> 2));
    int b = af_v3_furniture_import_profile(1024u + ((second & 0xFFFu) >> 2));
    if ((!a && !b) || af_v3_seasonal_stock_mode > 1 ||
            (!af_v3_seasonal_stock_mode && af_seasonal_random() >= 0.5f)) {
        af_seasonal_original(items, count);
        return;
    }
    /* N64 mode mixes native and imported pairs; GameCube mode prioritises the
       donor pair. Missing selections retain the corresponding native item.
       The complete native pair helper matches the donor's two-slot and
       one-slot/half-probability algorithm and owns the actual RNG call. */
    af_seasonal_pair(items, count, a ? first : af_seasonal_items[2],
                    b ? second : af_seasonal_items[3]);
}
