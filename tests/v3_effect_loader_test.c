#include <assert.h>
#include <setjmp.h>
#include <stdio.h>
#include <string.h>
#define AF_EFFECT_PROFILES 0x02600000u
#ifndef AF_EFFECT_COUNT
#define AF_EFFECT_COUNT 2u
#endif
#include "../overlays/v3/effect_loader.c"
static jmp_buf fault;
static int loaded,dmas,natives,load_ok=1,dma_bad,crc_bad;
static u32 body[8]={0,0,0,0,0xFFFE00FF,0xC47A0CFF,0x12345678,0x41464550};
static int load(void) { ++loaded;return load_ok; }
int (*effect_room_loader)(void)=load;
void af_effect_native_load(u32 a,u32 b,void *c,void *d,void *e) {
    assert(a==0x123400 && b==0x123800 && (uptr)c==0x80600000 && (uptr)d==0x80600020 && e);++natives;
}
int af_effect_dma(void *p,u32 v,u32 n) {
    assert(v>=AF_EFFECT_PROFILES && v<AF_EFFECT_PROFILES+AF_EFFECT_COUNT*64 && !(v%64) && n==32);
    memcpy(p,body,32);++dmas;return dma_bad;
}
u32 af_effect_crc(void *p,u32 n) { assert(p && n==24);return 0x12345678u+crc_bad; }
void af_effect_fault(const char *a,const char *b) { assert(a && b);longjmp(fault,1); }
int main(void) {
    _Alignas(16) u32 out[16];memset(out,0xA5,sizeof(out));
    af_v3_effect_profile_load(0x123400,0x123800,(void *)0x80600000,(void *)0x80600020,out+4);
    assert(natives==1 && !dmas && !loaded);
    for (u32 i=0;i<AF_EFFECT_COUNT;++i) {
        u32 v=AF_EFFECT_PROFILES+i*64;
        u32 base=AF_EFFECT_CODE_START;
#ifdef AF_EFFECT_SKY_START
        if(i>=AF_EFFECT_ROOM_COUNT)base=AF_EFFECT_SKY_START;
#endif
#ifdef AF_EFFECT_PARTICIPANT_START
        if(i>=AF_EFFECT_ROOM_COUNT+AF_EFFECT_SKY_COUNT)base=AF_EFFECT_PARTICIPANT_START;
#endif
        for(u32 k=0;k<4;k++)body[k]=base+256+k*64;
        af_v3_effect_profile_load(v,v+32,(void *)0x80700000,(void *)0x80700020,out+4);
        assert(!memcmp(out+4,body,32));
    }
    assert(dmas==AF_EFFECT_COUNT && loaded==AF_EFFECT_ROOM_COUNT);
    for(u32 k=0;k<4;k++)body[k]=AF_EFFECT_CODE_START+256+k*64;
    for (int i=0;i<11;++i) {
        u32 v=AF_EFFECT_PROFILES,n=32,ram_n=32;void *dst=out+4;
        load_ok=1;dma_bad=crc_bad=0;effect_room_loader=load;
        u32 saved=body[0],magic=body[7];
        switch(i) {
        case 0:++v;break;case 1:++n;break;case 2:++ram_n;break;
        case 3:dst=(char *)dst+1;break;case 4:effect_room_loader=0;break;
        case 5:load_ok=0;break;case 6:dma_bad=1;break;case 7:crc_bad=1;break;
        case 8:body[7]=0;break;case 9:body[0]=AF_EFFECT_CODE_END;break;case 10:body[0]|=1;break;
        }
        if (!setjmp(fault)) {
            af_v3_effect_profile_load(v,v+n,(void *)0x80700000,(void *)(uptr)(0x80700000u+ram_n),dst);
            assert(!"Corrupt effect profile accepted");
        }
        body[0]=saved;body[7]=magic;
    }
#ifdef AF_EFFECT_SKY_START
    for(volatile int i=0;i<3;i++) {
        effect_room_loader=load;load_ok=1;dma_bad=crc_bad=0;
        volatile u32 v=AF_EFFECT_PROFILES;
        if(i==0)body[0]=AF_EFFECT_SKY_START;
        else {v+=AF_EFFECT_ROOM_COUNT*64;body[0]=i==1?AF_EFFECT_CODE_START:AF_EFFECT_SKY_END;}
        if(!setjmp(fault)) {
            af_v3_effect_profile_load(v,v+32,(void *)0x80700000,(void *)0x80700020,out+4);
            assert(!"Wrong callback packet accepted");
        }
    }
#endif
#ifdef AF_EFFECT_PARTICIPANT_START
    for(volatile int i=0;i<4;i++) {
        volatile u32 v=AF_EFFECT_PROFILES+(AF_EFFECT_ROOM_COUNT+AF_EFFECT_SKY_COUNT)*64;
        for(u32 k=0;k<4;k++)body[k]=AF_EFFECT_PARTICIPANT_START+256+k*64;
        body[0]=i==0?AF_EFFECT_CODE_START:i==1?AF_EFFECT_SKY_START:
            i==2?AF_EFFECT_PARTICIPANT_END:AF_EFFECT_PARTICIPANT_START+1;
        if(!setjmp(fault)) {
            af_v3_effect_profile_load(v,v+32,(void *)0x80700000,(void *)0x80700020,out+4);
            assert(!"Wrong participant callback range accepted");
        }
    }
#endif
    for (int i=0;i<4;++i) assert(out[i]==0xA5A5A5A5 && out[i+12]==0xA5A5A5A5);
    puts("effect profile loader pass");
}
