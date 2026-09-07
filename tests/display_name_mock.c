/* Synthetic display-name cartridge for portable tests. */
#include <stdint.h>
#include <string.h>
#include "display_name.h"

unsigned int af_display_enabled = 1;
unsigned int af_display_header[8] = {0x41464E4E, 1, 8, 280, 216, 64, 0, 0};
unsigned int af_display_dma_calls, af_display_dma_error;
unsigned short af_display_special_ids[64];
unsigned char af_display_animal[12];
unsigned int af_display_native_calls;

const unsigned char *af_display_test_animal(const unsigned char *actor) {
    return actor[0x177] ? af_display_animal : 0;
}
void af_display_test_native(unsigned char *destination, const unsigned char *actor) {
    ++af_display_native_calls;
    memcpy(destination, actor ? "native" : "------", 6);
}
int af_display_test_code_size(unsigned char *data, int index) {
    return data[index] == 0x7Fu ? (data[index+1] == 0x50u ? 6 : 2) : 1;
}
int af_display_test_move(unsigned char *data, int to, int from, int length) {
    memmove(data+to, data+from, (unsigned int)(length-from));
    return length+to-from;
}
void af_display_test_copy(unsigned char *destination, const unsigned char *source, int length) {
    if (length) memcpy(destination, source, (unsigned int)length);
}

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
