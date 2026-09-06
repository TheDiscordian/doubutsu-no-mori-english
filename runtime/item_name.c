/* Original bounded item-name API. Existing ten-byte callers are not redirected. */
#include "item_name.h"

int af_item_name_index(unsigned int item) {
    static const unsigned short counts[16] = {
        64, 4, 36, 32, 255, 30, 64, 64, 7, 10, 55, 1, 96, 32, 2, 4
    };
    unsigned int group, index, offset = 0, i;
    if (item > 0xFFFFu) return -1;
    if ((item >> 12) == 1u) {
        index = item & 0xFFFu;
        return index < 3788u ? (int)(756u+index) : -1;
    }
    if ((item >> 12) != 2u) return -1;
    group = (item >> 8) & 15u;
    index = item & 255u;
    if (index >= counts[group]) return -1;
    for (i = 0; i < group; ++i) offset += counts[i];
    return (int)(offset+index);
}

int af_item_header_valid(const unsigned int *header) {
    unsigned int i;
    if (!header || header[0] != 0x4146494Eu || header[1] != 1u ||
        header[2] != AF_ITEM_WIDTH || header[3] != AF_ITEM_COUNT) return 0;
    for (i = 4; i < 8; ++i) if (header[i]) return 0;
    return 1;
}

#ifdef __mips__
static unsigned int installed(void) {
    return *(volatile unsigned int *)0x80194918u == AF_ITEM_VROM;
}
static void dma(void *destination, unsigned int source, unsigned int size) {
    ((void (*)(void *, unsigned int, unsigned int))0x80026B44u)(destination, source, size);
}
static unsigned int convert(unsigned int item) {
    return ((unsigned short (*)(unsigned short))0x800BF10Cu)((unsigned short)item);
}
#else
/* Host tests provide isolated memory-backed resource/retail-conversion mocks. */
extern unsigned int af_item_test_installed(void);
extern void af_item_test_dma(void *, unsigned int, unsigned int);
extern unsigned int af_item_test_convert(unsigned int);
#define installed af_item_test_installed
#define dma af_item_test_dma
#define convert af_item_test_convert
#endif

int af_load_item_name(unsigned char *destination, unsigned int capacity, unsigned int item) {
    unsigned int header[8] __attribute__((aligned(16)));
    unsigned char name[AF_ITEM_WIDTH] __attribute__((aligned(16)));
    unsigned int i;
    int index;
    if (!destination || capacity < AF_ITEM_WIDTH || item > 0xFFFFu || !installed()) return 0;
    index = item ? af_item_name_index(convert(item)) : -1;
    if (item && index < 0) return 0;
    dma(header, AF_ITEM_VROM, sizeof(header));
    if (!af_item_header_valid(header)) return 0;
    if (!item) {
        for (i = 0; i < AF_ITEM_WIDTH; ++i) destination[i] = ' ';
        return 1;
    }
    dma(name, AF_ITEM_VROM+32u+(unsigned int)index*AF_ITEM_WIDTH, AF_ITEM_WIDTH);
    for (i = 0; i < AF_ITEM_WIDTH; ++i) destination[i] = name[i];
    return 1;
}
