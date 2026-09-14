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
void af_v3_original_collect(u32 argument) { ++original_calls; original_argument = argument; }
void af_v3_original_private_clear(u8 *private) { ++clear_calls; memset(private, 0, 0xBD0); }

int main(void) {
    memset(state, 0, sizeof(*state));
    memset(players, 0xA5, sizeof(af_collection_players));
    state->working[49] = 2; state->working[53] = 64;
    for (u32 p = 0; p < 4; ++p) {
        active = players + p * 0xBD0;
        for (u32 rotation = 0; rotation < 4; ++rotation) {
            af_v3_catalogue_record(0x10000u + 0x3224 + rotation);
            af_v3_catalogue_record(0x32B8 + rotation);
            assert(af_v3_catalogue_owned(active, 0x3224 + rotation) == 1);
            assert(af_v3_catalogue_owned(active, 0x32B8 + rotation) == 1);
        }
    }
    assert(original_calls == 0);
    for (u32 p = 0; p < 4; ++p) {
        for (u32 i = 0; i < 128; ++i)
            assert(state->working[160 + p * 128 + i] == (i == 17 ? 2 : i == 21 ? 64 : 0));
        for (u32 i = 0; i < 0xBD0; ++i) assert(players[p * 0xBD0 + i] == 0xA5);
    }
    struct AfSaveRuntime before = *state;
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
    memset(before.working + 160 + 256, 0, 128);
    assert(!memcmp(&before, state, sizeof(before)) && clear_calls == 2);
    for (u32 p = 0; p < 4; ++p)
        for (u32 i = 0; i < 0xBD0; ++i) assert(players[p * 0xBD0 + i] == (p == 2 ? 0 : 0xA5));
    active = temporary;
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
