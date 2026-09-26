#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#define AF_EFFECT_PROFILES 0x02600000u
#define AF_EFFECT_COUNT 2u
#include "../overlays/v3/effect_loader.c"
static jmp_buf fault;
static int loaded,dmas,natives,load_ok=1,dma_bad,crc_bad;
static u32 body[8]={0x804C8100,0x804C8200,0x804C8300,0x804C8400,0xFFFE00FF,0xC47A0CFF,0x12345678,0x41464550};
static int load(void) { ++loaded;return load_ok; }
int (*effect_room_loader)(void)=load;
void af_effect_native_load(u32 a,u32 b,void *c,void *d,void *e) {
    assert(a==0x123400 && b==0x123800 && (uptr)c==0x80600000 && (uptr)d==0x80600020 && e);++natives;
}
int af_effect_dma(void *p,u32 v,u32 n) {
    assert((v==AF_EFFECT_PROFILES || v==AF_EFFECT_PROFILES+64) && n==32);
    memcpy(p,body,32);++dmas;return dma_bad;
}
u32 af_effect_crc(void *p,u32 n) { assert(p && n==24);return 0x12345678u+crc_bad; }
void af_effect_fault(const char *a,const char *b) { assert(a && b);longjmp(fault,1); }
int main(void) {
    _Alignas(16) u32 out[16];memset(out,0xA5,sizeof(out));
    af_v3_effect_profile_load(0x123400,0x123800,(void *)0x80600000,(void *)0x80600020,out+4);
    assert(natives==1 && !dmas && !loaded);
    for (u32 i=0;i<2;++i) {
        u32 v=AF_EFFECT_PROFILES+i*64;
        af_v3_effect_profile_load(v,v+32,(void *)0x80700000,(void *)0x80700020,out+4);
        assert(!memcmp(out+4,body,32));
    }
    assert(dmas==2 && loaded==2);
    for (int i=0;i<11;++i) {
        u32 v=AF_EFFECT_PROFILES,n=32,ram_n=32;void *dst=out+4;
        load_ok=1;dma_bad=crc_bad=0;effect_room_loader=load;
        u32 saved=body[0],magic=body[7];
        switch(i) {
        case 0:++v;break;case 1:++n;break;case 2:++ram_n;break;
        case 3:dst=(char *)dst+1;break;case 4:effect_room_loader=0;break;
        case 5:load_ok=0;break;case 6:dma_bad=1;break;case 7:crc_bad=1;break;
        case 8:body[7]=0;break;case 9:body[0]=0x804CC000;break;case 10:body[0]|=1;break;
        }
        if (!setjmp(fault)) {
            af_v3_effect_profile_load(v,v+n,(void *)0x80700000,(void *)(uptr)(0x80700000u+ram_n),dst);
            assert(!"Corrupt effect profile accepted");
        }
        body[0]=saved;body[7]=magic;
    }
    for (int i=0;i<4;++i) assert(out[i]==0xA5A5A5A5 && out[i+12]==0xA5A5A5A5);
    puts("effect profile loader pass");
}
