#include <assert.h>
#include <stdio.h>
#define AF_SURFACE_ITEMS_BYTES 32u
#define AF_SURFACE_ITEMS_VROM 0x100u
#define AF_SURFACE_ITEMS_CRC 11u
#define AF_ROOM_GOODS_BYTES 32u
#define AF_ROOM_GOODS_VROM 0x200u
#define AF_ROOM_GOODS_CRC 22u
#define AF_ROOM_CARRY_BYTES 32u
#define AF_ROOM_CARRY_VROM 0x300u
#define AF_ROOM_CARRY_CRC 33u
#define AF_PLAYER_EXERCISE_BYTES 32u
#define AF_PLAYER_EXERCISE_VROM 0x400u
#define AF_PLAYER_EXERCISE_CRC 44u
#ifdef AF_TEST_CONSOLE
#define AF_CONSOLE_STORAGE_BYTES 32u
#define AF_CONSOLE_STORAGE_VROM 0x500u
#define AF_CONSOLE_STORAGE_CRC 55u
#ifdef AF_TEST_CONSOLE_IMAGES
#define AF_CONSOLE_IMAGES_BYTES 32u
#define AF_CONSOLE_IMAGES_VROM 0x600u
#define AF_CONSOLE_IMAGES_CRC 66u
#define PACKETS 6u
#else
#define PACKETS 5u
#endif
#else
#define PACKETS 4u
#endif
#include "../overlays/v3/surface_bootstrap.c"
u32 af_test_surface_memory[8],af_test_goods_magic,af_test_carry_magic;
unsigned char af_test_goods_code[32],af_test_carry_code[32],af_test_exercise_code[32];
unsigned char af_test_console_code[32],af_test_console_images[32];
static void *targets[]={af_test_surface_memory,af_test_goods_code,af_test_carry_code,af_test_exercise_code,af_test_console_code,af_test_console_images};
static unsigned int calls,flushes,invalidations,prior_calls,fail_dma,fail_crc;
int af_surface_dma(void *p,u32 vrom,u32 bytes) {
    assert(calls<PACKETS&&p==targets[calls]&&bytes==32&&vrom==0x100*(calls+1));
    ++calls;return calls==fail_dma;
}
u32 af_surface_crc(const void *p,u32 bytes) {
    assert(calls&&p==targets[calls-1]&&bytes==32);
    return calls*11+(calls==fail_crc);
}
void af_surface_writeback(void *p,u32 bytes) {assert(p==targets[flushes]&&bytes==32);++flushes;}
void af_surface_invalidate(void *p,u32 bytes) {assert(p==targets[invalidations]&&bytes==32);++invalidations;}
int af_surface_prior_init(void) {assert(calls==PACKETS&&flushes==PACKETS&&invalidations==PACKETS);++prior_calls;return 9;}
int main(void) {
    for(unsigned int failure=0;failure<=2*PACKETS;++failure) {
        calls=flushes=invalidations=prior_calls=0;
        fail_dma=failure<=PACKETS?failure:0;fail_crc=failure>PACKETS?failure-PACKETS:0;
        af_test_goods_magic=af_test_carry_magic=0xFFFFFFFFu;
        int result=af_v3_surface_init();
        if (!failure) {
            assert(result==9&&prior_calls==1&&calls==PACKETS);
            assert(!af_test_goods_magic&&!af_test_carry_magic);
        } else {
            unsigned int failed=fail_dma?fail_dma:fail_crc;
            assert(!result&&!prior_calls&&calls==failed&&flushes==failed-1&&invalidations==failed-1);
        }
    }
#ifdef AF_TEST_CONSOLE_IMAGES
    puts("six-packet startup order and all twelve DMA/checksum rejection paths pass");
#elif defined(AF_TEST_CONSOLE)
    puts("five-packet startup order and all ten DMA/checksum rejection paths pass");
#else
    puts("four-packet startup order and all eight DMA/checksum rejection paths pass");
#endif
}
