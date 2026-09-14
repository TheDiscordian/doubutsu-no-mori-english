/* Native house-gift selection, including enabled imported furniture. */
typedef unsigned char u8;
typedef unsigned int u32;
#ifdef __mips__
#define native_allowed ((int (*)(u32))0x800AB80Cu)
#define imported ((int (*)(u32))0x80465000u)
#define random_value ((float (*)(void))0x8002C9ACu)
#else
extern int af_v3_reward_native(u32), af_v3_reward_imported(u32);
extern float af_v3_reward_random(void);
#define native_allowed af_v3_reward_native
#define imported af_v3_reward_imported
#define random_value af_v3_reward_random
#endif

static u32 read16(const u8 *p) { return ((u32)p[0] << 8) | p[1]; }

static int allowed(u32 item) {
    if ((item >> 12) == 1) return native_allowed(item) == 1;
    return (item >> 12) == 3 && imported(1024u+((item & 4095u) >> 2));
}

u32 af_v3_house_reward(const u8 *const *data, const u8 *npc, int base) {
    const u8 *items;
    int index, row, column, count = 0, ordinal;
    float draw;
    if (!data || !npc || base < 0) return 0;
    index = (int)read16(npc+0x30)-base;
    if (index < 0) index = 0;
    if (index >= 498 || !data[index]) return 0;
    items = data[index]+2;
    /* Retain the original 10x10 room scan inside its 16-cell row stride. */
    for (row = 0; row < 10; ++row)
        for (column = 0; column < 10; ++column)
            if (allowed(read16(items+(row*16+column)*2))) ++count;
    if (!count) return 0;
    draw = random_value();
    if (!(draw >= 0.0f && draw < 1.0f)) return 0;
    ordinal = (int)(draw*(float)count);
    for (row = 0; row < 10; ++row)
        for (column = 0; column < 10; ++column) {
            u32 item = read16(items+(row*16+column)*2);
            if (allowed(item) && ordinal-- == 0) return item;
        }
    return 0;
}
