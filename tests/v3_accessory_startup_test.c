#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_BLOB_SIZE 0xC000
#ifndef AF_V3_ABI
#define AF_V3_ABI 52
#endif
#define AF_V3_OBJECT_CAPACITY 448
#define AF_V3_ACCESSORIES 1
#include "../overlays/v3/startup.c"

_Alignas(16) unsigned char af_v3_memory[AF_V3_BLOB_SIZE];
_Alignas(16) unsigned char af_v3_accessory_memory[AF_V3_ACCESSORY_BYTES];
static _Alignas(16) unsigned char source[AF_V3_BLOB_SIZE], art[AF_V3_ACCESSORY_BYTES];
volatile u32 af_v3_config[4], af_v3_installed, af_v3_memsize;
static int transfers, failure, executions, writes, invalidations, item_invalidations;
int af_v3_previous(void) { return 1; }
int af_v3_dma(void *out, u32 vrom, u32 size) {
    ++transfers;
    if (out == af_v3_memory) {
        assert(vrom == AF_V3_STORAGE_VROM && size == sizeof(source)); memcpy(out, source, size);
    } else {
        assert(out == af_v3_accessory_memory && vrom == AF_V3_ACCESSORY_VROM && size == sizeof(art));
        if (failure) return -1;
        memcpy(out, art, size);
    }
    return 0;
}
void af_v3_writeback(void *p, u32 size) { (void)p; (void)size; ++writes; }
void af_v3_invalidate(void *p, u32 size) {
    (void)p; (void)size; ++invalidations;
#ifdef AF_V3_WESTERN_LARGE
    if (p == af_v3_accessory_memory + 0x10000) {
        assert(size == 0x1000 && size <= sizeof(art) - 0x10000);
        ++item_invalidations;
    }
#endif
}
int af_v3_execute(void) { ++executions; return 1; }
static void reset(void) {
    memset(source, 0, sizeof(source)); memset(art, 0, sizeof(art));
    memset(af_v3_memory, 0xA5, sizeof(af_v3_memory));
    memset(af_v3_accessory_memory, 0xA5, sizeof(af_v3_accessory_memory));
    u32 *h = (u32 *)source, *a = (u32 *)art, *d = h+0xF0/4;
    h[0] = 0x41465633; h[1] = AF_V3_ABI; h[2] = sizeof(source); h[3] = 448; h[4] = 410;
    h[AF_V3_GUARD] = 0xAF33C0DE;
    a[0] = AF_V3_ACCESSORY_MAGIC; a[1] = 1; a[2] = sizeof(art); a[3] = 20;
    a[(sizeof(art)-16)/4] = AF_V3_ACCESSORY_GUARD;
    d[0] = AF_V3_ACCESSORY_VROM; d[1] = sizeof(art); d[2] = af_crc32(art, sizeof(art)); d[3] = AF_V3_ACCESSORY_RAM;
    af_v3_config[0] = AF_V3_STORAGE_VROM; af_v3_config[1] = sizeof(source);
    af_v3_config[2] = af_crc32(source, sizeof(source)); af_v3_config[3] = AF_V3_ABI;
    af_v3_memsize = 0x800000; af_v3_installed = 0;
    transfers = failure = executions = writes = invalidations = item_invalidations = 0;
}
int main(void) {
    reset(); af_v3_memsize = 0x400000;
    assert(af_v3_startup() && !transfers && !writes && !executions && af_v3_accessory_memory[0] == 0xA5);
    for (int i = 0; i < 4; ++i) {
        reset(); ((u32 *)(source+0xF0))[i] ^= 1;
        af_v3_config[2] = af_crc32(source, sizeof(source));
        assert(!af_v3_startup() && !af_v3_installed && !executions && !writes);
    }
    reset(); failure = 1; assert(!af_v3_startup() && !writes && !executions);
    for (int i = 0; i < 5; ++i) {
        reset(); ((u32 *)art)[i < 4 ? (u32)i : (sizeof(art)-16)/4] ^= 1;
        ((u32 *)(source+0xF0))[2] = af_crc32(art, sizeof(art));
        af_v3_config[2] = af_crc32(source, sizeof(source));
        assert(!af_v3_startup() && !writes && !executions);
    }
    reset(); assert(af_v3_startup() && af_v3_installed == 1 && transfers == 2 && executions == 1);
#ifdef AF_V3_WESTERN_LARGE
    assert(invalidations == 3 && item_invalidations == 1);
#else
    assert(invalidations == 2 && !item_invalidations);
#endif
    assert(writes == 2 && !memcmp(art, af_v3_accessory_memory, sizeof(art)));
    assert(af_v3_startup() && transfers == 2);
    puts("accessory startup guards, DMA, CRC, caches, and low-memory path pass");
}
