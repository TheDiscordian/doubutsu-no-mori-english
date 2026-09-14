/* Resident static furniture profiles; native models keep their bank lifetime. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
#ifdef AF_V3_FURNITURE_TABLES
#include "furniture_tables.h"
#else
#define AF_V3_FURNITURE_CAPACITY 1267
#define AF_V3_FURNITURE_PROFILES 0x80465800u
#define AF_V3_FURNITURE_INDICES 0x80466C00u
#endif
enum { NATIVE = 947, CAPACITY = AF_V3_FURNITURE_CAPACITY, BANKS = 100, BANK_BYTES = 0x1400 };
struct Import { u16 index, item; u32 enabled; u32 profile[17]; u32 pad; };
_Static_assert(sizeof(struct Import) == 80, "Furniture import row");
#ifdef __mips__
#define imports ((const struct Import *)0x80467200u)
#define profiles ((const u32 *)AF_V3_FURNITURE_PROFILES)
#define indices ((u8 *)AF_V3_FURNITURE_INDICES)
#define owner ((volatile const u32 *)0x80100DF0u)
#define dma ((int (*)(void *, u32, u32))0x80026B44u)
#else
extern struct Import af_v3_furniture_imports[2];
extern u32 af_v3_furniture_profiles[CAPACITY];
extern u8 af_v3_furniture_indices[CAPACITY];
extern volatile u32 af_v3_furniture_owner[8];
extern u32 af_v3_furniture_banks[BANKS];
extern int af_v3_furniture_test_dma(void *, u32, u32);
#define imports af_v3_furniture_imports
#define profiles af_v3_furniture_profiles
#define indices af_v3_furniture_indices
#define owner af_v3_furniture_owner
#define dma af_v3_furniture_test_dma
#endif
#ifdef AF_V3_CLOTHING_DISPLAY
#include "clothing_display.h"
#ifdef __mips__
#define display_import ((const struct Import *)AF_V3_CLOTHING_DISPLAY_ROW)
#define display_dma ((void (*)(u32, u32))AF_V3_CLOTHING_DISPLAY_DMA)
#else
extern struct Import af_v3_display_import;
extern void af_v3_display_test_dma(u32, u32);
#define display_import (&af_v3_display_import)
#define display_dma af_v3_display_test_dma
#endif
#endif

static const struct Import *find(u32 argument) {
    u32 n = (u16)argument, i;
    if (n < NATIVE || n >= CAPACITY) return 0;
#ifdef AF_V3_CLOTHING_DISPLAY
    if (n == AF_V3_CLOTHING_DISPLAY_INDEX && display_import->enabled == 1 &&
            display_import->index == n && display_import->item == AF_V3_CLOTHING_DISPLAY_ITEM &&
            profiles[n] == AF_V3_CLOTHING_DISPLAY_PROFILE &&
            af_v3_display_clothing_index(display_import->item) == 0x10BFu) return display_import;
#endif
    for (i = 0; i < 2; ++i) {
        const struct Import *row = imports + i;
        if (row->enabled == 1 && row->index == n &&
                profiles[n] == 0x80467208u + i * 80u) return row;
    }
    return 0;
}

int af_v3_furniture_import_profile(u32 argument) {
    return find(argument) != 0;
}

int af_v3_furniture_bank(u32 argument) {
    u32 n = (u16)argument;
    if (n >= NATIVE && !find(n)) return -1;
    return indices[n] < BANKS ? indices[n] : -1;
}

int af_v3_furniture_has_bank(u32 argument) {
    return af_v3_furniture_bank(argument) != -1;
}

u32 af_v3_furniture_bank_address(int bank) {
    u32 live;
    if (bank < 0 || bank >= BANKS || owner[2] != 0x80936710u ||
            owner[3] != 0x8094F610u) return 0;
    live = owner[4];
    if (live < 0x8019C8E0u || live > 0x80400000u - 0x18F00u || (live & 7u)) return 0;
#ifdef __mips__
    return ((const u32 *)(uptr)(live + 0x18D68u))[bank];
#else
    return af_v3_furniture_banks[bank];
#endif
}

int af_v3_furniture_import_dma(u32 argument, u32 item, u32 bank, int bank_index) {
    const struct Import *row = find(argument);
    u32 size, active;
    (void)item; /* Static profiles have no item-dependent DMA callback. */
    if (!row || !bank || bank < 0x80000000u || bank > 0x80400000u - BANK_BYTES ||
            (bank & 7u)) return 0;
    if (bank_index == -1) {
        int existing = af_v3_furniture_bank(argument);
        if (existing < 0) return 0;
        active = (u32)existing;
    } else {
        if (bank_index < 0 || bank_index >= BANKS) return 0;
        active = (u32)bank_index;
    }
    if (af_v3_furniture_bank_address((int)active) != bank) return 0;
#ifdef AF_V3_CLOTHING_DISPLAY
    if (row == display_import) {
        if (row->profile[16] != AF_V3_CLOTHING_DISPLAY_VTABLE) return 0;
        display_dma(row->item | (item & 3u), bank);
        indices[(u16)argument] = (u8)active;
        return 1;
    }
#endif
    if (row->profile[2] != 0x06000000u || row->profile[3] <= row->profile[2]) return 0;
    size = row->profile[3] - row->profile[2];
    if (size > BANK_BYTES || !row->profile[0] ||
            row->profile[0] > 0x04000000u - size ||
            row->profile[1] != row->profile[0] + size || row->profile[16]) return 0;
    if (dma((void *)(uptr)bank, row->profile[0], size)) return 0;
    indices[(u16)argument] = (u8)active;
    return 1;
}

u32 af_v3_furniture_item(u32 argument, u32 rotation) {
    u32 n = (u16)argument;
    const struct Import *row;
    /* Keep the native extra index-947 conversion and its original fallback. */
    if (n < 948u) return (0x1000u + n * 4u) | (rotation & 3u);
    row = find(n);
    return row ? row->item | (rotation & 3u) : 0x1088u;
}
