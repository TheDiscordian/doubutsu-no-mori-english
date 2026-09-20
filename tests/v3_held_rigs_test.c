#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/held_rigs.c"

static uint64_t storage[0x13B0 / 8], game_storage[0x200 / 8], graph_storage[0x400 / 8];
static void *actor = storage, *game = game_storage, *graph = graph_storage;
static int kind, wade, wind_angle, animation_calls, setup_calls, smoothing_calls;
static int pushed, matrix_angle, drawn;
static float wind_power, target_seen, setup_speed, setup_morph, setup_frame;
static int setup_animation, setup_item;
static Vec3 point;
static u32 commands[32];
#ifdef AF_V3_BALLOON
static int paused, reflections, hand_matrices, balloon_draws;
static Vec3 translated, scaled;
static int rotations[4], rotation_count;
static float native_sin(int value) { return sinf(value * (3.14159265358979323846f / 32768.0f)); }
static void approach_angle(s16 *value, s16 target, float fraction, s16 maximum, s16 minimum) {
    assert(minimum == 0 && maximum > 0);
    s16 difference = (s16)(target - *value);
    int step = (int)(fraction * difference);
    if (step > maximum) step = maximum;
    if (step < -maximum) step = -maximum;
    *value = (s16)(*value + step);
}
static int is_paused(void *g) { assert(g == game); return paused; }
static void translate(float x, float y, float z, int mode) {
    assert(mode == 0 && pushed == 1); translated = (Vec3){x,y,z};
}
static void scale(float x, float y, float z, int mode) {
    assert(mode == 1 && pushed == 1); scaled = (Vec3){x,y,z};
}
static void hand_matrix(void *p) { assert(p == (u8 *)actor + 0x1054); ++hand_matrices; }
static void reflect(Vec3 *p, void *g) {
    assert(p == (Vec3 *)((u8 *)actor + 0x103C) && g == game); ++reflections;
}
#endif
#ifdef AF_V3_PINWHEEL_SOUND
float af_test_loop_level;
u8 af_test_level_rows[120];
static int sound_calls, volume_calls;
static u32 volume_command;
static float volume_seen;
static void sound_position(void *identity, int id, void *position_) {
    assert(identity == actor && id == AF_V3_PINWHEEL_SOUND && position_ == (u8 *)actor + 0x28);
    ++sound_calls;
}
static void queue_volume(u32 command, float volume) {
    volume_command = command; volume_seen = volume; ++volume_calls;
}
#endif

