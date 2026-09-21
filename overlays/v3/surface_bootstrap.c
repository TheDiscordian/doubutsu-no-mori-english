/* Loaded with the existing equipment packet before the startup init chain. */
typedef unsigned int u32;
#ifndef AF_SURFACE_ITEMS_BYTES
#define AF_SURFACE_ITEMS_BYTES 4096u
#endif
extern int af_surface_dma(void *,u32,u32);
extern u32 af_surface_crc(const void *,u32);
extern void af_surface_writeback(void *,u32),af_surface_invalidate(void *,u32);
extern int af_surface_prior_init(void);
#ifdef __mips__
#define memory ((u32 *)0x804BC000u)
#else
extern u32 af_test_surface_memory[AF_SURFACE_ITEMS_BYTES/4];
#define memory af_test_surface_memory
#endif
#ifdef AF_V3_EDITABLE_CHECKSUMS
const u32 af_v3_surface_crc_expected = AF_SURFACE_ITEMS_CRC;
#define surface_crc (*(volatile const u32 *)&af_v3_surface_crc_expected)
#else
#define surface_crc AF_SURFACE_ITEMS_CRC
#endif

int af_v3_surface_init(void) {
    if (af_surface_dma(memory,AF_SURFACE_ITEMS_VROM,AF_SURFACE_ITEMS_BYTES) ||
            af_surface_crc(memory,AF_SURFACE_ITEMS_BYTES)!=surface_crc) return 0;
    af_surface_writeback(memory,AF_SURFACE_ITEMS_BYTES);
    af_surface_invalidate(memory,AF_SURFACE_ITEMS_BYTES);
    return af_surface_prior_init();
}
