/* Additive clothing resource lookup. Item/gameplay consumers remain separate. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct Clothing {
    u16 item, index;
    u32 vrom;
    u16 price;
    u8 enabled, reserved;
    u8 name[16];
    u32 padding;
};
_Static_assert(sizeof(struct Clothing) == 32, "Clothing metadata layout");
#ifdef __mips__
#define clothing ((const struct Clothing *)0x80462820u)
#define dma ((int (*)(void *, u32, u32))0x80026B44u)
#else
extern struct Clothing af_v3_clothing;
extern int af_v3_clothing_dma(void *, u32, u32);
#define clothing (&af_v3_clothing)
#define dma af_v3_clothing_dma
#endif

u32 af_v3_clothing_source(int index, u32 palette) {
    if (palette > 1) return 0;
    if (index >= 0 && index < 256)
        return palette ? 0x00B88000u + (u32)index * 32u : 0x00B68000u + (u32)index * 512u;
    if (index != 0x10BF || clothing->enabled != 1 || clothing->item != 0x34BF
            || clothing->index != (u32)index || clothing->vrom != 0x03F0F000u
            || clothing->reserved || clothing->padding) return 0;
    return clothing->vrom + (palette ? 512u : 0u);
}

void af_v3_load_clothing(void *texture, void *palette, int index) {
    u32 tex = af_v3_clothing_source(index, 0), pal = af_v3_clothing_source(index, 1);
    if (!texture || !palette || !tex || !pal) return;
    if (dma(texture, tex, 512)) return;
    dma(palette, pal, 32);
}
