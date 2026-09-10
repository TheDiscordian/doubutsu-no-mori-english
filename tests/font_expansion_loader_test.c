#include <assert.h>
#include <stdio.h>
#include <string.h>
typedef unsigned int u32;
struct FontConfig { u32 vrom,blob,image,reloc,text,entry,crc,abi; };
volatile struct FontConfig af_expansion_config;
void *af_expansion_loaded;
u32 af_expansion_busy, af_expansion_memsize;
unsigned char af_expansion_memory[0x8000] __attribute__((aligned(16)));
extern int af_font_expansion_init(void);
extern u32 af_crc32(const void *,u32);
static unsigned char blob[0x8000];
static u32 used, events[16], fail_dma, corrupt, fail_execute, nested;
static void event(u32 id) {
    events[used++]=id;
    assert(af_expansion_busy==1);
    if (nested==id) assert(af_font_expansion_init()==0);
}
static void check_owner(void *p) { assert(p==af_expansion_memory+16); }
int af_expansion_dma(void *p,u32 vrom,u32 bytes) {
    event(1);check_owner(p);assert(vrom==0x03400000);
    assert(bytes==af_expansion_config.blob && bytes<=0x7FE0);
    memcpy(p,blob,bytes);
    if(corrupt) ((unsigned char *)p)[corrupt-1]^=1;
    return fail_dma;
}
void af_expansion_relocate(void *p,void *r,u32 origin) {
    event(2);check_owner(p);assert(r==(unsigned char *)p+af_expansion_config.image);
    assert(origin==0x80C00000 && !memcmp(p,blob,af_expansion_config.blob));
}
void af_expansion_writeback(void *p,u32 bytes) {
    event(3);check_owner(p);assert(bytes==af_expansion_config.image);
}
void af_expansion_invalidate(void *p,u32 bytes) {
    event(4);check_owner(p);assert(bytes==af_expansion_config.text);
}
int af_expansion_execute(void *p) {
    event(5);check_owner(p);return fail_execute?0:1;
}
static void reset(void) {
    af_expansion_loaded=NULL;af_expansion_busy=0;af_expansion_memsize=0x800000;
    used=0;fail_dma=0;corrupt=0;fail_execute=0;nested=0;
    memset(af_expansion_memory,0xCC,sizeof(af_expansion_memory));
    for(u32 i=0;i<sizeof(blob);++i) blob[i]=(unsigned char)i;
    af_expansion_config=(struct FontConfig){0x03400000,96,64,32,32,0,0x51C87372,0x41464701};
}
static void expect(int result,u32 calls) {
    assert(af_font_expansion_init()==result && used==calls && !af_expansion_busy);
    for(u32 i=0;i<calls;++i) assert(events[i]==i+1);
    if(calls) {
        u32 *g=(u32 *)af_expansion_memory;
        for(u32 i=0;i<4;++i) assert(g[i]==0xAF46C0DE && g[0x1FFC+i]==0xAF46C0DE);
        for(u32 i=16+af_expansion_config.blob;i<0x7FF0;++i) assert(af_expansion_memory[i]==0xCC);
    } else {
        for(u32 i=0;i<sizeof(af_expansion_memory);++i) assert(af_expansion_memory[i]==0xCC);
    }
    if(result && calls) {
        assert(af_expansion_loaded==af_expansion_memory+16);
        assert(af_font_expansion_init()==1 && used==calls);
    } else assert(!af_expansion_loaded);
}
int main(void) {
    reset();expect(1,5);
    const u32 sizes[]={0,0x400000,0x800001,0x1000000,0xFFFFFFFF};
    for(u32 i=0;i<sizeof(sizes)/sizeof(*sizes);++i) {reset();af_expansion_memsize=sizes[i];expect(1,0);}
    for(u32 i=1;i<=5;++i) {reset();nested=i;expect(1,5);}
    reset();fail_dma=1;expect(0,1);
    reset();fail_execute=1;expect(0,5);
    for(u32 i=1;i<=96;++i) {reset();corrupt=i;expect(0,1);}
    for(u32 field=0;field<8;++field) {
        const u32 bad[]={0,1,15,0xFFFFFFFF};
        for(u32 i=0;i<4;++i) {
            reset();u32 old=((volatile u32 *)&af_expansion_config)[field];
            if(bad[i]==old) continue;
            ((volatile u32 *)&af_expansion_config)[field]=bad[i];
            expect(0,field==6?1:0);
        }
    }
    reset();af_expansion_config.image=0x7000;af_expansion_config.reloc=0xFE0;
    af_expansion_config.blob=0x7FE0;af_expansion_config.text=0x7000;
    af_expansion_config.crc=af_crc32(blob,0x7FE0);expect(1,5);
    reset();af_expansion_config.image=0x7000;af_expansion_config.reloc=0xFF0;
    af_expansion_config.blob=0x7FF0;expect(0,0);
    reset();fail_dma=1;expect(0,1);used=0;fail_dma=0;expect(1,5);
    puts("expansion font ownership, absent RAM, bounds, failures, and re-entry passed");
}
