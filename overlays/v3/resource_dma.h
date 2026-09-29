#ifndef AF_V3_RESOURCE_DMA_H
#define AF_V3_RESOURCE_DMA_H
/* Virtual DMA does not understand our high-bit physical-ROM marker. */
static int af_v3_resource_read(void *dest,unsigned int source,unsigned int bytes,
        int (*virtual_read)(void *,unsigned int,unsigned int)) {
    if(source&0x80000000u) {
        source&=0x7FFFFFFFu;
        if(!bytes || (source&1u) || (bytes&1u) || source>0x4000000u ||
                bytes>0x4000000u-source)return -1;
#ifdef __mips__
        return ((int (*)(unsigned int,void *,unsigned int))0x80026500u)(source,dest,bytes);
#else
        extern int af_test_resource_pi(unsigned int,void *,unsigned int);
        return af_test_resource_pi(source,dest,bytes);
#endif
    }
    return virtual_read(dest,source,bytes);
}
#endif
