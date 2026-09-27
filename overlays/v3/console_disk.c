/* Source behaviour: checked GAFE01 QD boot/save, disk I/O, IRQ, and frame code.
 * Malformed ranges reject before mutation instead of reproducing overreads. */
#include "console_disk.h"
typedef unsigned char u8;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ addr;
#define MAGIC 0x41465144u
static u32 le16(const u8 *p) {return p[0]|(u32)p[1]<<8;}
static int same(const u8 *a,const u8 *b,u32 n) {while(n--)if(*a++!=*b++)return 0;return 1;}
static void copy(u8 *d,const u8 *s,u32 n) {while(n--)*d++=*s++;}
static void zero(void *p,u32 n) {u8 *b=p;while(n--)*b++=0;}
static int separate(const void *a,u32 an,const void *b,u32 bn) {
    addr x=(addr)a,y=(addr)b;
    if(!a || !b || an>(addr)-1-x || bn>(addr)-1-y)return 0;
    return x<=y?y-x>=an:x-y>=bn;
}
static int valid(const AFQDisk *q) {
    return q && q->magic==MAGIC && q->disk && q->work && q->program && q->characters &&
        q->bios && q->boot_state &&
        q->disk_bytes && q->disk_bytes<=4*AF_QD_SIDE && !(q->disk_bytes&(AF_QD_SIDE-1));
}
static int block(const u8 *disk,u32 at) {
    if(at>AF_QD_SIDE-21 || disk[at]!=3 || disk[at+18]!=4 || disk[at+15]>2)return -1;
    u32 n=le16(disk+at+13);
    return n<=AF_QD_SIDE-at-21?(int)(at+21+n):-1;
}

int af_v3_qd_validate(const u8 *disk,u32 bytes) {
    static const u8 signature[15]={1,'*','N','I','N','T','E','N','D','O','-','H','V','C','*'};
    if(!disk || !bytes || bytes>4*AF_QD_SIDE || (bytes&(AF_QD_SIDE-1)))return AF_QD_BAD_DATA;
    for(u32 side=0;side<bytes;side+=AF_QD_SIDE) {
        const u8 *p=disk+side;int at=0x3E;
        if(!same(p,signature,15) || p[0x3A]!=2)return AF_QD_BAD_DATA;
        for(u32 i=0;i<p[0x3B];i++) {at=block(p,(u32)at);if(at<0)return AF_QD_BAD_DATA;}
    }
    return 0;
}

void af_v3_qd_reset(AFQDisk *q) {
    if(!valid(q))return;
    q->timer_lo=q->timer_hi=q->timer_control=q->irq_enable=0;
    q->head=0;q->control=0x27;q->motor=0;q->ready=120;q->target=0x7FFF;
    q->drive[2]=q->disk_status=0x47;q->drive[3]=0x80;
    q->bios[0xEBD]=0x42;
    q->bios[0x1A0]=same(q->disk+16,(const u8 *)"koro",4)?0xFF:0x7F;
}
int af_v3_qd_bind(AFQDisk *q,u8 *disk,u32 bytes,u8 *work,u8 *program,u8 *characters,
    u8 *bios,const u8 *boot_state) {
    const void *buffers[]={q,disk,work,program,characters,bios,boot_state};
    const u32 sizes[]={sizeof(*q),bytes,AF_QD_WORK,AF_QD_PROGRAM,AF_QD_CHARACTER,AF_QD_BIOS,AF_QD_BOOT_STATE};
    for(u32 i=0;i<7;i++)for(u32 j=i+1;j<7;j++)
        if(!separate(buffers[i],sizes[i],buffers[j],sizes[j]))return AF_QD_BAD_STATE;
    if(af_v3_qd_validate(disk,bytes))return AF_QD_BAD_DATA;
    zero(q,sizeof(*q));q->magic=MAGIC;q->disk=disk;q->disk_bytes=bytes;
    q->work=work;q->program=program;q->characters=characters;
    q->bios=bios;q->boot_state=boot_state;
    for(u32 i=0;i<8;i++) {
        q->cpu[i]=i<3?work:i==7?bios:program+(i-3)*8192;
        q->cpu_bytes[i]=i<3?AF_QD_WORK:8192;
    }
    af_v3_qd_reset(q);return 0;
}

