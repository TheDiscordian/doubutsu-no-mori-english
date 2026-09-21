#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_PW_PACKET_VROM 0x03F10000u
#define AF_PW_PACKET_CRC 0x12345678u
#include "../overlays/v3/password_bootstrap.c"
volatile af_pw_u32 af_pw_cache;
af_pw_u8 af_pw_packet[0x8000];
static unsigned dma_calls, crc_calls, faults, cache_calls, executions;
static int dma_result, wrong_crc;
int af_pw_dma(void *p, af_pw_u32 vrom, af_pw_u32 size) {
    assert(p==packet && vrom==AF_PW_PACKET_VROM && size==sizeof(af_pw_packet));
    dma_calls++; return dma_result;
}
af_pw_u32 af_pw_crc(void *p, af_pw_u32 size) {
    assert(p==packet && size==sizeof(af_pw_packet));crc_calls++;
    return AF_PW_PACKET_CRC ^ (af_pw_u32)wrong_crc;
}
void af_pw_writeback(void *p, af_pw_u32 size) {
    assert(p==packet && size==sizeof(af_pw_packet) && cache_calls==0);
    assert(cache!=AF_PW_PACKET_CRC);cache_calls++;
}
void af_pw_invalidate(void *p, af_pw_u32 size) {
    assert(p==packet && size==sizeof(af_pw_packet) && cache_calls==1);
    assert(cache!=AF_PW_PACKET_CRC);cache_calls++;
}
void af_pw_fault(const char *a, const char *b) { assert(a&&b); faults++; }
int af_pw_execute(const af_pw_u8 *code, const af_pw_u8 *player,
                  const af_pw_u8 *town, struct AfPasswordOffer *offer) {
    assert(cache==AF_PW_PACKET_CRC && cache_calls==2);
    assert(code && player && town && offer); executions++;
    return AF_PW_CANCEL;
}
int main(void) {
    af_pw_u8 text[28]={0}, name[8]={0};
    struct AfPasswordOffer offer, original;
    memset(&offer,0xA5,sizeof(offer));original=offer;
    dma_result=1;
    assert(!af_v3_password_boot_check(text,name,name,&offer));
    assert(dma_calls==1 && !crc_calls && faults==1 && !cache_calls && !executions && !cache);
    dma_result=0;wrong_crc=1;
    assert(!af_v3_password_boot_check(text,name,name,&offer));
    assert(dma_calls==2 && crc_calls==1 && faults==2 && !cache_calls && !executions && !cache);
    wrong_crc=0;
    for(int i=0;i<3;i++)assert(af_v3_password_boot_check(text,name,name,&offer)==AF_PW_CANCEL);
    assert(dma_calls==3 && crc_calls==2 && faults==2 && cache_calls==2 && executions==3);
    cache=0;cache_calls=0; /* Actual startup resets this field on a new session. */
    assert(af_v3_password_boot_check(text,name,name,&offer)==AF_PW_CANCEL);
    assert(dma_calls==4 && crc_calls==3 && cache_calls==2 && executions==4);
    assert(!memcmp(&offer,&original,sizeof(offer)));
    puts("Loader failure, cache ordering, repeated calls, and cold-session reset pass");
}
