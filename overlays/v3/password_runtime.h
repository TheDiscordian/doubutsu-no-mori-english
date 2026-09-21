#ifndef AF_V3_PASSWORD_RUNTIME_H
#define AF_V3_PASSWORD_RUNTIME_H
#include "password_policy.h"
/* Fixed frontend entry: af_v3_password_boot_check at 804B4D00. Buffers must be
 * readable for 28, 8, and 8 bytes respectively. Names use donor font encoding,
 * not native saved bytes. The frontend must call once per submitted attempt.
 * Cancel/invalid leave offer untouched. No result writes inventory or a save. */
int af_v3_password_boot_check(const af_pw_u8 *, const af_pw_u8 *,
    const af_pw_u8 *, struct AfPasswordOffer *);
int af_v3_password_check(const af_pw_u8 *, const af_pw_u8 *,
    const af_pw_u8 *, struct AfPasswordOffer *);
#endif
