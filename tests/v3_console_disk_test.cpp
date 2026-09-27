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
static u8 original[65536],disk[2*65536],donor_disk[2*65536],bios[8192];
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
    CHECK(!af_v3_qd_bind(&q,disk,sides*65536,work,prg,chr,bios));
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
int main(int argc,char **argv) {
    CHECK(argc==3);load(argv[1],original,sizeof(original));load(argv[2],bios,sizeof(bios));
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
    CHECK(af_v3_qd_bind(&q,disk,65536,work,prg,prg,bios)<0);CHECK(!std::memcmp(&q,&before,sizeof(q)));
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
    std::printf("%u QD checks: complete donor boot/save comparisons, disk registers/timing, malformed bounds; no native execution\n",checks);
}
