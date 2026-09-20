#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/tool_effects.c"

volatile DigPosition af_test_dig_previous;
static DigPosition expected_position;
static int source_status, status_calls, random_calls;
static u16 source_item;
static float next_random;
int af_test_dig_status(u16 *item, DigPosition position) {
    ++status_calls;
    assert(memcmp(&position, &expected_position, sizeof(position)) == 0);
    *item = source_item;
    return source_status;
}
float af_test_dig_random(void) { ++random_calls; return next_random; }

static void check(DigPosition position, int golden, int result, int rolls, u16 item) {
    u16 output[] = {0xA55A, 0xFFFF, 0x5AA5};
    DigPosition before = af_test_dig_previous;
    expected_position = position; status_calls = random_calls = 0;
    assert(af_v3_shovel_status(output+1, position, golden) == result);
    assert(status_calls == 1 && random_calls == rolls);
    assert(output[0] == 0xA55A && output[1] == item && output[2] == 0x5AA5);
    DigPosition after = af_test_dig_previous;
    assert(memcmp(&after, source_status == 3 ? &position : &before, sizeof(after)) == 0);
}

int main(void) {
    const DigPosition origin = {100, 9, -100};
    const DigPosition positions[] = {
        {100,9,-100}, {120,9,-100}, {80,9,-100}, {100,9,-80}, {100,9,-120},
        {120.001f,9,-100}, {79.999f,9,-100}, {100,9,-79.999f}, {100,9,-120.001f},
        {100,99999,-100}, {120,9,-120}, {140,9,-140}
    };
    for (int status = 0; status < 6; ++status)
    for (int golden = 0; golden <= 2; ++golden)
    for (unsigned p = 0; p < sizeof(positions)/sizeof(*positions); ++p)
    for (int roll = 0; roll < 10; ++roll) {
        af_test_dig_previous = origin; source_status = status; source_item = 0x4321;
        next_random = (roll + 0.5f) / 10.0f;
        int diff = (p >= 5 && p <= 8) || p == 11;
        int eligible = status == 3 && golden == 1 && diff;
        int bonus = eligible && roll == 1;
        check(positions[p], golden, bonus ? 5 : status, eligible, bonus ? 0x2103 : source_item);
    }
    /* Original ordinary digs suppress farming the same spot with a gold tool. */
    af_test_dig_previous = (DigPosition){0,0,0}; source_status = 3; source_item = 0;
    next_random = 0.15f;
    check(origin, 0, 3, 0, 0);
    check(origin, 1, 3, 0, 0);
    check((DigPosition){140,9,-100}, 1, 5, 1, 0x2103);
    check((DigPosition){140,9,-100}, 1, 3, 0, 0);
    /* The exact RNG endpoints retain C truncation semantics. */
    const float samples[] = {0.0f,0.09999f,0.1f,0.19999f,0.2f,0.99999f};
    for (unsigned i=0;i<sizeof(samples)/sizeof(*samples);++i) {
        af_test_dig_previous = (DigPosition){0,0,0}; next_random = samples[i];
        int bonus = i == 2 || i == 3;
        check(origin, 1, bonus ? 5 : 3, 1, bonus ? 0x2103 : 0);
    }
    puts("Source shovel status, strict position bounds, RNG, ordinary digs, and output guards pass");
    return 0;
}
