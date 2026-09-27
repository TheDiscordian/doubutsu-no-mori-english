/* Native CPU/CHR bindings for the complete QD service. No cartridge header is
 * fabricated. Native audio initialization and session installation
 * must be supplied before a disk game can be enabled. */
#include "console_disk_native.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ addr;
#define BASE 0x8082A070u
#define MAGIC 0x51444E31u
#define GUARD 0x51444721u
#ifdef __mips__
#define context ((AFQNative *)0x80638000u)
#define MEMORY(at) ((u8 *)(at))
#define FN(at,type,...) ((type (*)(__VA_ARGS__))(at))
#else
extern AFQNative af_qdn_test_context;
extern void *af_qdn_test_function(u32);
extern u8 *af_qdn_test_memory(u32);
#define context (&af_qdn_test_context)
#define MEMORY(at) af_qdn_test_memory(at)
#define FN(at,type,...) ((type (*)(__VA_ARGS__))af_qdn_test_function(at))
#endif
_Static_assert(sizeof(AFQNative)<=0x200,"Disk context exceeds reservation");
_Static_assert(sizeof(AFQNativeRegisters)==272,"Changed native bridge frame");
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void half(u8 *p,u32 v) {p[0]=v>>8;p[1]=v;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static void fill(u8 *d,u8 v,u32 n) {while(n--)*d++=v;}
static u8 *native(const AFQNative *n,u32 linked) {return MEMORY(n->base+linked-BASE);}
static unsigned long long pointer(u32 at) {return (unsigned long long)(long long)(int)at;}
static void schedule(AFQNative *n) {
    half(n->state+0x1B30,(unsigned short)n->disk.target);
    half(n->state+0x1B32,n->disk.latch);
    n->state[0x1AF9]=n->disk.irq_enable;
}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    addr x=(addr)a,y=(addr)b;
    if(!a || !b || an>(addr)-1-x || bn>(addr)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static int valid(const AFQNative *n) {
    return n && n->magic==MAGIC && n->guard==GUARD && n->state && n->graphics &&
        n->disk.work==n->state && !(n->base&15) && n->base>=0x80000400u &&
        n->base<=0x80400000u-0x2E990u;
}

int af_v3_qd_native_bind(AFQNative *n,const AFQNativeBuffers *b) {
    if(!b || !n || !separate(n,sizeof(*n),b,sizeof(*b)) ||
        b->state_bytes<AF_QDN_STATE_BYTES || b->graphics_bytes<AF_QDN_GRAPHICS_BYTES ||
        (b->base&15) || b->base<0x80000400u || b->base>0x80400000u-0x2E990u)
        return AF_QD_BAD_STATE;
    const void *buffers[]={n,b->state,b->graphics,b->disk,b->program,b->characters,b->bios,b->boot_state};
    const u32 sizes[]={sizeof(*n),AF_QDN_STATE_BYTES,b->graphics_bytes,b->disk_bytes,
        AF_QD_PROGRAM,AF_QD_CHARACTER,AF_QD_BIOS,AF_QD_BOOT_STATE};
    for(u32 i=0;i<8;i++) {
        if(!separate(buffers[i],sizes[i],b,sizeof(*b)))return AF_QD_BAD_STATE;
        for(u32 j=i+1;j<8;j++)if(!separate(buffers[i],sizes[i],buffers[j],sizes[j]))return AF_QD_BAD_STATE;
    }
    /* af_v3_qd_bind checks the complete disk and all its targets before writes. */
    int result=af_v3_qd_bind(&n->disk,b->disk,b->disk_bytes,b->state,
        b->program,b->characters,b->bios,b->boot_state);
    if(result)return result;
    n->state=b->state;n->graphics=b->graphics;n->base=b->base;
    n->error=0;n->guard=GUARD;n->magic=MAGIC;n->initialized=0;
    return 0;
}

int af_v3_qd_native_graphics(AFQNative *n) {
    if(!valid(n))return AF_QD_BAD_STATE;
    /* The native frame/reset wrapper waits for the previous RSP task. Keep
     * that ownership barrier even for a BIOS service running inside a frame. */
    FN(n->base+0x8082A070u-BASE,void,void)();
    int result=af_v3_qd_native_characters(&n->disk,n->state+0x62C8,AF_QD_CHARACTER);
    if(result)return result;
    copy(n->graphics+0x2008,n->state+0x62C8,AF_QD_CHARACTER);
    FN(0x8002FE00u,void,void *,u32)(n->graphics+0x2008,AF_QD_CHARACTER);
    FN(0x8002FE00u,void,void *,u32)(n->state+0x62C8,AF_QD_CHARACTER);
    return 0;
}

int af_v3_qd_native_map(AFQNative *n) {
    if(!valid(n))return AF_QD_BAD_STATE;
    u8 *s=n->state;
    /* Unlike the bounded service views, native CPU banks are biases to which
     * the interpreter adds the full 16-bit CPU address. Its low banks use the
     * existing mirrored work/PPU/I/O callbacks, not these direct RAM stores. */
    for(u32 bank=0;bank<8;bank++) {
        u32 bias=bank<3?(u32)(addr)s:bank==7?(u32)(addr)n->disk.bios-0xE000u:
            (u32)(addr)n->disk.program-0x6000u;
        put(s+0x1A38+bank*4,bias);
        if(bank>=3)put(s+0x18E4+bank*4,n->base+0x8082F994u-BASE);
        if(bank>=3 && bank<=6)put(s+0x18C0+bank*4,(u32)(addr)af_v3_qd_ram_bridge);
    }
    /* BIOS is read-only; retain the native no-op store for E000..FFFF. */
    put(s+0x18DC,n->base+0x8082F964u-BASE);
    put(s+0x18EC,(u32)(addr)af_v3_qd_read_bridge);
    put(s+0x18C8,(u32)(addr)af_v3_qd_write_bridge);
    put(s+0x1AB8,(u32)(addr)af_v3_qd_irq_bridge);
    put(s+0x1A74,0); /* QD has no PRG ROM; do not misidentify RAM as a cartridge. */
    put(s+0x1A7C,AF_QD_PROGRAM);
    put(s+0x1A78,(u32)(addr)n->disk.characters);
    put(s+0x1A80,0); /* Native dynamic character-RAM rendering path. */
    put(s+0x1A84,AF_QD_CHARACTER-1);
    put(s+0x1AA0,(u32)(addr)n->graphics);
    s[0x1B03]=255;s[0x1B4B]=3;
    put(s+0x181C,n->base+0x8083055Cu-BASE);
    for(u32 i=0;i<8;i++) {s[0x1B68+i*2]=0;s[0x1B69+i*2]=(u8)i;}
    /* Size=2 and cycles=2*256 follow the native instruction-table encoding.
     * Only this instance's WDM row changes; cartridge tables stay untouched. */
    put(s+0x0C20,(u32)(addr)af_v3_qd_wdm_bridge);
    put(s+0x0C24,0);put(s+0x0C28,0);
    s[0x0C2C]=2;s[0x0C2D]=255;s[0x0C2E]=2;s[0x0C2F]=0;
    return af_v3_qd_native_graphics(n);
}

int af_v3_qd_native_reset_button(AFQNative *n) {
    if(!valid(n) || !n->initialized)return AF_QD_BAD_STATE;
    u8 *s=n->state;AFQDisk *q=&n->disk;
    /* GAFE01 ksNesPushResetButton, expressed in the native interpreter's
     * register layout. In particular this is NOT af_v3_qd_reset: that cold
     * reset patches BIOS and drive status which the reset button retains. */
    fill(s+0x1B42,0,3);s[0x1B45]=255;s[0x1B4A]=4;
    s[0x1AFA]=0;s[0x1B5D]=0x40;s[0x1B5B]=0;s[0x1AF9]=0;
    half(s+0x1B30,0x7FFF);half(s+0x1B2A,0x7FFF);s[0x1AED]=255;
    q->timer_lo=q->timer_hi=0;q->head=0;q->control=0x27;
    q->motor=0;q->ready=120;q->target=0x7FFF;q->irq_enable=0;
    half(s+0x1B3E,(u32)q->bios[0x1FFC]|(u32)q->bios[0x1FFD]<<8);
    return 0;
}

int af_v3_qd_native_initialize(AFQNative *n) {
    if(!valid(n) || n->initialized)return AF_QD_BAD_STATE;
    u8 *s=n->state;
    /* This is a fresh allocated session. Establish the real state pointer and
     * idle RSP flag before the shared graphics operation invokes native wait. */
    fill(s,0,AF_QDN_STATE_BYTES);put(s+0x1ACC,0x400);
    put(native(n,0x80852690u),(u32)(addr)n->disk.disk);
    put(native(n,0x80852694u),(u32)(addr)s);
    fill(native(n,0x80852698u),0,64);*native(n,0x80835DA0u)=1;
    put(s+0x1A70,(u32)(addr)n->disk.disk);put(s+0x1A9C,(u32)(addr)n->disk.disk);
    /* Native common renderer/interpreter initialization, excluding iNES
     * header, trainer, mapper-table, and PRG-ROM-vector reads. */
    copy(s+0x800,native(n,0x80836770u),0x1000);
    copy(s+0x1800,native(n,0x80835DD0u),0x168);
    put(s+0x1AC8,(u32)-7167);put(s+0x1AD0,n->base+0x8082F138u-BASE);
    put(s+0x1AB4,n->base+0x8082F424u-BASE);
    fill(s+0x1FA0,255,0x100);fill(s+0x20A0,255,0x2000);
    fill(s+0x1A58,0x20,8);half(s+0x1B40,0xFFFF);
    s[0x1B5E]=1; /* native audio timestamp divisor, refreshed by each frame */
    half(s+0x1B36,0x800); /* donor's initial horizontal nametables */
    fill(s+0x42A0,15,32);
    fill(n->graphics+0x2008,0,0x4000);
    fill(n->disk.program,255,AF_QD_PROGRAM);
    fill(n->disk.characters,0,AF_QD_CHARACTER);
    for(u32 i=0;i<AF_QD_WORK;i+=4)put(s+i,0x0FEFFE7Du);
    af_v3_qd_reset(&n->disk);
    int result=af_v3_qd_native_map(n);
    if(result) {n->error=(u32)-result;return result;}
    n->initialized=1;
    return af_v3_qd_native_reset_button(n);
}

void af_v3_qd_native_wdm_dispatch(u8 *s,AFQNativeRegisters *r) {
    AFQNative *n=context;
    if(!valid(n) || n->state!=s || !r)return;
    AFQCpu cpu={(unsigned short)r->r[19],(u8)r->r[16],(u8)r->r[20],
        (u32)r->r[21],(u32)r->r[25]};
    /* Native 1ACC is the RSP completion flag, not donor frame_flags. The
     * lifecycle owns disk frame_flags; do not confuse those unrelated fields. */
    int result=af_v3_qd_wdm(&n->disk,&cpu,word(s+0x42C4));
    if(!result && n->disk.chr_dirty)result=af_v3_qd_native_graphics(n);
    if(result<0) {n->error=(u32)-result;return;}
    if(cpu.a!=(u8)r->r[16])r->r[16]=cpu.a;
    if(cpu.pc!=(unsigned short)r->r[19])r->r[19]=cpu.pc;
    if(cpu.stack!=(u8)r->r[20])r->r[20]=cpu.stack;
    if(cpu.zero!=(u32)r->r[21])r->r[21]=(unsigned long long)(long long)(int)cpu.zero;
    if(cpu.cycles!=(u32)r->r[25])r->r[25]=(unsigned long long)(long long)(int)cpu.cycles;
}

void af_v3_qd_native_ram_dispatch(u8 *s,AFQNativeRegisters *r) {
    AFQNative *n=context;
    if(!valid(n) || n->state!=s || !r)return;
    u32 at=(u32)r->r[4];
    if(at<0x6000 || at>=0xE000) {n->error=3;return;}
    n->disk.program[at-0x6000]=(u8)r->r[5];
}

void af_v3_qd_native_read_dispatch(u8 *s,AFQNativeRegisters *r) {
    AFQNative *n=context;
    if(!r)return;
    r->r[8]=r->r[31]; /* native load continuation, not the store/WDM t6 */
    if(!valid(n) || n->state!=s) {r->r[2]=0;return;}
    u32 at=(u32)r->r[4];
    if(at<0x4030 || at>0x4033) {
        r->r[8]=pointer(n->base+0x808303E0u-BASE);return;
    }
    int result=af_v3_qd_read(&n->disk,at,(unsigned short)r->r[19]);
    if(result<0) {n->error=(u32)-result;r->r[2]=0;return;}
    r->r[2]=(u32)result;
}

static void motor_sync(AFQNative *n) {
    /* Complete donor ksNesQDSoundSync: timed audio events for thirteen frames.
     * Yield to the existing native timer instead of busy-waiting on the CPU.
     * Audio still requires its real startup/DPCM binding before installation. */
    for(u32 frame=0;frame<13;frame++) {
        for(u32 line=0;line<262;line++)
            FN(n->base+0x80835098u-BASE,void,u32,u32,u32)(0,0,line*114);
        FN(0x8002DA3Cu,void,u32)(16000);
    }
}

void af_v3_qd_native_write_dispatch(u8 *s,AFQNativeRegisters *r) {
    AFQNative *n=context;
    if(!r)return;
    r->r[8]=r->r[14];
    if(!valid(n) || n->state!=s)return;
    u32 at=(u32)r->r[4];
    if(at<0x4020 || at>0x4026) {
        r->r[8]=pointer(n->base+0x808308C4u-BASE);return;
    }
    int line=(short)((unsigned int)s[0x1B2E]<<8|s[0x1B2F]);
    int result=af_v3_qd_write(&n->disk,at,(u8)r->r[5],line);
    if(result<0) {n->error=(u32)-result;return;}
    if(result&AF_QD_SOUND_SYNC)motor_sync(n);
    schedule(n);
    if(result&AF_QD_MIRROR) {
        half(s+0x1B36,n->disk.mirror?0x800:0x400);half(s+0x1B38,0);
    }
    /* Native generic audio store handles the same timestamp division and
     * queue as ordinary APU writes; restore all live interpreter registers
     * before entering it. No C call with a nonstandard interpreter ABI. */
    if(result&AF_QD_AUDIO_WRITE)r->r[8]=pointer(n->base+0x808308ECu-BASE);
}

void af_v3_qd_native_irq_dispatch(u8 *s,AFQNativeRegisters *r) {
    AFQNative *n=context;
    if(!r)return;
    r->r[8]=r->r[14];
    if(!valid(n) || n->state!=s)return;
    r->r[8]=pointer(n->base+0x8082F23Cu-BASE);
    int result=af_v3_qd_irq(&n->disk,(short)r->r[12]);
    if(result<0) {n->error=(u32)-result;return;}
    schedule(n);
    /* The native IRQ request handles P's interrupt mask, its pending bit
     * (0x20, not the donor's 0x04), vector, stack, and return continuation. */
    if(result&AF_QD_IRQ)r->r[8]=pointer(n->base+0x8083100Cu-BASE);
}
