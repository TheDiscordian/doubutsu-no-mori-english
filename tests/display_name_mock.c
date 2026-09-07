/* Synthetic display-name cartridge for portable tests. */
#include <stdint.h>
#include <string.h>
#include "display_name.h"

unsigned int af_display_enabled = 1;
unsigned int af_display_header[8] = {0x41464E4E, 1, 8, 280, 216, 64, 0, 0};
unsigned int af_display_dma_calls, af_display_dma_error;
unsigned short af_display_special_ids[64];

unsigned int af_display_test_installed(void) { return af_display_enabled; }
unsigned int af_display_test_special_id(unsigned int index) { return af_display_special_ids[index]; }
void af_display_test_dma(void *destination, unsigned int source, unsigned int size) {
    unsigned int i, offset;
    ++af_display_dma_calls;
    if ((uintptr_t)destination % 16u) af_display_dma_error = 1;
    if (source == AF_DISPLAY_NAME_VROM && size == 32u) {
        memcpy(destination, af_display_header, 32);
        return;
    }
    offset = source-AF_DISPLAY_NAME_VROM-32u;
    if (source < AF_DISPLAY_NAME_VROM+32u || offset % 16u || size != 16u || offset+size > 280u*8u) {
        af_display_dma_error = 1;
        return;
    }
    for (i = 0; i < size; ++i) ((unsigned char *)destination)[i] = 32u+(offset+i) % 95u;
}
