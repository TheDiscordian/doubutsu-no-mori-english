/* Synthetic cartridge fixture for the original item-name loader's host tests. */
#include <stdint.h>
#include <string.h>
#include "item_name.h"

unsigned int af_test_enabled = 1;
unsigned int af_test_header[8] = {0x4146494Eu, 1, 16, 4544, 0, 0, 0, 0};
unsigned int af_test_dma_calls, af_test_dma_error;
unsigned char af_test_window[0x300];
unsigned int af_test_native_calls;

void *af_item_test_window(void) { return af_test_window; }
int af_item_test_code_size(unsigned char *data, int index) {
    return data[index] == 0x7Fu || data[index] == 0x80u ? 2 : 1;
}
int af_item_test_move(unsigned char *data, int to, int from, int length) {
    int result = length+to-from;
    memmove(data+to, data+from, (unsigned int)(length-from));
    if (result < length) memset(data+result, ' ', (unsigned int)(length-result));
    return result;
}
void af_item_test_copy(unsigned char *destination, const unsigned char *source, int length) {
    memcpy(destination, source, (unsigned int)length);
}
void af_item_test_native_name(unsigned char *destination, unsigned int item) {
    unsigned int i;
    ++af_test_native_calls;
    for (i = 0; i < 10; ++i) destination[i] = 'A'+((item+i) % 26u);
}

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
