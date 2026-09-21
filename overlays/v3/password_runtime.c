#include "password_runtime.h"

/* Frontend arguments are exactly 28 ASCII code characters and two eight-byte
 * donor-font names. Native keyboard/saved-name conversion belongs to the UI.
 * This entry classifies once; it never gives a gift or writes saved state. */
#ifdef __mips__
#define tables ((const af_pw_u8 *)0x804C2800u)
#define policy ((const af_pw_u8 *)0x804C3000u)
#define destinations ((const af_pw_u8 *)0x804C5000u)
#else
extern const af_pw_u8 *af_pw_tables, *af_pw_policy, *af_pw_destinations;
extern af_pw_u32 af_pw_read(af_pw_u32, af_pw_u32);
#define tables af_pw_tables
#define policy af_pw_policy
#define destinations af_pw_destinations
#endif
extern float af_pw_native_random(void);

static af_pw_u32 read_selection(void *unused, af_pw_u32 address, af_pw_u32 width) {
    (void)unused;
#ifdef __mips__
    if (width == 1) return *(volatile const af_pw_u8 *)address;
    if (width == 4) return *(volatile const af_pw_u32 *)address;
    return 0;
#else
    return af_pw_read(address, width);
#endif
}
static af_pw_u32 resolve(void *unused, af_pw_u32 source) {
    (void)unused;
    return af_v3_password_resolve(destinations, AF_PW_MAP_BYTES, source, read_selection, 0);
}
static float random_percent(void *unused) {
    (void)unused;
    return af_pw_native_random() * 100.0f;
}
int af_v3_password_check(const af_pw_u8 *code, const af_pw_u8 *player,
                         const af_pw_u8 *town, struct AfPasswordOffer *offer) {
    af_v3_password decoded;
    struct AfPasswordOps ops = {0, resolve, random_percent};
    if (!code || !player || !town || !offer) return AF_PW_INVALID;
    if (code[27] == ' ') return AF_PW_CANCEL;
    if (!af_v3_password_decode(tables, AF_PW_TABLE_BYTES, code, 28, &decoded))
        return AF_PW_INVALID;
    return af_v3_password_decide(policy, AF_PW_POLICY_BYTES, &decoded, player, town, &ops, offer);
}
