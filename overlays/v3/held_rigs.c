/* Animated held categories share the existing model/motion banks and native
 * skeleton renderer. Additional transient state belongs to the enlarged player
 * allocation, never to a saved field or another tool's work area.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed short s16;
typedef struct { float x, y, z; } Vec3;
typedef struct { s16 x, y, z; } Angle3;
typedef struct {
    Vec3 previous, current;
    float distance;
    Angle3 parameter, angle;
    int valid;
} RigState;
typedef int (*JointCallback)(void *, void *, int, void *, void *, void *, void *, void *);
typedef char RigStateSize[(sizeof(RigState) == 44) ? 1 : -1];

#ifdef __mips__
static void *native(u32 address) {
    if (address >= 0x808B2D50u)
        address = *(volatile u32 *)0x80143900u - 0x808DD748u + address;
    return (void *)address;
}
static float square_root(float value) {
    float result;
    __asm__("sqrt.s %0,%1" : "=f"(result) : "f"(value));
    return result;
}
#else
extern void *af_test_rig_function(u32);
extern float sqrtf(float);
#define native af_test_rig_function
#define square_root sqrtf
#endif
#define FN(at, result, ...) ((result (*)(__VA_ARGS__))native(at))
#define WORD(p, at) (*(int *)((u8 *)(p) + (at)))
#define REAL(p, at) (*(float *)((u8 *)(p) + (at)))
#define SHORT(p, at) (*(s16 *)((u8 *)(p) + (at)))
#define STATE(p) ((RigState *)((u8 *)(p) + 0x12D8))

#ifdef AF_V3_BALLOON
typedef struct {
    s16 lean;
    Angle3 angle;
    float z_velocity, saved_frame, saved_speed;
    int stop;
    s16 extra_x, counter;
    float drawn_frame;
    Vec3 hand_move;
    int second_step;
} BalloonState;
typedef char BalloonStateSize[(sizeof(BalloonState) == 48) ? 1 : -1];
#define BALLOON(p) ((BalloonState *)((u8 *)(p) + 0x1370))

void af_v3_held_balloon_setup(void *actor, int previous_main) {
    BalloonState *s = BALLOON(actor);
    /* The native frame controller is start/end/duration, not duration/start/end. */
    WORD(actor, 0xA2C) = 0; /* Source balloon initialization uses STOP. */
    if (previous_main != 21) {
        u8 *bytes = (u8 *)s;
        unsigned i;
        for (i = 0; i < sizeof(*s); ++i) bytes[i] = 0;
        s->lean = (s16)-SHORT(actor, 0xDC);
        s->saved_frame = REAL(actor, 0xA20);
        s->stop = 1;
        s->z_velocity = 30.0f;
        REAL(actor, 0xA28) = s->saved_frame;
        REAL(actor, 0xA24) = s->saved_speed;
    }
}
#endif

extern void af_v3_held_setup_original(void *, int, int, float, float, float, int *, int *);

static int pinwheel(int kind) { return (u32)(kind - 99) < 8u; }

void af_v3_held_setup(void *actor, int animation, int item_animation, float speed,
                      float morph, float frame, int *animation_out, int *part_out) {
    int kind = FN(0x808BD5C4u, int, void *, int)(actor, WORD(actor, 0xD00));
    int previous = *(signed char *)((u8 *)actor + 0x1117);
#ifdef AF_V3_BALLOON
    int previous_main = WORD(actor, 0xCFC);
#endif
    RigState *state = STATE(actor);
    if (pinwheel(kind)) {
        if (!pinwheel(previous)) {
            u8 *bytes = (u8 *)state;
            unsigned int i;
            for (i = 0; i < sizeof(*state); ++i) bytes[i] = 0;
        }
        item_animation = FN(0x808BD6E0u, int, int)(kind);
        speed = kind == previous ? REAL(actor, 0xA24) : 0.0f;
        frame = kind == previous ? REAL(actor, 0xA28) : 1.0f;
        morph = 0.0f;
    } else {
        state->valid = 0;
    }
    af_v3_held_setup_original(actor, animation, item_animation, speed, morph,
                              frame, animation_out, part_out);
#ifdef AF_V3_BALLOON
    if (WORD(actor, 0xCFC) == 21) af_v3_held_balloon_setup(actor, previous_main);
#endif
}

static float absolute(float value) { return value < 0.0f ? -value : value; }
static float cosine(s16 angle) { return FN(0x80099A54u, float, int)(angle); }

