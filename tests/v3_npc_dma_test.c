#include <assert.h>
#include <stdio.h>
#include "npc_dma.h"
const AFNpcDma af_v3_npc_dma={0x41464E44,1,10,12,{
    {0x03FE0000,0x03FE24F0,0x03000000},{0x03FE4000,0x03FE5020,0x03010000},
    {0x03FE8000,0x03FE8010,0x03020000},{0x03FEC000,0x03FEC010,0x03030000},
    {0x03FF0000,0x03FF0010,0x03040000},{0x03FF4000,0x03FF4010,0x03050000},
    {0x03FF8000,0x03FF8010,0x03060000},{0x03FFC000,0x03FFC010,0x03070000},
    {0x04800000,0x04801A20,0x03080000},{0x04804000,0x04805020,0x03090000}}};
volatile unsigned int af_npc_dma_worker[2]={0x0C009A0A,0x00808025};
static unsigned int old_calls,transfers,errors,flushed,pi_fails;
static AFNpcDmaRequest *expected;
void af_npc_dma_previous(AFNpcDmaRequest *q) {assert(q==expected);++old_calls;}
int af_npc_dma_pi(unsigned int rom,void *ram,unsigned int bytes) {
    assert(ram==expected->vram && bytes==expected->bytes);
    const AFNpcDmaRow *row=0;
    for(unsigned i=0;i<af_v3_npc_dma.count;i++)
        if(expected->vrom>=af_v3_npc_dma.rows[i].start && expected->vrom<af_v3_npc_dma.rows[i].end)
            row=af_v3_npc_dma.rows+i;
    assert(row && rom==row->physical+expected->vrom-row->start);
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
    pi_fails=0;q.vrom=0x04800000;q.bytes=0x1A20;
    af_v3_npc_dma_request(&q);assert(transfers==4 && errors==5);
    q.vrom=0x04804010;q.bytes=0x1010;
    af_v3_npc_dma_request(&q);assert(transfers==5 && errors==5);
    q.bytes+=16;af_v3_npc_dma_request(&q);assert(transfers==5 && errors==6);
    q.vrom=0x04000000;q.bytes=16;af_v3_npc_dma_request(&q);assert(old_calls==3);
    puts("Shared object DMA: whole/partial transfers, bounds, failure, unchanged notifications and fallback pass");
}
