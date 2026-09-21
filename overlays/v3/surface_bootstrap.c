/* Loaded with the existing equipment packet before the startup init chain. */
typedef unsigned int u32;
extern int af_surface_dma(void *,u32,u32);
extern u32 af_surface_crc(const void *,u32);
extern void af_surface_writeback(void *,u32),af_surface_invalidate(void *,u32);
extern int af_surface_prior_init(void);
#ifdef __mips__
#define memory ((u32 *)0x804BC000u)
#else
extern u32 af_test_surface_memory[1024];
#define memory af_test_surface_memory
#endif

int af_v3_surface_init(void) {
    if (af_surface_dma(memory,AF_SURFACE_ITEMS_VROM,4096u) ||
            af_surface_crc(memory,4096u)!=AF_SURFACE_ITEMS_CRC) return 0;
    af_surface_writeback(memory,4096u);
    af_surface_invalidate(memory,4096u);
    return af_surface_prior_init();
}