static int boot_target(const u8 *p) {
    u32 n=le16(p+13),at=le16(p+11);
    if(p[15]) {
        if(at>=AF_QD_CHARACTER || n>AF_QD_CHARACTER)return 0;
        return n<=AF_QD_CHARACTER-at?3:AF_QD_BAD_DATA;
    }
    /* Retain the donor's skip rules for unmapped files. Reject its unsafe
     * cross-window case instead of writing beyond work/program memory. */
    if(!n || n>AF_QD_PROGRAM || at>=0xE000 || at+n>0xE000 ||
       !(at<AF_QD_WORK || at>=0x6000) || !(at+n<=AF_QD_WORK || at+n>0x6000))return 0;
    if(at<AF_QD_WORK)return n<=AF_QD_WORK-at?1:AF_QD_BAD_DATA;
    return 2;
}
int af_v3_qd_boot(AFQDisk *q) {
    if(!valid(q) || (q->frame_flags&0x400))return AF_QD_BAD_STATE;
    if(q->disk[21])return 0x45C;
    if(af_v3_qd_validate(q->disk,q->disk_bytes))return AF_QD_BAD_DATA;
    u32 at=0x3E;
    for(u32 i=0;i<q->disk[0x3B];i++) {
        const u8 *p=q->disk+at;
        if(p[2]<=q->disk[25] && boot_target(p)<0)return AF_QD_BAD_DATA;
        at+=21+le16(p+13);
    }
    zero(q->work+0x200,0x600);at=0x3E;
    for(u32 i=0;i<q->disk[0x3B];i++) {
        const u8 *p=q->disk+at;u32 n=le16(p+13),target=le16(p+11);
        if(p[2]<=q->disk[25]) {
            int kind=boot_target(p);
            if(kind==1)copy(q->work+target,p+19,n);
            if(kind==2)copy(q->program+target-0x6000,p+19,n);
            if(kind==3)copy(q->characters+target,p+19,n);
        }
        at+=21+n;
    }
    q->chr_dirty=1;return 0;
}

int af_v3_qd_save(AFQDisk *q,const u8 request[27]) {
    if(!valid(q) || !request || (q->frame_flags&0x400) || q->fast_locked)return AF_QD_BAD_STATE;
    if(!separate(request,27,q->disk,q->disk_bytes) || af_v3_qd_validate(q->disk,q->disk_bytes))return AF_QD_BAD_DATA;
    u8 *disk=0;
    for(u32 side=0;side<q->disk_bytes;side+=AF_QD_SIDE)
        if(same(q->disk+side+15,request,10)) {disk=q->disk+side;break;}
    if(!disk)return AF_QD_BAD_STATE;
    u32 slot=q->work[14],at=0x3E,n=le16(request+21),source=le16(request+24);
    if(slot>disk[0x3B] || slot==255 || request[23]>2)return AF_QD_BAD_DATA;
    for(u32 i=0;i<slot;i++)at=(u32)block(disk,at);
    if(n+21>=AF_QD_SIDE-at || n>65536-source)return AF_QD_BAD_DATA;
    if(n)for(u32 bank=source>>13;bank<=(source+n-1)>>13;bank++) {
        u32 length=q->cpu_bytes[bank];
        if(!length || length>8192 || (length&(length-1)) ||
           !separate(q->cpu[bank],length,q->disk,q->disk_bytes))return AF_QD_BAD_DATA;
    }
    disk[at]=3;disk[at+1]=(u8)slot;copy(disk+at+2,request+10,14);disk[at+18]=4;
    for(u32 i=0;i<n;i++) {
        u32 address=source+i,bank=address>>13;
        disk[at+19+i]=q->cpu[bank][address&(q->cpu_bytes[bank]-1)];
    }
    disk[0x3B]=(u8)(slot+1);q->changed=1;return 0;
}

static int cpu_copy(const AFQDisk *q,u32 address,u8 *out,u32 bytes) {
    if(address>65535 || bytes>65536-address)return AF_QD_BAD_DATA;
    for(u32 i=0;i<bytes;i++) {
        u32 at=address+i,bank=at>>13,n=q->cpu_bytes[bank];
        if(!n || n>8192 || (n&(n-1)) ||
           !separate(q->cpu[bank],n,q->disk,q->disk_bytes))return AF_QD_BAD_DATA;
        out[i]=q->cpu[bank][at&(n-1)];
    }
    return 0;
}
int af_v3_qd_wdm(AFQDisk *q,AFQCpu *cpu,u32 buttons) {
    if(!valid(q))return AF_QD_BAD_STATE;
    const void *buffers[]={q,q->disk,q->work,q->program,q->characters,q->bios,q->boot_state};
    const u32 sizes[]={sizeof(*q),q->disk_bytes,AF_QD_WORK,AF_QD_PROGRAM,AF_QD_CHARACTER,AF_QD_BIOS,AF_QD_BOOT_STATE};
    for(u32 i=0;i<7;i++)if(!separate(cpu,sizeof(*cpu),buffers[i],sizes[i]))return AF_QD_BAD_STATE;
    switch(cpu->pc) {
    case 0xE7A6:
        cpu->cycles&=7;cpu->pc-=2;break;
    case 0xE408: {
        u8 id[8],old=q->work[1];u32 at=((u32)cpu->a<<8)|q->work[0];
        q->work[1]=cpu->a;
        if(cpu_copy(q,at+1,id,8)) {q->work[1]=old;return AF_QD_BAD_DATA;}
        if(id[0]==255 && id[1]==255 && id[2]==255 && id[3]==255)break;
        for(u32 side=0;side<q->disk_bytes;side+=AF_QD_SIDE)
            if(same(id,q->disk+side+16,8)) {q->head=side;break;}
        break;
    }
    case 0xEEBF: {
        if((cpu->a&0xF0)==0x60)break;
        int result=af_v3_qd_boot(q);
        if(result==AF_QD_BAD_DATA)return result;
        q->bios[0xEBD]=0xA9;cpu->zero=(u8)result;
        if(!result) {
            q->drive[2]=q->disk_status=0x46;
            zero(q->work,0xFA);
            /* Actual donor instructions read table+1 for 0x104 bytes, not
             * just the declared 11-byte symbol. Preserve the checked span. */
            copy(q->work+0xFA,q->boot_state,AF_QD_BOOT_STATE);
            cpu->pc-=0x24;
        }
        break;
    }
    case 0xEEF6:
        if((buttons>>28)!=6)q->disk_status=0x46;
        cpu->a=q->work[0x90];break;
    case 0xE23B: {
        u8 old=q->work[14],pointers[4],request[27];
        q->work[14]=cpu->a;
        if(cpu->a==255)break;
        /* Source stack fetches are linear within work RAM; the final RTS
         * wraps S to eight bits and replaces PC with the saved return+5. */
        u32 ret=le16(q->work+0x101+cpu->stack);
        if(cpu_copy(q,ret+1,pointers,4) ||
           cpu_copy(q,le16(pointers),request,10) ||
           cpu_copy(q,le16(pointers+2),request+10,17)) {
            q->work[14]=old;return AF_QD_BAD_DATA;
        }
        int result=af_v3_qd_save(q,request);
        if(result==AF_QD_BAD_DATA) {q->work[14]=old;return result;}
        cpu->zero=cpu->a=(u8)result;
        if(!result) {cpu->stack+=2;cpu->pc=(unsigned short)(ret+5);}
        break;
    }
    }
    return 0;
}

