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

extern void af_v3_held_setup_original(void *, int, int, float, float, float, int *, int *);

static int pinwheel(int kind) { return (u32)(kind - 99) < 8u; }

void af_v3_held_setup(void *actor, int animation, int item_animation, float speed,
                      float morph, float frame, int *animation_out, int *part_out) {
    int kind = FN(0x808BD5C4u, int, void *, int)(actor, WORD(actor, 0xD00));
    int previous = *(signed char *)((u8 *)actor + 0x1117);
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
}

static float absolute(float value) { return value < 0.0f ? -value : value; }
static float cosine(s16 angle) { return FN(0x80099A54u, float, int)(angle); }

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
