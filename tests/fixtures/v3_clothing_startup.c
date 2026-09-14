#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_BLOB_SIZE 0xC000u
#define AF_V3_ABI 31u
#define AF_V3_SAVE_RUNTIME 1
#define AF_V3_CLOTHING_PROFILE 1
#include "../../overlays/v3/startup.c"
_Alignas(16) unsigned char af_v3_memory[AF_V3_BLOB_SIZE], af_v3_save_extra[0xC00];
static _Alignas(16) unsigned char prefix[AF_V3_BLOB_SIZE], code[32];
volatile u32 af_v3_config[4], af_v3_installed, af_v3_memsize;
static int fail_dma, corrupt_code, calls, cached, invalidated, executions, resets;
int af_v3_previous(void) { return 1; }
int af_v3_dma(void *out, u32 source, u32 size) {
    ++calls;
    if (source == 0x3F00000) {
        assert(out == af_v3_memory && size == sizeof(prefix)); memcpy(out, prefix, size);
    } else {
        assert(source == 0x3F0F400 && out == af_v3_save_extra && size == sizeof(code));
        if (fail_dma) return -1;
        memcpy(out, code, size);
        if (corrupt_code) af_v3_save_extra[0] ^= 1;
    }
    return 0;
}
void af_v3_writeback(void *p, u32 n) {
    assert((p == af_v3_save_extra && n == sizeof(code)) || (p == af_v3_memory && n == sizeof(prefix)));
    ++cached;
}
void af_v3_invalidate(void *p, u32 n) {
    assert((p == af_v3_save_extra && n == sizeof(code)) || (p == af_v3_memory+0x100 && n == 0xBEF0));
    ++invalidated;
}
int af_v3_execute(void) { assert(cached == 2 && invalidated == 2); ++executions; return 1; }
int af_v3_save_reset(void) { assert(executions == 1); ++resets; return 1; }
static void seal(void) { af_v3_config[2] = af_crc32(prefix, sizeof(prefix)); }
static void reset(void) {
    memset(prefix, 0, sizeof(prefix)); memset(code, 0x3A, sizeof(code));
    u32 *h = (u32 *)prefix, *d = (u32 *)(prefix+0xE0);
    h[0] = 0x41465633; h[1] = 31; h[2] = sizeof(prefix); h[3] = 430; h[4] = 410; h[AF_V3_GUARD] = 0xAF33C0DE;
    d[0] = 0x3F0F400; d[1] = sizeof(code); d[2] = af_crc32(code, sizeof(code)); d[3] = 0x8046D000;
    af_v3_config[0] = 0x3F00000; af_v3_config[1] = sizeof(prefix); af_v3_config[3] = 31;
    af_v3_installed = 0; af_v3_memsize = 0x800000;
    fail_dma = corrupt_code = calls = cached = invalidated = executions = resets = 0;
    seal();
}
int main(void) {
    reset(); assert(af_v3_startup() && af_v3_installed && calls == 2 && resets == 1);
    assert(!memcmp(af_v3_save_extra, code, sizeof(code)));
    assert(af_v3_startup() && calls == 2 && resets == 1);
    for (int word = 0; word < 4; ++word) {
        reset(); ((u32 *)(prefix+0xE0))[word] ^= 1; seal();
        assert(!af_v3_startup() && !af_v3_installed && !executions && !resets);
    }
    reset(); ((u32 *)(prefix+0xE0))[1] = 0; seal(); assert(!af_v3_startup() && calls == 1);
    reset(); ((u32 *)(prefix+0xE0))[1] = 0xC10; seal(); assert(!af_v3_startup() && calls == 1);
    reset(); fail_dma = 1; assert(!af_v3_startup() && !af_v3_installed && !cached && !resets);
    reset(); corrupt_code = 1; assert(!af_v3_startup() && !af_v3_installed && !cached && !resets);
    reset(); af_v3_memsize = 0x400000; assert(af_v3_startup() && !calls && !executions);
    puts("Clothing extension startup, descriptor, CRC, cache, and rejection checks pass");
    return 0;
}