#ifdef AF_V3_PINWHEEL_SOUND
#ifdef __mips__
#ifdef AF_V3_BALLOON
#define loop_level (*(volatile float *)0x804B1FE0u)
#else
#define loop_level (*(volatile float *)0x804B0FE0u)
#endif
#define level_rows ((const u8 *)0x80113D3Cu)
#else
extern float af_test_loop_level;
extern u8 af_test_level_rows[120];
#define loop_level af_test_loop_level
#define level_rows af_test_level_rows
#endif
/* Only the ordinary level-volume call is adapted. The original pause branch,
 * fade factor, pan, reverb, voice ownership, and expiry remain native. */
void af_v3_held_loop_volume(u32 command, float volume) {
    u32 channel = ((command >> 8) & 255u) - 8u;
    if (channel < 6u && level_rows[channel * 20u] == AF_V3_PINWHEEL_SOUND)
        volume *= loop_level;
    FN(0x800EEDFCu, void, u32, float)(command, volume);
}

void af_v3_held_pinwheel_sound(void *actor) {
    /* Native frame speed spans two source updates, hence 2 * 44. */
    float level = absolute(REAL(actor, 0xA24) / 88.0f);
    if (level > 1.0f) level = 1.0f;
    if (level != 0.0f) {
        loop_level = level;
        FN(0x800D1D08u, void, void *, int, void *)(actor, AF_V3_PINWHEEL_SOUND, (u8 *)actor + 0x28);
    }
}
#endif

int af_v3_held_pinwheel_main(void *actor, void *game) {
    RigState *state = STATE(actor);
    Vec3 delta = {0.0f, 0.0f, 0.0f};
    float target = 0.0f, power, speed, fraction, step, minimum;
    int moved = 0, i;
    if (state->valid) {
        delta.x = state->current.x - state->previous.x;
        delta.y = state->current.y - state->previous.y;
        delta.z = state->current.z - state->previous.z;
    }
    if (delta.x != 0.0f || delta.y != 0.0f || delta.z != 0.0f) {
        float horizontal = delta.x * delta.x + delta.z * delta.z;
        state->distance = square_root(horizontal + delta.y * delta.y);
        state->parameter.x = FN(0x800E0008u, s16, float, float)(square_root(horizontal), delta.y);
        state->parameter.y = FN(0x800E0008u, s16, float, float)(delta.z, delta.x);
    } else {
        state->distance = 0.0f;
        state->parameter.x = state->parameter.y = 0;
    }
    for (i = 0; i < 3; ++i)
        if (REAL(actor, 0x28 + 4 * i) != REAL(actor, 0x3C + 4 * i) ||
            REAL(actor, 0xDF4 + 4 * i) != 0.0f) moved = 1;
    if (moved && !FN(0x800B6074u, int, void *)(game) && state->distance != 0.0f) {
        float projection = absolute(cosine((s16)(state->parameter.x - state->angle.x))) *
                           cosine((s16)(state->parameter.y - state->angle.y));
        /* One N64 update advances twice the source animation interval. */
        target = 8.0f * (0.5f * state->distance * projection);
    }
    power = FN(0x80098980u, float, void)();
    if (power != 0.0f) {
        s16 wind = (s16)FN(0x8009895Cu, int, void)();
        float wind_target = 10.0f * (power * (cosine((s16)(wind - state->angle.y)) *
                            absolute(cosine((s16)-state->angle.x))));
        if (target * wind_target >= 0.0f) target += wind_target;
    }
    fraction = absolute(0.005f * target) + 0.02f;
    minimum = (absolute(0.005f * target) + 0.1f) * 0.5f;
    step = (absolute(0.03f * target) + 0.3f) * 0.5f;
    /* Preserve ordinary source behaviour; a discontinuous position must not
       feed a negative radicand to the animation controller. */
    if (fraction > 1.0f) fraction = 1.0f;
    fraction = 1.0f - square_root(1.0f - fraction);
    speed = 0.5f * REAL(actor, 0xA24);
    for (i = 0; i < 2; ++i)
        FN(0x8009A570u, float, float *, float, float, float, float)
            (&speed, target, fraction, step, minimum);
    REAL(actor, 0xA24) = 2.0f * speed;
    /* This owner helper temporarily binds segment six to the animation bank;
       calling the skeleton player directly would interpret model bytes. */
    FN(0x808BD81Cu, void, void *)(actor);
#ifdef AF_V3_PINWHEEL_SOUND
    af_v3_held_pinwheel_sound(actor);
#endif
    return 0;
}

