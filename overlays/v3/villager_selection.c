/* Subset-aware town selection; saved IDs remain the fixed registry identities. */
typedef unsigned char u8;
typedef unsigned int u32;
#include "villager_outfit.h"
#ifndef AF_V3_GROWTH_ADDRESS
#define AF_V3_GROWTH_ADDRESS 0x80461D80u
#endif

#ifdef __mips__
#define flags ((const u8 *)0x80461E60u)
#define metadata ((const u8 *)0x80462C00u)
#define growth ((const signed char *)AF_V3_GROWTH_ADDRESS)
#define candidates ((u8 *)0x80464700u)
#define shuffle ((int *)0x80464800u)
#define ready (*(volatile const u32 *)0x8019ACD0u == 1u)
#define animals ((u8 *)0x80130DB8u)
#define appeared ((u8 *)0x8013670Cu)
#define seen ((int (*)(int))0x800AA35Cu)
#define looks ((u32 (*)(u32))0x800AA1E0u)
#define search ((int (*)(u8 *, u32, int))0x800A7C30u)
#define reset_common ((void (*)(u8 *, u8 *))0x800AA438u)
#define rand_table ((void (*)(int *, int, int))0x800A6810u)
#define random_value ((float (*)(void))0x8002C9ACu)
#define set_index ((void (*)(u8 *, int))0x800AD8C4u)
#define mark_seen ((void (*)(u32))0x800AA2F8u)
#else
extern u8 af_v3_select_flags[20], af_v3_select_metadata[640], af_v3_select_candidates[32];
extern u8 af_v3_select_animals[0x528*15], af_v3_select_appeared[32];
extern signed char af_v3_select_growth[224];
extern int af_v3_select_shuffle[238], af_v3_select_ready;
extern int af_v3_select_seen(int), af_v3_select_search(u8 *, u32, int);
extern u32 af_v3_select_looks(u32);
extern void af_v3_select_reset(u8 *, u8 *), af_v3_select_rand(int *, int, int);
extern float af_v3_select_random(void);
extern void af_v3_select_set(u8 *, int), af_v3_select_mark(u32);
#define flags af_v3_select_flags
#define metadata af_v3_select_metadata
#define growth af_v3_select_growth
#define candidates af_v3_select_candidates
#define shuffle af_v3_select_shuffle
#define ready af_v3_select_ready
#define animals af_v3_select_animals
#define appeared af_v3_select_appeared
#define seen af_v3_select_seen
#define looks af_v3_select_looks
#define search af_v3_select_search
#define reset_common af_v3_select_reset
#define rand_table af_v3_select_rand
#define random_value af_v3_select_random
#define set_index af_v3_select_set
#define mark_seen af_v3_select_mark
#endif

static int eligible(int index) {
    const u8 *row;
    u32 cloth;
    if (index >= 0 && index < 216) return 1;
    if (!ready || index < 218 || index >= 238 || flags[index-218] != 1) return 0;
    row = metadata+(index-218)*32;
    cloth = ((u32)row[30] << 8) | row[31];
    return row[0] == 0xE0 && row[1] == index && row[4] < 6 && row[6] == 0
        && row[7] == 1 && outfit_ready(cloth);
}

int af_v3_unseen_personality(u32 argument) {
    u8 personality = (u8)argument;
    int count = 0, index;
    if (personality >= 6) return 0;
    for (index = 0; index < 238; ++index)
        if (eligible(index) && looks(0xE000u+(u32)index) == personality && !seen(index)) ++count;
    return count;
}

void af_v3_reset_appeared(void) {
    int index;
    for (index = 0; index < 238; ++index)
        if (eligible(index) && !seen(index)) return;
    reset_common(appeared, animals);
}

int af_v3_grow_personality(u32 argument) {
    u8 personality = (u8)argument;
    int count = 0, index, selected;
    float draw;
    if (personality >= 6) return -1;
    for (index = 0; index < 32; ++index) candidates[index] = 0;
    for (index = 0; index < 238; ++index) {
        if (eligible(index) && looks(0xE000u+(u32)index) == personality
                && search(animals, 0xE000u+(u32)index, 15) == -1 && !seen(index)) {
            candidates[index/8] |= 1u << (index & 7);
            ++count;
        }
    }
    if (!count) return -1;
    draw = random_value();
    if (!(draw >= 0.0f && draw < 1.0f)) return -1;
    selected = (int)(draw * (float)count);
    for (index = 0; index < 238; ++index)
        if (candidates[index/8] & (1u << (index & 7))) {
            if (!selected) return index;
            --selected;
        }
    return -1;
}

void af_v3_initial_population(u8 *destination, u32 argument, int malloc_flag) {
    int size = 216, slot, index, offset, ordinal;
    u8 count = (u8)argument, used = 0;
    u32 personality;
    (void)malloc_flag;
    if (!destination || !count || count > 15) return;
    for (index = 218; index < 238; ++index) if (eligible(index)) ++size;
    /* With no imports, this is exactly the native 216-entry/216-swap draw.
     * Compact shuffle positions are transient, never stored as identity IDs. */
    rand_table(shuffle, size, size);
    for (slot = 0; slot < size && count; ++slot) {
        if (destination[0] || destination[1]) {
            destination += 0x528; --count;
            continue;
        }
        index = shuffle[slot];
        if (index >= 216) {
            ordinal = index-216;
            for (offset = 218; offset < 238; ++offset)
                if (eligible(offset) && ordinal-- == 0) break;
            index = offset;
        }
        if (!eligible(index)) continue;
        if (index < 216 && growth[index]) {
            if (growth[index] == -1) mark_seen(0xE000u+(u32)index);
            continue;
        }
        personality = looks(0xE000u+(u32)index);
        if (personality >= 6 || (used & (1u << personality))) continue;
        set_index(destination, index);
        used |= 1u << personality;
        mark_seen(0xE000u+(u32)index);
        destination += 0x528; --count;
    }
}
