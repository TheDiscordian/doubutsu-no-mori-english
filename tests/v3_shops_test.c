#include <assert.h>
#include <stdio.h>
#include "../overlays/v3/shops.c"
static u32 disabled, original_argument;
static int original_calls;
#ifdef AF_V3_CLOTHING_PROFILE
static int shirt_disabled;
int af_v3_item_type(u32 item) { return item == 0x34BF && !shirt_disabled ? 12 : 0; }
#endif
int af_v3_furniture_import_profile(u32 index) {
    return index != disabled && (index == 1161 || index == 1198);
}
int af_v3_original_shop_category(u32 argument) {
    ++original_calls; original_argument = argument; return 27;
}
int main(void) {
    for (u32 i = 0; i < 4; ++i) {
        assert(af_v3_shop_category(0x13224 + i) == 0);
        assert(af_v3_shop_category(0x32B8 + i) == 0);
    }
    disabled = 1198;
    assert(af_v3_shop_category(0x32B8) == -1);
    assert(af_v3_shop_category(0x3000) == -1);
    assert(original_calls == 0);
#ifdef AF_V3_CLOTHING_PROFILE
    assert(af_v3_shop_category(0x34BF) == 2);
    assert(af_v3_shop_category(0x134BF) == 2); /* Retain native 16-bit argument semantics. */
    assert(af_v3_shop_category(0x34BC) == -1);
    assert(af_v3_shop_category(0x3400) == -1);
    assert(af_v3_shop_category(0x34FF) == -1);
    shirt_disabled = 1;
    assert(af_v3_shop_category(0x34BF) == -1);
    assert(original_calls == 0);
#endif
    assert(af_v3_shop_category(0x11004) == 27);
    assert(original_calls == 1 && original_argument == 0x11004);
    assert(af_v3_shop_category(0x2000) == 27);
    assert(original_calls == 2 && original_argument == 0x2000);
    puts("Selected shop categories and original fallbacks pass");
}
