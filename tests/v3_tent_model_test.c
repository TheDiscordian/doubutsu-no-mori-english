#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/tent_model.c"

static _Alignas(32) u8 arena[8192], bank[4288];
static TentGfx graphics;
static unsigned matrices, flushes;
void *_Matrix_to_Mtx(void *destination) {
    assert((u8 *)destination == graphics.tail && ((uptr)destination & 31) == 0);
    memset(destination, 0x7B, 64); ++matrices; return destination;
}
void osWritebackDCache(void *address, int bytes) {
    assert(address == graphics.tail && bytes == 96);
    for (int i = 0; i < 64; ++i) assert(((u8 *)address)[i] == 0x7B);
    ++flushes;
}
static float step(float value, int on) {
    float target = on == 1 ? 1.0f : 0.0f;
    if (value > target) { value -= 0.1f; if (value < target) value = target; }
    else if (value < target) { value += 0.1f; if (value > target) value = target; }
    return value;
}
static void palette_is(const u16 *palette, float fade) {
    const u16 *on = (const u16 *)(bank + 32), *off = (const u16 *)(bank + 64);
    for (int i = 0; i < 16; ++i) {
        int r = (off[i] >> 11) + fade * ((int)(on[i] >> 11) - (off[i] >> 11));
        int g = (off[i] >> 6 & 31) + fade * ((int)(on[i] >> 6 & 31) - (off[i] >> 6 & 31));
        int b = (off[i] >> 1 & 31) + fade * ((int)(on[i] >> 1 & 31) - (off[i] >> 1 & 31));
        assert(palette[i] == (r << 11 | g << 6 | b << 1 | (off[i] & 1)));
        if (i != 7) assert(palette[i] == off[i]);
    }
}
static const u16 *draw(Tent *actor) {
    TentGame game = {&graphics};
    Command *head = graphics.head;
    u8 *tail = graphics.tail;
    unsigned before = matrices;
    af_v3_tent_model_dw(actor, 0, &game, bank);
    assert(matrices == before + 1 && matrices == flushes);
    assert(graphics.head == head + 6 && tail - graphics.tail >= 96 && tail - graphics.tail <= 112);
    assert(head[0].a == 0xDA380003 && head[0].b == (u32)(uptr)graphics.tail);
    assert(head[1].a == 0xDB060020 && head[1].b == (u32)(uptr)(graphics.tail + 64));
    const u32 expected[] = {0x06000C50, 0x06000D18, 0x06000E00, 0x06000FF0};
    for (int i = 0; i < 4; ++i) assert(head[i + 2].a == 0xDE000000 && head[i + 2].b == expected[i]);
    palette_is((const u16 *)(graphics.tail + 64), actor->fade.f);
    return (const u16 *)(graphics.tail + 64);
}
int main(int argc, char **argv) {
    assert(argc == 2);
    FILE *file = fopen(argv[1], "rb"); assert(file);
    assert(fread(bank, 1, sizeof bank, file) == sizeof bank && fgetc(file) == EOF);
    assert(!fclose(file));
    /* The native C callback reads native-endian u16s. Decode the supplied
     * converted big-endian endpoints for this host execution only. */
    for (int i = 0; i < 96; i += 2) {
        u16 value = bank[i] * 256u + bank[i + 1]; memcpy(bank + i, &value, 2);
    }
    Tent actors[2], original;
    memset(actors, 0xA5, sizeof actors); memset(arena, 0xA5, sizeof arena);
    graphics.head = (Command *)(arena + 32); graphics.tail = arena + sizeof arena - 32;
    for (int i = 0; i < 2; ++i) {
        actors[i].switch_bit = i; original = actors[i];
        af_v3_tent_model_ct(actors + i, bank);
        assert(actors[i].fade.f == (float)i);
        original.fade = actors[i].fade; assert(!memcmp(&original, actors + i, sizeof original));
    }
    const u16 *first = draw(actors), *second = draw(actors + 1);
    assert(first != second); palette_is(first, 0); palette_is(second, 1);
    float expected[2] = {0, 1};
    for (int frame = 0; frame < 24; ++frame) {
        for (int i = 0; i < 2; ++i) {
            actors[i].switch_bit = (frame < 4 || frame >= 8) ? !i : i;
            expected[i] = step(expected[i], actors[i].switch_bit);
            original = actors[i];
            af_v3_tent_model_mv(actors + i, 0, 0, bank);
            assert(actors[i].fade.f == expected[i]);
            original.fade = actors[i].fade; assert(!memcmp(&original, actors + i, sizeof original));
            draw(actors + i);
        }
        palette_is(first, 0); palette_is(second, 1);
    }
    assert(actors[0].fade.f == 1 && actors[1].fade.f == 0);
    actors[0].switch_bit = 2;
    af_v3_tent_model_ct(actors, bank); assert(actors[0].fade.f == 0);
    for (int i = 0; i < 2; ++i) af_v3_tent_model_dt(actors + i, bank);
    palette_is(first, 0); palette_is(second, 1);
    TentGame game = {&graphics};
    for (int available = 0; available <= 176; available += 8) {
        memset(arena + 32, 0xA5, 256);
        graphics.head = (Command *)(arena + 32); graphics.tail = arena + 32 + available;
        Command *head = graphics.head; u8 *tail = graphics.tail;
        uptr allocation = available >= 96 ? ((uptr)tail - 96) & ~(uptr)31 : 0;
        int fits = !((uptr)tail & 15) && available >= 144 && allocation >= (uptr)head + 48;
        unsigned before = matrices;
        af_v3_tent_model_dw(actors, 0, &game, bank);
        if (fits) assert(matrices == before + 1 && graphics.head == head + 6);
        else {
            assert(matrices == before && graphics.head == head && graphics.tail == tail);
            for (int i = 32; i < 288; ++i) assert(arena[i] == 0xA5);
        }
    }
    for (int i = 0; i < 32; ++i) assert(arena[i] == 0xA5 && arena[sizeof arena - 1 - i] == 0xA5);
    puts("Tent source palettes, independent fades, frame lifetime, six commands, bounds, and actor guards pass");
}
