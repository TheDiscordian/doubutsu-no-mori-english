#include <assert.h>
#include <stdio.h>
#include "npc_dma.h"
const AFNpcDma af_v3_npc_dma={0x41464E44,1,2,12,{
    {0x03FE0000,0x03FE24F0,0x03000000},{0x03FE4000,0x03FE5020,0x03010000}}};
volatile unsigned int af_npc_dma_worker[2]={0x0C009A0A,0x00808025};
static unsigned int old_calls,transfers,errors,flushed,pi_fails;
static AFNpcDmaRequest *expected;
void af_npc_dma_previous(AFNpcDmaRequest *q) {assert(q==expected);++old_calls;}
int af_npc_dma_pi(unsigned int rom,void *ram,unsigned int bytes) {
    assert(ram==expected->vram && bytes==expected->bytes);
    unsigned int offset=expected->vrom-0x03FE0000;
    assert(rom==(offset<0x4000?0x03000000+offset:0x03010000+offset-0x4000));
    ++transfers;return pi_fails;
}
void af_npc_dma_error(AFNpcDmaRequest *q,const char *file,const char *error,const char *detail) {
    assert(q==expected && !file && error && !detail);++errors;
}
void af_npc_dma_writeback(void *p,unsigned int n) {assert(p==(void *)af_npc_dma_worker && n==8 && !flushed);flushed=1;}
void af_npc_dma_invalidate(void *p,unsigned int n) {assert(p==(void *)af_npc_dma_worker && n==8 && flushed==1);flushed=2;}
int main(void) {
    assert(af_v3_npc_dma_init()==1 && flushed==2 && af_npc_dma_worker[1]==0x00808025);
    assert(af_v3_npc_dma_init()==1 && flushed==2);
    af_npc_dma_worker[0]=0;assert(!af_v3_npc_dma_init());
    AFNpcDmaRequest q={.vrom=0x03FE0000,.vram=(void *)0x80600000,.bytes=0x24F0,
        .queue=(void *)17,.message=(void *)29};expected=&q;
    af_v3_npc_dma_request(&q);assert(transfers==1 && !errors && !old_calls);
    q.vrom=0x03FE4010;q.bytes=0x1010;
    af_v3_npc_dma_request(&q);assert(transfers==2 && !errors);
    assert(q.queue==(void *)17 && q.message==(void *)29);
    q.bytes=0x1020;af_v3_npc_dma_request(&q);assert(errors==1 && transfers==2);
    q.bytes=0xFFFFFFF0;af_v3_npc_dma_request(&q);assert(errors==2 && transfers==2);
    q.bytes=16;q.vram=(void *)0x807FFFF8;af_v3_npc_dma_request(&q);assert(errors==3 && transfers==2);
    q.vram=(void *)0x80000001;af_v3_npc_dma_request(&q);assert(errors==4 && transfers==2);
    q.vram=(void *)0x80000000;pi_fails=1;af_v3_npc_dma_request(&q);assert(errors==5 && transfers==3);
    q.vrom=0x02200000;af_v3_npc_dma_request(&q);assert(old_calls==1);
    q.vrom=0x03FE3000;af_v3_npc_dma_request(&q);assert(old_calls==2);
    puts("Shared object DMA: whole/partial transfers, bounds, failure, unchanged notifications and fallback pass");
}
