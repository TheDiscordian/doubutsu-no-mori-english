#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/clothing_stock.c"

static union { u32 alignment; u8 bytes[720]; } bank;
static const u8 seasons[] = {32, 10, 11, 9, 9};
u8 af_stock_month = 1, af_stock_selected = 1;
static float next_random;
static int random_calls, native_calls, resource_disabled;
const void *af_stock_segment(u32 address) {
    assert(address == 0x06000230); return bank.bytes+0x230;
}
float af_stock_random_float(void) { ++random_calls; return next_random; }
u32 af_v3_clothing_source(int index, u32 palette) {
    assert(index == 0x10BF && palette == 0); return resource_disabled ? 0 : 0x03F0F000;
}
static int reference(int *indices, int expanded) {
    static const int by_month[] = {0,4,4,1,1,1,2,2,2,3,3,3,4};
    int season = by_month[af_stock_month], start = 32+expanded, count = 0;
    for (int i = 0; i < 32+expanded; ++i) indices[count++] = i;
    for (int i = 1; i < season; ++i) start += seasons[i];
    for (int i = 0; i < seasons[season]; ++i) indices[count++] = start+i;
    return count;
}
int af_stock_native_index(int *index) {
    int eligible[80]; ++native_calls;
    int count = reference(eligible, 0);
    *index = eligible[(int)(af_stock_random_float()*(float)count)];
    return count;
}
int main(void) {
    memset(bank.bytes, 0xA5, sizeof(bank.bytes));
    memcpy(bank.bytes+0x21C, seasons, sizeof(seasons));
    const u16 *list = (const u16 *)(bank.bytes+0x230);
    for (af_stock_month = 1; af_stock_month <= 12; ++af_stock_month) {
        int eligible[80], count = reference(eligible, 1), result;
        float samples[] = {0.0f, 32.25f/(float)count, 33.25f/(float)count, 0.99999994f};
        for (unsigned i = 0; i < sizeof(samples)/sizeof(*samples); ++i) {
            next_random = samples[i]; random_calls = native_calls = 0;
            int guarded[] = {0x1357, -1, 0x2468};
            assert(af_v3_clothing_stock_index(guarded+1, list) == count);
            assert(guarded[1] == eligible[(int)(next_random*(float)count)]);
            assert(guarded[0] == 0x1357 && guarded[2] == 0x2468);
            assert(random_calls == 1 && native_calls == 0);
        }
        for (int missing = 0; missing < 2; ++missing) {
            af_stock_selected = missing; resource_disabled = missing;
            count = reference(eligible, 0);
            next_random = 0.99999994f; random_calls = native_calls = 0;
            assert(af_v3_clothing_stock_index(&result, list) == count);
            int wanted = eligible[(int)(next_random*(float)count)];
            assert(result == wanted+(wanted >= 32));
            assert(random_calls == 1 && native_calls == 1);
        }
        af_stock_selected = 1; resource_disabled = 0;
        next_random = 0.0f; random_calls = native_calls = 0;
        assert(af_v3_clothing_stock_index(&result, list-1) == count);
        assert(result == 0 && random_calls == 1 && native_calls == 1);
    }
    random_calls = native_calls = 0;
    assert(af_v3_clothing_stock_index(NULL, list) == 0);
    assert(random_calls == 0 && native_calls == 0);
    assert(memcmp(bank.bytes+0x21C, seasons, sizeof(seasons)) == 0);
    puts("Clothing stock seasons, disabled selection, one RNG draw, and native lists pass");
}
