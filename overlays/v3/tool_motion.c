/* Shared native action setup for imported tool families. Keep actual kinds and
 * use the complete donor animations; original tools keep their native indices.
 */
typedef unsigned int u32;
typedef unsigned char u8;
#ifdef __mips__
static void *native(u32 address) {
    if (address >= 0x808B2D50u)
        address = *(volatile u32 *)0x80143900u - 0x808DD748u + address;
    return (void *)address;
}
#else
extern void *af_test_tool_motion_function(u32);
#define native af_test_tool_motion_function
#endif
#define FN(at, result, ...) ((result (*)(__VA_ARGS__))native(at))
#define WORD(p, at) (*(int *)((u8 *)(p) + (at)))

static int family(int kind) {
    if ((u32)kind - 36u < 9u) return 0;
    if ((u32)kind - 45u < 2u) return 1;
    if ((u32)kind - 87u < 2u) return 34;
    if ((u32)kind - 89u < 2u) return 35;
    return kind;
}

void af_v3_tool_action_setup(void *actor, int requested_kind, int animation,
                             int main, float morph, float frame, int mode) {
    int actual = FN(0x808BD5C4u, int, void *, int)(actor, WORD(actor, 0xD00));
    int category = family(actual);
    if (requested_kind != actual && requested_kind != category) return;
    if (actual != category) {
        /* Native net motions 2..8 correspond to donor 6..12 (resource 23..29).
         * Native rod motions 10..15 correspond to donor 15..20 (32..37). */
        if (category == 1 && (u32)animation - 2u < 7u) animation += 21;
        else if (category == 34 && (u32)animation - 10u < 6u) animation += 22;
    }
    if (!FN(0x808BDF6Cu, int, int, int)(category, animation)) return;
    FN(0x808BDDB4u, void, void *, int, int, float, float, float, int)
        (actor, actual, animation, 1.0f, morph, frame, mode);
    WORD(actor, 0xCFC) = main;
    *((signed char *)actor + 0x1117) = (signed char)actual;
}

/* The native rod-aware setup has a separate rod-speed argument. Other tools
 * use one native frame per update. The existing common setup retains the
 * pinwheel/balloon rules, holding pose, part mask, and real identity. */
void af_v3_tool_moving_setup(void *actor, int animation, float rod_speed,
                             float morph, int *animation_out, int *part_out) {
    int actual = FN(0x808BD5C4u, int, void *, int)(actor, WORD(actor, 0xD00));
    int item_animation;
    float speed = 1.0f;
    if (family(actual) == 34) {
        item_animation = actual == 34 ? 11 : 33;
        speed = rod_speed;
    } else {
        item_animation = FN(0x808BD6E0u, int, int)(actual);
    }
    FN(0x808B83B4u, void, void *, int, int, float, float, float, int *, int *)
        (actor, animation, item_animation, speed, morph, -1.0f, animation_out, part_out);
}
