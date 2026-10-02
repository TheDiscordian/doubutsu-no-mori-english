/* Real wrapper under sanitizers; native stock, profile, and RNG APIs doubled. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
const u16 af_seasonal_items[4] = {0x3298, 0x327C, 0x1220, 0x1224};
volatile u8 af_seasonal_rtc[8];
extern u32 af_v3_seasonal_stock_mode;
extern void af_v3_seasonal_stock(u16 *, int);
static int selected, profile_calls, original_calls, pair_calls, draws;
static float random_values[2];
int af_v3_furniture_import_profile(u32 index) {
    ++profile_calls;
    if (index == 1024 + ((0x3298 & 0xFFF) >> 2)) return selected & 1;
    assert(index == 1024 + ((0x327C & 0xFFF) >> 2));
    return selected & 2;
}
float af_seasonal_random(void) {
    assert(draws < 2);
    return random_values[draws++];
}
void af_seasonal_pair(u16 *items, int count, u32 first, u32 second) {
    ++pair_calls;
    if (count > 1) { items[0] = first; items[1] = second; }
    else items[0] = af_seasonal_random() < 0.5f ? first : second;
}
void af_seasonal_original(u16 *items, int count) {
    ++original_calls;
    if (af_seasonal_rtc[5] == 12 && af_seasonal_rtc[3] >= 26)
        af_seasonal_pair(items, count, 0x1220, 0x1224);
    else items[0] = 0x0BAD; /* delegation marker, not a native behaviour claim */
}
int main(void) {
    const int dates[][2] = {{12,25},{12,26},{12,31},{12,32},{1,26},{2,20},{3,3},{5,5}};
    const float rolls[] = {0.0f, 0.49f, 0.5f, 0.99f};
    int cases = 0;
    for (u32 mode = 0; mode < 5; ++mode)
    for (selected = 0; selected < 4; ++selected)
    for (unsigned date = 0; date < sizeof(dates)/sizeof(*dates); ++date)
    for (int count = -1; count <= 3; ++count)
    for (unsigned roll = 0; roll < sizeof(rolls)/sizeof(*rolls); ++roll)
    for (unsigned second = 0; second < sizeof(rolls)/sizeof(*rolls); ++second) {
        struct { u32 before; u16 items[4]; u32 after; } buffer =
            {0xAF53544B, {0xF001,0xF002,0xF003,0xF004}, 0xAF53544B};
        u16 expected[4]; memcpy(expected, buffer.items, sizeof expected);
        af_v3_seasonal_stock_mode = mode;
        af_seasonal_rtc[5] = dates[date][0]; af_seasonal_rtc[3] = dates[date][1];
        random_values[0] = rolls[roll]; random_values[1] = rolls[second];
        profile_calls = original_calls = pair_calls = draws = 0;
        int seasonal = dates[date][0] == 12 && dates[date][1] >= 26 && dates[date][1] <= 31;
        int original = count > 0 && (!seasonal || mode > 3 || (!selected && mode == 0));
        unsigned expected_draws = 0, total = 0;
        u16 pool[4];
        if (count > 0 && !original) {
            if (!(mode & 1)) pool[total++] = 0x1220;
            if (!(mode & 2)) pool[total++] = 0x1224;
            if (selected & 1) pool[total++] = 0x3298;
            if (selected & 2) pool[total++] = 0x327C;
            for (unsigned slot = 0; slot < 2 && slot < (unsigned)count && total; ++slot) {
                unsigned pick = 0;
                if (total > 1) pick = (unsigned)(random_values[expected_draws++] * total);
                expected[slot] = pool[pick];
                pool[pick] = pool[--total];
            }
        } else if (original) {
            if (dates[date][0] == 12 && dates[date][1] >= 26) {
                expected[0] = 0x1220;
                if (count > 1) expected[1] = 0x1224;
                else {
                    expected[0] = random_values[expected_draws++] < 0.5f ? 0x1220 : 0x1224;
                }
            } else expected[0] = 0x0BAD;
        }
        af_v3_seasonal_stock(buffer.items, count);
        assert(memcmp(expected, buffer.items, sizeof expected) == 0);
        assert(buffer.before == 0xAF53544B && buffer.after == 0xAF53544B);
        assert(profile_calls == (count > 0 && seasonal && mode < 4 ? 2 : 0));
        assert(original_calls == original);
        assert(pair_calls == (original && dates[date][0] == 12 && dates[date][1] >= 26));
        assert(draws == (int)expected_draws);
        ++cases;
    }
    profile_calls = original_calls = pair_calls = draws = 0;
    af_v3_seasonal_stock(0, 2);
    assert(!profile_calls && !original_calls && !pair_calls && !draws);
    printf("Seasonal stock selection, native delegation, RNG, and guards: %d cases pass\n", cases);
    return 0;
}
