#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/console_disk_native.h"
typedef unsigned char u8;
typedef unsigned int u32;
static unsigned checks,waits,flushes,sequence;
#define CHECK(x) do {checks++;if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
AFQNative af_qdn_test_context;
static _Alignas(16) u8 state[AF_QDN_STATE_BYTES+32],graphics[AF_QDN_GRAPHICS_BYTES+32];
static _Alignas(16) u8 disk[65536],original[65536],program[32768],characters[8192],bios[8192],boot[260];
static u8 expected_characters[8192];
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void wait_rsp(void) {CHECK(sequence%3==0);sequence++;waits++;}
static void flush(void *p,u32 bytes) {
    CHECK(bytes==8192);
    CHECK(p==(sequence%3==1?graphics+16+0x2008:state+16+0x62C8));
    CHECK(sequence%3!=0);sequence++;flushes++;
}
void *af_qdn_test_function(u32 at) {
    if(at==0x80300000)return wait_rsp;
    CHECK(at==0x8002FE00);return flush;
}
void af_v3_qd_wdm_bridge(void) {}
void af_v3_qd_ram_bridge(void) {}
static AFQNativeBuffers buffers(void) {
    AFQNativeBuffers b={state+16,graphics+16,disk,program,characters,bios,boot,
        AF_QDN_STATE_BYTES,AF_QDN_GRAPHICS_BYTES,65536,0x80300000};
    return b;
}
static void load(const char *name,u8 *data,size_t n) {
    FILE *f=fopen(name,"rb");CHECK(f);CHECK(fread(data,1,n,f)==n);CHECK(fgetc(f)==EOF);CHECK(!fclose(f));
}
static AFQNativeRegisters registers(void) {
    AFQNativeRegisters r;
    for(unsigned i=0;i<32;i++)r.r[i]=0xF8E7D6C500000000ull+i*0x100001;
    r.hi=0xBBAADDFF00112233ull;r.lo=0x9988776655443322ull;
    return r;
}
static void untouched(const AFQNativeRegisters *r,const AFQNativeRegisters *before,u32 mask) {
    for(unsigned i=0;i<32;i++)if(!(mask&(1u<<i)))CHECK(r->r[i]==before->r[i]);
    CHECK(r->hi==before->hi && r->lo==before->lo);
}
int main(int argc,char **argv) {
    CHECK(argc==4);load(argv[1],disk,sizeof(disk));load(argv[2],bios,sizeof(bios));load(argv[3],boot,sizeof(boot));
    memcpy(original,disk,sizeof(disk));
    memset(state,0x5A,sizeof(state));memset(graphics,0xA5,sizeof(graphics));
    AFQNative *n=&af_qdn_test_context;AFQNativeBuffers b=buffers(),bad=b;
    AFQNative before=*n;
    bad.state_bytes--;CHECK(af_v3_qd_native_bind(n,&bad)==AF_QD_BAD_STATE);
    bad=b;bad.graphics_bytes--;CHECK(af_v3_qd_native_bind(n,&bad)==AF_QD_BAD_STATE);
    bad=b;bad.characters=b.state+8192;CHECK(af_v3_qd_native_bind(n,&bad)==AF_QD_BAD_STATE);
    bad=b;bad.bios=b.graphics+0x2008;CHECK(af_v3_qd_native_bind(n,&bad)==AF_QD_BAD_STATE);
    bad=b;bad.base+=4;CHECK(af_v3_qd_native_bind(n,&bad)==AF_QD_BAD_STATE);
    CHECK(!memcmp(n,&before,sizeof(*n)) && !waits);
    CHECK(!af_v3_qd_native_bind(n,&b));
    CHECK(!af_v3_qd_boot(&n->disk));memcpy(expected_characters,characters,8192);
    CHECK(!af_v3_qd_native_map(n));CHECK(waits==1 && flushes==2);
    u8 *s=b.state;
    for(unsigned bank=0;bank<8;bank++) {
        u32 bias=word(s+0x1A38+bank*4);
        if(bank<3)CHECK(bias==(u32)(uintptr_t)s);
        else {
            u8 *mapped=(u8 *)(uintptr_t)(bias+bank*8192u);
            CHECK(mapped==(bank==7?bios:program+(bank-3)*8192));
            CHECK(mapped[0]==(bank==7?bios[0]:program[(bank-3)*8192]));
            CHECK(mapped[8191]==(bank==7?bios[8191]:program[(bank-2)*8192-1]));
            CHECK(word(s+0x18E4+bank*4)==b.base+0x8082F994u-0x8082A070u);
        }
    }
    CHECK(word(s+0x1A78)==(u32)(uintptr_t)characters);
    CHECK(word(s+0x1A74)==0 && word(s+0x1A7C)==32768 && word(s+0x1A80)==0);
    CHECK(word(s+0x181C)==b.base+0x8083055Cu-0x8082A070u);
    CHECK(word(s+0xC20)==(u32)(uintptr_t)af_v3_qd_wdm_bridge);
    CHECK(!memcmp(s+0xC2C,"\x02\xFF\x02\x00",4));
    for(unsigned i=0;i<8;i++)CHECK(s[0x1B68+i*2]==0 && s[0x1B69+i*2]==i);
    for(unsigned group=0;group<8;group++)for(unsigned row=0;row<8;row++)for(unsigned tile=0;tile<64;tile++) {
        unsigned raw=(group*64+tile)*16+row,at=group*1024+row*128+tile*2;
        CHECK(s[0x62C8+at]==characters[raw+8] && s[0x62C8+at+1]==characters[raw]);
        CHECK(!memcmp(s+0x62C8+at,b.graphics+0x2008+at,2));
    }
    AFQNativeRegisters r=registers(),saved=r;
    for(unsigned bank=3;bank<=6;bank++)for(unsigned edge=0;edge<2;edge++) {
        r.r[4]=bank*8192+edge*8191;r.r[5]=bank+edge*0x10;saved=r;
        af_v3_qd_native_ram_dispatch(s,&r);
        CHECK(program[(u32)r.r[4]-0x6000]==(u8)r.r[5]);untouched(&r,&saved,0);
    }
    r.r[4]=0xE000;u8 first=bios[0];saved=r;af_v3_qd_native_ram_dispatch(s,&r);
    CHECK(n->error && bios[0]==first);untouched(&r,&saved,0);n->error=0;
    /* WDM does not confuse the native RSP completion word (0400) with the
     * donor protected-frame flag. Exercise the full fast boot and registers. */
    put(s+0x1ACC,0x400);put(s+0x42C4,0x60000000);
    r=registers();r.r[16]=0;r.r[19]=0xEEBF;r.r[20]=0xFA;r.r[25]=0xFFFFFFFFFFFFE401ull;saved=r;
    af_v3_qd_native_wdm_dispatch(s,&r);
    CHECK(!n->error && r.r[19]==0xEE9B && !r.r[21] && r.r[16]==0);
    CHECK(r.r[25]==saved.r[25] && r.r[20]==saved.r[20]);
    untouched(&r,&saved,(1u<<16)|(1u<<19)|(1u<<20)|(1u<<21)|(1u<<25));
    CHECK(!memcmp(s+0xFA,boot,sizeof(boot)) && !memcmp(characters,expected_characters,8192));
    CHECK(waits==2 && flushes==4 && !n->disk.chr_dirty && bios[0xEBD]==0xA9);
    r=registers();r.r[16]=0x21;r.r[19]=0xE7A6;r.r[20]=0xFD;r.r[25]=0xFEDCBA987654321Full;saved=r;
    af_v3_qd_native_wdm_dispatch(s,&r);CHECK(r.r[19]==0xE7A4 && r.r[25]==7);
    untouched(&r,&saved,(1u<<16)|(1u<<19)|(1u<<20)|(1u<<21)|(1u<<25));
    s[0x90]=0x73;r.r[19]=0xEEF6;r.r[21]=0xFE;af_v3_qd_native_wdm_dispatch(s,&r);
    CHECK(r.r[16]==0x73 && r.r[21]==0xFE);
    saved=r;af_v3_qd_native_wdm_dispatch(s+16,&r);CHECK(!memcmp(&r,&saved,sizeof(r)));
    for(unsigned i=0;i<16;i++) {
        CHECK(state[i]==0x5A && state[AF_QDN_STATE_BYTES+16+i]==0x5A);
        CHECK(graphics[i]==0xA5 && graphics[AF_QDN_GRAPHICS_BYTES+16+i]==0xA5);
    }
    CHECK(!memcmp(disk,original,sizeof(disk)));
    printf("%u native QD adapter checks: full CPU banks, RAM stores, WDM register frame, CHR buffers/cache order and guards; native calls stubbed\n",checks);
}
