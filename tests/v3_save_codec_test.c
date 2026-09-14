#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/save_codec.c"

int main(void) {
    struct { u8 pre[16], data[AF_SAVE_BANK], post[16]; } bank;
    struct { u8 pre[16], data[AF_SAVE_STATE], post[16]; } state, output;
    u8 profile[AF_SAVE_PROFILE], saved[AF_SAVE_BANK];
    memset(&bank, 0xA5, sizeof(bank));
    memset(&state, 0xA5, sizeof(state));
    memset(&output, 0xA5, sizeof(output));
    memset(profile, 0xFF, sizeof(profile));
    memcpy(state.data, profile, sizeof(profile));
    memset(state.data + AF_SAVE_PROFILE, 0, AF_SAVE_CATALOGUE);
    bank.data[8] = bank.data[0x2F68] = 0x30;
    bank.data[9] = bank.data[0x2F69] = 0x12;
    for (u32 player = 0; player < 4; ++player) {
        for (u32 group = 0; group < 1024; ++group) {
            u32 item = 0x3000 + group * 4;
            assert(af_v3_save_collect(state.data, player, item, 0) == 0);
            assert(af_v3_save_collect(state.data, player, item + (group & 3), 1) == 1);
            for (u32 rotation = 0; rotation < 4; ++rotation)
                assert(af_v3_save_collect(state.data, player, item + rotation, 0) == 1);
        }
    }
    assert(af_v3_save_pack(bank.data, AF_SAVE_BANK, state.data) == AF_SAVE_OK);
    memcpy(saved, bank.data, sizeof(saved));
    assert(af_v3_save_check(bank.data, AF_SAVE_BANK, profile, output.data) == AF_SAVE_OK);
    assert(!memcmp(state.data, output.data, AF_SAVE_STATE));
    assert(!memcmp(saved, bank.data, sizeof(saved)));
    assert(af_v3_save_check(0, AF_SAVE_BANK, profile, 0) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_check(bank.data, AF_SAVE_PAYLOAD, profile, 0) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_check(bank.data, AF_SAVE_BANK, 0, 0) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_check(bank.data, AF_SAVE_BANK, profile, bank.data + AF_SAVE_PAYLOAD) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_check(bank.data, AF_SAVE_BANK, state.data, state.data) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_pack(bank.data, AF_SAVE_BANK, bank.data + AF_SAVE_PAYLOAD) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_pack(bank.data, AF_SAVE_BANK - 1, state.data) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_pack(0, AF_SAVE_BANK, state.data) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_pack(bank.data, AF_SAVE_BANK, 0) == AF_SAVE_ARGUMENT);
    assert(!memcmp(saved, bank.data, sizeof(saved)));
    assert(af_v3_save_collect(0, 0, 0x3224, 1) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_collect(state.data, 4, 0x3224, 1) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_collect(state.data, 0, 0x2FFF, 1) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_collect(state.data, 0, 0x4000, 1) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_collect(state.data, 0, 0x13224, 1) == AF_SAVE_ARGUMENT);
    assert(af_v3_save_collect(state.data, 0, 0x3224, 2) == AF_SAVE_ARGUMENT);
    for (u32 i = 0; i < 16; ++i) {
        assert(bank.pre[i] == 0xA5 && bank.post[i] == 0xA5);
        assert(state.pre[i] == 0xA5 && state.post[i] == 0xA5);
        assert(output.pre[i] == 0xA5 && output.post[i] == 0xA5);
    }
    puts("Four players, all 1024 groups/rotations, invalid arguments, overlap checks, and guards pass");
}