static int pinwheel_after(void *game, void *keyframe, int joint, void *shape,
                           void *flags, void *actor, void *rotation, void *position) {
    RigState *state = STATE(actor);
    (void)game; (void)keyframe; (void)shape; (void)flags; (void)rotation; (void)position;
    if (joint == 2) {
        void *matrix;
        state->previous = state->current;
        FN(0x800E14D4u, void, Vec3 *)(&state->current);
        matrix = FN(0x800E02ACu, void *, void)();
        FN(0x800E1AA0u, void, void *, Angle3 *, int)(matrix, &state->angle, 0);
        state->angle.x = (s16)-state->angle.x;
        state->angle.y = (s16)(state->angle.y + 0x8000);
    }
    return 1;
}

void af_v3_held_pinwheel_draw(void *actor, void *game) {
    RigState *state = STATE(actor);
    void *graph = *(void **)game;
    u32 **cursor = (u32 **)((u8 *)graph + 0x298);
    u32 *command;
    u32 matrix;
    void *matrices = (u8 *)actor + 0xAE0 + (WORD(game, 0xA0) & 1) * 0x100;
    FN(0x800E020Cu, void, void)();
    FN(0x800E0698u, void, int, int)((s16)(-0.5f * SHORT(actor, 0xDC)), 1);
    matrix = FN(0x800E13C4u, u32, void *)(graph);
    command = *cursor;
    command[0] = 0xDA380003u;
    command[1] = matrix;
    *cursor = command + 2;
    FN(0x800530D8u, void, void *, void *, void *, JointCallback, JointCallback, void *)
        (game, (u8 *)actor + 0xA18, matrices, (JointCallback)0, pinwheel_after, actor);
    FN(0x800E0244u, void, void)();
    WORD(actor, 0xF44) = 0;
    if (!state->valid) {
        state->previous = state->current;
        state->valid = 1;
    }
}

#ifdef AF_V3_BALLOON
static float sine(s16 angle) { return FN(0x80099A94u, float, int)(angle); }

/* Replace the complete native hand-position callback. The matrix and original
 * position retain their native locations; only the missing delta is appended. */
void af_v3_held_hand_position(void *actor) {
    Vec3 *hand = (Vec3 *)((u8 *)actor + 0x103C), previous = *hand;
    FN(0x800E14D4u, void, Vec3 *)(hand);
    if (WORD(actor, 0xCFC) == 21) {
        BalloonState *s = BALLOON(actor);
        s->hand_move.x = hand->x - previous.x;
        s->hand_move.y = hand->y - previous.y;
        s->hand_move.z = hand->z - previous.z;
    }
    FN(0x800E0260u, void, void *)((u8 *)actor + 0x1054);
}

static void balloon_advance(void *actor) {
    BalloonState *s = BALLOON(actor);
    float frame = REAL(actor, 0xA28), max = REAL(actor, 0xA20);
    FN(0x8009A974u, void, s16 *, s16, float, s16, s16)
        (&s->lean, (s16)-SHORT(actor, 0xDC), 1.0f - square_root(.91f), 250, 0);
    s->saved_frame = frame;
    s->saved_speed = REAL(actor, 0xA24);
    frame += s->saved_speed;
    if (frame > max) frame = max;
    else if (frame < .5f * max) frame = .5f * max;
    REAL(actor, 0xA28) = frame;
}

int af_v3_held_balloon_main(void *actor, void *game) {
    (void)game;
    balloon_advance(actor);
    BALLOON(actor)->second_step = 1;
    return 0;
}

