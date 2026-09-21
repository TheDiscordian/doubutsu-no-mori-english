#ifndef AF_V3_PASSWORD_POLICY_H
#define AF_V3_PASSWORD_POLICY_H
#include "password.h"
enum AfPasswordResult {
    AF_PW_INVALID, AF_PW_FAMICOM, AF_PW_NPC, AF_PW_MAGAZINE_WIN,
    AF_PW_CARD_E, AF_PW_USER, AF_PW_CARD_E_MINI, AF_PW_MAGAZINE_LOSE,
    AF_PW_WRONG_NAME, AF_PW_CANCEL
};
struct AfPasswordOps {
    void *context;
    /* Pure source-to-destination resolution; zero means unavailable. It must
     * check installed behaviour and the live selected profile, not just ID. */
    af_pw_u32 (*resolve)(void *,af_pw_u32);
    /* The game's continuous [0,100) RNG, consumed only for valid magazine
     * attempts, including the source's zero- and hundred-percent rates. */
    float (*random_percent)(void *);
};
struct AfPasswordOffer { af_pw_u32 source_item,item,result; };
int af_v3_password_policy_valid(const af_pw_u8 *,af_pw_u32);
int af_v3_password_allowed(const af_pw_u8 *,af_pw_u32,af_pw_u32,af_pw_u32);
int af_v3_password_map_valid(const af_pw_u8 *,af_pw_u32);
/* The reader loads a checked live selection field; it must not award items.
 * The separate map contains actual installed destinations, never guesses for
 * unknown native correspondences or unfinished imported representations. */
af_pw_u32 af_v3_password_resolve(const af_pw_u8 *,af_pw_u32,af_pw_u32,
    af_pw_u32 (*)(void *,af_pw_u32,af_pw_u32),void *);
/* Names must already be converted to eight-byte donor-font fields.
 * Returns a donor result, never gives an item or modifies a saved field.
 * Invalid inputs leave the offer untouched; successful no-gift results have
 * their own result values and must never enter the animated handover path. */
int af_v3_password_decide(const af_pw_u8 *,af_pw_u32,const af_v3_password *,
    const af_pw_u8 *,const af_pw_u8 *,const struct AfPasswordOps *,struct AfPasswordOffer *);
int af_v3_password_result_gives_item(af_pw_u32);
#endif
