#include <assert.h>
#include <stdio.h>
/* Exercise the complete creature chain, including failure before execution. */
#define AF_SURFACE_ITEMS_VROM 101u
#define AF_SURFACE_ITEMS_CRC 201u
#define AF_SURFACE_ITEMS_BYTES 16u
#define AF_ROOM_GOODS_VROM 102u
#define AF_ROOM_GOODS_CRC 202u
#define AF_ROOM_GOODS_BYTES 16u
#define AF_ROOM_CARRY_VROM 103u
#define AF_ROOM_CARRY_CRC 203u
#define AF_ROOM_CARRY_BYTES 16u
#define AF_PLAYER_EXERCISE_VROM 104u
#define AF_PLAYER_EXERCISE_CRC 204u
#define AF_PLAYER_EXERCISE_BYTES 16u
#define AF_CONSOLE_STORAGE_VROM 105u
#define AF_CONSOLE_STORAGE_CRC 205u
#define AF_CONSOLE_STORAGE_BYTES 16u
#define AF_CONSOLE_IMAGES_VROM 106u
#define AF_CONSOLE_IMAGES_CRC 206u
#define AF_CONSOLE_IMAGES_BYTES 16u
#define AF_CONSOLE_DISK_VROM 107u
#define AF_CONSOLE_DISK_CRC 207u
#define AF_CONSOLE_DISK_BYTES 16u
#define AF_CREATURE_ITEMS_VROM 108u
#define AF_CREATURE_ITEMS_CRC 208u
#define AF_CREATURE_ITEMS_BYTES 16u
#define AF_CREATURE_FIELD_VROM 109u
#define AF_CREATURE_FIELD_CRC 209u
#define AF_CREATURE_FIELD_BYTES 16u
#define AF_FISH_WORLD_VROM 110u
#define AF_FISH_WORLD_CRC 210u
#define AF_FISH_WORLD_BYTES 16u
#define AF_INSECT_PHYSICAL 0x03000000u
#define AF_INSECT_CRC 211u
#define AF_INSECT_BYTES 16u
#include "../overlays/v3/surface_bootstrap.c"
u32 af_test_surface_memory[4],af_test_goods_magic,af_test_carry_magic;
unsigned char af_test_goods_code[16],af_test_carry_code[16],af_test_exercise_code[16];
unsigned char af_test_console_code[16],af_test_console_images[16],af_test_console_disk[16],af_test_creature_code[16];
unsigned char af_test_creature_field[16];
unsigned char af_test_fish_world[16],af_test_insect_code[16];
static void *addresses[]={af_test_surface_memory,af_test_goods_code,af_test_carry_code,
    af_test_exercise_code,af_test_console_code,af_test_console_images,af_test_console_disk,af_test_creature_code,
    af_test_creature_field,af_test_fish_world,af_test_insect_code};
static u32 current,stage,fail_dma,fail_crc,init_calls;
int af_surface_dma(void *p,u32 vrom,u32 n) {
    assert(stage==0 && current<10 && p==addresses[current] && vrom==101+current && n==16);
    stage=1;return current+1==fail_dma;
}
int af_surface_pi(u32 rom,void *p,u32 n) {
    assert(stage==0 && current==10 && p==addresses[current] && rom==AF_INSECT_PHYSICAL && n==16);
    stage=1;return current+1==fail_dma;
}
u32 af_surface_crc(const void *p,u32 n) {
    assert(stage==1 && p==addresses[current] && n==16);stage=2;
    return current+1==fail_crc ? 0 : 201+current;
}
void af_surface_writeback(void *p,u32 n) {assert(stage==2 && p==addresses[current] && n==16);stage=3;}
void af_surface_invalidate(void *p,u32 n) {assert(stage==3 && p==addresses[current] && n==16);stage=0;current++;}
int af_surface_prior_init(void) {assert(current==11 && !stage);init_calls++;return 1;}
int main(void) {
    af_test_goods_magic=af_test_carry_magic=123;
    assert(af_v3_surface_init()==1 && init_calls==1);
    assert(!af_test_goods_magic && !af_test_carry_magic);
    for(u32 i=1;i<=11;i++) {
        current=stage=init_calls=0;fail_dma=i;fail_crc=0;
        assert(!af_v3_surface_init() && current==i-1 && stage==1 && !init_calls);
        current=stage=init_calls=0;fail_dma=0;fail_crc=i;
        assert(!af_v3_surface_init() && current==i-1 && stage==2 && !init_calls);
    }
    puts("Shared eleven-packet checked startup, physical transfer, and failure before execution: pass");
}
