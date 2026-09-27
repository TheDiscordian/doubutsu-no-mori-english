#ifndef AF_V3_CONSOLE_DISK_H
#define AF_V3_CONSOLE_DISK_H

/* GAFE01 QD disk services. CPU instruction dispatch, CHR buffer binding, BIOS
 * mapping, and expansion sound remain responsibilities of the native adapter.
 * All buffers must outlive the context. Boot/save preserve complete disk sides.
 * No resident memory, FlashRAM writes, or game enablement is implied here. */
enum {
    AF_QD_SIDE=65536, AF_QD_WORK=2048, AF_QD_PROGRAM=32768,
    AF_QD_CHARACTER=8192, AF_QD_BIOS=8192, AF_QD_BOOT_STATE=260,
    AF_QD_BAD_STATE=-1, AF_QD_BAD_DATA=-2,
    AF_QD_SOUND_SYNC=1, AF_QD_MIRROR=2, AF_QD_AUDIO_WRITE=4,
    AF_QD_IRQ=8
};
typedef struct {
    unsigned int magic;
    unsigned char *disk,*work,*program,*characters,*bios;
    const unsigned char *boot_state;
    unsigned int disk_bytes;
    const unsigned char *cpu[8];
    unsigned int cpu_bytes[8];
    unsigned int frame_flags,head,latch;
    short target;
    unsigned char control,timer_control,timer_lo,timer_hi,master;
    unsigned char drive[4],disk_status,ready,motor,changed,fast_locked,irq_enable;
    unsigned char mirror,chr_dirty;
} AFQDisk;
/* Interpreter values at WDM dispatch, after fetching its two bytes. zero is
 * the interpreter's result value (zero means Z set), not a boolean flag.
 * Other CPU registers/flags are untouched by these source BIOS services. */
typedef struct {
    unsigned short pc;
    unsigned char a,stack;
    unsigned int zero,cycles;
} AFQCpu;

int af_v3_qd_validate(const unsigned char *disk,unsigned int bytes);
int af_v3_qd_bind(AFQDisk *q,unsigned char *disk,unsigned int disk_bytes,
    unsigned char *work,unsigned char *program,unsigned char *characters,
    unsigned char *private_bios,const unsigned char *boot_state);
void af_v3_qd_reset(AFQDisk *q);
int af_v3_qd_boot(AFQDisk *q);
/* 27-byte request is the donor BIOS's complete fast-save descriptor. The
 * context's CPU-bank views supply bounded, mirrored memory, not I/O callbacks.
 * Invalid input rejects before output/context changes. */
int af_v3_qd_save(AFQDisk *q,const unsigned char request[27]);
/* Execute the five donor WDM BIOS services. Source BIOS error results are
 * reflected in CPU registers; negative API returns mean unsafe input. The
 * caller still owns native instruction dispatch and CHR conversion. */
int af_v3_qd_wdm(AFQDisk *q,AFQCpu *cpu,unsigned int buttons);
/* Convert all raw CHR into the native interpreter/RSP's tiled, paired-plane
 * layout. The caller binds the actual native working buffer and handles its
 * cache/RSP lifetime. No native state or graphics pointer is inferred here. */
int af_v3_qd_native_characters(AFQDisk *q,unsigned char *patterns,unsigned int bytes);
int af_v3_qd_read(AFQDisk *q,unsigned int address,unsigned int pc);
/* Positive return bits request work by the native CPU/PPU/audio adapter. */
int af_v3_qd_write(AFQDisk *q,unsigned int address,unsigned int value,int scanline);
int af_v3_qd_irq(AFQDisk *q,int scanline);
void af_v3_qd_frame(AFQDisk *q,unsigned int buttons);

#endif
