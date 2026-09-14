#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/catalogue.c"

u8 *af_catalogue_active;
u32 af_catalogue_profiles[1267];
static u8 player[0xBD0], other[0xBD0];
static int bit_calls, program_calls, available_calls, halt_reason;
static u32 disabled, owned_item, available_argument;
static const u32 *bit_pointer;
static int bit_index, available_category, available_list;
static void *available_game;
static jmp_buf halted;

void af_v3_save_halt(int reason) { halt_reason = reason; longjmp(halted, 1); }
int af_v3_furniture_import_profile(u32 index) {
    return index != disabled && (index == 1161 || index == 1198);
}
int af_v3_catalogue_owned(const u8 *p, u32 item) {
    assert(p == player); owned_item = item;
    return af_v3_furniture_import_profile(1024 + ((item & 0xFFF) >> 2));
}
int af_v3_native_catalogue_bit(const u32 *p, int index) {
    ++bit_calls; bit_pointer = p; bit_index = index; return 17;
}
void af_v3_original_catalogue_program(struct Preview *p) { assert(p); ++program_calls; }
int af_v3_native_catalogue_available(u32 arg, int cat, int list, void *game) {
    ++available_calls; available_argument = arg; available_category = cat;
    available_list = list; available_game = game; return 29;
}

int main(void) {
    active = player;
    const u32 *bits = (const u32 *)(player + 0xAF0);
    assert(af_v3_catalogue_bit(bits, 946) == 17);
    assert(bit_calls == 1 && bit_pointer == bits && bit_index == 946);
    assert(af_v3_catalogue_bit(bits, 2185) == 1 && owned_item == 0x3224);
    assert(af_v3_catalogue_bit(bits, 2222) == 1 && owned_item == 0x32B8);
    disabled = 1198;
    assert(af_v3_catalogue_bit(bits, 2222) == 0);
    assert(af_v3_catalogue_bit(bits, 2048) == 0);
    assert(af_v3_catalogue_bit(bits, 3072) == 0);
    assert(af_v3_catalogue_bit((const u32 *)(other + 0xAF0), 2185) == 0);
    active = 0;
    assert(af_v3_catalogue_bit(bits, 2185) == 0);
    active = player; disabled = 0;
    struct Preview preview, expected;
    memset(&preview, 0xA5, sizeof(preview));
    preview.index = 946; expected = preview;
    af_v3_catalogue_program(&preview);
    assert(program_calls == 1 && !memcmp(&preview, &expected, sizeof(preview)));
    for (u32 i = 0; i < 2; ++i) {
        u32 index = i ? 1198 : 1161;
        profiles[index] = 0x80467208 + i * 80;
        preview.index = index + 1024; expected = preview;
        expected.profile = profiles[index];
        af_v3_catalogue_program(&preview);
        assert(!memcmp(&preview, &expected, sizeof(preview)));
    }
    if (!setjmp(halted)) { af_v3_catalogue_program(0); assert(0); }
    assert(halt_reason == -1);
    static const u16 invalid[] = {947, 1024, 2047, 2048, 3071, 3072, 65535};
    for (volatile unsigned i = 0; i < sizeof(invalid) / sizeof(*invalid); ++i) {
        preview.index = invalid[i];
        if (!setjmp(halted)) { af_v3_catalogue_program(&preview); assert(0); }
        assert(halt_reason == -7);
    }
    disabled = 1198; preview.index = 2222;
    if (!setjmp(halted)) { af_v3_catalogue_program(&preview); assert(0); }
    assert(halt_reason == -7); disabled = 0;
    for (int list = -1; list < 6; ++list) {
        assert(af_v3_catalogue_available(0x13224, 0, list, player) == (list >= 0 && list < 3));
        assert(af_v3_catalogue_available(0x32B8, 1, list, player) == 0);
        assert(af_v3_catalogue_available(0x3000, 0, list, player) == 0);
    }
    assert(af_v3_catalogue_available(0x11004, 2, 4, other) == 29);
    assert(available_calls == 1 && available_argument == 0x11004 && available_category == 2
           && available_list == 4 && available_game == other);
    puts("Catalogue ownership, previews, eligibility, fallbacks, and rejection pass");
}
