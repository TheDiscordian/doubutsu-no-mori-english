#ifndef AF_V3_PASSWORD_H
#define AF_V3_PASSWORD_H
typedef unsigned char af_pw_u8;
typedef unsigned short af_pw_u16;
typedef unsigned int af_pw_u32;
/* Names are the complete eight-byte donor-font fields, not native save names.
 * This codec does not validate item eligibility, identity, or delivery. */
typedef struct {
    af_pw_u16 item;
    af_pw_u8 type, hit_rate_index, npc_type, npc_code, checksum, reserved;
    af_pw_u8 str0[8], str1[8];
} af_v3_password;
int af_v3_password_decode(const af_pw_u8 *tables, af_pw_u32 size,
    const af_pw_u8 *text, af_pw_u32 length, af_v3_password *out);
int af_v3_password_encode(const af_pw_u8 *tables, af_pw_u32 size,
    const af_v3_password *password, af_pw_u8 *text, af_pw_u32 length);
#endif
