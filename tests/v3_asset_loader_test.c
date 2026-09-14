#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/asset.c"
#include "../overlays/v3/startup.c"

struct Object af_v3_objects[430];
volatile u32 af_v3_object_entry[2], af_v3_config[4], af_v3_installed, af_v3_memsize;
_Alignas(16) unsigned char af_v3_memory[AF_V3_BLOB_SIZE];
static _Alignas(16) unsigned char source[AF_V3_BLOB_SIZE];
static int previous_ok, dma_bad, execute_bad, dma_calls, writes, invalidates, executions;

int af_v3_previous(void) { return previous_ok; }
int af_v3_dma(void *dst, u32 vrom, u32 size) {
    assert(dst == af_v3_memory && vrom == 0x03F00000 && size == sizeof(source));
    ++dma_calls;
    if (dma_bad) return -1;
    memcpy(dst, source, size);
    return 0;
}
void af_v3_writeback(void *dst, u32 size) {
    assert((dst == af_v3_memory && size == sizeof(source)) ||
           (dst == (void *)af_v3_object_entry && size == 8));
    ++writes;
}
void af_v3_invalidate(void *dst, u32 size) {
    assert((dst == af_v3_memory + 0x100 && size == 0xF00) ||
           (dst == (void *)af_v3_object_entry && size == 8));
    ++invalidates;
}
int af_v3_execute(void) {
    ++executions;
    return execute_bad ? 0 : af_v3_asset_init();
}
static void reset(void) {
    u32 *h = (u32 *)source;
    memset(source, 0, sizeof(source));
    memset(af_v3_memory, 0xA5, sizeof(af_v3_memory));
    h[0] = 0x41465633; h[1] = AF_V3_ABI; h[2] = AF_V3_BLOB_SIZE; h[3] = 430; h[4] = 410;
    h[AF_V3_GUARD] = 0xAF33C0DE;
    af_v3_config[0] = 0x03F00000; af_v3_config[1] = AF_V3_BLOB_SIZE;
    af_v3_config[2] = af_crc32(source, sizeof(source)); af_v3_config[3] = AF_V3_ABI;
    af_v3_installed = 0; af_v3_memsize = 0x800000;
    af_v3_object_entry[0] = 0xAFA60008; af_v3_object_entry[1] = 0x00063400;
    previous_ok = 1; dma_bad = execute_bad = dma_calls = writes = invalidates = executions = 0;
}
static void startup_tests(void) {
    reset(); previous_ok = 0;
    assert(!af_v3_startup() && !dma_calls);
    reset(); af_v3_memsize = 0x400000;
    assert(af_v3_startup() && !dma_calls && !writes && !executions);
    assert(af_v3_memory[0] == 0xA5 && af_v3_object_entry[0] == 0xAFA60008);
    for (int i = 0; i < 4; ++i) {
        reset(); af_v3_config[i] ^= 1;
        assert(!af_v3_startup() && !af_v3_installed && !executions);
    }
    reset(); dma_bad = 1;
    assert(!af_v3_startup() && !writes && !executions);
    for (int i = 0; i < 6; ++i) {
        reset(); ((u32 *)source)[i < 5 ? (u32)i : AF_V3_GUARD] ^= 1;
        af_v3_config[2] = af_crc32(source, sizeof(source));
        assert(!af_v3_startup() && !writes && !executions);
    }
    reset(); execute_bad = 1;
    assert(!af_v3_startup() && !af_v3_installed && writes == 1 && invalidates == 1);
    reset(); af_v3_object_entry[1] ^= 1;
    assert(!af_v3_startup() && !af_v3_installed && af_v3_object_entry[0] == 0xAFA60008);
    reset();
    assert(af_v3_startup() && af_v3_installed && writes == 2 && invalidates == 2);
    assert(af_v3_object_entry[0] == 0x08118050 && !af_v3_object_entry[1]);
    assert(af_v3_startup() && dma_calls == 1 && executions == 1);
    assert(af_v3_asset_init() && writes == 2);
    ((u32 *)af_v3_memory)[AF_V3_GUARD] = 0;
    assert(!af_v3_startup() && dma_calls == 1);
}
static void reject(struct Status *status, struct Arena *arena, s16 bank) {
    struct Status before = *status;
    struct Arena original = *arena;
    assert(!af_v3_object_status(status, arena, bank));
    assert(!memcmp(status, &before, sizeof(before)));
    assert(!memcmp(arena, &original, sizeof(original)));
}
static void object_tests(void) {
    struct Status status, before;
    struct Arena arena;
    memset(&status, 0xA5, sizeof(status));
    memset(&arena, 0x6C, sizeof(arena));
    for (int i = 0; i < 430; ++i) {
        af_v3_objects[i].start = 0x01000000u + (u32)i * 0x2000u;
        af_v3_objects[i].end = af_v3_objects[i].start + 5664;
        arena.next = 0x80300010; arena.end = 0x80310000;
        before = status;
        assert(af_v3_object_status(&status, &arena, i));
        assert(status.id == -i && status.segment == 0 && status.vram == 0x80300010);
        assert(status.vrom == af_v3_objects[i].start && status.size == 5664);
        assert(status.keep == 0 && status.pending == 1 && arena.next == 0x80301630);
        assert(status.pad == before.pad && status.unknown == before.unknown);
        assert(!memcmp(status.reserved, before.reserved, sizeof(status.reserved)));
    }
    reject(&status, &arena, -1); reject(&status, &arena, 430); reject(&status, &arena, 32767);
    arena.next = 0x80300010; arena.end = 0x80310000;
    assert(af_v3_object_status(&status, &arena, 0x123401ADu));
    assert(status.id == -429 && status.vrom == af_v3_objects[429].start);
    af_v3_objects[410].start = af_v3_objects[410].end = 0;
    reject(&status, &arena, 410);
    af_v3_objects[410].start = 1;
    reject(&status, &arena, 410);
    arena.next = 0x80300010; arena.end = 0x80301630;
    reject(&status, &arena, 429); /* Exact-fit allocation is also rejected natively. */
    arena.next = 0xFFFFFFF8u; arena.end = 0xFFFFFFFFu;
    reject(&status, &arena, 429);
    arena.next = 0x80300000; arena.end = 0xFFFFFFFFu;
    af_v3_objects[429].start = 0; af_v3_objects[429].end = 0xFFFFFFF0u;
    reject(&status, &arena, 429);
    af_v3_objects[0].start = af_v3_objects[0].end = 0;
    assert(af_v3_object_status(&status, &arena, 0)); /* Retain native empty-bank semantics. */
}
int main(void) {
    startup_tests(); object_tests();
    puts("V3 startup, native status layout, banks, bounds, caches, and rejection paths pass");
    return 0;
}
