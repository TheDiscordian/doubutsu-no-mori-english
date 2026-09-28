#ifndef AF_V3_SAVE_COMPRESSED_H
#define AF_V3_SAVE_COMPRESSED_H
/* Disk envelope around a validated format-four bank and four console saves.
 * Preparation only: this API does not write flash or install native hooks.
 * It preserves two independent 64-KiB banks. All buffers must be disjoint. */
enum {
    AF_CZ_BANK = 65536,
    AF_CZ_CONSOLE = 6528,
    AF_CZ_RAW = AF_CZ_BANK + AF_CZ_CONSOLE,
    AF_CZ_HASH_WORDS = 4096,
    AF_CZ_WORK_BYTES = AF_CZ_HASH_WORDS * sizeof(unsigned int),
    AF_CZ_ARGUMENT = -1,
    AF_CZ_FORMAT = -2,
    AF_CZ_CHECKSUM = -3,
    AF_CZ_SPACE = -4,
    AF_CZ_STREAM = -5
};
/* Caller validates the canonical bank's profile/ownership using save_codec.
 * The envelope additionally checks its format, both CRCs, and native checksum.
 * Returns compressed byte count, or a negative error. Output is unchanged on
 * every error. Hash scratch is explicitly caller-owned and may change. */
int af_v3_save_compress(unsigned char *bank, unsigned int bank_bytes,
    const unsigned char *canonical, unsigned int canonical_bytes,
    const unsigned char *console, unsigned int console_bytes,
    unsigned int *hash, unsigned int hash_bytes);
/* On success scratch holds canonical bank followed by four console records.
 * Check ownership/profile with save_codec before committing ANY live state.
 * On failure scratch may change, but bank is never modified. */
int af_v3_save_expand(const unsigned char *bank, unsigned int bank_bytes,
    unsigned char *scratch, unsigned int scratch_bytes);
#ifdef AF_V3_DIARY_STORAGE
#include "diary.h"
enum { AF_CZ_DIARY_RAW=AF_CZ_RAW+AF_DIARY_BYTES };
/* Format eleven adds all monthly pages and calendar/lock state without changing
 * the canonical format-eight town. No device writes. Older envelopes migrate
 * with empty diary pages; old readers reject format eleven. */
int af_v3_save_compress_diary(unsigned char *bank,unsigned int bank_bytes,
    const unsigned char *canonical,unsigned int canonical_bytes,
    const unsigned char *console,unsigned int console_bytes,const AFDiary *diary,
    unsigned int *hash,unsigned int hash_bytes);
int af_v3_save_measure_diary(const unsigned char *canonical,unsigned int canonical_bytes,
    const unsigned char *console,unsigned int console_bytes,const AFDiary *diary,
    unsigned int *hash,unsigned int hash_bytes);
int af_v3_save_expand_diary(const unsigned char *bank,unsigned int bank_bytes,
    unsigned char *scratch,unsigned int scratch_bytes);
#endif
#endif
