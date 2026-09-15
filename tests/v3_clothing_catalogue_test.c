#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_CLOTHING_CATALOGUE 1
#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/catalogue.c"

u8 *af_catalogue_active;
u32 af_catalogue_profiles[AF_V3_FURNITURE_CAPACITY];
static u8 player[0xBD0], other[0xBD0];
static int selected = 1, owned = 1, bit_calls, init_calls;
static u32 last_item; static int last_category, last_list; static void *last_game;
static jmp_buf halted;
void af_v3_save_halt(int reason) { (void)reason; longjmp(halted, 1); }
int af_v3_furniture_import_profile(u32 index) {
#ifdef AF_V3_WESTERN_LARGE
    if (index == 1201 || index == 1205 || index == 1206) return selected;
#endif
    return (index == 1727 && selected) || index == 1161;
}
int af_v3_catalogue_owned(const u8 *p, u32 item) {
    assert(p == player); last_item = item;
    return item == 0x3AFC && selected && owned;
}
int af_v3_native_catalogue_bit(const u32 *bits, int index) {
    assert(bits && index < 2048); ++bit_calls; return 13;
}
void af_v3_original_catalogue_program(struct Preview *preview) { assert(preview); }
int af_v3_native_catalogue_available(u32 argument, int category, int list, void *game) {
    last_item = argument; last_category = category; last_list = list; last_game = game;
    return list == 0 ? 7 : 0;
}
void af_v3_original_catalogue_furniture_init(struct Preview *preview, u32 argument) {
    ++init_calls; last_item = argument;
    memset(preview, 0xA5, sizeof(*preview));
    preview->model_y = -3.0f; preview->scale = 0.9f; preview->height = 42.0f;
}

int main(void) {
    active = player;
    const u32 *bits = (const u32 *)(player+0xAF0);
    assert(af_v3_catalogue_bit(bits, 491) == 13 && bit_calls == 1);
    assert(af_v3_catalogue_bit(bits, 2751) == 1 && last_item == 0x3AFC);
    owned = 0; assert(af_v3_catalogue_bit(bits, 2751) == 0); owned = 1;
    assert(af_v3_catalogue_bit((const u32 *)(other+0xAF0), 2751) == 0);
    struct Preview preview, expected;
    for (int enabled = 0; enabled < 2; ++enabled) {
        selected = enabled;
        assert(af_v3_catalogue_bit(bits, 2751) == enabled);
        for (u32 r = 0; r < 4; ++r) {
            u32 argument = 0xABCD3AFCu | r;
            af_v3_original_catalogue_furniture_init(&expected, argument);
            if (enabled) { expected.model_y = -4.0f; expected.scale = 1.0f; expected.height = 38.0f; }
            int calls = init_calls;
            af_v3_catalogue_furniture_init(&preview, argument);
            assert(init_calls == calls+1 && last_item == argument);
            assert(!memcmp(&preview, &expected, sizeof(preview)));
            assert(af_v3_catalogue_available(argument, 0, 0, other) == enabled);
            if (enabled) assert(last_item == 0x34BF && last_category == 2 && last_list == 0 && last_game == other);
            for (int list = -1; list < 7; ++list)
                assert(af_v3_catalogue_available(argument, 0, list, other) == (enabled && list == 0));
        }
    }
    for (u32 item = 0x17AC; item <= 0x1BA4; item += 4) {
        af_v3_original_catalogue_furniture_init(&expected, item);
        af_v3_catalogue_furniture_init(&preview, item);
        assert(!memcmp(&preview, &expected, sizeof(preview)));
    }
    assert(af_v3_catalogue_available(0xABCD2400, 2, 0, other) == 7 && last_item == 0xABCD2400);
    assert(af_v3_catalogue_available(0x3224, 0, 1, other) == 1);
    preview.index = 2751; profiles[1727] = 0x80466608;
    af_v3_catalogue_program(&preview); assert(preview.profile == 0x80466608);
#ifdef AF_V3_WESTERN_LARGE
    const u32 large_items[] = {0x32C4, 0x32D4, 0x32D8};
    for (int enabled = 0; enabled < 2; ++enabled) {
        selected = enabled;
        for (int item_index = 0; item_index < 3; ++item_index) {
            for (u32 rotation = 0; rotation < 4; ++rotation) {
                u32 argument = 0xABCD0000u | large_items[item_index] | rotation;
                af_v3_original_catalogue_furniture_init(&expected, argument);
                if (enabled && item_index) {
                    expected.model_y = -5.0f;
                    expected.scale = item_index == 1 ? 0.87f : 0.82f;
                }
                int calls = init_calls;
                af_v3_catalogue_furniture_init(&preview, argument);
                assert(init_calls == calls + 1 && last_item == argument);
                assert(!memcmp(&preview, &expected, sizeof(preview)));
                for (int list = -1; list < 7; ++list) {
                    int allowed = item_index == 1 ? list == 5 : list >= 0 && list < 3;
                    assert(af_v3_catalogue_available(argument, 0, list, other) == (enabled && allowed));
                    assert(!af_v3_catalogue_available(argument, 2, list, other));
                }
            }
        }
    }
    puts("Large Western exact previews, four rotations, selection, and lottery rules pass");
#endif
    puts("clothing ownership, exact presentation, original previews, and native availability pass");
    return 0;
}
