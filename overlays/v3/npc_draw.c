/* Registry 1: native/test rows stay in place; imported rows are independent. */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
struct ImportDraw { u16 actor, voice; u8 draw[100]; };
_Static_assert(sizeof(struct ImportDraw) == 104, "V3 draw record layout");
#ifdef __mips__
#define imports ((const struct ImportDraw *)0x80462000u)
#define event ((const u16 *(*)(u32))0x800AA14Cu)
#define draw_dma ((int (*)(void *, u32, u32))0x80026B44u)
#else
extern struct ImportDraw af_v3_draws[20];
extern const u16 *af_v3_event(u32);
extern int af_v3_draw_dma(void *, u32, u32);
#define imports af_v3_draws
#define event af_v3_event
#define draw_dma af_v3_draw_dma
#endif

static const struct ImportDraw *imported(u32 actor) {
    const struct ImportDraw *row;
    if (actor < 0xE0DAu || actor >= 0xE0EEu) return 0;
    row = &imports[actor - 0xE0DAu];
    return row->actor == actor ? row : 0;
}

int af_v3_npc_draw(void *destination, u32 name_argument) {
    u32 name = (u16)name_argument, index;
    const struct ImportDraw *row;
    const u16 *same_event;
    /* Native callers can supply a four-byte-aligned destination. PI DMA needs
       eight-byte alignment, so retain the original staging/copy contract. */
    u8 staged[104] __attribute__((aligned(8)));
    u8 *out = destination;
    if (!out) return 0;
    if ((name & 0xF000u) == 0xD000u) {
        same_event = event(name);
        if (same_event) name = same_event[1];
    }
    if ((name & 0xF000u) == 0xE000u) {
        index = name - 0xE000u;
        if (index >= 218) {
            row = imported(name);
            if (!row) return 0;
            for (u32 i = 0; i < 100; ++i) out[i] = row->draw[i];
            return 1;
        }
    } else if ((name & 0xF000u) == 0xD000u) {
        index = 218 + name - 0xD000u;
        if (index >= 327) return 0;
    } else return 0;
    if (draw_dma(staged, 0x00E05008u + index * 100u, 100)) return 0;
    for (u32 i = 0; i < 100; ++i) out[i] = staged[i];
    return 1;
}

u32 af_v3_npc_voice(const u8 *draw) {
    const struct ImportDraw *row;
    u32 bank = (u32)draw[2] * 256u + draw[3];
    if (draw[0x5F] != 255 || bank < 410 || bank >= 430) return draw[0x5F];
    row = imported(0xE0DAu + bank - 410u);
    if (!row || row->draw[2] != draw[2] || row->draw[3] != draw[3]) return 255;
    return row->voice;
}
