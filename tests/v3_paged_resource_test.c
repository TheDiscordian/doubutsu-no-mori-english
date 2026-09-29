#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/paged_resource.h"
static unsigned int reads,fail_at;
static unsigned char expected[0x24000],output[0x24000+16];
static int dma(void *p,unsigned int source,unsigned int n) {
    assert(source>=0x80100000u && source<0x80124000u && n<=4096u);
    reads++;if(reads==fail_at)return -1;
    memcpy(p,expected+source-0x80100000u,n);return 0;
}
static unsigned int crc(const void *p,unsigned int n) {
    assert(p==output && n==sizeof(expected));
    return memcmp(p,expected,n)?1u:0x12345678u;
}
int main(void) {
    unsigned int pages[40]={0x41465047u,sizeof(expected),4096,36};
    for(unsigned int i=0;i<sizeof(expected);i++)expected[i]=(unsigned char)(i*17+i/4096);
    for(unsigned int i=0;i<36;i++)pages[4+i]=0x100000u+i*4096u;
    memset(output,0xA5,sizeof(output));
    assert(af_v3_paged_read(output,sizeof(expected),pages,40,0x12345678,dma,crc));
    assert(reads==36 && !memcmp(output,expected,sizeof(expected)));
    for(unsigned int i=sizeof(expected);i<sizeof(output);i++)assert(output[i]==0xA5);
    const unsigned int invalid[][2]={{0,0},{1,0},{2,2048},{3,0},{3,37},
        {4,0x100004},{39,0xFFFF0},{39,0x3FFFFF0},{39,0x4000000}};
    for(unsigned int i=0;i<sizeof(invalid)/sizeof(*invalid);i++) {
        unsigned int at=invalid[i][0],old=pages[at];pages[at]=invalid[i][1];
        reads=0;memset(output,0xA5,sizeof(output));
        assert(!af_v3_paged_read(output,sizeof(expected),pages,40,0x12345678,dma,crc));
        assert(!reads);for(unsigned int j=0;j<sizeof(output);j++)assert(output[j]==0xA5);
        pages[at]=old;
    }
    assert(!af_v3_paged_read(output,sizeof(expected),pages,39,0x12345678,dma,crc));
    assert(!af_v3_paged_read(output,sizeof(expected)-1,pages,40,0x12345678,dma,crc));
    assert(!af_v3_paged_read(output,sizeof(expected),pages,40,0,dma,crc));
    reads=0;fail_at=12;
    assert(!af_v3_paged_read(output,sizeof(expected),pages,40,0x12345678,dma,crc) && reads==12);
    reads=fail_at=0;
    assert(af_v3_paged_read(output,sizeof(expected),pages,40,0x12345678,dma,crc));
    puts("Complete paged loading, destination bounds, source rejection, CRC and transfer failures pass");
}
