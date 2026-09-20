/* Common fall/get-up setup. Keep original tool behaviour and imported identity;
 * only net families need a different motion and stopped playback. */
typedef unsigned int u32;
typedef unsigned char u8;
#define RECOVERY __attribute__((section(".af_tool_recovery")))
#ifdef __mips__
static __attribute__((always_inline)) inline void *recovery_native(u32 address) {
    return (void *)(*(volatile u32 *)0x80143900u - 0x808DD748u + address);
}
#else
extern void *af_test_tool_motion_function(u32);
#define recovery_native af_test_tool_motion_function
#endif
#define RFN(at, result, ...) ((result (*)(__VA_ARGS__))recovery_native(at))

static RECOVERY void recover(void *actor, int kind, float morph, int getup) {
    int imported_net = (u32)kind - 45u < 2u;
    int net = kind == 1 || imported_net;
    int animation, main;
    if (net) {
        animation = getup ? 5 : 6;
        if (imported_net) animation += 21;
        main = getup ? 6 : 5;
    } else {
        animation = RFN(0x808BD6E0u, int, int)(kind);
        main = RFN(0x808BD690u, int, int)(kind);
    }
    RFN(0x808BDDB4u, void, void *, int, int, float, float, float, int)
        (actor, kind, animation, 1.0f, morph, -1.0f, !net);
    *(int *)((u8 *)actor + 0xCFC) = main;
    *((signed char *)actor + 0x1117) = (signed char)kind;
}

RECOVERY void af_v3_tool_tumble(void *actor, void *game, int kind, float morph) {
    (void)game;
    recover(actor, kind, morph, 0);
}

RECOVERY void af_v3_tool_getup(void *actor, void *game, int kind, float morph) {
    (void)game;
    recover(actor, kind, morph, 1);
}
