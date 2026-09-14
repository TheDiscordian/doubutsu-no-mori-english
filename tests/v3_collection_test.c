#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/save_codec.c"
#include "../overlays/v3/collection.c"

struct AfSaveRuntime af_collection_state;
u8 af_collection_players[4 * 0xBD0], *af_collection_active;
static u8 temporary[0xBD0];
static u32 original_calls, original_argument, clear_calls, missing;
static int failed_state, halt_reason;
static jmp_buf halted;

void af_v3_save_halt(int reason) { halt_reason = reason; longjmp(halted, 1); }
void af_v3_require_save_state(void) { if (failed_state) af_v3_save_halt(AF_SAVE_ARGUMENT); }
int af_v3_furniture_import_profile(u32 index) {
    return index != missing && (index == 1161 || index == 1198);
}
#ifdef AF_V3_CLOTHING_PROFILE
int af_v3_item_type(u32 item) {
    if (item == 0x34BF) return missing == item ? 0 : 12;
    return af_v3_furniture_import_profile(1024+((item & 0xFFF)>>2)) ? 10 : 0;
}
#endif
void af_v3_original_collect(u32 argument) { ++original_calls; original_argument = argument; }
void af_v3_original_private_clear(u8 *private) { ++clear_calls; memset(private, 0, 0xBD0); }

int main(void) {
    memset(state, 0, sizeof(*state));
    memset(players, 0xA5, sizeof(af_collection_players));
    state->working[49] = 2; state->working[53] = 64;
#ifdef AF_V3_CLOTHING_PROFILE
    state->working[183] = 0x80;
#endif
    for (u32 p = 0; p < 4; ++p) {
        active = players + p * 0xBD0;
        for (u32 rotation = 0; rotation < 4; ++rotation) {
            af_v3_catalogue_record(0x10000u + 0x3224 + rotation);
            af_v3_catalogue_record(0x32B8 + rotation);
            assert(af_v3_catalogue_owned(active, 0x3224 + rotation) == 1);
            assert(af_v3_catalogue_owned(active, 0x32B8 + rotation) == 1);
        }
#ifdef AF_V3_CLOTHING_PROFILE
        af_v3_catalogue_record(0x34BF);
        assert(af_v3_catalogue_owned(active, 0x34BF) == 1);
        assert(af_v3_catalogue_owned(active, 0x34BC) == 0);
        for (u32 i = 0; i < 32; ++i)
            assert(state->working[AF_SAVE_PROFILE+512+p*32+i] == (i == 23 ? 0x80 : 0));
#endif
    }
    assert(original_calls == 0);
    for (u32 p = 0; p < 4; ++p) {
        for (u32 i = 0; i < 128; ++i)
            assert(state->working[AF_SAVE_PROFILE + p * 128 + i] == (i == 17 ? 2 : i == 21 ? 64 : 0));
        for (u32 i = 0; i < 0xBD0; ++i) assert(players[p * 0xBD0 + i] == 0xA5);
    }
    struct AfSaveRuntime before = *state;
#ifdef AF_V3_CLOTHING_PROFILE
    missing = 0x34BF;
    af_v3_catalogue_record(0x34BF);
    assert(af_v3_catalogue_owned(active, 0x34BF) == 0);
    assert(af_v3_catalogue_owned(active, 0x134BF) == 0);
    assert(!memcmp(&before, state, sizeof(before)));
#endif
    missing = 1161;
    af_v3_catalogue_record(0x3224);
    assert(af_v3_catalogue_owned(active, 0x3224) == 0);
    missing = 0;
    af_v3_catalogue_record(0x3000);
    assert(af_v3_catalogue_owned(active, 0x3000) == 0);
    assert(af_v3_catalogue_owned(active, 0x13224) == 0);
    assert(af_v3_catalogue_owned(0, 0x3224) == 0);
    assert(af_v3_catalogue_owned(players + 1, 0x3224) == 0);
    assert(af_v3_catalogue_owned(temporary, 0x3224) == 0);
    assert(!memcmp(&before, state, sizeof(before)));
    af_v3_catalogue_record(0x11004);
    assert(original_calls == 1 && original_argument == 0x11004);
    af_v3_catalogue_record(0x2400);
    assert(original_calls == 2 && original_argument == 0x2400);
    af_v3_catalogue_clear(temporary);
    assert(!memcmp(&before, state, sizeof(before)) && clear_calls == 1);
    af_v3_catalogue_clear(players + 2 * 0xBD0);
    memset(before.working + AF_SAVE_PROFILE + 256, 0, 128);
#ifdef AF_V3_CLOTHING_PROFILE
    memset(before.working + AF_SAVE_PROFILE + 512 + 64, 0, 32);
#endif
    assert(!memcmp(&before, state, sizeof(before)) && clear_calls == 2);
    for (u32 p = 0; p < 4; ++p)
        for (u32 i = 0; i < 0xBD0; ++i) assert(players[p * 0xBD0 + i] == (p == 2 ? 0 : 0xA5));
    active = temporary;
#ifdef AF_V3_CLOTHING_PROFILE
    if (!setjmp(halted)) { af_v3_catalogue_record(0x34BF); assert(0); }
    assert(halt_reason == AF_SAVE_ARGUMENT && !memcmp(&before, state, sizeof(before)));
#endif
    if (!setjmp(halted)) { af_v3_catalogue_record(0x3224); assert(0); }
    assert(halt_reason == AF_SAVE_ARGUMENT && !memcmp(&before, state, sizeof(before)));
    active = players;
    failed_state = 1;
    if (!setjmp(halted)) { af_v3_catalogue_record(0x3224); assert(0); }
    if (!setjmp(halted)) { af_v3_catalogue_clear(players); assert(0); }
    assert(clear_calls == 2 && !memcmp(&before, state, sizeof(before)));
    failed_state = 0;
    state->working[49] = 0;
    if (!setjmp(halted)) { af_v3_catalogue_record(0x3224); assert(0); }
    assert(halt_reason == AF_SAVE_PROFILE_MISSING);
    puts("Four-player collection, rotation sharing, clearing, fallbacks, and rejection pass");
}
