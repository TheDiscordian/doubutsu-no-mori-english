#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/accessory.c"

struct Row af_accessory_rows[20];
u16 af_accessory_draws[1040];
int af_accessory_ready = 1;
u32 af_accessory_segments[16];
static float current[16], saved[4][16], captured[16];
static int depth, skeleton_calls, setups, callbacks, skip_joint, direct;
static _Alignas(16) u8 actor[0x100];
static _Alignas(16) struct Gfx buffer[128];
static struct Graph graph;
static struct Graph *game = &graph;

static int original_before(void *g, void *s, int j, void *sh, void *f, void *a, void *r, void *p) {
    assert(g == &game && s == actor && a == actor && sh == &graph && f == buffer && r == actor && p == actor);
    assert(j == 13 || j == 25); ++callbacks;
    return 7;
}
static int original_after(void *g, void *s, int j, void *sh, void *f, void *a, void *r, void *p) {
    assert(original_before(g, s, j, sh, f, a, r, p) == 7);
    return 9;
}
void af_accessory_skeleton(void *g, void *s, void *m, Callback b, Callback a, void *arg) {
    ++skeleton_calls;
    if (direct) assert(arg == actor && b == original_before && a == original_after);
    if (!m) return;
    for (int j = 13; j <= 25; j += 12) {
        if (j == skip_joint) continue;
        assert(b(g, s, j, &graph, buffer, arg, actor, actor) == 7);
        assert(a(g, s, j, &graph, buffer, arg, actor, actor) == 9);
    }
}
void af_accessory_push(void) { assert(depth < 4); memcpy(saved[depth++], current, sizeof(current)); }
void af_accessory_pop(void) { assert(depth > 0); memcpy(current, saved[--depth], sizeof(current)); }
void af_accessory_get(float *p) { memcpy(p, current, sizeof(current)); }
void af_accessory_put(const float *p) { memcpy(current, p, sizeof(current)); }
void af_accessory_scale(float x, float y, float z, u8 apply) {
    assert(x == y && x == z && apply == 1);
    for (int i = 0; i < 12; ++i) current[i] *= x;
}
void *af_accessory_matrix(struct Graph *g) {
    assert(g == &graph);
    g->d -= 8;
    memcpy(captured, current, sizeof(current));
    return g->d;
}
void af_accessory_setup(struct Graph *g) { assert(g == &graph); ++setups; g->p += 3; }
static void reset(void) {
    memset(actor, 0, sizeof(actor)); memset(af_accessory_rows, 0, sizeof(af_accessory_rows));
    memset(af_accessory_draws, 0, sizeof(af_accessory_draws));
    memset(buffer, 0xA5, sizeof(buffer));
    af_accessory_ready = 1; depth = skeleton_calls = setups = callbacks = skip_joint = direct = 0;
    for (int i = 0; i < 16; ++i) current[i] = (float)(i+1);
    *(u16 *)(actor+6) = 0xE0DA;
    *(float *)(actor+0x5C) = 0.005f;
    af_accessory_rows[0] = (struct Row){0xE0DA, 432, AF_V3_ACCESSORY_RAM+0x2000, 0x06000080, 25, 1, 0x100};
    af_accessory_draws[0] = 0xE0DA;
    af_accessory_segments[6] = 0x00300000;
    graph.p = buffer; graph.d = buffer+128;
}
static void run(void *mtx) {
    float previous[16]; memcpy(previous, current, sizeof(previous));
    af_v3_accessory_draw(&game, actor, mtx, original_before, original_after, actor);
    assert(depth == 0 && !memcmp(previous, current, sizeof(current)));
    assert(af_accessory_segments[6] == 0x00300000);
}
int main(void) {
    for (int joint = 13; joint <= 25; joint += 12) {
        reset(); af_accessory_rows[0].joint = joint; run(actor);
        assert(skeleton_calls == 1 && callbacks == 4 && setups == 1);
        for (int i = 0; i < 16; ++i) assert(captured[i] == (i+1)*(i < 12 ? 2.0f : 1.0f));
        assert(graph.p == buffer+7 && graph.d == buffer+120);
        assert(buffer[3].w0 == 0xDB060018 && buffer[3].w1 == 0x00475000);
        assert(buffer[4].w0 == 0xDA380003 && buffer[4].w1 == (u32)(uptr)(buffer+120));
        assert(buffer[5].w0 == 0xDE000000 && buffer[5].w1 == 0x06000080);
        assert(buffer[6].w0 == 0xDB060018 && buffer[6].w1 == 0x00300000);
        /* A second frame with no matching joint cannot reuse the first matrix. */
        graph.p = buffer; graph.d = buffer+128; skip_joint = joint; run(actor);
        assert(graph.p == buffer && graph.d == buffer+128 && setups == 1);
    }
    reset(); run(NULL); assert(setups == 0 && graph.p == buffer);
    reset(); graph.d = buffer+15; run(actor); assert(setups == 0 && graph.d == buffer+15);
    reset(); graph.d = buffer+16; run(actor); assert(setups == 1 && graph.d == buffer+8);
    reset(); *(float *)(actor+0x5C) = NAN; run(actor); assert(setups == 0);
    reset(); *(float *)(actor+0x5C) = 0; run(actor); assert(setups == 0);
    for (int failure = 0; failure < 11; ++failure) {
        reset(); direct = 1;
        switch (failure) {
            case 0: af_accessory_ready = 0; break;
            case 1: *(u16 *)(actor+6) = 0xE000; break;
            case 2: af_accessory_draws[0] = 0; break;
            case 3: af_accessory_rows[0].enabled = 0; break;
            case 4: af_accessory_rows[0].bank = 448; break;
            case 5: af_accessory_rows[0].joint = 26; break;
            case 6: af_accessory_rows[0].address++; break;
            case 7: af_accessory_rows[0].address = AF_V3_ACCESSORY_RAM+0xBFE0; break;
            case 8: af_accessory_rows[0].display = 0x07000080; break;
            case 9: af_accessory_rows[0].display = 0x06000100; break;
            case 10: af_accessory_rows[0].bytes = 1; break;
        }
        run(actor); assert(setups == 0 && callbacks == 4 && skeleton_calls == 1);
    }
    puts("attachment transforms, callbacks, frame lifetime, bounds, and state restoration pass");
}
