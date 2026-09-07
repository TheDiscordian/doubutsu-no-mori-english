/* Original display-only API. Native six-byte name loaders remain unchanged. */
#include "display_name.h"

#ifdef __mips__
static unsigned int installed(void) {
    return *(volatile unsigned int *)0x8019491Cu == AF_DISPLAY_NAME_VROM;
}
static unsigned int special_id(unsigned int index) {
    return *(const unsigned short *)(0x8010B510u+index*12u);
}
static void dma(void *destination, unsigned int source, unsigned int size) {
    ((void (*)(void *, unsigned int, unsigned int))0x80026B44u)(destination, source, size);
}
#else
extern unsigned int af_display_test_installed(void);
extern unsigned int af_display_test_special_id(unsigned int);
extern void af_display_test_dma(void *, unsigned int, unsigned int);
#define installed af_display_test_installed
#define special_id af_display_test_special_id
#define dma af_display_test_dma
#endif

int af_display_name_index(unsigned int npc) {
    unsigned int index;
    if (npc > 0xFFFFu) return -1;
    if (npc >= 0xE000u && npc < 0xE000u+AF_VILLAGER_COUNT) return (int)(npc-0xE000u);
    for (index = 0; index < AF_SPECIAL_COUNT; ++index)
        if (npc == special_id(index)) return (int)(AF_VILLAGER_COUNT+index);
    return -1;
}

int af_display_name_header_valid(const unsigned int *header) {
    return header && header[0] == 0x41464E4Eu && header[1] == 1u &&
        header[2] == AF_DISPLAY_NAME_WIDTH && header[3] == AF_DISPLAY_NAME_COUNT &&
        header[4] == AF_VILLAGER_COUNT && header[5] == AF_SPECIAL_COUNT &&
        !header[6] && !header[7];
}

int af_load_display_name(unsigned char *destination, unsigned int capacity, unsigned int npc) {
    unsigned int header[8] __attribute__((aligned(16)));
    unsigned char pair[16] __attribute__((aligned(16)));
    unsigned int i, offset;
    int index;
    if (!destination || capacity < AF_DISPLAY_NAME_WIDTH || !installed()) return 0;
    index = af_display_name_index(npc);
    if (index < 0) return 0;
    dma(header, AF_DISPLAY_NAME_VROM, sizeof(header));
    if (!af_display_name_header_valid(header)) return 0;
    dma(pair, AF_DISPLAY_NAME_VROM+32u+((unsigned int)index & ~1u)*8u, sizeof(pair));
    offset = ((unsigned int)index & 1u)*8u;
    for (i = 0; i < AF_DISPLAY_NAME_WIDTH; ++i) destination[i] = pair[offset+i];
    return 1;
}
