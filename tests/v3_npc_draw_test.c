#include <assert.h>
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include "../overlays/v3/npc_draw.c"

struct ImportDraw af_v3_draws[20];
static u16 event_data[2];
static int event_enabled, dma_calls, dma_bad;
static u32 last_vrom;
const u16 *af_v3_event(u32 name) {
    assert((name & 0xF000u) == 0xD000u);
    return event_enabled ? event_data : 0;
}
int af_v3_draw_dma(void *dest, u32 vrom, u32 size) {
    assert((uintptr_t)dest % 8 == 0);
    assert(size == 100 && vrom >= 0xE05008 && vrom < 0xE05008 + 327 * 100);
    last_vrom = vrom; ++dma_calls;
    if (dma_bad) return -1;
    memset(dest, 0x6C, size);
    return 0;
}
int main(void) {
    u8 guarded[102];
    memset(guarded, 0xA5, sizeof(guarded));
    for (u32 i = 0; i < 327; ++i) {
        u32 actor = i < 218 ? 0xE000 + i : 0xD000 + i - 218;
        assert(af_v3_npc_draw(guarded + 1, actor));
        assert(last_vrom == 0xE05008 + i * 100);
        assert(guarded[0] == 0xA5 && guarded[101] == 0xA5);
    }
    for (u32 i = 0; i < 20; ++i) {
        struct ImportDraw *row = &af_v3_draws[i];
        row->actor = 0xE0DA + i; row->voice = 270 + i;
        memset(row->draw, i, 100);
        row->draw[2] = 1; row->draw[3] = 410 + i - 256; row->draw[95] = 255;
        assert(af_v3_npc_draw(guarded + 1, 0x12340000u | row->actor));
        assert(!memcmp(guarded + 1, row->draw, 100));
        assert(af_v3_npc_voice(guarded + 1) == row->voice);
        assert(guarded[0] == 0xA5 && guarded[101] == 0xA5);
    }
    assert(dma_calls == 327);
    event_enabled = 1; event_data[1] = 0xE0ED;
    assert(af_v3_npc_draw(guarded + 1, 0xD000));
    assert(!memcmp(guarded + 1, af_v3_draws[19].draw, 100));
    event_data[1] = 0xE0D9;
    assert(af_v3_npc_draw(guarded + 1, 0xD000) && last_vrom == 0xE05008 + 217 * 100);
    event_data[1] = 0xD002;
    assert(af_v3_npc_draw(guarded + 1, 0xD000) && last_vrom == 0xE05008 + 220 * 100);
    event_enabled = 0;
    memset(guarded, 0xA5, sizeof(guarded));
    af_v3_draws[0].actor = 0;
    const u32 bad[] = {0xE0DA, 0xE0EE, 0xEFFF, 0xD06D, 0xDFFF, 0, 0xFFFF};
    for (u32 i = 0; i < sizeof(bad) / sizeof(bad[0]); ++i) {
        assert(!af_v3_npc_draw(guarded + 1, bad[i]));
        for (u32 j = 0; j < sizeof(guarded); ++j) assert(guarded[j] == 0xA5);
    }
    assert(!af_v3_npc_draw(0, 0xE000));
    dma_bad = 1; assert(!af_v3_npc_draw(guarded + 1, 0xE000));
    for (u32 i = 0; i < 256; ++i) {
        guarded[95] = i;
        assert(af_v3_npc_voice(guarded) == i);
    }
    puts("V3 native/special/event draw routes, guards, missing slots, and full voice IDs pass");
    return 0;
}
