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
#if defined(AF_V3_EDITABLE_CHECKSUMS) && defined(AF_FISH_WORLD_VROM)
const u32 af_v3_fish_world_crc_expected = AF_FISH_WORLD_CRC;
#define fish_world_crc (*(volatile const u32 *)&af_v3_fish_world_crc_expected)
#else
#define fish_world_crc AF_FISH_WORLD_CRC
#endif

static __attribute__((noinline)) int load_code(void *p,u32 vrom,u32 bytes,u32 crc) {
    if (af_surface_dma(p,vrom,bytes) || af_surface_crc(p,bytes)!=crc) return 0;
    af_surface_writeback(p,bytes);
    af_surface_invalidate(p,bytes);
    return 1;
}

int af_v3_surface_init(void) {
    if (!load_code(memory,AF_SURFACE_ITEMS_VROM,AF_SURFACE_ITEMS_BYTES,surface_crc)) return 0;
#ifdef AF_ROOM_GOODS_VROM
    /* Room-item hooks are resident before native actors can call them. This
       immutable packet is independent of the selected import profile. */
#ifdef __mips__
    void *goods=(void *)0x804D9000u;
#else
    extern unsigned char af_test_goods_code[AF_ROOM_GOODS_BYTES];
    void *goods=af_test_goods_code;
#endif
    if (!load_code(goods,AF_ROOM_GOODS_VROM,AF_ROOM_GOODS_BYTES,AF_ROOM_GOODS_CRC)) return 0;
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
    if (!load_code(carrying,AF_ROOM_CARRY_VROM,AF_ROOM_CARRY_BYTES,AF_ROOM_CARRY_CRC)) return 0;
#ifdef __mips__
    *(volatile u32 *)0x804DC400u=0;
#else
    extern u32 af_test_carry_magic;
    af_test_carry_magic=0;
#endif
#endif
#ifdef AF_PLAYER_EXERCISE_VROM
#ifdef __mips__
    void *exercise=(void *)0x804CE000u;
#else
    extern unsigned char af_test_exercise_code[AF_PLAYER_EXERCISE_BYTES];
    void *exercise=af_test_exercise_code;
#endif
    if (!load_code(exercise,AF_PLAYER_EXERCISE_VROM,AF_PLAYER_EXERCISE_BYTES,AF_PLAYER_EXERCISE_CRC)) return 0;
#endif
#ifdef AF_CONSOLE_STORAGE_VROM
#ifdef __mips__
    void *console=(void *)0x804DE200u;
#else
    extern unsigned char af_test_console_code[AF_CONSOLE_STORAGE_BYTES];
    void *console=af_test_console_code;
#endif
    if (!load_code(console,AF_CONSOLE_STORAGE_VROM,AF_CONSOLE_STORAGE_BYTES,AF_CONSOLE_STORAGE_CRC)) return 0;
#endif
#ifdef AF_CONSOLE_IMAGES_VROM
#ifdef __mips__
    void *images=(void *)0x804F9020u;
#else
    extern unsigned char af_test_console_images[AF_CONSOLE_IMAGES_BYTES];
    void *images=af_test_console_images;
#endif
    if (!load_code(images,AF_CONSOLE_IMAGES_VROM,AF_CONSOLE_IMAGES_BYTES,AF_CONSOLE_IMAGES_CRC)) return 0;
#endif
#ifdef AF_CONSOLE_DISK_VROM
#ifdef __mips__
    void *disk=(void *)0x80630000u;
#else
    extern unsigned char af_test_console_disk[AF_CONSOLE_DISK_BYTES];
    void *disk=af_test_console_disk;
#endif
    /* Complete code, both BIOS copies, boot data, zeroed transient buffers,
     * and guard load together. No hook can enter partially verified code. */
    if (!load_code(disk,AF_CONSOLE_DISK_VROM,AF_CONSOLE_DISK_BYTES,AF_CONSOLE_DISK_CRC)) return 0;
#endif
#ifdef AF_CREATURE_ITEMS_VROM
#ifdef __mips__
    void *creatures=(void *)0x804FF100u;
#else
    extern unsigned char af_test_creature_code[AF_CREATURE_ITEMS_BYTES];
    void *creatures=af_test_creature_code;
#endif
    if (!load_code(creatures,AF_CREATURE_ITEMS_VROM,AF_CREATURE_ITEMS_BYTES,AF_CREATURE_ITEMS_CRC)) return 0;
#endif
#ifdef AF_CREATURE_FIELD_VROM
#ifdef __mips__
    void *field=(void *)0x80647000u;
#else
    extern unsigned char af_test_creature_field[AF_CREATURE_FIELD_BYTES];
    void *field=af_test_creature_field;
#endif
    if (!load_code(field,AF_CREATURE_FIELD_VROM,AF_CREATURE_FIELD_BYTES,AF_CREATURE_FIELD_CRC)) return 0;
#endif
#ifdef AF_FISH_WORLD_VROM
#ifdef __mips__
    void *fish_world=(void *)0x8064A000u;
#else
    extern unsigned char af_test_fish_world[AF_FISH_WORLD_BYTES];
    void *fish_world=af_test_fish_world;
#endif
    if (!load_code(fish_world,AF_FISH_WORLD_VROM,AF_FISH_WORLD_BYTES,fish_world_crc)) return 0;
#endif
    return af_surface_prior_init();
}
