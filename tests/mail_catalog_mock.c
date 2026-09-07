/* Isolated host DMA adapter. Metadata words follow the native big-endian ABI. */
#include <string.h>
#include "../runtime/mail/catalog.h"

unsigned char af_mail_catalog_rom[0x100000];
unsigned int af_mail_catalog_enabled = 1;
unsigned int af_mail_catalog_reads, af_mail_catalog_dma_error, af_mail_catalog_fail_read;

unsigned int af_mail_catalog_test_installed(void) { return af_mail_catalog_enabled; }
unsigned int af_mail_catalog_workspace_size(void) { return sizeof(AfMailWorkspace); }

int af_mail_catalog_test_dma(void *destination, unsigned int source, unsigned int size) {
    unsigned int offset, i;
    unsigned char *out = destination;
    ++af_mail_catalog_reads;
    if (source < AF_MAIL_CATALOG_VROM || source-AF_MAIL_CATALOG_VROM > AF_MAIL_CATALOG_BYTES
            || size > AF_MAIL_CATALOG_BYTES-(source-AF_MAIL_CATALOG_VROM)
            || ((__UINTPTR_TYPE__)destination & 15u) || (source & 15u) || (size & 15u)) {
        ++af_mail_catalog_dma_error;
        return 0;
    }
    offset = source-AF_MAIL_CATALOG_VROM;
    if (af_mail_catalog_fail_read == af_mail_catalog_reads) {
        if (size) out[0] = 0xEE; /* Partial DMA must not publish output. */
        return 0;
    }
    if (offset < 78112u) {
        unsigned int *words = destination;
        for (i = 0; i < size; i += 4) {
            const unsigned char *p = af_mail_catalog_rom+offset+i;
            words[i/4] = ((unsigned int)p[0] << 24) | ((unsigned int)p[1] << 16)
                | ((unsigned int)p[2] << 8) | p[3];
        }
    } else {
        memcpy(destination, af_mail_catalog_rom+offset, size);
    }
    return 1;
}
