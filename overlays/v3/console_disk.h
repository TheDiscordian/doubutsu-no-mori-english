#ifndef AF_V3_CONSOLE_DISK_H
#define AF_V3_CONSOLE_DISK_H

/* GAFE01 QD disk services. CPU instruction dispatch, CHR conversion, BIOS
 * mapping, and expansion sound remain responsibilities of the native adapter.
 * All buffers must outlive the context. Boot/save preserve complete disk sides.
 * No resident memory, FlashRAM writes, or game enablement is implied here. */
enum {
    AF_QD_SIDE=65536, AF_QD_WORK=2048, AF_QD_PROGRAM=32768,
    AF_QD_CHARACTER=8192, AF_QD_BIOS=8192,
    AF_QD_BAD_STATE=-1, AF_QD_BAD_DATA=-2,
    AF_QD_SOUND_SYNC=1, AF_QD_MIRROR=2, AF_QD_AUDIO_WRITE=4,
    AF_QD_IRQ=8
};
typedef struct {
    unsigned int magic;
    unsigned char *disk,*work,*program,*characters;
    unsigned int disk_bytes;
    const unsigned char *cpu[8];
    unsigned int cpu_bytes[8];
    unsigned int frame_flags,head,latch;
    short target;
    unsigned char control,timer_control,timer_lo,timer_hi,master;
    unsigned char drive[4],disk_status,ready,motor,changed,fast_locked,irq_enable;
    unsigned char mirror,chr_dirty;
} AFQDisk;

int af_v3_qd_validate(const unsigned char *disk,unsigned int bytes);
int af_v3_qd_bind(AFQDisk *q,unsigned char *disk,unsigned int disk_bytes,
    unsigned char *work,unsigned char *program,unsigned char *characters,
    const unsigned char *bios);
void af_v3_qd_reset(AFQDisk *q);
int af_v3_qd_boot(AFQDisk *q);
/* 27-byte request is the donor BIOS's complete fast-save descriptor. The
 * context's CPU-bank views supply bounded, mirrored memory, not I/O callbacks.
 * Invalid input rejects before output/context changes. */
int af_v3_qd_save(AFQDisk *q,const unsigned char request[27]);
int af_v3_qd_read(AFQDisk *q,unsigned int address,unsigned int pc);
/* Positive return bits request work by the native CPU/PPU/audio adapter. */
int af_v3_qd_write(AFQDisk *q,unsigned int address,unsigned int value,int scanline);
int af_v3_qd_irq(AFQDisk *q,int scanline);
void af_v3_qd_frame(AFQDisk *q,unsigned int buttons);

#endif
