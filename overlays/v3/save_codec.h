#ifndef AF_V3_SAVE_CODEC_H
#define AF_V3_SAVE_CODEC_H

typedef unsigned char af_save_u8;
typedef unsigned int af_save_u32;

#define AF_SAVE_PAYLOAD 0xF980u
#define AF_SAVE_BANK 0x10000u
#define AF_SAVE_CAPSULE (AF_SAVE_BANK - AF_SAVE_PAYLOAD)
#define AF_SAVE_PROFILE 160u
#define AF_SAVE_CATALOGUE 512u
#define AF_SAVE_STATE (AF_SAVE_PROFILE + AF_SAVE_CATALOGUE)

enum {
    AF_SAVE_LEGACY = 0, AF_SAVE_OK = 1,
    AF_SAVE_ARGUMENT = -1, AF_SAVE_HEADER = -2, AF_SAVE_CHECKSUM = -3,
    AF_SAVE_FORMAT = -4, AF_SAVE_BINDING = -5, AF_SAVE_CRC = -6,
    AF_SAVE_PROFILE_MISSING = -7, AF_SAVE_CATALOGUE_INVALID = -8
};

/* Exact bank-sized input. Output state may be null, but must not overlap input
 * or current profile. Errors leave every caller buffer unchanged. */
int af_v3_save_check(const af_save_u8 *bank, af_save_u32 size,
                     const af_save_u8 *current, af_save_u8 *state);
/* State = 32 villager bytes, 128 furniture bytes, four 128-byte catalogues.
 * State and bank must be disjoint. Preparation only; this does no device I/O. */
int af_v3_save_pack(af_save_u8 *bank, af_save_u32 size, const af_save_u8 *state);
/* Registry 1 uses bits (actor index) and ((item & 0xFFF) >> 2), LSB first.
 * mark=0 queries; mark=1 records ownership. Original items are rejected. */
int af_v3_save_collect(af_save_u8 *state, af_save_u32 player,
                       af_save_u32 item, af_save_u32 mark);
#endif
