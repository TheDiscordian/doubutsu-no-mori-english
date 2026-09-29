#include "resource_dma.h"
extern int af_resource_virtual(void *,unsigned int,unsigned int);
int af_v3_paged_dma(void *dest,unsigned int source,unsigned int bytes) {
    return af_v3_resource_read(dest,source,bytes,af_resource_virtual);
}
