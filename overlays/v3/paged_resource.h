#ifndef AF_V3_PAGED_RESOURCE_H
#define AF_V3_PAGED_RESOURCE_H
/* AFPG directories are part of a previously verified code/configuration packet.
 * Reject every malformed extent before the first destination write. Callers
 * provide a complete reserved destination, its size, and its expected CRC. */
static int af_v3_paged_read(unsigned char *dest,unsigned int size,
        const unsigned int *pages,unsigned int words,unsigned int expected_crc,
        int (*dma)(void *,unsigned int,unsigned int),
        unsigned int (*crc)(const void *,unsigned int)) {
    if(!dest || !pages || words<4u || !size || (size&15u) || size>0x800000u ||
       pages[0]!=0x41465047u || pages[1]!=size || pages[2]!=4096u ||
       !pages[3] || pages[3]>words-4u || pages[3]!=(size+4095u)/4096u)return 0;
    for(unsigned int i=0;i<pages[3];i++) {
        unsigned int n=size-i*4096u;if(n>4096u)n=4096u;
        if((pages[i+4]&15u) || pages[i+4]<0x100000u || pages[i+4]>0x4000000u-n)return 0;
    }
    for(unsigned int i=0;i<pages[3];i++) {
        unsigned int n=size-i*4096u;if(n>4096u)n=4096u;
        if(dma(dest+i*4096u,pages[i+4]|0x80000000u,n))return 0;
    }
    return crc(dest,size)==expected_crc;
}
#endif