static int item_kind(void *a, int action) {
    assert(a == actor && action == WORD(actor, 0xD00)); return kind;
}
static int item_animation(int k) { assert(k == kind); return 58; }
void af_v3_held_setup_original(void *a, int animation, int item, float speed,
                              float morph, float frame, int *out, int *part) {
    assert(a == actor); ++setup_calls;
    setup_animation = animation; setup_item = item; setup_speed = speed;
    setup_morph = morph; setup_frame = frame; *out = 261; *part = 3;
#ifdef AF_V3_BALLOON
    WORD(actor, 0xCFC) = kind >= 91 && kind <= 98 ? 21 : 0;
    REAL(actor, 0xA18) = 1; REAL(actor, 0xA1C) = REAL(actor, 0xA20) = 27;
    REAL(actor, 0xA24) = speed;
    REAL(actor, 0xA28) = frame < 0 ? REAL(actor, 0xA28) : frame;
    WORD(actor, 0xA2C) = 1;
#endif
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
static void rotate(int angle, int mode) {
    assert(mode == 1 && pushed); matrix_angle = angle;
#ifdef AF_V3_BALLOON
    if (WORD(actor, 0xCFC) == 21) {
        assert(rotation_count < 4); rotations[rotation_count++] = angle;
    }
#endif
}
static u32 matrix(void *g) { assert(g == graph); return 0x80301000; }
static void position(Vec3 *p) { *p = point; }
static void *current_matrix(void) { return graph; }
static void angle(void *m, Angle3 *a, int mode) {
    assert(m == graph && !mode); a->x = 0x1000; a->y = 0x2000; a->z = 0x3000;
}
static void draw(void *g, void *kf, void *matrices, JointCallback before, JointCallback after, void *a) {
    assert(g == game && kf == (u8 *)actor + 0xA18 && a == actor && !before);
    assert(matrices == (u8 *)actor + 0xAE0 + (WORD(game, 0xA0) & 1) * 256);
    assert(commands[0] == 0xDA380003 && commands[1] == 0x80301000);
    assert(*(u32 **)((u8 *)graph + 0x298) == commands + 2 && pushed == 1);
#ifdef AF_V3_BALLOON
    if (WORD(actor, 0xCFC) == 21) { assert(!after); ++balloon_draws; return; }
#endif
    assert(after);
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
#ifdef AF_V3_BALLOON
    case 0x80099A94: return native_sin;
    case 0x8009A974: return approach_angle;
    case 0x8009AD98: return is_paused;
    case 0x800E0260: return hand_matrix;
    case 0x800E0314: return translate;
    case 0x800E041C: return scale;
    case 0x800E0500: case 0x800E0834: return rotate;
    case 0x800588B8: return reflect;
#endif
#ifdef AF_V3_PINWHEEL_SOUND
    case 0x800D1D08: return sound_position;
    case 0x800EEDFC: return queue_volume;
#endif
    default: assert(!"Unknown native held-rig API"); return NULL;
    }
}
static void near(float actual, float expected) { assert(fabsf(actual - expected) < 0.0001f); }
static void reset(void) {
    memset(storage, 0, sizeof(storage)); memset(game_storage, 0, sizeof(game_storage));
    memset(graph_storage, 0, sizeof(graph_storage)); memset(commands, 0, sizeof(commands));
    *(void **)game = graph; *(u32 **)((u8 *)graph + 0x298) = commands;
    memset((u8 *)actor + 0x1310, 0xA5, 16);
    memset((u8 *)actor + 0x13A0, 0xA5, 16);
    kind = 99; wade = wind_angle = animation_calls = setup_calls = smoothing_calls = 0;
    pushed = drawn = 0; wind_power = 0.0f;
    *(signed char *)((u8 *)actor + 0x1117) = -1;
#ifdef AF_V3_PINWHEEL_SOUND
    af_test_loop_level = 0; sound_calls = volume_calls = 0;
    memset(af_test_level_rows, 0, sizeof(af_test_level_rows));
#endif
#ifdef AF_V3_BALLOON
    paused = reflections = hand_matrices = balloon_draws = rotation_count = 0;
#endif
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
#ifdef AF_V3_PINWHEEL_SOUND
    reset();
    const float speeds[] = {0, 22, -44, 88, -176, 0};
    const float gains[] = {0, .25f, .5f, 1, 1, 1};
    for (unsigned i = 0; i < sizeof(speeds) / sizeof(speeds[0]); ++i) {
        REAL(actor, 0xA24) = speeds[i];
        af_v3_held_pinwheel_sound(actor); near(af_test_loop_level, gains[i]);
    }
    assert(sound_calls == 4); /* No registration/refresh at zero speed. */
    af_test_loop_level = .25f;
    for (unsigned channel = 0; channel < 256; ++channel) {
        memset(af_test_level_rows, 0, sizeof(af_test_level_rows));
        if (channel >= 8 && channel < 14) af_test_level_rows[(channel - 8) * 20] = AF_V3_PINWHEEL_SOUND;
        u32 command = 0x01000000u | (channel << 8);
        af_v3_held_loop_volume(command, .8f);
        assert(volume_command == command);
        near(volume_seen, channel >= 8 && channel < 14 ? .2f : .8f);
        memset(af_test_level_rows, 0x4C, sizeof(af_test_level_rows));
        af_v3_held_loop_volume(command, .8f); near(volume_seen, .8f);
    }
    assert(volume_calls == 512);
    reset(); wind_power = 1; af_v3_held_pinwheel_main(actor, game);
    assert(sound_calls == 1); near(af_test_loop_level, 1.2f / 88);
#endif
#ifdef AF_V3_BALLOON
    for (int k = 91; k <= 98; ++k) {
        reset(); kind = k; SHORT(actor, 0xDC) = 400;
        memset(BALLOON(actor), 0xA5, sizeof(BalloonState));
        af_v3_held_setup(actor, 6, 49, 1, -4, -1, &out, &part);
        BalloonState *s = BALLOON(actor);
        assert(s->lean == -400 && s->stop && !s->second_step);
        near(s->z_velocity, 30); near(REAL(actor, 0xA28), 27);
        near(REAL(actor, 0xA20), 27); near(REAL(actor, 0xA18), 1);
        near(REAL(actor, 0xA24), 0); assert(WORD(actor, 0xA2C) == 0);
        s->extra_x = 123;
        af_v3_held_setup(actor, 6, 49, 1, -4, -1, &out, &part);
        assert(s->extra_x == 123); /* Same category does not reset source state. */
        REAL(actor, 0xA24) = 0; REAL(actor, 0xDF0) = 1;
        REAL(actor, 0x5C) = .01f; REAL(actor, 0x60) = .02f; REAL(actor, 0x64) = .03f;
        point = (Vec3){10,20,30}; af_v3_held_hand_position(actor);
        assert(hand_matrices == 1); near(s->hand_move.x, 10); near(s->hand_move.y, 20);
        af_v3_held_balloon_main(actor, game); assert(s->second_step);
        af_v3_held_balloon_draw(actor, game);
        assert(!s->second_step && !s->stop && !pushed && reflections == 1 && balloon_draws == 1);
        near(REAL(actor, 0xA28), 26.915f); near(REAL(actor, 0xA24), -.0810415f);
        near(REAL(actor, 0xA20), 27); near(translated.z, 30); near(scaled.y, .02f);
        assert(rotations[0] == 0 && rotations[2] == 0x4000 && animation_calls == 1);
        point = (Vec3){12,19,33}; af_v3_held_hand_position(actor);
        near(s->hand_move.x, 2); near(s->hand_move.y, -1); near(s->hand_move.z, 3);
        for (int frame = 0; frame < 1000; ++frame) {
            WORD(actor, 0xCF0) = frame & 1 ? 8 : 9; REAL(actor, 0x74) = 2;
            WORD(game, 0xA0) = frame; rotation_count = 0;
            *(u32 **)((u8 *)graph + 0x298) = commands;
            af_v3_held_balloon_main(actor, game); af_v3_held_balloon_draw(actor, game);
            assert(isfinite(REAL(actor, 0xA28)) && REAL(actor, 0xA28) >= 14 && REAL(actor, 0xA28) <= 27);
            assert(s->angle.z >= -0x800 && s->angle.z <= 0x800 && !pushed);
        }
        BalloonState snapshot = *s;
        float old_frame = REAL(actor, 0xA28), old_speed = REAL(actor, 0xA24);
        paused = 1; rotation_count = 0; *(u32 **)((u8 *)graph + 0x298) = commands;
        af_v3_held_balloon_draw(actor, game);
        assert(!memcmp(s, &snapshot, sizeof(snapshot)));
        near(REAL(actor, 0xA28), old_frame); near(REAL(actor, 0xA24), old_speed);
        paused = 0; REAL(actor, 0xDF0) = .5f; rotation_count = 0;
        *(u32 **)((u8 *)graph + 0x298) = commands;
        af_v3_held_balloon_draw(actor, game); assert(s->angle.z == 0);
        WORD(actor, 0xCFC) = 0; snapshot = *s;
        af_v3_held_hand_position(actor); assert(!memcmp(s, &snapshot, sizeof(snapshot)));
        for (int i = 0; i < 16; ++i) {
            assert(*((u8 *)actor + 0x1310 + i) == 0xA5);
            assert(*((u8 *)actor + 0x13A0 + i) == 0xA5);
        }
    }
#endif
    puts("held rig setup, timing, movement/wind, drawing callbacks, and bounds pass");
    return 0;
}
