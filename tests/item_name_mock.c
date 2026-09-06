/* Synthetic cartridge fixture for the original item-name loader's host tests. */
#include <stdint.h>
#include <string.h>
#include "item_name.h"

unsigned int af_test_enabled = 1;
unsigned int af_test_header[8] = {0x4146494Eu, 1, 16, 4544, 0, 0, 0, 0};
unsigned int af_test_dma_calls, af_test_dma_error;

unsigned int af_item_test_installed(void) { return af_test_enabled; }
unsigned int af_item_test_convert(unsigned int item) {
    if (item >= 0x17ACu && item < 0x1BA8u) return 0x2400u+((item-0x17ACu) >> 2);
    if (item >= 0x1BA8u && item < 0x1C28u) return 0x2D00u+((item-0x1BA8u) >> 2);
    if (item >= 0x1C28u && item < 0x1CA8u) return 0x2300u+((item-0x1C28u) >> 2);
    if (item >= 0x1CA8u && item < 0x1D28u) return 0x2204u+((item-0x1CA8u) >> 2);
    return item;
}
void af_item_test_dma(void *destination, unsigned int source, unsigned int size) {
    unsigned int i, index;
    ++af_test_dma_calls;
    if ((uintptr_t)destination % 8u) af_test_dma_error = 1;
    if (source == AF_ITEM_VROM && size == 32u) {
        memcpy(destination, af_test_header, 32);
        return;
    }
    if (source < AF_ITEM_VROM+32u || (source-AF_ITEM_VROM-32u) % 16u || size != 16u) {
        af_test_dma_error = 1;
        return;
    }
    index = (source-AF_ITEM_VROM-32u)/16u;
    if (index >= AF_ITEM_COUNT) af_test_dma_error = 1;
    for (i = 0; i < size; ++i) ((unsigned char *)destination)[i] = 32u+(index+i) % 95u;
}
