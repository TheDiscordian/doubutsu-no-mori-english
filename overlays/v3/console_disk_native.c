/* Native CPU/CHR bindings for the complete QD service. No cartridge header is
 * fabricated. Native common reset, disk I/O/IRQ/audio and session installation
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
#define FN(at,type,...) ((type (*)(__VA_ARGS__))(at))
#else
extern AFQNative af_qdn_test_context;
extern void *af_qdn_test_function(u32);
#define context (&af_qdn_test_context)
#define FN(at,type,...) ((type (*)(__VA_ARGS__))af_qdn_test_function(at))
#endif
_Static_assert(sizeof(AFQNative)<=0x200,"Disk context exceeds reservation");
_Static_assert(sizeof(AFQNativeRegisters)==272,"Changed native bridge frame");
static u32 word(const u8 *p) {return (u32)p[0]<<24|(u32)p[1]<<16|(u32)p[2]<<8|p[3];}
static void put(u8 *p,u32 v) {p[0]=v>>24;p[1]=v>>16;p[2]=v>>8;p[3]=v;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
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
    n->error=0;n->guard=GUARD;n->magic=MAGIC;
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
