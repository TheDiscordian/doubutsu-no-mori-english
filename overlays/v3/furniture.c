/* Resident static furniture profiles; native models keep their bank lifetime. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
#ifdef AF_V3_CONSTRUCTION_ITEMS
#include "construction.h"
#else
#define AF_V3_STATIC_IMPORT_COUNT 2
#define AF_V3_STATIC_IMPORT_RAM 0x80467200u
#endif
#ifdef AF_V3_FURNITURE_TABLES
#include "furniture_tables.h"
#else
#define AF_V3_FURNITURE_CAPACITY 1267
#define AF_V3_FURNITURE_PROFILES 0x80465800u
#define AF_V3_FURNITURE_INDICES 0x80466C00u
#endif
#ifdef AF_V3_EXPANDED_BANKS
#include "furniture_banks.h"
#else
#define AF_V3_BANK_BYTES 0x1400u
#endif
enum { NATIVE = 947, CAPACITY = AF_V3_FURNITURE_CAPACITY, BANKS = 100, BANK_BYTES = AF_V3_BANK_BYTES };
struct Import { u16 index, item; u32 enabled; u32 profile[17]; u32 pad; };
_Static_assert(sizeof(struct Import) == 80, "Furniture import row");
#ifdef __mips__
#define imports ((const struct Import *)AF_V3_STATIC_IMPORT_RAM)
#define profiles ((const u32 *)AF_V3_FURNITURE_PROFILES)
#define indices ((u8 *)AF_V3_FURNITURE_INDICES)
#define owner ((volatile const u32 *)0x80100DF0u)
#define dma ((int (*)(void *, u32, u32))0x80026B44u)
#else
extern struct Import af_v3_furniture_imports[AF_V3_STATIC_IMPORT_COUNT];
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
#ifdef AF_V3_ALOHA_DISPLAY
#ifdef __mips__
#define red_display ((const struct Import *)AF_V3_RED_DISPLAY_ROW)
#define blue_display ((const struct Import *)AF_V3_BLUE_DISPLAY_ROW)
#else
extern struct Import af_v3_red_display_import,af_v3_blue_display_import;
#define red_display (&af_v3_red_display_import)
#define blue_display (&af_v3_blue_display_import)
#endif
#endif
#endif

#ifdef AF_V3_SPEED_BAG
#include "speed_bag.h"
#ifdef __mips__
#define speed_bag ((const struct Import *)AF_V3_SPEED_BAG_ROW)
#else
extern struct Import af_v3_speed_bag_import;
#define speed_bag (&af_v3_speed_bag_import)
#endif
#endif

static const struct Import *find(u32 argument) {
    u32 n = (u16)argument;
    if (n < NATIVE || n >= CAPACITY) return 0;
#ifdef AF_V3_SPEED_BAG
    if (n == AF_V3_SPEED_BAG_INDEX && speed_bag->enabled == 1 &&
            speed_bag->index == n && speed_bag->item == AF_V3_SPEED_BAG_ITEM &&
            profiles[n] == AF_V3_SPEED_BAG_PROFILE &&
            speed_bag->profile[16] == AF_V3_SPEED_BAG_VTABLE) return speed_bag;
#endif
#ifdef AF_V3_CLOTHING_DISPLAY
#ifdef AF_V3_ALOHA_DISPLAY
    const struct Import *display = n==AF_V3_CLOTHING_DISPLAY_INDEX ? display_import :
        n==AF_V3_RED_DISPLAY_INDEX ? red_display : n==AF_V3_BLUE_DISPLAY_INDEX ? blue_display : 0;
    if (display && display->enabled==1 && display->index==n &&
            display->item==0x3000u+(n-1024u)*4u &&
            profiles[n]==(u32)(uptr)display+8u &&
            display->profile[16]==AF_V3_CLOTHING_DISPLAY_VTABLE &&
            af_v3_display_clothing_index(display->item)==0x1000u+((display->item-0x3800u)>>2))
        return display;
#else
    if (n == AF_V3_CLOTHING_DISPLAY_INDEX && display_import->enabled == 1 &&
            display_import->index == n && display_import->item == AF_V3_CLOTHING_DISPLAY_ITEM &&
            profiles[n] == AF_V3_CLOTHING_DISPLAY_PROFILE &&
            af_v3_display_clothing_index(display_import->item) == 0x10BFu) return display_import;
#endif
#endif
#ifdef AF_V3_SPARSE_FURNITURE
    if (n < AF_V3_SPARSE_FIRST || n >= AF_V3_SPARSE_END) return 0;
    u32 i = n - AF_V3_SPARSE_FIRST;
    const struct Import *row = imports + i;
    if (row->enabled == 1 && row->index == n && row->item == 0x3000u + i * 4u &&
            profiles[n] == AF_V3_STATIC_IMPORT_RAM + 8u + i * 80u) return row;
#else
    for (u32 i = 0; i < AF_V3_STATIC_IMPORT_COUNT; ++i) {
        const struct Import *row = imports + i;
        if (row->enabled == 1 && row->index == n &&
                profiles[n] == AF_V3_STATIC_IMPORT_RAM + 8u + i * 80u) return row;
    }
#endif
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

#if defined(AF_V3_EXPANDED_BANKS) && defined(__mips__)
extern void af_v3_save_halt(int) __attribute__((noreturn));

void af_v3_furniture_secure_banks(u32 room) {
    u32 live = owner[4], i, count;
    if (*(volatile u32 *)0x80000318u != 0x800000u ||
            owner[2] != 0x80936710u || owner[3] != 0x8094F610u ||
            live < 0x8019C8E0u || live > 0x80400000u - 0x18F00u || (live & 7u) ||
            room < 0x8019C8E0u || room > 0x80400000u - 0x4C8u || (room & 3u))
        af_v3_save_halt(-1);
    u32 *counts = (u32 *)(uptr)(room + 0x4C0u);
    if (counts[0] > BANKS || counts[1] > BANKS - counts[0]) af_v3_save_halt(-1);
    count = counts[0] + counts[1];
    /* The native destructor frees only count1 heap banks. The dedicated pool
     * has the lifetime of the single loaded My_Room owner, not a heap block. */
    counts[0] = count;
    counts[1] = 0;
    u32 *table = (u32 *)(uptr)(live + 0x18D68u);
    for (i = 0; i < BANKS; ++i)
        table[i] = i < count ? AF_V3_BANK_POOL_DATA + i * BANK_BYTES : 0;
    for (i = 0; i < 4; ++i) {
        ((volatile u32 *)AF_V3_BANK_POOL_START)[i] = AF_V3_BANK_GUARD;
        ((volatile u32 *)AF_V3_BANK_POOL_GUARD)[i] = AF_V3_BANK_GUARD;
    }
}
#endif

