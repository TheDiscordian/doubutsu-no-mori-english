/* Startup code owns 0x6000..0x63DF; configuration follows at 0x63E0. */
typedef unsigned int u32;
#include "storage.h"
#ifdef AF_V3_ACCESSORIES
#include "accessory.h"
#endif
#ifndef AF_V3_OBJECT_CAPACITY
#define AF_V3_OBJECT_CAPACITY 430
#endif
extern u32 af_crc32(const void *, u32);
#ifndef AF_V3_BLOB_SIZE
#define AF_V3_BLOB_SIZE 0x2000u
#endif
#ifndef AF_V3_ABI
#define AF_V3_ABI 1u
#endif
#define AF_V3_GUARD ((AF_V3_BLOB_SIZE - 16u) / 4u)
#ifdef __mips__
#define memory ((unsigned char *)0x80460000u)
#define config ((volatile const u32 *)0x8019ACC0u)
#define installed (*(volatile u32 *)0x8019ACD0u)
#define memsize (*(volatile const u32 *)0x80000318u)
#define previous ((int (*)(void))0x8009D6D0u)
#define dma ((int (*)(void *, u32, u32))0x80026B44u)
#define writeback ((void (*)(void *, u32))0x8002FE00u)
#define invalidate ((void (*)(void *, u32))0x80034CE0u)
#define execute() (((int (*)(void))0x80460100u)())
#else
extern unsigned char af_v3_memory[AF_V3_BLOB_SIZE];
extern volatile u32 af_v3_config[4], af_v3_installed, af_v3_memsize;
extern int af_v3_previous(void), af_v3_dma(void *, u32, u32), af_v3_execute(void);
extern void af_v3_writeback(void *, u32), af_v3_invalidate(void *, u32);
#define memory af_v3_memory
#define config af_v3_config
#define installed af_v3_installed
#define memsize af_v3_memsize
#define previous af_v3_previous
#define dma af_v3_dma
#define writeback af_v3_writeback
#define invalidate af_v3_invalidate
#define execute af_v3_execute
#endif
#ifdef AF_V3_CLOTHING_PROFILE
#ifdef __mips__
#define extra_code (memory+0xD000)
#else
extern unsigned char af_v3_save_extra[AF_V3_EXTRA_CODE_LIMIT];
#define extra_code af_v3_save_extra
#endif
#endif

#ifdef AF_V3_ACCESSORIES
#ifdef __mips__
#define accessory_memory ((unsigned char *)AF_V3_ACCESSORY_RAM)
#else
extern unsigned char af_v3_accessory_memory[AF_V3_ACCESSORY_BYTES];
#define accessory_memory af_v3_accessory_memory
#endif
#endif

/* Share the transfer/check sequence without growing the resident reservation. */
static __attribute__((noinline)) int load_checked(void *destination, u32 vrom,
                                                 u32 bytes, u32 crc) {
    return !dma(destination, vrom, bytes) && af_crc32(destination, bytes) == crc;
}

int af_v3_startup(void) {
    const u32 *header = (const u32 *)memory;
    if (!previous()) return 0;
    /* Retain the low-memory English Expansion Pak warning path. */
    if (memsize != 0x800000u) return 1;
    if (installed) return header[0] == 0x41465633u && header[AF_V3_GUARD] == 0xAF33C0DEu;
    if (config[0] != AF_V3_STORAGE_VROM || config[1] != AF_V3_BLOB_SIZE || config[3] != AF_V3_ABI) return 0;
    if (!load_checked(memory, AF_V3_STORAGE_VROM, AF_V3_BLOB_SIZE, config[2])) return 0;
    if (header[0] != 0x41465633u || header[1] != AF_V3_ABI || header[2] != AF_V3_BLOB_SIZE
            || header[3] != AF_V3_OBJECT_CAPACITY || header[4] != 410 || header[AF_V3_GUARD] != 0xAF33C0DEu) return 0;
#ifdef AF_V3_CLOTHING_PROFILE
    const u32 *extra = (const u32 *)(memory+0xE0);
    if (extra[0] != AF_V3_SAVE_CODE_VROM || !extra[1] || extra[1] > AF_V3_EXTRA_CODE_LIMIT || (extra[1] & 15)
            || extra[3] != 0x8046D000u) return 0;
    if (!load_checked(extra_code, extra[0], extra[1], extra[2])) return 0;
    writeback(extra_code, extra[1]);
    invalidate(extra_code, extra[1]);
#endif
#ifdef AF_V3_ACCESSORIES
    const u32 *accessory = (const u32 *)(memory+0xF0);
    if (accessory[0] != AF_V3_ACCESSORY_VROM || accessory[1] != AF_V3_ACCESSORY_BYTES
            || accessory[3] != AF_V3_ACCESSORY_RAM) return 0;
    if (!load_checked(accessory_memory, accessory[0], accessory[1], accessory[2])) return 0;
    const u32 *accessory_header = (const u32 *)accessory_memory;
    if (accessory_header[0] != AF_V3_ACCESSORY_MAGIC || accessory_header[1] != 1
            || accessory_header[2] != AF_V3_ACCESSORY_BYTES || accessory_header[3] != 20
            || accessory_header[(AF_V3_ACCESSORY_BYTES-16)/4] != AF_V3_ACCESSORY_GUARD) return 0;
    writeback(accessory_memory, AF_V3_ACCESSORY_BYTES);
    /* Flush all possible code in this verified, newly loaded package once.
       Including data in an instruction-cache flush does not alter its bytes. */
    invalidate(accessory_memory+0x100, AF_V3_ACCESSORY_BYTES-0x110u);
#endif
#ifdef AF_V3_EQUIPMENT_VROM
    /* Separate from the full resident package; no live artwork is moved. */
#ifdef __mips__
    unsigned char *equipment = (unsigned char *)0x804A3000u;
#else
    extern unsigned char af_v3_equipment_memory[0x2000];
    unsigned char *equipment = af_v3_equipment_memory;
#endif
    if (!load_checked(equipment, AF_V3_EQUIPMENT_VROM, 0x2000u, AF_V3_EQUIPMENT_CRC)) return 0;
    /* The compiled checksum binds the complete module, including its table
       header and footer. Unlike the other packages, it is not a RAM descriptor. */
    writeback(equipment, 0x2000u);
    invalidate(equipment, 0x1000u);
#endif
    writeback(memory, AF_V3_BLOB_SIZE);
    invalidate(memory + 0x100, AF_V3_ABI >= 4 ? AF_V3_BLOB_SIZE - 0x110u : 0xF00u);
    if (execute() != 1) return 0;
#ifdef AF_V3_FURNITURE_TABLES
#ifdef __mips__
    if (((int (*)(void))0x8046A000u)() != 1) return 0;
#else
    extern int af_v3_furniture_tables_init(void);
    if (af_v3_furniture_tables_init() != 1) return 0;
#endif
#endif
#ifdef AF_V3_SAVE_RUNTIME
#ifdef __mips__
    if (((int (*)(void))0x80469200u)() != 1) return 0;
#else
    extern int af_v3_save_reset(void);
    if (af_v3_save_reset() != 1) return 0;
#endif
#endif
    installed = 1;
    return 1;
}
