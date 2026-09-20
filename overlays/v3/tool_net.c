/* Source-correct net dimensions for the retained native collision routines.
 * The checked caller reserves two outgoing words at sp+24/sp+28. Its sole
 * local-capture callee reads the first as an additional radius argument. */
typedef unsigned int u32;
typedef unsigned char u8;
#ifdef __mips__
static __attribute__((always_inline)) inline void *net_native(u32 address) {
    return (void *)(*(volatile u32 *)0x80143900u - 0x808DD748u + address);
}
#else
extern void *af_test_net_function(u32);
#define net_native af_test_net_function
#endif
#define NFN(at, result, ...) ((result (*)(__VA_ARGS__))net_native(at))

__attribute__((section(".af_tool_net")))
int af_v3_net_parameters(void *actor, u32 *label, signed char *type, u32 *parameters) {
    int kind;
    if (NFN(0x808CC7B4u, int, void *, u32 *, signed char *)(actor, label, type)) return 1;
    if ((u32)*(int *)((u8 *)actor + 0xF18) - 1u >= 8u) return 0;
    kind = NFN(0x808BD3F8u, int, void)();
    /* IEEE single-precision bits avoid moving old linked float constants. */
    parameters[0] = kind == 46 ? 0x41A80000u : 0x41700000u; /* 21 / 15 */
    parameters[1] = kind == 46 ? 0x42700000u : 0x42480000u; /* 60 / 50 */
    return 0;
}
