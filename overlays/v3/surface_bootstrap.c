/* Load every complete packet before entering the shared initialization chain. */
typedef unsigned int u32;
#ifndef AF_SURFACE_ITEMS_BYTES
#define AF_SURFACE_ITEMS_BYTES 4096u
#endif
extern int af_surface_dma(void *,u32,u32);
extern u32 af_surface_crc(const void *,u32);
extern void af_surface_writeback(void *,u32),af_surface_invalidate(void *,u32);
extern int af_surface_prior_init(void);
#ifdef AF_INSECT_PHYSICAL
extern int af_surface_pi(u32,void *,u32);
#endif

/* Named words remain editable by the offline and browser profile composers.
 * A single descriptor loop avoids duplicating the checked transfer sequence. */
const u32 af_v3_surface_crc_expected=AF_SURFACE_ITEMS_CRC;
#ifdef AF_ROOM_GOODS_VROM
static const u32 goods_crc=AF_ROOM_GOODS_CRC;
#endif
#ifdef AF_ROOM_CARRY_VROM
static const u32 carry_crc=AF_ROOM_CARRY_CRC;
#endif
#ifdef AF_PLAYER_EXERCISE_VROM
static const u32 exercise_crc=AF_PLAYER_EXERCISE_CRC;
#endif
#ifdef AF_CONSOLE_STORAGE_VROM
static const u32 storage_crc=AF_CONSOLE_STORAGE_CRC;
#endif
#ifdef AF_CONSOLE_IMAGES_VROM
static const u32 images_crc=AF_CONSOLE_IMAGES_CRC;
#endif
#ifdef AF_CONSOLE_DISK_VROM
static const u32 disk_crc=AF_CONSOLE_DISK_CRC;
#endif
#ifdef AF_CREATURE_ITEMS_VROM
const u32 af_v3_creature_items_crc_expected=AF_CREATURE_ITEMS_CRC;
#endif
#ifdef AF_CREATURE_FIELD_VROM
static const u32 field_crc=AF_CREATURE_FIELD_CRC;
#endif
#ifdef AF_FISH_WORLD_VROM
const u32 af_v3_fish_world_crc_expected=AF_FISH_WORLD_CRC;
#endif
#ifdef AF_INSECT_PHYSICAL
const u32 af_v3_insect_crc_expected=AF_INSECT_CRC;
#endif
#ifdef AF_CLOTHING_VROM
const u32 af_v3_clothing_crc_expected=AF_CLOTHING_CRC;
#endif

#ifdef __mips__
#define DEST(name,address) ((void *)(address))
#define CLEAR(name,address) ((volatile u32 *)(address))
#else
extern u32 af_test_surface_memory[AF_SURFACE_ITEMS_BYTES/4];
extern u32 af_test_goods_magic,af_test_carry_magic;
extern unsigned char af_test_goods_code[],af_test_carry_code[],af_test_exercise_code[];
extern unsigned char af_test_console_code[],af_test_console_images[],af_test_console_disk[];
extern unsigned char af_test_creature_code[],af_test_creature_field[],af_test_fish_world[];
extern unsigned char af_test_insect_code[],af_test_clothing_code[];
#define DEST(name,address) (af_test_##name)
#define CLEAR(name,address) (&af_test_##name)
#endif

struct StartupPacket {
    void *destination;
    u32 source,bytes;
    const u32 *crc;
    volatile u32 *clear;
};
static const struct StartupPacket packets[]={
    {DEST(surface_memory,0x804BC000u),AF_SURFACE_ITEMS_VROM,AF_SURFACE_ITEMS_BYTES,&af_v3_surface_crc_expected,0},
#ifdef AF_ROOM_GOODS_VROM
    {DEST(goods_code,0x804D9000u),AF_ROOM_GOODS_VROM,AF_ROOM_GOODS_BYTES,&goods_crc,CLEAR(goods_magic,0x804DC000u)},
#endif
#ifdef AF_ROOM_CARRY_VROM
    {DEST(carry_code,0x804DA000u),AF_ROOM_CARRY_VROM,AF_ROOM_CARRY_BYTES,&carry_crc,CLEAR(carry_magic,0x804DC400u)},
#endif
#ifdef AF_PLAYER_EXERCISE_VROM
    {DEST(exercise_code,0x804CE000u),AF_PLAYER_EXERCISE_VROM,AF_PLAYER_EXERCISE_BYTES,&exercise_crc,0},
#endif
#ifdef AF_CONSOLE_STORAGE_VROM
    {DEST(console_code,0x804DE200u),AF_CONSOLE_STORAGE_VROM,AF_CONSOLE_STORAGE_BYTES,&storage_crc,0},
#endif
#ifdef AF_CONSOLE_IMAGES_VROM
    {DEST(console_images,0x804F9020u),AF_CONSOLE_IMAGES_VROM,AF_CONSOLE_IMAGES_BYTES,&images_crc,0},
#endif
#ifdef AF_CONSOLE_DISK_VROM
    {DEST(console_disk,0x80630000u),AF_CONSOLE_DISK_VROM,AF_CONSOLE_DISK_BYTES,&disk_crc,0},
#endif
#ifdef AF_CREATURE_ITEMS_VROM
    {DEST(creature_code,0x804FF100u),AF_CREATURE_ITEMS_VROM,AF_CREATURE_ITEMS_BYTES,&af_v3_creature_items_crc_expected,0},
#endif
#ifdef AF_CREATURE_FIELD_VROM
    {DEST(creature_field,0x80647000u),AF_CREATURE_FIELD_VROM,AF_CREATURE_FIELD_BYTES,&field_crc,0},
#endif
#ifdef AF_FISH_WORLD_VROM
    {DEST(fish_world,0x8064A000u),AF_FISH_WORLD_VROM,AF_FISH_WORLD_BYTES,&af_v3_fish_world_crc_expected,0},
#endif
#ifdef AF_INSECT_PHYSICAL
    {DEST(insect_code,AF_INSECT_RAM),AF_INSECT_PHYSICAL|0x80000000u,AF_INSECT_BYTES,&af_v3_insect_crc_expected,0},
#endif
#ifdef AF_CLOTHING_VROM
    {DEST(clothing_code,AF_CLOTHING_RAM),AF_CLOTHING_VROM,AF_CLOTHING_BYTES,&af_v3_clothing_crc_expected,0},
#endif
};

int af_v3_surface_init(void) {
    for (u32 i=0;i<sizeof(packets)/sizeof(*packets);i++) {
        const struct StartupPacket *p=packets+i;
#ifdef AF_INSECT_PHYSICAL
        int status=(p->source&0x80000000u)?
            af_surface_pi(p->source&0x7FFFFFFFu,p->destination,p->bytes):
            af_surface_dma(p->destination,p->source,p->bytes);
#else
        int status=af_surface_dma(p->destination,p->source,p->bytes);
#endif
        if (status || af_surface_crc(p->destination,p->bytes)!=*(volatile const u32 *)p->crc) return 0;
        af_surface_writeback(p->destination,p->bytes);
        af_surface_invalidate(p->destination,p->bytes);
        if (p->clear) *p->clear=0;
    }
    return af_surface_prior_init();
}
