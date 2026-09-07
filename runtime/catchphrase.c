/* Display-time translation of default catchphrases; saved bytes never change. */
#include "catchphrase.h"

#ifdef __mips__
static unsigned int installed(void) {
    return *(volatile unsigned int *)0x80194920u == AF_CATCHPHRASE_VROM;
}
static void dma(void *destination, unsigned int source, unsigned int size) {
    ((void (*)(void *, unsigned int, unsigned int))0x80026B44u)(destination, source, size);
}
#else
extern unsigned int af_catchphrase_test_installed(void);
extern void af_catchphrase_test_dma(void *, unsigned int, unsigned int);
#define installed af_catchphrase_test_installed
#define dma af_catchphrase_test_dma
#endif

static unsigned int key_at(const unsigned char *source) {
    return ((unsigned int)source[0] << 24) | ((unsigned int)source[1] << 16)
        | ((unsigned int)source[2] << 8) | source[3];
}

int af_catchphrase_header_valid(const unsigned int *header) {
    return header && header[0] == 0x41464350u && header[1] == 1u
        && header[2] == AF_CATCHPHRASE_WIDTH && header[3] == AF_CATCHPHRASE_COUNT
        && header[4] == 16u && header[5] == 4u && !header[6] && !header[7];
}

int af_load_catchphrase(unsigned char *destination, unsigned int capacity,
                       unsigned int npc, const unsigned char *saved) {
    unsigned int header[8] __attribute__((aligned(16)));
    unsigned char row[16] __attribute__((aligned(16)));
    unsigned char candidate[AF_CATCHPHRASE_WIDTH];
    unsigned int key, low = 0, high = AF_CATCHPHRASE_COUNT, middle, i;
    int found = 0, conflict = 0;
    if (!destination || capacity < AF_CATCHPHRASE_WIDTH || !saved || !installed()
            || npc < 0xE000u || npc >= 0xE000u+AF_CATCHPHRASE_COUNT) return 0;
    key = key_at(saved);
    dma(header, AF_CATCHPHRASE_VROM, sizeof(header));
    if (!af_catchphrase_header_valid(header)) return 0;
    while (low < high) {
        middle = low+(high-low)/2;
        dma(row, AF_CATCHPHRASE_VROM+32u+middle*16u, sizeof(row));
        if (key_at(row) < key) low = middle+1;
        else high = middle;
    }
    for (; low < AF_CATCHPHRASE_COUNT; ++low) {
        dma(row, AF_CATCHPHRASE_VROM+32u+low*16u, sizeof(row));
        if (key_at(row) != key) break;
        if ((((unsigned int)row[4] << 8) | row[5]) == npc) {
            for (i = 0; i < AF_CATCHPHRASE_WIDTH; ++i) destination[i] = row[6+i];
            return 1;
        }
        for (i = 0; i < AF_CATCHPHRASE_WIDTH; ++i) {
            if (found && candidate[i] != row[6+i]) conflict = 1;
            if (!found) candidate[i] = row[6+i];
        }
        found = 1;
    }
    if (!found || conflict) return 0;
    for (i = 0; i < AF_CATCHPHRASE_WIDTH; ++i) destination[i] = candidate[i];
    return 1;
}
