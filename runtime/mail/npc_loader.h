#ifndef AF_NPC_MAIL_LOADER_H
#define AF_NPC_MAIL_LOADER_H

#include "npc_generation.h"

#define AF_NPC_MAIL_WORK_BYTES 5344u
#define AF_NPC_MAIL_LOADER_ABI 0x41464E01u
#define AF_NPC_MAIL_CREATOR_VROM 0x03200000u
#define AF_NPC_MAIL_CREATOR_RAM 0x80B00000u

typedef struct {
    unsigned int vrom, blob_bytes, image_bytes, relocation_bytes;
    unsigned int entry_offset, text_bytes, crc32, abi;
} AfNpcMailLoaderConfig;

/* Shared transient GameCube-style state; never stored in a native save field. */
extern unsigned int af_mail_generation_capital;

/* Original metadata arguments, but return a complete caller-owned letter only
 * on success. Disabled/failed creation returns null and cannot deliver stale
 * staging data. The cartridge image and work have one synchronous heap owner.
 */
unsigned char *af_npc_mail_load(unsigned char *, const unsigned char *,
                              const unsigned char *, const unsigned char *,
                              unsigned int, unsigned int);

static inline int af_npc_mail_heap_range(unsigned int address, unsigned int size) {
    return address >= 0x8019C8E0u && address <= 0x80400000u
        && size <= 0x80400000u-address;
}

#endif