static void balloon_movement(void *actor) {
    BalloonState *s = BALLOON(actor);
    float max = REAL(actor, 0xA20), frame = REAL(actor, 0xA28);
    float speed = REAL(actor, 0xA24);
    if (REAL(actor, 0xDF0) == 1.0f) {
        float normalized = 26.0f * (frame - 1.0f) / (max - 1.0f);
        if (!s->stop) {
            s16 yaw = SHORT(actor, 0xDE), target;
            float projected = .5f * (sine(yaw) * s->hand_move.x + cosine(yaw) * s->hand_move.z);
            int z;
            normalized -= .5f * s->hand_move.y * cosine(s->lean)
                          + projected * cosine((s16)(0x4000 - s->lean));
            s->z_velocity -= .0014f * s->angle.z;
            z = (s16)(s->angle.z + (int)s->z_velocity);
            if (z > 0x800) z = 0x800;
            else if (z < -0x800) z = -0x800;
            s->angle.z = (s16)z;
            /* Convert through int before narrowing, matching the source's
               integer conversion even when a teleported hand crosses 32767. */
            target = (s16)(int)(-1200.0f * projected);
            FN(0x8009A974u, void, s16 *, s16, float, s16, s16)
                (&s->angle.x, target, 1.0f - square_root(
                    absolute((float)target) < absolute((float)s->angle.x) ? .9f : .6f), 2500, 0);
            target = 0;
            if (WORD(actor, 0xCF0) == 8 || WORD(actor, 0xCF0) == 9) {
                /* Actor speed is per native update; the source runs twice. */
                s->counter = (s16)(s->counter + (s16)(int)(200.0f * REAL(actor, 0x74)));
                target = (s16)(int)(1000.0f * sine(s->counter));
            }
            FN(0x8009A974u, void, s16 *, s16, float, s16, s16)
                (&s->extra_x, target, 1.0f - square_root(.6f), 2500, 0);
        }
        if (normalized < 13.0f) normalized = 13.0f;
        else if (normalized > 26.0f) normalized = 26.0f;
        frame = 1.0f + normalized * (max - 1.0f) / 26.0f;
        REAL(actor, 0xA28) = frame;
    } else s->angle.z = 0;
    if (frame >= max) speed = -.085f;
    else if (speed <= 0.0f && frame <= .7f * max) speed = 0.0f;
    else speed += .0039585f;
    REAL(actor, 0xA24) = speed;
}

static void balloon_play(void *actor) {
    BalloonState *s = BALLOON(actor);
    float frame = REAL(actor, 0xA28), max = REAL(actor, 0xA20);
    if (s->drawn_frame != frame) {
        float delta = frame - s->drawn_frame, speed = REAL(actor, 0xA24);
        REAL(actor, 0xA18) = delta >= 0.0f ? 1.0f : max;
        REAL(actor, 0xA1C) = delta >= 0.0f ? max : 1.0f;
        REAL(actor, 0xA24) = delta;
        FN(0x808BD81Cu, void, void *)(actor);
        REAL(actor, 0xA28) = frame;
        s->drawn_frame = frame;
        REAL(actor, 0xA24) = speed;
    }
}

void af_v3_held_balloon_draw(void *actor, void *game) {
    BalloonState *s = BALLOON(actor);
    Vec3 *hand = (Vec3 *)((u8 *)actor + 0x103C);
    void *graph = *(void **)game;
    u32 **cursor = (u32 **)((u8 *)graph + 0x298), *command;
    void *matrices = (u8 *)actor + 0xAE0 + (WORD(game, 0xA0) & 1) * 0x100;
    float scale = REAL(actor, 0xDF0);
    if (!FN(0x8009AD98u, int, void *)(game)) {
        balloon_movement(actor);
        if (s->second_step) {
            balloon_advance(actor);
            balloon_movement(actor);
            s->second_step = 0;
        }
        balloon_play(actor);
    }
    FN(0x800E020Cu, void, void)();
    FN(0x800E0314u, void, float, float, float, int)(hand->x, hand->y, hand->z, 0);
    FN(0x800E0698u, void, int, int)(SHORT(actor, 0xDE), 1);
    FN(0x800E0500u, void, int, int)((s16)(-0x4000 + s->lean + s->angle.x + s->extra_x), 1);
    FN(0x800E0834u, void, int, int)(0x4000, 1);
    FN(0x800E0500u, void, int, int)(s->angle.z, 1);
    FN(0x800E041Cu, void, float, float, float, int)
        (REAL(actor, 0x5C) * scale, REAL(actor, 0x60) * scale, REAL(actor, 0x64) * scale, 1);
    command = *cursor;
    command[0] = 0xDA380003u;
    command[1] = FN(0x800E13C4u, u32, void *)(graph);
    *cursor = command + 2;
    FN(0x800588B8u, void, Vec3 *, void *)(hand, game);
    /* The donor's TexEdgeAlpha callbacks tune GX's binary approximation of
       RDP alpha coverage. N64 materials retain native AA/CVG_X_ALPHA instead;
       emitting that GameCube-only opcode would be invalid on real hardware. */
    FN(0x800530D8u, void, void *, void *, void *, JointCallback, JointCallback, void *)
        (game, (u8 *)actor + 0xA18, matrices, (JointCallback)0, (JointCallback)0, actor);
    FN(0x800E0244u, void, void)();
    WORD(actor, 0xF44) = 0;
    if (!STATE(actor)->valid) {
        STATE(actor)->previous = STATE(actor)->current;
        STATE(actor)->valid = 1;
    }
    s->stop = 0;
}
#endif
