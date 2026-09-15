#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_BLOB_SIZE 0xC000u
#define AF_V3_ABI 83u
#define AF_V3_OBJECT_CAPACITY 448
#define AF_V3_SAVE_CODE_VROM 0x024A1080u
#define AF_V3_EXTRA_CODE_LIMIT 0x3000u
#define AF_V3_CLOTHING_PROFILE 1
#define AF_V3_SAVE_RUNTIME 1
#include "../overlays/v3/startup.c"
_Alignas(16) unsigned char af_v3_memory[AF_V3_BLOB_SIZE],af_v3_save_extra[AF_V3_EXTRA_CODE_LIMIT];
static _Alignas(16) unsigned char prefix[AF_V3_BLOB_SIZE],code[AF_V3_EXTRA_CODE_LIMIT];
volatile u32 af_v3_config[4],af_v3_installed,af_v3_memsize;
static int calls,fail_dma,corrupt,writes,caches,executions,resets;
int af_v3_previous(void) { return 1; }
int af_v3_dma(void *out,u32 vrom,u32 n) {
    ++calls;
    if(out==af_v3_memory) {
        assert(vrom==AF_V3_STORAGE_VROM && n==sizeof(prefix));memcpy(out,prefix,n);
    } else {
        assert(out==af_v3_save_extra && vrom==AF_V3_SAVE_CODE_VROM && n==sizeof(code));
        if(fail_dma)return -1;
        memcpy(out,code,n);if(corrupt)af_v3_save_extra[n-1]^=1;
    }
    return 0;
}
void af_v3_writeback(void *p,u32 n) {
    assert((p==af_v3_memory && n==sizeof(prefix))||(p==af_v3_save_extra && n==sizeof(code)));++writes;
}
void af_v3_invalidate(void *p,u32 n) {
    assert((p==af_v3_memory+0x100 && n==0xBEF0)||(p==af_v3_save_extra && n==sizeof(code)));++caches;
}
int af_v3_execute(void) { assert(writes==2 && caches==2);++executions;return 1; }
int af_v3_save_reset(void) { assert(executions==1);++resets;return 1; }
static void seal(void) { af_v3_config[2]=af_crc32(prefix,sizeof(prefix)); }
static void reset(void) {
    memset(prefix,0,sizeof(prefix));memset(code,0x3A,sizeof(code));
    u32 *h=(u32*)prefix,*d=(u32*)(prefix+0xE0);
    h[0]=0x41465633;h[1]=83;h[2]=sizeof(prefix);h[3]=448;h[4]=410;h[AF_V3_GUARD]=0xAF33C0DE;
    d[0]=AF_V3_SAVE_CODE_VROM;d[1]=sizeof(code);d[2]=af_crc32(code,sizeof(code));d[3]=0x8046D000;
    af_v3_config[0]=AF_V3_STORAGE_VROM;af_v3_config[1]=sizeof(prefix);af_v3_config[3]=83;
    af_v3_installed=0;af_v3_memsize=0x800000;
    calls=fail_dma=corrupt=writes=caches=executions=resets=0;seal();
}
int main(void) {
    reset();assert(af_v3_startup() && af_v3_installed && calls==2 && resets==1);
    assert(!memcmp(code,af_v3_save_extra,sizeof(code)));
    assert(af_v3_startup() && calls==2 && resets==1);
    for(int i=0;i<4;++i) {
        reset();((u32*)(prefix+0xE0))[i]^=1;seal();
        assert(!af_v3_startup() && !af_v3_installed && !executions && !writes && !resets);
    }
    for(unsigned i=0;i<3;++i) {
        static const u32 bad_size[]={0,0x3001,0x3010};
        reset();((u32*)(prefix+0xE0))[1]=bad_size[i];seal();assert(!af_v3_startup() && calls==1);
    }
    reset();fail_dma=1;assert(!af_v3_startup() && !writes && !executions);
    reset();corrupt=1;assert(!af_v3_startup() && !writes && !executions);
    reset();af_v3_memsize=0x400000;assert(af_v3_startup() && !calls && !executions);
    puts("pass: current extended startup bounds, CRC, caches, failure, and 4-MiB warning");
}
