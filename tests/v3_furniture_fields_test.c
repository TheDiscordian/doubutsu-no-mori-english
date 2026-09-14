#include <assert.h>
#include <stdio.h>
#include "../overlays/v3/fields.c"

static int disabled, fallbacks;
int af_v3_furniture_import_profile(u32 index) {
    return !disabled && (index == 1161 || index == 1198);
}
int af_v3_original_shop_furniture(u32 item) {
    ++fallbacks;
    return item == 0x1004;
}
int main(void) {
    for (u32 rotation = 0; rotation < 4; ++rotation) {
        assert(af_v3_field_shop(0x3224 | rotation) == 1);
        assert(af_v3_field_shop(0x32B8 | rotation) == 1);
    }
    assert(!af_v3_field_shop(0x3000));
    disabled = 1;
    assert(!af_v3_field_shop(0x3224));
    assert(!af_v3_field_shop(0x32B8));
    assert(fallbacks == 0);
    assert(af_v3_field_shop(0x1004) == 1);
    assert(af_v3_field_shop(0x1000) == 0);
    assert(fallbacks == 2);
    puts("Selected shop groups and unchanged original dispatch pass");
    return 0;
}
