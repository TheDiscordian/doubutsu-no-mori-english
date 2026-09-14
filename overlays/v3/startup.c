/* V3 owns 0x6000..0x63FF of the existing resident reservation. */
typedef unsigned int u32;
extern u32 af_crc32(const void *, u32);
#ifdef __mips__
#define memory ((unsigned char *)0x80460000u)
#define config ((volatile const u32 *)0x8019ACC0u)
#define installed (*(volatile u32 *)0x8019ACD0u)
#define memsize (*(volatile const u32 *)0x80000318u)
#define previous ((int (*)(void))0x8009D6D0u)
#define dma ((int (*)(void *, u32, u32))0x80026B44u)
#define writeback ((void (*)(void *, u32))0x8002FE00u)
#define invalidate ((void (*)(void *, u32))0x80034CE0u)
#define execute() (((int (*)(void))0x80460100u)())
#else
extern unsigned char af_v3_memory[0x2000];
extern volatile u32 af_v3_config[4], af_v3_installed, af_v3_memsize;
extern int af_v3_previous(void), af_v3_dma(void *, u32, u32), af_v3_execute(void);
extern void af_v3_writeback(void *, u32), af_v3_invalidate(void *, u32);
#define memory af_v3_memory
#define config af_v3_config
#define installed af_v3_installed
#define memsize af_v3_memsize
#define previous af_v3_previous
#define dma af_v3_dma
#define writeback af_v3_writeback
#define invalidate af_v3_invalidate
#define execute af_v3_execute
#endif

int af_v3_startup(void) {
    const u32 *header = (const u32 *)memory;
    if (!previous()) return 0;
    /* Retain the low-memory English Expansion Pak warning path. */
    if (memsize != 0x800000u) return 1;
    if (installed) return header[0] == 0x41465633u && header[0x7FC] == 0xAF33C0DEu;
    if (config[0] != 0x03F00000u || config[1] != 0x2000u || config[3] != 1) return 0;
    if (dma(memory, config[0], config[1])) return 0;
    if (af_crc32(memory, config[1]) != config[2]) return 0;
    if (header[0] != 0x41465633u || header[1] != 1 || header[2] != 0x2000u
            || header[3] != 430 || header[4] != 410 || header[0x7FC] != 0xAF33C0DEu) return 0;
    writeback(memory, 0x2000u);
    invalidate(memory + 0x100, 0xF00u);
    if (execute() != 1) return 0;
    installed = 1;
    return 1;
}
