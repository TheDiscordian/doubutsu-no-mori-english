#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../overlays/v3/console_disk_native.h"
typedef unsigned char u8;
typedef unsigned int u32;
static unsigned checks,waits,flushes,sequence,sound_events,sound_delays,sound_resets,sound_binds;
#define CHECK(x) do {checks++;if(!(x)){fprintf(stderr,"line %d: %s\n",__LINE__,#x);exit(1);}}while(0)
AFQNative af_qdn_test_context;
static _Alignas(16) u8 state[AF_QDN_STATE_BYTES+32],graphics[AF_QDN_GRAPHICS_BYTES+32];
static _Alignas(16) u8 disk[65536],original[65536],program[32768],characters[8192],bios[8192],boot[260];
static u8 expected_characters[8192];
static u8 native_owner[0x2E990];
u8 *af_qdn_test_memory(u32 at) {
    if(at>=(u32)(uintptr_t)program && at<(u32)(uintptr_t)(program+sizeof(program)))return (u8 *)(uintptr_t)at;
    CHECK(at>=0x80300000 && at<0x8032E990);
    return native_owner+at-0x80300000;
}
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void wait_rsp(void) {CHECK(sequence%3==0);sequence++;waits++;}
static void flush(void *p,u32 bytes) {
    CHECK(bytes==8192);
    CHECK(p==(sequence%3==1?graphics+16+0x2008:state+16+0x62C8));
    CHECK(sequence%3!=0);sequence++;flushes++;
}
static void sound_event(u32 at,u32 value) {
    static const unsigned expected[][2]={{0x15,0},{8,0},{0x80,0x80},{0x80,0x15},{0xD5,0},{0x10,15},{15,0x11}};
    CHECK(sound_events<7 && at==expected[sound_events][0] && value==expected[sound_events][1]);
    sound_events++;
}
static void sound_reset(void) {CHECK(sound_events==7 && !sound_resets && !sound_binds);sound_resets++;}
static void sound_bind(void *p) {CHECK(p==program+0x6000 && sound_resets==1 && !sound_binds);sound_binds++;}
static void delay(u32 us) {
    CHECK(us==16000);sound_delays++;
}
void *af_qdn_test_function(u32 at) {
    if(at==0x80300000)return wait_rsp;
    if(at==0x80300000+0x808345B8-0x8082A070)return sound_event;
    if(at==0x80300000+0x808352D8-0x8082A070)return sound_reset;
    if(at==0x80300000+0x80835778-0x8082A070)return sound_bind;
    if(at==0x8002DA3C)return delay;
    CHECK(at==0x8002FE00);return flush;
}
void af_v3_qd_wdm_bridge(void) {}
void af_v3_qd_ram_bridge(void) {}
void af_v3_qd_read_bridge(void) {}
void af_v3_qd_write_bridge(void) {}
void af_v3_qd_irq_bridge(void) {}
void af_v3_qd_dpcm_bridge(void) {}
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
    CHECK(argc==5);load(argv[1],disk,sizeof(disk));load(argv[2],bios,sizeof(bios));load(argv[3],boot,sizeof(boot));
    load(argv[4],native_owner,sizeof(native_owner));
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
    CHECK(word(s+0x18EC)==(u32)(uintptr_t)af_v3_qd_read_bridge);
    CHECK(word(s+0x18C8)==(u32)(uintptr_t)af_v3_qd_write_bridge);
    CHECK(word(s+0x1AB8)==(u32)(uintptr_t)af_v3_qd_irq_bridge);
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
    /* Cold startup uses complete relocated native tables without interpreting
     * the disk signature as an iNES header. Sound and IRQ hooks are not faked. */
    CHECK(af_v3_qd_native_reset_button(n)==AF_QD_BAD_STATE);
    CHECK(!af_v3_qd_native_initialize(n));CHECK(n->initialized);
    CHECK(waits==3 && flushes==6);
    CHECK(word(native_owner+0x80852694-0x8082A070)==(u32)(uintptr_t)s);
    CHECK(word(native_owner+0x80852690-0x8082A070)==(u32)(uintptr_t)disk);
    for(unsigned i=0;i<64;i++)CHECK(native_owner[0x80852698-0x8082A070+i]==0);
    CHECK(word(s+0x1A70)==(u32)(uintptr_t)disk && word(s+0x1A9C)==(u32)(uintptr_t)disk);
    for(unsigned i=0;i<2048;i+=4)CHECK(word(s+i)==0x0FEFFE7D);
    for(unsigned i=0;i<4096;i++)if(i<0x420 || i>=0x430)
        CHECK(s[0x800+i]==native_owner[0x80836770-0x8082A070+i]);
    for(unsigned i=0;i<32768;i++)CHECK(program[i]==255);
    for(unsigned i=0;i<8192;i++)CHECK(!characters[i] && !s[0x62C8+i] && !b.graphics[0x2008+i]);
    CHECK(s[0x1B3E]==0xEE && s[0x1B3F]==0x24 && s[0x1B45]==255 && s[0x1B4A]==4);
    CHECK(word(s+0x1ACC)==0x400 && word(s+0x1AC8)==(u32)-7167);
    CHECK(word(s+0x1AD0)==b.base+0x8082F138u-0x8082A070u);
    CHECK(s[0x1B36]==8 && s[0x1B37]==0 && s[0x1B30]==0x7F && s[0x1B31]==255);
    CHECK(af_v3_qd_native_initialize(n)==AF_QD_BAD_STATE && waits==3);
    /* Reset button retains all programme/work/CHR memory, rendering tables,
     * controller latch, condition flags, and patched BIOS, unlike cold start. */
    s[0x90]=0x19;program[1234]=0x56;characters[4321]=0x78;bios[0xEBD]=0xA9;
    s[0x1B46]=0x92;s[0x1B47]=1;s[0x1B48]=0x40;s[0x1B49]=0x80;
    s[0x1B5C]=0xFF;s[0x4EC0]=0x6B;
    n->disk.head=19;n->disk.ready=5;n->disk.control=0x80;n->disk.motor=90;
    n->disk.timer_control=3;n->disk.master=5;n->disk.changed=1;n->disk.fast_locked=1;
    n->disk.drive[2]=0x46;
    CHECK(!af_v3_qd_native_reset_button(n));
    CHECK(s[0x90]==0x19 && program[1234]==0x56 && characters[4321]==0x78 && bios[0xEBD]==0xA9);
    CHECK(!memcmp(s+0x1B46,"\x92\x01\x40\x80",4) && s[0x1B5C]==255 && s[0x4EC0]==0x6B);
    CHECK(!n->disk.head && n->disk.ready==120 && n->disk.control==0x27 && !n->disk.motor);
    CHECK(n->disk.timer_control==3 && n->disk.master==5 && n->disk.changed && n->disk.fast_locked);
    CHECK(n->disk.drive[2]==0x46 && waits==3 && flushes==6);
    /* Actual bank-2 fallbacks are retained for the native APU/controller
     * callbacks. No fabricated C ABI is used for those interpreter entries. */
    const u32 reads[]={0x4000,0x4015,0x4016,0x4017,0x402F,0x4034,0x4092,0x5FFF};
    for(unsigned i=0;i<sizeof(reads)/sizeof(*reads);i++) {
        r=registers();r.r[4]=reads[i];saved=r;
        af_v3_qd_native_read_dispatch(s,&r);untouched(&r,&saved,1u<<8);
        CHECK(r.r[8]==(uint64_t)(int64_t)(int32_t)(b.base+0x808303E0u-0x8082A070u));
    }
    n->disk.drive[0]=0x81;n->disk.drive[1]=0xA7;n->disk.drive[3]=0x80;n->disk.head=65535;
    for(u32 at=0x4030;at<=0x4033;at++) {
        r=registers();r.r[4]=at;r.r[19]=0xEEE2;saved=r;
        AFQDisk expected=n->disk;int value=af_v3_qd_read(&expected,at,0xEEE2);
        af_v3_qd_native_read_dispatch(s,&r);untouched(&r,&saved,(1u<<2)|(1u<<8));
        CHECK(r.r[2]==(u32)value && r.r[8]==saved.r[31]);
        CHECK(!memcmp(&n->disk,&expected,sizeof(expected)));
    }
    CHECK(!n->disk.head && !n->disk.drive[0]);
    for(u32 pc=0xDFFF;pc<=0xF000;pc+=0x801) {
        r=registers();r.r[4]=0x4032;r.r[19]=pc;
        AFQDisk expected=n->disk;int value=af_v3_qd_read(&expected,0x4032,pc);
        af_v3_qd_native_read_dispatch(s,&r);CHECK(r.r[2]==(u32)value);
    }
    const u32 writes[]={0x4000,0x4014,0x4016,0x4017,0x401F,0x4027,0x4080,0x5FFF};
    for(unsigned i=0;i<sizeof(writes)/sizeof(*writes);i++) {
        r=registers();r.r[4]=writes[i];saved=r;
        af_v3_qd_native_write_dispatch(s,&r);untouched(&r,&saved,1u<<8);
        CHECK(r.r[8]==(uint64_t)(int64_t)(int32_t)(b.base+0x808308C4u-0x8082A070u));
    }
    /* Timer latch: 1140 cycles / 114 = ten scanlines, starting at -20. */
    s[0x1B2E]=0xFF;s[0x1B2F]=0xEC;
    const u32 addresses[]={0x4020,0x4021,0x4022,0x4023,0x4026};
    const u32 values[]={0x74,4,2,3,0x53};
    for(unsigned i=0;i<5;i++) {
        r=registers();r.r[4]=addresses[i];r.r[5]=values[i];saved=r;
        af_v3_qd_native_write_dispatch(s,&r);untouched(&r,&saved,1u<<8);
        CHECK(r.r[8]==(i==3?(uint64_t)(int64_t)(int32_t)(b.base+0x808308ECu-0x8082A070u):saved.r[14]));
    }
    CHECK(n->disk.latch==10 && n->disk.target==-10 && s[0x1B32]==0 && s[0x1B33]==10);
    CHECK(s[0x1B30]==0xFF && s[0x1B31]==0xF6 && s[0x1AF9]==2);
    CHECK(n->disk.master==3 && n->disk.drive[3]==0x53);
    r=registers();r.r[12]=(uint64_t)(int64_t)-10;saved=r;
    af_v3_qd_native_irq_dispatch(s,&r);untouched(&r,&saved,1u<<8);
    CHECK(r.r[8]==(uint64_t)(int64_t)(int32_t)(b.base+0x8083100Cu-0x8082A070u));
    CHECK(s[0x1B30]==0x7F && s[0x1B31]==255 && !s[0x1AF9] && n->disk.drive[0]==1);
    r=registers();r.r[12]=0;saved=r;
    af_v3_qd_native_irq_dispatch(s,&r);untouched(&r,&saved,1u<<8);
    CHECK(r.r[8]==(uint64_t)(int64_t)(int32_t)(b.base+0x8082F23Cu-0x8082A070u));
    /* Transfer start invokes the full motor sequence, changes native mirroring,
     * and wraps scheduling from the last visible scanline to -20. */
    s[0x1B2E]=0;s[0x1B2F]=238;
    r=registers();r.r[4]=0x4025;r.r[5]=0xED;saved=r;
    af_v3_qd_native_write_dispatch(s,&r);untouched(&r,&saved,1u<<8);
    CHECK(!sound_events && sound_delays==13 && r.r[8]==saved.r[14]);
    CHECK(s[0x1B36]==8 && !s[0x1B37] && n->disk.target==-20 && s[0x1AF9]==0x80);
    r=registers();r.r[12]=(uint64_t)(int64_t)-20;saved=r;
    af_v3_qd_native_irq_dispatch(s,&r);untouched(&r,&saved,1u<<8);
    CHECK(r.r[8]==(uint64_t)(int64_t)(int32_t)(b.base+0x8083100Cu-0x8082A070u));
    CHECK(n->disk.drive[1]==disk[0] && n->disk.target==-19);
    r=registers();r.r[4]=0x4025;r.r[5]=0xE7;saved=r;
    af_v3_qd_native_write_dispatch(s,&r);untouched(&r,&saved,1u<<8);
    CHECK(!sound_events && sound_delays==26 && s[0x1B36]==4 && !s[0x1B37]);
    /* Invalid transfer input records an error without changing disk memory. */
    n->disk.control=0x81;n->disk.head=0;r=registers();r.r[4]=0x4024;r.r[5]=0x45;
    af_v3_qd_native_write_dispatch(s,&r);CHECK(n->error==2);
    n->error=0;n->disk.control=0xE5;n->disk.head=65536;r=registers();r.r[12]=0;
    af_v3_qd_native_irq_dispatch(s,&r);CHECK(n->error==2);
    /* Audio cannot start on an unpatched owner or after its thread is enabled. */
    CHECK(af_v3_qd_native_audio_initialize(n)==AF_QD_BAD_STATE && !sound_events);
    put(native_owner+0x80833DBC-0x8082A070,0x08000000u|((u32)(uintptr_t)af_v3_qd_dpcm_bridge>>2&0x03FFFFFFu));
    put(native_owner+0x80833DC0-0x8082A070,0);
    native_owner[0x808549CF-0x8082A070]=255;
    CHECK(af_v3_qd_native_audio_initialize(n)==AF_QD_BAD_STATE && !sound_events);
    native_owner[0x808549CF-0x8082A070]=0;
    native_owner[0x808549C4-0x8082A070]=1;
    CHECK(af_v3_qd_native_audio_initialize(n)==AF_QD_BAD_STATE && !sound_events);
    native_owner[0x808549C4-0x8082A070]=0;
    CHECK(!af_v3_qd_native_audio_initialize(n) && n->audio_initialized);
    CHECK(sound_events==7 && sound_resets==1 && sound_binds==1);
    CHECK(af_v3_qd_native_audio_initialize(n)==AF_QD_BAD_STATE && sound_events==7);
    /* DPCM crosses programme/BIOS boundaries and wraps FFFF -> 8000 without
     * depending on adjacent allocations. The existing waveform code retains
     * all registers except the fetched byte and its continuation scratch. */
    for(unsigned i=0;i<32768;i++)program[i]=(u8)(i*13+(i>>8));
    for(unsigned i=0;i<8192;i++)bios[i]=(u8)(0x87+i*29+(i>>7));
    u8 *audio=native_owner+0x80854DF0-0x8082A070;
    const u32 starts[]={0,0x1FC0,0x2000,0x3FC0};
    const u32 offsets[]={0,63,64,127,0x1000,0x1FFF};
    for(unsigned i=0;i<4;i++)for(unsigned j=0;j<6;j++) {
        audio[0x18]=starts[i]>>8;audio[0x19]=starts[i];
        r=registers();r.r[6]=b.base+0x80854DF0-0x8082A070;r.r[4]=offsets[j];saved=r;
        af_v3_qd_native_dpcm_dispatch(audio,&r);untouched(&r,&saved,(1u<<8)|(1u<<13));
        u32 at=0xC000+starts[i]+offsets[j];if(at>=0x10000)at-=0x8000;
        u32 expected=at>=0xE000?bios[at-0xE000]:program[at-0x6000];
        CHECK(r.r[13]==expected && audio[0x1C]==expected);
        CHECK(r.r[8]==(uint64_t)(int64_t)(int32_t)(b.base+0x80833DD8u-0x8082A070u));
    }
    n->error=0;r.r[4]=0x2000;af_v3_qd_native_dpcm_dispatch(audio,&r);
    CHECK(n->error==3 && !r.r[13] && !audio[0x1C]);
    /* Closed/different sessions retain the original cartridge reader. */
    put(native_owner+0x80837BC0-0x8082A070,(u32)(uintptr_t)program);
    u32 magic=n->magic;n->magic=0;audio[0x18]=0x12;audio[0x19]=0x40;
    r=registers();r.r[6]=b.base+0x80854DF0-0x8082A070;r.r[4]=0x321;saved=r;
    af_v3_qd_native_dpcm_dispatch(audio,&r);untouched(&r,&saved,(1u<<8)|(1u<<13));
    CHECK(r.r[13]==program[0x1561] && audio[0x1C]==program[0x1561]);n->magic=magic;
    for(unsigned i=0;i<16;i++) {
        CHECK(state[i]==0x5A && state[AF_QDN_STATE_BYTES+16+i]==0x5A);
        CHECK(graphics[i]==0xA5 && graphics[AF_QDN_GRAPHICS_BYTES+16+i]==0xA5);
    }
    CHECK(!memcmp(disk,original,sizeof(disk)));
    printf("%u native QD adapter checks: startup/reset, I/O/IRQ, motor yield, audio initialization/DPCM banks, CPU/RAM/WDM, CHR/cache and guards; native calls stubbed\n",checks);
}
