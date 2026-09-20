#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/held_rigs.c"

static uint64_t storage[0x1320 / 8], game_storage[0x200 / 8], graph_storage[0x400 / 8];
static void *actor = storage, *game = game_storage, *graph = graph_storage;
static int kind, wade, wind_angle, animation_calls, setup_calls, smoothing_calls;
static int pushed, matrix_angle, drawn;
static float wind_power, target_seen, setup_speed, setup_morph, setup_frame;
static int setup_animation, setup_item;
static Vec3 point;
static u32 commands[32];

static int item_kind(void *a, int action) {
    assert(a == actor && action == WORD(actor, 0xD00)); return kind;
}
static int item_animation(int k) { assert(k == kind); return 58; }
void af_v3_held_setup_original(void *a, int animation, int item, float speed,
                              float morph, float frame, int *out, int *part) {
    assert(a == actor); ++setup_calls;
    setup_animation = animation; setup_item = item; setup_speed = speed;
    setup_morph = morph; setup_frame = frame; *out = 261; *part = 3;
}
static float native_cos(int angle) {
    if (!(angle & 0x3FFF)) return (s16)angle == 0 ? 1.0f : (s16)angle == -32768 ? -1.0f : 0.0f;
    return cosf(angle * (3.14159265358979323846f / 32768.0f));
}
static s16 native_atan(float x, float y) {
    return (s16)(int)(atan2f(y, x) * (32768.0f / 3.14159265358979323846f));
}
static int all_wade(void *g) { assert(g == game); return wade; }
static float wind(void) { return wind_power; }
static int direction(void) { return wind_angle; }
static float approach(float *v, float target, float fraction, float step, float minimum) {
    ++smoothing_calls; target_seen = target;
    float delta = target - *v, change = fraction * delta;
    if (delta != 0.0f) {
        float magnitude = fminf(step, fmaxf(minimum, fabsf(change)));
        *v += copysignf(fminf(fabsf(delta), magnitude), delta);
    }
    return target - *v;
}
static void animate(void *a) { assert(a == actor); ++animation_calls; }
static void push(void) { ++pushed; }
static void pull(void) { assert(pushed == 1); --pushed; }
static void rotate(int angle, int mode) { assert(mode == 1 && pushed); matrix_angle = angle; }
static u32 matrix(void *g) { assert(g == graph); return 0x80301000; }
static void position(Vec3 *p) { *p = point; }
static void *current_matrix(void) { return graph; }
static void angle(void *m, Angle3 *a, int mode) {
    assert(m == graph && !mode); a->x = 0x1000; a->y = 0x2000; a->z = 0x3000;
}
static void draw(void *g, void *kf, void *matrices, JointCallback before, JointCallback after, void *a) {
    assert(g == game && kf == (u8 *)actor + 0xA18 && a == actor && !before && after);
    assert(matrices == (u8 *)actor + 0xAE0 + (WORD(game, 0xA0) & 1) * 256);
    assert(commands[0] == 0xDA380003 && commands[1] == 0x80301000);
    assert(*(u32 **)((u8 *)graph + 0x298) == commands + 2 && pushed == 1);
    RigState snapshot = *STATE(actor);
    for (int j = -1; j <= 3; ++j) {
        assert(after(g, kf, j, NULL, NULL, a, NULL, NULL) == 1);
        if (j < 2) assert(memcmp(&snapshot, STATE(actor), sizeof(snapshot)) == 0);
    }
    ++drawn;
}
void *af_test_rig_function(u32 at) {
    switch (at) {
    case 0x808BD5C4: return item_kind;
    case 0x808BD6E0: return item_animation;
    case 0x80099A54: return native_cos;
    case 0x800E0008: return native_atan;
    case 0x800B6074: return all_wade;
    case 0x80098980: return wind;
    case 0x8009895C: return direction;
    case 0x8009A570: return approach;
    case 0x808BD81C: return animate;
    case 0x800E020C: return push;
    case 0x800E0244: return pull;
    case 0x800E0698: return rotate;
    case 0x800E13C4: return matrix;
    case 0x800E14D4: return position;
    case 0x800E02AC: return current_matrix;
    case 0x800E1AA0: return angle;
    case 0x800530D8: return draw;
    default: assert(!"Unknown native held-rig API"); return NULL;
    }
}
static void near(float actual, float expected) { assert(fabsf(actual - expected) < 0.0001f); }
static void reset(void) {
    memset(storage, 0, sizeof(storage)); memset(game_storage, 0, sizeof(game_storage));
    memset(graph_storage, 0, sizeof(graph_storage)); memset(commands, 0, sizeof(commands));
    *(void **)game = graph; *(u32 **)((u8 *)graph + 0x298) = commands;
    memset((u8 *)actor + 0x1310, 0xA5, 16);
    kind = 99; wade = wind_angle = animation_calls = setup_calls = smoothing_calls = 0;
    pushed = drawn = 0; wind_power = 0.0f;
    *(signed char *)((u8 *)actor + 0x1117) = -1;
}
int main(void) {
    int out, part;
    for (int k = -1; k < 115; ++k) {
        reset(); kind = k; memset(STATE(actor), 0xA5, sizeof(RigState));
        af_v3_held_setup(actor, 6, 2, 1.0f, -4.0f, -1.0f, &out, &part);
        assert(setup_calls == 1 && setup_animation == 6 && out == 261 && part == 3);
        if (k >= 99 && k <= 106) {
            RigState zero = {0}; assert(!memcmp(STATE(actor), &zero, sizeof(zero)));
            assert(setup_item == 58 && setup_speed == 0 && setup_morph == 0 && setup_frame == 1);
            *(signed char *)((u8 *)actor + 0x1117) = (signed char)k;
            REAL(actor, 0xA24) = -3.0f; REAL(actor, 0xA28) = 8.5f; STATE(actor)->valid = 1;
            af_v3_held_setup(actor, 6, 2, 1, -4, -1, &out, &part);
            assert(setup_speed == -3 && setup_frame == 8.5f && STATE(actor)->valid == 1);
            kind = k == 106 ? 99 : k + 1;
            af_v3_held_setup(actor, 6, 2, 1, -4, -1, &out, &part);
            assert(setup_speed == 0 && setup_frame == 1 && STATE(actor)->valid == 1);
        } else {
            assert(setup_item == 2 && setup_speed == 1 && setup_morph == -4 && setup_frame == -1);
            assert(STATE(actor)->valid == 0);
        }
        for (int i = 0; i < 16; ++i) assert(*((u8 *)actor + 0x1310 + i) == 0xA5);
    }
    reset(); wind_power = 1;
    assert(!af_v3_held_pinwheel_main(actor, game)); near(target_seen, 10); near(REAL(actor, 0xA24), 1.2f);
    assert(animation_calls == 1 && smoothing_calls == 2 && STATE(actor)->distance == 0);
    reset(); wind_power = 1; wind_angle = -32768;
    af_v3_held_pinwheel_main(actor, game); near(target_seen, -10); near(REAL(actor, 0xA24), -1.2f);
    reset(); STATE(actor)->valid = 1; STATE(actor)->current.z = 4; REAL(actor, 0x28) = 1;
    af_v3_held_pinwheel_main(actor, game); near(target_seen, 16); near(REAL(actor, 0xA24), 1.56f);
    wind_power = 1; wind_angle = -32768;
    af_v3_held_pinwheel_main(actor, game); near(target_seen, 16); /* Opposing wind is omitted. */
    wade = 1; wind_power = 0; af_v3_held_pinwheel_main(actor, game); near(target_seen, 0);
    wade = 0; REAL(actor, 0x28) = 0; af_v3_held_pinwheel_main(actor, game); near(target_seen, 0);
    REAL(actor, 0xDF8) = 1; af_v3_held_pinwheel_main(actor, game); near(target_seen, 16);
    STATE(actor)->current.z = 10000; af_v3_held_pinwheel_main(actor, game);
    assert(isfinite(REAL(actor, 0xA24)) && target_seen > 1000);
    reset(); REAL(actor, 0xA24) = 2; af_v3_held_pinwheel_main(actor, game); near(REAL(actor, 0xA24), 1.8f);
    reset(); SHORT(actor, 0xDC) = 7; point = (Vec3){10, 20, 30}; WORD(actor, 0xF44) = 1;
    af_v3_held_pinwheel_draw(actor, game);
    assert(drawn == 1 && !pushed && matrix_angle == -3 && !WORD(actor, 0xF44));
    assert(STATE(actor)->valid && !memcmp(&STATE(actor)->previous, &point, sizeof(point)));
    assert(STATE(actor)->angle.x == -0x1000 && STATE(actor)->angle.y == (s16)0xA000);
    WORD(game, 0xA0) = 1; point.z = 35; *(u32 **)((u8 *)graph + 0x298) = commands;
    af_v3_held_pinwheel_draw(actor, game);
    near(STATE(actor)->previous.z, 30); near(STATE(actor)->current.z, 35);
    assert(drawn == 2 && !pushed);
    puts("held rig setup, timing, movement/wind, drawing callbacks, and bounds pass");
    return 0;
}
