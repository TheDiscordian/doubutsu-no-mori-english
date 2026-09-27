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
#ifdef AF_ROOM_GOODS_VROM
    /* Room-item hooks are resident before native actors can call them. This
       immutable packet is independent of the selected import profile. */
#ifdef __mips__
    void *goods=(void *)0x804D9000u;
#else
    extern unsigned char af_test_goods_code[AF_ROOM_GOODS_BYTES];
    void *goods=af_test_goods_code;
#endif
    if (af_surface_dma(goods,AF_ROOM_GOODS_VROM,AF_ROOM_GOODS_BYTES) ||
            af_surface_crc(goods,AF_ROOM_GOODS_BYTES)!=AF_ROOM_GOODS_CRC) return 0;
    af_surface_writeback(goods,AF_ROOM_GOODS_BYTES);
    af_surface_invalidate(goods,AF_ROOM_GOODS_BYTES);
#ifdef __mips__
    *(volatile u32 *)0x804DC000u=0;
#else
    extern u32 af_test_goods_magic;
    af_test_goods_magic=0;
#endif
#endif
#ifdef AF_ROOM_CARRY_VROM
#ifdef __mips__
    void *carrying=(void *)0x804DA000u;
#else
    extern unsigned char af_test_carry_code[AF_ROOM_CARRY_BYTES];
    void *carrying=af_test_carry_code;
#endif
    if (af_surface_dma(carrying,AF_ROOM_CARRY_VROM,AF_ROOM_CARRY_BYTES) ||
            af_surface_crc(carrying,AF_ROOM_CARRY_BYTES)!=AF_ROOM_CARRY_CRC) return 0;
    af_surface_writeback(carrying,AF_ROOM_CARRY_BYTES);
    af_surface_invalidate(carrying,AF_ROOM_CARRY_BYTES);
#ifdef __mips__
    *(volatile u32 *)0x804DC400u=0;
#else
    extern u32 af_test_carry_magic;
    af_test_carry_magic=0;
#endif
#endif
    return af_surface_prior_init();
}
