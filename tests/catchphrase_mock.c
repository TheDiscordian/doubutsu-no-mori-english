/* Synthetic catchphrase cartridge and actor fixture for portable runtime tests. */
#include <stdint.h>
#include <string.h>
#include "catchphrase.h"

unsigned int af_catchphrase_enabled = 1, af_catchphrase_dma_calls, af_catchphrase_dma_error;
unsigned int af_catchphrase_header[8] = {0x41464350, 1, 10, 216, 16, 4, 0, 0};
unsigned char af_catchphrase_rows[216*16], af_catchphrase_animal[0x528];
unsigned int af_catchphrase_native_calls;

unsigned int af_catchphrase_test_installed(void) { return af_catchphrase_enabled; }
void af_catchphrase_test_dma(void *destination, unsigned int source, unsigned int size) {
    unsigned int offset = source-AF_CATCHPHRASE_VROM-32u;
    ++af_catchphrase_dma_calls;
    if ((uintptr_t)destination % 16u) af_catchphrase_dma_error = 1;
    if (source == AF_CATCHPHRASE_VROM && size == 32u) {
        memcpy(destination, af_catchphrase_header, 32);
    } else if (source >= AF_CATCHPHRASE_VROM+32u && offset % 16u == 0u
               && size == 16u && offset+size <= sizeof(af_catchphrase_rows)) {
        memcpy(destination, af_catchphrase_rows+offset, size);
    } else af_catchphrase_dma_error = 1;
}
const unsigned char *af_catchphrase_test_animal(const unsigned char *actor) {
    return actor[0x177] ? af_catchphrase_animal : 0;
}
const unsigned char *af_catchphrase_test_native(const unsigned char *actor) {
    ++af_catchphrase_native_calls;
    return actor[2] == 3 && actor[0x177] ? af_catchphrase_animal+0x4E5 : (const unsigned char *)"none";
}
int af_catchphrase_test_code_size(unsigned char *data, int index) {
    return data[index] == 0x7Fu ? (data[index+1] == 0x50u ? 6 : 2) : 1;
}
int af_catchphrase_test_move(unsigned char *data, int to, int from, int length) {
    memmove(data+to, data+from, (unsigned int)(length-from));
    return length+to-from;
}
void af_catchphrase_test_copy(unsigned char *destination, const unsigned char *source, int length) {
    if (length) memcpy(destination, source, (unsigned int)length);
}
