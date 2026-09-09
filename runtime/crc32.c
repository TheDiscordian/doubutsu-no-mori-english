#include "crc32.h"

unsigned int af_crc32(const unsigned char *data, unsigned int size) {
    unsigned int crc = 0xFFFFFFFFu, i, bit;
    for (i = 0; i < size; ++i) {
        crc ^= data[i];
        for (bit = 0; bit < 8; ++bit)
            crc = (crc >> 1) ^ ((0u-(crc & 1u)) & 0xEDB88320u);
    }
    return crc ^ 0xFFFFFFFFu;
}