int af_v3_furniture_import_dma(u32 argument, u32 item, u32 bank, int bank_index) {
    const struct Import *row = find(argument);
    u32 size, active;
    (void)item; /* Static profiles have no item-dependent DMA callback. */
#ifdef AF_V3_EXPANDED_BANKS
    if (!row || bank < AF_V3_BANK_POOL_DATA || bank > AF_V3_BANK_POOL_GUARD - BANK_BYTES ||
#else
    if (!row || !bank || bank < 0x80000000u || bank > 0x80400000u - BANK_BYTES ||
#endif
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
    if (row == display_import
#ifdef AF_V3_ALOHA_DISPLAY
            || row==red_display || row==blue_display
#endif
            ) {
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
            row->profile[1] != row->profile[0] + size) return 0;
    if (row->profile[16]) {
        int complete_object_callback = 0;
#ifdef AF_V3_SPEED_BAG
        /* Its constructor/move/draw callbacks consume the complete object;
           there is no separate item-dependent DMA callback. */
        complete_object_callback = row == speed_bag && row->profile[16] == AF_V3_SPEED_BAG_VTABLE;
#endif
#ifdef AF_V3_TENT_MODEL
        /* The checked tent vtable has create/move/draw/destroy only, and no
         * item-dependent DMA entry. All four parts and palettes share its bank.
         * Other callback-bearing profiles still require an explicit adapter. */
        if (row->index == 1243 && row->item == 0x336Cu && row->profile[16] == 0x80483700u)
            complete_object_callback = 1;
#endif
#ifdef AF_V3_FIRE
        /* Both reviewed fire tables have only create/move/draw callbacks. */
        if ((row->index == 1239 && row->item == 0x335Cu && row->profile[16] == 0x80483FC0u) ||
            (row->index == 1240 && row->item == 0x3360u && row->profile[16] == 0x80483FD8u))
            complete_object_callback = 1;
#endif
#ifdef AF_V3_SHARED_PALETTE_FADE
        /* Generated object headers describe this shared callback category.
         * No item identity or theme determines its DMA behaviour. */
        if (row->profile[16] == 0x80483720u) complete_object_callback = 1;
#endif
        if (!complete_object_callback) return 0;
    }
    if (dma((void *)(uptr)bank, row->profile[0], size)) return 0;
#ifdef AF_V3_SHARED_PALETTE_FADE
    if (row->profile[16] == 0x80483720u) {
        const u32 *layout = (const u32 *)(uptr)bank;
        if (size < 96 || layout[0] != 0x41465031u || layout[1] != (size << 16 | 3u)) return 0;
    }
#endif
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