int af_v3_qd_read(AFQDisk *q,u32 address,u32 pc) {
    if(!valid(q) || address<0x4030 || address>0x4033 || pc>65535)return AF_QD_BAD_STATE;
    int value=q->drive[address-0x4030];
    if(address==0x4030)q->drive[0]=0;
    if(address==0x4031)q->head=(q->head&0xFFFF0000u)|((q->head+1)&65535);
    if(address==0x4032) {
        value&=q->disk_status;
        if(pc>=0xE000) {if(pc!=0xEEE2 && pc!=0xEF36)value=0x40;}
        else {value|=0x47;if(q->ready<195)value=(value&0xFD)|(q->control&2);}
    }
    return value;
}
static short next_line(int scanline) {return (short)(scanline+1>238?-20:scanline+1);}
int af_v3_qd_write(AFQDisk *q,u32 address,u32 value,int scanline) {
    if(!valid(q) || address<0x4020 || address>0x4026 || value>255 ||
       scanline<-32768 || scanline>32767)return AF_QD_BAD_STATE;
    switch(address) {
    case 0x4020:q->timer_lo=(u8)value;break;
    case 0x4021:q->timer_hi=(u8)value;break;
    case 0x4022:
        q->timer_control=(u8)value;q->irq_enable=(u8)(value&2);
        q->latch=((u32)q->timer_hi*256+q->timer_lo)/114;
        q->target=(short)(scanline+(int)q->latch);break;
    case 0x4023:q->master=(u8)value;return AF_QD_AUDIO_WRITE;
    case 0x4024:
        if((q->control&0x87)==0x81) {
            if(q->head<2 || q->head>q->disk_bytes+1)return AF_QD_BAD_DATA;
            q->disk[q->head-2]=(u8)value;q->changed=1;
        }
        break;
    case 0x4025: {
        int result=AF_QD_MIRROR|(((q->control^value)&2)?AF_QD_SOUND_SYNC:0);
        q->control=(u8)value;
        if(value&0x80) {q->irq_enable=0x80;q->target=next_line(scanline);}
        else {q->irq_enable=q->timer_control&2;if(!q->irq_enable)q->target=0x7FFF;}
        if((value&3)==2) {q->drive[2]&=0xFD;q->head&=0xFFFF0000u;}
        q->mirror=(u8)(value&8);return result;
    }
    case 0x4026:q->drive[3]=(u8)value;break;
    }
    return 0;
}
int af_v3_qd_irq(AFQDisk *q,int scanline) {
    if(!valid(q) || scanline<-32768 || scanline>32767)return AF_QD_BAD_STATE;
    if(q->control&0x80) {
        if((q->control&0xE3)!=0xE1)return 0;
        if((q->control&4) && q->head>=q->disk_bytes)return AF_QD_BAD_DATA;
        q->target=next_line(scanline);
        if(q->control&4)q->drive[1]=q->disk[q->head];
        return AF_QD_IRQ;
    }
    int result=q->irq_enable?AF_QD_IRQ:0;
    u8 control=q->timer_control&0xFD;
    q->target=0x7FFF;
    if(q->timer_control&1) {control=q->timer_control&1;q->target=(short)(scanline+(int)q->latch);}
    q->timer_control=control;q->irq_enable=control&2;q->drive[0]=1;
    return result;
}
void af_v3_qd_frame(AFQDisk *q,u32 buttons) {
    if(!valid(q))return;
    if(q->ready<120 || q->ready>195)q->ready++;
    else if(buttons&0x80000000u)q->ready=196;
    if(!(q->control&2))q->motor=90;
    if(q->motor)q->motor--;
}
