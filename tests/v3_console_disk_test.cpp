/* Complete donor C fast-I/O functions plus focused disk register expectations.
 * No CPU interpreter, renderer, or native sound is stubbed into a gameplay claim. */
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <cstdint>
#include <climits>
extern "C" {
#include "../overlays/v3/console_disk.h"
}
using u8=unsigned char;
using u32=unsigned int;
#define KS_NES_WRAM_SIZE 2048
#define KS_NES_CHRRAM_SIZE 8192
#define KS_NES_BBRAM_SIZE 32768
static unsigned checks,conversions;
#define CHECK(t) do {checks++;if(!(t)){std::fprintf(stderr,"line %d: %s\n",__LINE__,#t);std::abort();}} while(0)
struct ksNesCommonWorkObj {};
struct ksNesStateObj {
    u8 wram[2048];u8 *nesromp,*chrramp,*bbramp;
    u32 frame_flags;
    u8 fds_fast_io_lock,fds_disk_count,_176E[27],qd_irq_acknowledged_flag;
    union { struct {u8 *cpu_0000_1fff,*cpu_2000_3fff,*cpu_4000_5fff,*cpu_6000_7fff,
        *cpu_8000_9fff,*cpu_a000_bfff,*cpu_c000_dfff,*cpu_e000_ffff;};u8 *banks[8];};
};
static AFQDisk q;
static ksNesStateObj sp;
static ksNesCommonWorkObj wp;
static u8 original[65536],disk[2*65536],donor_disk[2*65536],bios[8192],original_bios[8192],boot_state[AF_QD_BOOT_STATE];
static u8 work[2048],prg[32768],chr[8192],donor_prg[32768],donor_chr[8192];
static void ksNesConvertChrToI8(ksNesCommonWorkObj *,const u8 *data,u32 tile) {
    CHECK(tile==conversions && data==donor_chr+tile*16);conversions++;
}
#include "donor_disk.inc"
static void le(u8 *p,u32 n) {p[0]=(u8)n;p[1]=(u8)(n>>8);}
static void load(const char *name,u8 *data,size_t bytes) {
    FILE *f=std::fopen(name,"rb");CHECK(f);CHECK(std::fread(data,1,bytes,f)==bytes);CHECK(std::fgetc(f)==EOF);CHECK(!std::fclose(f));
}
static void setup(unsigned sides=1) {
    for(unsigned s=0;s<sides;s++) {
        std::memcpy(disk+s*65536,original,65536);disk[s*65536+15]+=(u8)s;
    }
    std::memcpy(donor_disk,disk,sides*65536);
    std::memset(&sp,0,sizeof(sp));std::memset(work,0xA5,sizeof(work));std::memset(prg,0x5A,sizeof(prg));
    std::memset(chr,0xC3,sizeof(chr));std::memcpy(sp.wram,work,sizeof(work));
    std::memcpy(donor_prg,prg,sizeof(prg));std::memcpy(donor_chr,chr,sizeof(chr));
    std::memcpy(bios,original_bios,sizeof(bios));
    CHECK(!af_v3_qd_bind(&q,disk,sides*65536,work,prg,chr,bios,boot_state));
    sp.nesromp=donor_disk;sp.chrramp=donor_chr;sp.bbramp=donor_prg;sp.fds_disk_count=(u8)sides;
    /* Donor pointer tables use address-biased native views. Construct their
     * numeric biases without C pointer subtraction outside an object. */
    for(unsigned i=0;i<8;i++)sp.banks[i]=(u8 *)((uintptr_t)(i<3?sp.wram:i==7?bios:donor_prg+(i-3)*8192)-i*8192);
    conversions=0;
}
static void compare_boot(void) {
    CHECK(af_v3_qd_boot(&q)==ksNesQDFastLoad(&wp,&sp));
    CHECK(!std::memcmp(work,sp.wram,sizeof(work)));
    CHECK(!std::memcmp(prg,donor_prg,sizeof(prg)));CHECK(!std::memcmp(chr,donor_chr,sizeof(chr)));
    CHECK(!std::memcmp(disk,donor_disk,q.disk_bytes));
}
static void compare_save(unsigned side,unsigned slot,u32 source,u32 size) {
    u8 request[27]={};std::memcpy(request,disk+side*65536+15,10);
    std::memcpy(request+10,original+0xA15D+2,14);le(request+21,size);le(request+24,source);
    work[14]=sp.wram[14]=(u8)slot;std::memcpy(sp._176E,request,sizeof(request));
    CHECK(af_v3_qd_save(&q,request)==ksNesQDFastSave(&wp,&sp));
    CHECK(!std::memcmp(disk,donor_disk,q.disk_bytes));CHECK(q.changed==sp.qd_irq_acknowledged_flag);
}
static void save_call(AFQCpu *cpu,u32 ret=0x7FFD) {
    /* Descriptor pointers straddle a CPU bank; payload itself remains the
     * actual score file. Neither the request nor return address is fabricated
     * by the service being tested. */
    le(work+0x101+cpu->stack,ret);
    le(prg+ret+1-0x6000,0x8200);le(prg+ret+3-0x6000,0x8400);
    std::memcpy(prg+0x2200,disk+15,10);
    std::memcpy(prg+0x2400,original+0xA15D+2,14);
    le(prg+0x2400+14,0x750);prg[0x2400+16]=0;
    for(unsigned i=0;i<84;i++)work[0x750+i]=(u8)(i*9+7);
}
static void wdm_checks(void) {
    setup();
    for(unsigned i=0;i<sizeof(bios);i++)
        CHECK(bios[i]==(i==0xEBD?0x42:i==0x1A0?0x7F:original_bios[i]));
    AFQCpu cpu={0xE7A6,0x22,0xFD,0x8080,0xFFFF1235},before=cpu;
    CHECK(!af_v3_qd_wdm(&q,&cpu,0));CHECK(cpu.pc==0xE7A4 && cpu.cycles==5);
    CHECK(cpu.a==before.a && cpu.stack==before.stack && cpu.zero==before.zero);
    cpu.pc=0xEEBF;cpu.a=0x61;before=cpu;AFQDisk disk_before=q;
    CHECK(!af_v3_qd_wdm(&q,&cpu,0));CHECK(!std::memcmp(&cpu,&before,sizeof(cpu)));
    CHECK(!std::memcmp(&q,&disk_before,sizeof(q)));
    cpu.a=0x40;
    CHECK(!af_v3_qd_wdm(&q,&cpu,0));CHECK(cpu.pc==0xEE9B && !cpu.zero && cpu.a==0x40);
    CHECK(cpu.stack==0xFD && cpu.cycles==5 && q.chr_dirty);
    CHECK(q.drive[2]==0x46 && q.disk_status==0x46 && bios[0xEBD]==0xA9);
    for(unsigned i=0;i<0xFA;i++)CHECK(!work[i]);
    CHECK(!std::memcmp(work+0xFA,boot_state,sizeof(boot_state)));
    CHECK(work[0x1FE]==0xA5 && work[0x1FF]==0xA5);
    CHECK(!std::memcmp(prg,original+0x146,sizeof(prg)));
    CHECK(!std::memcmp(chr,original+0x815B,sizeof(chr)));
    CHECK(!std::memcmp(work+0x750,original+0xA170,84));
    af_v3_qd_reset(&q);CHECK(bios[0xEBD]==0x42 && q.disk_status==0x47);
    std::memcpy(disk+16,"koro",4);af_v3_qd_reset(&q);CHECK(bios[0x1A0]==0xFF);
    for(unsigned failure=0;failure<3;failure++) {
        setup();cpu={0xEEBF,0x40,0xFD,0x88,0x99};before=cpu;
        if(failure==0)disk[21]=1;
        if(failure==1)q.frame_flags=0x400;
        if(failure==2)le(disk+0x8148+11,1);
        CHECK(af_v3_qd_wdm(&q,&cpu,0)==(failure==2?AF_QD_BAD_DATA:0));
        CHECK(cpu.pc==before.pc && cpu.a==before.a && cpu.stack==before.stack && cpu.cycles==before.cycles);
        CHECK(cpu.zero==(failure==0?0x5C:failure==1?0xFF:before.zero));
        CHECK(bios[0xEBD]==(failure==2?0x42:0xA9) && !q.chr_dirty);
        CHECK(!std::memcmp(prg,donor_prg,sizeof(prg)) && !std::memcmp(chr,donor_chr,sizeof(chr)));
    }
    setup(2);disk[65536+16]^=1;cpu={0xE408,0x60,0xFD,0xFFFF,0xFFFF1234};
    work[0]=0x20;std::memcpy(prg+0x21,disk+65536+16,8);before=cpu;
    CHECK(!af_v3_qd_wdm(&q,&cpu,0));CHECK(q.head==65536 && work[1]==0x60);
    CHECK(!std::memcmp(&cpu,&before,sizeof(cpu)));
    q.head=123;std::memset(prg+0x21,255,4);
    CHECK(!af_v3_qd_wdm(&q,&cpu,0) && q.head==123);
    std::memset(prg+0x21,0,8);
    CHECK(!af_v3_qd_wdm(&q,&cpu,0) && q.head==123);
    cpu.a=255;work[0]=255;work[1]=0x55;disk_before=q;before=cpu;
    CHECK(af_v3_qd_wdm(&q,&cpu,0)==AF_QD_BAD_DATA && work[1]==0x55);
    CHECK(!std::memcmp(&q,&disk_before,sizeof(q)) && !std::memcmp(&cpu,&before,sizeof(cpu)));
    setup();cpu={0xEEF6,0x22,0xFD,0x8080,0x1234};work[0x90]=0x55;
    CHECK(!af_v3_qd_wdm(&q,&cpu,0x60000000));CHECK(cpu.a==0x55 && q.disk_status==0x47);
    CHECK(cpu.zero==0x8080 && cpu.cycles==0x1234 && cpu.pc==0xEEF6 && cpu.stack==0xFD);
    CHECK(!af_v3_qd_wdm(&q,&cpu,0));CHECK(q.disk_status==0x46);
    setup();cpu={0xE23B,3,0xFD,0x1234,0xF001};save_call(&cpu);
    CHECK(!af_v3_qd_wdm(&q,&cpu,0));CHECK(cpu.pc==0x8002 && cpu.stack==255 && !cpu.zero && !cpu.a);
    CHECK(cpu.cycles==0xF001 && q.changed && disk[0x3B]==4);
    CHECK(!std::memcmp(disk+0xA170,work+0x750,84));
    for(unsigned path=0;path<4;path++) {
        setup();cpu={0xE23B,3,255,0x1234,0xF001};save_call(&cpu);before=cpu;
        if(path==0) {cpu.a=255;before=cpu;}
        if(path==1)q.fast_locked=1;
        if(path==2)prg[0x2200]^=1;
        if(path==3)le(prg+0x7FFE - 0x6000,65532);
        u8 old=work[14];
        CHECK(af_v3_qd_wdm(&q,&cpu,0)==(path==3?AF_QD_BAD_DATA:0));
        CHECK(cpu.pc==before.pc && cpu.stack==before.stack && cpu.cycles==before.cycles);
        CHECK(cpu.a==(path==1 || path==2?255:before.a));
        CHECK(cpu.zero==(path==1 || path==2?255:before.zero));
        CHECK(!q.changed && !std::memcmp(disk,donor_disk,65536));
        CHECK(work[14]==(path==3?old:before.a));
    }
    setup();cpu={0xE23B,3,255,0,0};save_call(&cpu);
    CHECK(!af_v3_qd_wdm(&q,&cpu,0) && cpu.stack==1 && cpu.pc==0x8002);
    setup();cpu={0x1234,0,0,1,0};before=cpu;disk_before=q;
    CHECK(!af_v3_qd_wdm(&q,&cpu,0));CHECK(!std::memcmp(&cpu,&before,sizeof(cpu)));
    CHECK(!std::memcmp(&q,&disk_before,sizeof(q)));
    CHECK(af_v3_qd_wdm(&q,(AFQCpu *)work,0)==AF_QD_BAD_STATE);
    disk_before=q;CHECK(af_v3_qd_bind(&q,disk,65536,work,prg,chr,bios,bios)<0);
    CHECK(!std::memcmp(&q,&disk_before,sizeof(q)));
}
static void native_characters(void) {
    setup();CHECK(!af_v3_qd_boot(&q));CHECK(q.chr_dirty);
    u8 patterns[AF_QD_CHARACTER+32];std::memset(patterns,0x5A,sizeof(patterns));
    AFQDisk before=q;
    CHECK(af_v3_qd_native_characters(&q,patterns,8191)==AF_QD_BAD_STATE);
    CHECK(!std::memcmp(&q,&before,sizeof(q)));
    CHECK(af_v3_qd_native_characters(&q,chr,8192)==AF_QD_BAD_STATE);
    CHECK(!std::memcmp(&q,&before,sizeof(q)));
    CHECK(!af_v3_qd_native_characters(&q,patterns+16,8192) && !q.chr_dirty);
    /* Read the native rows back as 64 paired tiles per block; reconstruct
     * both raw planes and compare every tile to the actual donor boot output. */
    for(unsigned group=0;group<8;group++)for(unsigned row=0;row<8;row++)
        for(unsigned column=0;column<64;column++) {
            unsigned dest=16+group*1024+row*128+column*2;
            unsigned src=(group*64+column)*16+row;
            CHECK(patterns[dest]==chr[src+8] && patterns[dest+1]==chr[src]);
        }
    for(unsigned i=0;i<16;i++)CHECK(patterns[i]==0x5A && patterns[8208+i]==0x5A);
    CHECK(!std::memcmp(chr,original+0x815B,8192));
}
int main(int argc,char **argv) {
    CHECK(argc==4);load(argv[1],original,sizeof(original));load(argv[2],original_bios,sizeof(original_bios));
    load(argv[3],boot_state,sizeof(boot_state));
    setup();compare_boot();CHECK(conversions==512 && q.chr_dirty);
    for(unsigned i=0;i<84;i++)work[0x750+i]=sp.wram[0x750+i]=(u8)(i*7+3);
    compare_save(0,3,0x750,84);
    setup(2);compare_boot();
    for(unsigned i=0;i<sizeof(prg);i++)prg[i]=donor_prg[i]=(u8)(i*17+3);
    compare_save(1,3,0x7FF0,84); /* CPU bank boundary, second disk identity. */
    for(unsigned failure=0;failure<3;failure++) {
        setup();
        if(failure==0)q.frame_flags=sp.frame_flags=0x400;
        if(failure==1)disk[21]=donor_disk[21]=1;
        if(failure==2)q.fast_locked=sp.fds_fast_io_lock=1;
        if(failure<2) {compare_boot();CHECK(!conversions && !q.chr_dirty);}
        if(failure!=1)compare_save(0,3,0x750,84);
    }
    /* Unsafe donor-input cases must fail before modifying output buffers. */
    for(unsigned bad=0;bad<4;bad++) {
        setup();AFQDisk before=q;u8 saved_work[2048];std::memcpy(saved_work,work,sizeof(work));
        if(bad==0)le(disk+0x8148+11,1); // 8-KiB CHR would overrun by one.
        if(bad==1)le(disk+0xA15D+13,0xFFFF);
        if(bad==2)disk[0x3E]=0;
        if(bad==3) {le(disk+0x133+11,0x700);le(disk+0x133+13,32768);}
        CHECK(af_v3_qd_boot(&q)==AF_QD_BAD_DATA);
        CHECK(!std::memcmp(&q,&before,sizeof(q)));CHECK(!std::memcmp(work,saved_work,sizeof(work)));
        CHECK(!std::memcmp(prg,donor_prg,sizeof(prg)));CHECK(!std::memcmp(chr,donor_chr,sizeof(chr)));
    }
    setup();AFQDisk before=q;
    CHECK(af_v3_qd_bind(&q,disk,65536,work,prg,prg,bios,boot_state)<0);CHECK(!std::memcmp(&q,&before,sizeof(q)));
    for(unsigned bad=0;bad<5;bad++) {
        setup();u8 request[27]={};std::memcpy(request,disk+15,10);
        std::memcpy(request+10,original+0xA15D+2,14);le(request+21,84);le(request+24,0x750);work[14]=3;
        if(bad==0)le(request+24,65530);
        if(bad==1)q.cpu_bytes[0]=7;
        if(bad==2)q.cpu[0]=disk;
        if(bad==3)work[14]=5;
        if(bad==4)request[23]=3;
        before=q;CHECK(af_v3_qd_save(&q,request)<0);
        CHECK(!std::memcmp(disk,donor_disk,65536));CHECK(!std::memcmp(&q,&before,sizeof(q)));
    }
    setup();
    CHECK(af_v3_qd_write(&q,0x4020,228,0)==0);
    CHECK(af_v3_qd_write(&q,0x4021,0,0)==0);
    CHECK(af_v3_qd_write(&q,0x4022,3,20)==0 && q.latch==2 && q.target==22 && q.irq_enable==2);
    CHECK(af_v3_qd_irq(&q,22)==AF_QD_IRQ && q.target==24 && q.timer_control==1 && !q.irq_enable);
    CHECK(af_v3_qd_read(&q,0x4030,0x6000)==1 && !q.drive[0]);
    q.head=100;
    CHECK(af_v3_qd_write(&q,0x4025,0xE5,238)==(AF_QD_SOUND_SYNC|AF_QD_MIRROR));
    CHECK(q.target==-20 && q.irq_enable==128);
    CHECK(af_v3_qd_irq(&q,-20)==AF_QD_IRQ && q.drive[1]==disk[100] && q.target==-19);
    CHECK(af_v3_qd_read(&q,0x4031,0x6000)==disk[100] && q.head==101);
    CHECK(af_v3_qd_write(&q,0x4025,0x81,0)==AF_QD_MIRROR);
    CHECK(af_v3_qd_write(&q,0x4024,0x5A,0)==0 && disk[99]==0x5A && q.changed);
    q.head=1;before=q;CHECK(af_v3_qd_write(&q,0x4024,0x5A,0)==AF_QD_BAD_DATA);
    CHECK(!std::memcmp(&q,&before,sizeof(q)));
    q.head=65536;q.control=0xE5;before=q;
    CHECK(af_v3_qd_irq(&q,0)==AF_QD_BAD_DATA && !std::memcmp(&q,&before,sizeof(q)));
    for(unsigned control=0;control<256;control++) {
        setup();int result=af_v3_qd_write(&q,0x4025,control,238);
        CHECK(result==(AF_QD_MIRROR|(((control^0x27)&2)?AF_QD_SOUND_SYNC:0)));
        CHECK(q.mirror==(control&8) && q.control==control);
        CHECK(q.target==((control&128)?-20:32767));
        CHECK(af_v3_qd_read(&q,0x4032,0xE000)==0x40);
        CHECK(af_v3_qd_read(&q,0x4032,0xEEE2)==(q.drive[2]&q.disk_status));
        CHECK(af_v3_qd_read(&q,0x4032,0x6000)==0x45+(int)(control&2));
    }
    setup();
    for(unsigned n=0;n<300;n++)af_v3_qd_frame(&q,0);
    CHECK(q.ready==120);af_v3_qd_frame(&q,0x80000000);CHECK(q.ready==196);
    for(unsigned n=0;n<60;n++)af_v3_qd_frame(&q,0);
    CHECK(!q.ready);q.control&=0xFD;af_v3_qd_frame(&q,0);CHECK(q.motor==89);
    q.control|=2;af_v3_qd_frame(&q,0);CHECK(q.motor==88);
    before=q;CHECK(af_v3_qd_write(&q,0x4025,0,INT_MAX)==AF_QD_BAD_STATE);
    CHECK(!std::memcmp(&q,&before,sizeof(q)));
    wdm_checks();
    native_characters();
    std::printf("%u QD checks: donor boot/save, BIOS WDM/reset, native CHR conversion, disk timing/bounds; no native execution\n",checks);
}
