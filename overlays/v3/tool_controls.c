/* Classify equipment only for native input predicates. The real kind remains
 * available to artwork, collision, tool effects, inventory, and saved identity.
 * The normal selector still owns scene permissions and selected-profile checks.
 */
typedef unsigned int u32;
#ifdef __mips__
static int visible_kind(void *actor, int action) {
    u32 entry = *(volatile u32 *)0x80143900u - 0x808DD748u + 0x808BD5C4u;
    return ((int (*)(void *, int))entry)(actor, action);
}
#else
extern int af_test_visible_tool_kind(void *, int);
#define visible_kind af_test_visible_tool_kind
#endif

__attribute__((section(".af_tool_controls")))
int af_v3_player_control_kind(void *actor, int action) {
    int kind = visible_kind(actor, action);
    if ((u32)kind - 36u >= 79u) return kind;
    /* Extended indices are 36 + the donor kind. Tool families, including
       worn axes and golden variants, use the corresponding native action.
       Passive items are valid non-tools, like the original umbrellas, for
       pickup/tree-shaking predicates. The umbrella-spin input is not hooked. */
    if (kind < 45) return 0;  /* Axe: source 0..8. */
    if (kind < 47) return 1;  /* Net: source 9..10. */
    if (kind < 87) return 2;  /* Umbrellas: source 11..50. */
    if (kind < 89) return 34; /* Rod: source 51..52. */
    if (kind < 91) return 35; /* Shovel: source 53..54. */
    return 2;               /* Balloons, pinwheels, and fans: source 55..78. */
}
