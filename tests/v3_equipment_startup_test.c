#include <assert.h>
#include <stdio.h>
#include <string.h>
static unsigned int expected_equipment_crc;
#define AF_V3_BLOB_SIZE 0xC000u
#define AF_V3_ABI 97u
#define AF_V3_OBJECT_CAPACITY 448
#define AF_V3_SAVE_CODE_VROM 0x024A1080u
#define AF_V3_EXTRA_CODE_LIMIT 0x3000u
#define AF_V3_CLOTHING_PROFILE 1
#define AF_V3_SAVE_RUNTIME 1
#define AF_V3_FURNITURE_TABLES 1
#define AF_V3_ACCESSORIES 1
#define AF_V3_ACCESSORY_BYTES 0x30000u
#define AF_V3_ACCESSORY_VROM 0x02400000u
#define AF_V3_ACCESSORY_RAM 0x80473000u
#define AF_V3_EQUIPMENT_VROM 0x02500000u
#define AF_V3_EQUIPMENT_CRC expected_equipment_crc
#include "../overlays/v3/startup.c"
_Alignas(16) unsigned char af_v3_memory[AF_V3_BLOB_SIZE];
_Alignas(16) unsigned char af_v3_save_extra[AF_V3_EXTRA_CODE_LIMIT];
_Alignas(16) unsigned char af_v3_accessory_memory[AF_V3_ACCESSORY_BYTES];
_Alignas(16) unsigned char af_v3_equipment_memory[AF_V3_EQUIPMENT_BYTES];
static _Alignas(16) unsigned char prefix[AF_V3_BLOB_SIZE],extra[AF_V3_EXTRA_CODE_LIMIT];
static _Alignas(16) unsigned char package[AF_V3_ACCESSORY_BYTES],equipment[AF_V3_EQUIPMENT_BYTES];
volatile u32 af_v3_config[4],af_v3_installed,af_v3_memsize;
static int calls,fail_dma,corrupt,writes,caches,executions,resets,tables,previous_ok;
int af_v3_previous(void) {return previous_ok;}
int af_v3_dma(void *out,u32 vrom,u32 bytes) {
    ++calls;
    if(calls==fail_dma)return -1;
    const void *in=0;
    if(out==af_v3_memory) {assert(vrom==AF_V3_STORAGE_VROM && bytes==sizeof(prefix));in=prefix;}
    else if(out==af_v3_save_extra) {assert(vrom==AF_V3_SAVE_CODE_VROM && bytes==sizeof(extra));in=extra;}
    else if(out==af_v3_accessory_memory) {assert(vrom==AF_V3_ACCESSORY_VROM && bytes==sizeof(package));in=package;}
    else {assert(out==af_v3_equipment_memory && vrom==AF_V3_EQUIPMENT_VROM && bytes==sizeof(equipment));in=equipment;}
    memcpy(out,in,bytes);
    if(calls==corrupt)((unsigned char *)out)[bytes-1]^=1;
    return 0;
}
void af_v3_writeback(void *p,u32 n) {
    assert((p==af_v3_memory && n==sizeof(prefix)) || (p==af_v3_save_extra && n==sizeof(extra)) ||
           (p==af_v3_accessory_memory && n==sizeof(package)) || (p==af_v3_equipment_memory && n==sizeof(equipment)));
    ++writes;
}
void af_v3_invalidate(void *p,u32 n) {
    assert((p==af_v3_memory+0x100 && n==sizeof(prefix)-0x110) || (p==af_v3_save_extra && n==sizeof(extra)) ||
           (p==af_v3_accessory_memory+0x100 && n==sizeof(package)-0x110) ||
           (p==af_v3_equipment_memory && n==sizeof(equipment)));
    ++caches;
}
int af_v3_execute(void) {assert(writes==4 && caches==4);++executions;return 1;}
int af_v3_furniture_tables_init(void) {assert(executions==1);++tables;return 1;}
int af_v3_save_reset(void) {assert(tables==1);++resets;return 1;}
static void reset(void) {
    memset(prefix,0,sizeof(prefix));memset(extra,0x3A,sizeof(extra));memset(package,0,sizeof(package));
    memset(equipment,0x19,sizeof(equipment));
    u32 *h=(u32 *)prefix,*p=(u32 *)package,*d=(u32 *)(prefix+0xE0);
    h[0]=0x41465633;h[1]=AF_V3_ABI;h[2]=sizeof(prefix);h[3]=448;h[4]=410;h[AF_V3_GUARD]=0xAF33C0DE;
    p[0]=AF_V3_ACCESSORY_MAGIC;p[1]=1;p[2]=sizeof(package);p[3]=20;p[(sizeof(package)-16)/4]=AF_V3_ACCESSORY_GUARD;
    d[0]=AF_V3_SAVE_CODE_VROM;d[1]=sizeof(extra);d[2]=af_crc32(extra,sizeof(extra));d[3]=0x8046D000;
    d+=4;d[0]=AF_V3_ACCESSORY_VROM;d[1]=sizeof(package);d[2]=af_crc32(package,sizeof(package));d[3]=AF_V3_ACCESSORY_RAM;
    expected_equipment_crc=af_crc32(equipment,sizeof(equipment));
    af_v3_config[0]=AF_V3_STORAGE_VROM;af_v3_config[1]=sizeof(prefix);af_v3_config[2]=af_crc32(prefix,sizeof(prefix));af_v3_config[3]=AF_V3_ABI;
    af_v3_installed=0;af_v3_memsize=0x800000;previous_ok=1;
    calls=fail_dma=corrupt=writes=caches=executions=resets=tables=0;
}
int main(void) {
    reset();assert(af_v3_startup() && af_v3_installed && calls==4 && resets==1);
    assert(!memcmp(equipment,af_v3_equipment_memory,sizeof(equipment)));
    assert(af_v3_startup() && calls==4 && resets==1);
    for(int i=1;i<=4;++i) {
        reset();fail_dma=i;assert(!af_v3_startup() && !af_v3_installed && !executions && !resets && calls==i);
        reset();corrupt=i;assert(!af_v3_startup() && !af_v3_installed && !executions && !resets && calls==i);
    }
    reset();af_v3_config[3]^=1;assert(!af_v3_startup() && !calls);
    reset();af_v3_memsize=0x400000;assert(af_v3_startup() && !calls && !executions);
    reset();previous_ok=0;assert(!af_v3_startup() && !calls);
    puts("pass: all four startup resources, failures, cache coverage, repeat and low-memory paths");
}
