/* Shared player-action extensions, using the currently loaded native owner.
 * Fan controls/setup/transitions retain GAFE01-r0 semantics. These entry points
 * form complete callback groups registered by the importer. Inventory choices
 * remain a separate requirement. No saved fields or player allocation are added.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed char s8;

#ifdef __mips__
static void *native(u32 address) {
    if (address >= 0x808B2D50u)
        address = *(volatile u32 *)0x80143900u - 0x808DD748u + address;
    return (void *)address;
}
#else
extern void *af_test_player_function(u32 address);
#define native af_test_player_function
#endif
#define FN(at, result, ...) ((result (*)(__VA_ARGS__))native(at))
#define WORD(p, at) (*(int *)((u8 *)(p) + (at)))
#define REAL(p, at) (*(float *)((u8 *)(p) + (at)))

#ifdef AF_V3_HELD_POINTER
/* The common native draw dispatcher supplies the hand matrix, scale, opaque
   stream, and temporary segment-six binding. A static held fan only emits its
   complete model; it does not borrow an axe/shovel's collision-point update. */
void af_v3_player_draw_static_item(void *actor, void *game) {
    int bank = WORD(actor, 0xDEC);
    if ((u32)bank < 2u) {
        int shape = WORD(actor, 0xDDC + bank * 4);
        u32 model = FN(AF_V3_HELD_POINTER, u32, int)(shape);
        if (model) {
            void *graph = *(void **)game;
            u32 **cursor = (u32 **)((u8 *)graph + 0x298);
            u32 *command = *cursor;
            command[0] = 0xDE000000u;
            command[1] = model;
            *cursor = command + 2;
        }
    }
    /* N64 has the rod-tip flag but no balloon-start flag. Balloon ownership
       and its additional rig/state are a separate unimplemented category. */
    WORD(actor, 0xF44) = 0;
}
#endif
enum { FAN_ACTION = 109, FAN_FIRST_KIND = 107, FAN_KINDS = 8 };

int af_v3_player_fan_controller(void *game, int trigger) {
    void *actor = FN(0x800B1C84u, void *, void *)(game);
    int kind = FN(0x808BD5C4u, int, void *, int)(actor, WORD(actor, 0xCF0));
    if ((u32)(kind - FAN_FIRST_KIND) >= FAN_KINDS) return 0;
    if (FN(0x8007D90Cu, int, void)()) {
        const s8 *controller = FN(0x800B593Cu, const s8 *, void)();
        return controller[trigger ? 0x38 : 0x39];
    }
    if (trigger) return FN(0x80078DACu, int, int)(0x8000);
    return FN(0x80078D30u, int, int)(0x8000);
}

int af_v3_player_fan_request(void *game, int start, int priority) {
    if (!FN(0x808B8874u, int, void *, int, int)(game, FAN_ACTION, priority)) return 0;
    void *actor = FN(0x800B1C84u, void *, void *)(game);
    FN(0x808B3334u, void, void *, int, int)(game, FAN_ACTION, priority);
    WORD(actor, 0xD58) = start;
    return 1;
}

int af_v3_player_fan_check(void *game, int trigger, int start, int priority) {
    if (!af_v3_player_fan_controller(game, trigger)) return 0;
    void *actor = FN(0x800B1C84u, void *, void *)(game);
    int action = WORD(actor, 0xCF0);
    /* Existing WAIT/WALK frames advance twice as far per native update as
       in GAFE01. Compare against the native equivalent of its 0.5 gate. */
    if (action >= 8 && action <= 10 && REAL(actor, 0x180) >= 1.0f) return 0;
    return af_v3_player_fan_request(game, start, priority);
}

void af_v3_player_handheld_poll(void *game, int priority) {
    FN(0x808B7DD8u, int, void *, int)(game, priority);
    af_v3_player_fan_check(game, 1, 1, priority);
}

void af_v3_player_fan_setup(void *actor, void *game) {
    int start = WORD(actor, 0xD58);
    float frame = start ? 1.0f : REAL(actor, 0x1F4);
    float morph = start ? -5.0f : 0.0f;
    /* Native Base2, not the reverse initializer at 808B4B6C. WAIT1 is native
       animation zero; imported UTIWA_D1 is 130 + donor animation 140. The
       donor's ContinueAnimation optimization only applies to WAIT1 in both
       layers and therefore cannot alter this fan initializer. */
    FN(0x808B4A44u, void, void *, void *, int, int,
       float, float, float, float, int, int)
        (actor, game, 270, 0, 1.0f, frame, 1.0f, morph, 1, 4);
    FN(0x808B3BD0u, void, void *, void *)(actor, game);
    FN(0x808B36E8u, void, void *, int)(actor, 5);
}

#ifdef AF_V3_FAN_SOUND
void af_v3_player_fan_finish(void *actor, void *game);
static void fan_finish_frame(void *actor, void *game, float current);
void af_v3_player_fan_main(void *actor, void *game) {
    float last_frame;
    /* Use the corresponding native braking routine, not the donor's
       per-update movement constant. Native physics uses a different step. */
    FN(0x808B3C74u, int, void *)(actor);
    FN(0x808B61E4u, void, void *, void *)(actor, game);
    FN(0x808B488Cu, int, void *, float *)(actor, &last_frame);
    if (!FN(0x808B5698u, int, void *, float)(actor, last_frame) &&
        FN(0x808B5844u, int, void *, float)((u8 *)actor + 0x174, 1.5f))
        FN(0x800D1D58u, void, int, void *)(AF_V3_FAN_SOUND, (u8 *)actor + 0x28);
    FN(0x808B5310u, void, void *)(actor);
    FN(0x808B4DACu, void, void *, void *)(actor, game);
    FN(0x808B5FB0u, void, void *)(actor);
    FN(0x808BF410u, void, void *, void *)(actor, game);
    float current = REAL(actor, 0x184);
    /* Native steps can cross the donor's final half-frame and wrap before
       the end request runs. Retain that crossed event without changing the
       rendered frame or introducing a second animation/morph update. */
    if (last_frame >= 8.0f && current < last_frame) current = REAL(actor, 0x178);
    fan_finish_frame(actor, game, current);
}
#endif

static void fan_finish_frame(void *actor, void *game, float current) {
    void *frame_control = (u8 *)actor + 0x174;
    if (FN(0x808B5844u, int, void *, float)(frame_control, 7.5f)) {
        FN(0x808B3648u, void, void *)(actor);
        FN(0x808B3AF0u, void, void *, int)(actor, 1);
    }
    /* A native step can cross 7.5 and 8 together. Both source events must
       execute in order; an else branch would permanently swallow release. */
    if (current >= 8.0f && !af_v3_player_fan_check(game, 0, 0, 4)) {
        if (FN(0x808B312Cu, float, void)() || FN(0x808B3170u, float, void)())
            FN(0x808C13F0u, int, void *, void *, float, int, int)
                (game, (void *)0, -5.0f, 0, 1);
        if (current >= REAL(actor, 0x178) - 0.5f) {
            FN(0x808B3648u, void, void *)(actor);
            /* GAFE01 stores a delay-frame argument but its WAIT setup
               never reads it. Both implementations ignore flag two.
               Native request signature is (game, morph, flags, priority),
               not the donor's five-argument signature. */
            FN(0x808C1064u, int, void *, float, int, int)(game, -5.0f, 2, 1);
        }
    }
}

void af_v3_player_fan_finish(void *actor, void *game) {
    fan_finish_frame(actor, game, REAL(actor, 0x184));
}
