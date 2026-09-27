#ifndef AF_V3_CONSOLE_DISK_NATIVE_H
#define AF_V3_CONSOLE_DISK_NATIVE_H
#include "console_disk.h"

enum { AF_QDN_STATE_BYTES=0x16F90, AF_QDN_GRAPHICS_BYTES=0x6008 };
typedef struct {
    unsigned char *state,*graphics,*disk,*program,*characters,*bios;
    const unsigned char *boot_state;
    unsigned int state_bytes,graphics_bytes,disk_bytes,base;
} AFQNativeBuffers;
typedef struct {
    AFQDisk disk;
    unsigned char *state,*graphics;
    unsigned int magic,base,error,guard,initialized;
} AFQNative;
/* Full-width integer register frame shared with console_disk_bridge.S.
 * C o32 callees do not preserve the upper halves of saved registers. */
typedef struct {
    unsigned long long r[32],hi,lo;
} AFQNativeRegisters;

/* Bind only an allocated disk instance, never an iNES instance. Does not run
 * the unsafe native iNES initializer or install ROM/startup hooks. The caller
 * owns complete buffers and stops the renderer before resetting/binding. */
int af_v3_qd_native_bind(AFQNative *,const AFQNativeBuffers *);
/* Bind CPU banks, CHR, WDM, disk I/O, and scanline IRQs to one native state.
 * Common initialization, audio startup, and lifecycle are separate operations;
 * this function alone is not a replacement full emulator initializer. */
int af_v3_qd_native_map(AFQNative *);
int af_v3_qd_native_graphics(AFQNative *);
/* Cold initialization consumes the actual relocated native instruction/I/O
 * tables, with no fake cartridge header. Reset-button semantics preserve RAM,
 * disk edits, PPU state, and the BIOS fast-boot patch, as the donor does.
 * Audio initialization and session hooks still require installation. */
int af_v3_qd_native_initialize(AFQNative *);
int af_v3_qd_native_reset_button(AFQNative *);
void af_v3_qd_native_wdm_dispatch(unsigned char *,AFQNativeRegisters *);
void af_v3_qd_native_ram_dispatch(unsigned char *,AFQNativeRegisters *);
void af_v3_qd_native_read_dispatch(unsigned char *,AFQNativeRegisters *);
void af_v3_qd_native_write_dispatch(unsigned char *,AFQNativeRegisters *);
void af_v3_qd_native_irq_dispatch(unsigned char *,AFQNativeRegisters *);
void af_v3_qd_wdm_bridge(void);
void af_v3_qd_ram_bridge(void);
void af_v3_qd_read_bridge(void);
void af_v3_qd_write_bridge(void);
void af_v3_qd_irq_bridge(void);
#endif
