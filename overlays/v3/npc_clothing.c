/* Preserve native NPC clothing slots, queues, and transfer sizes. */
typedef unsigned char u8;
typedef unsigned int u32;
extern u32 af_v3_clothing_source(int index, u32 palette);
#ifdef __mips__
#define destination(bank) ((void *)*(u32 *)((bank) + 4))
#define queue_create ((void (*)(void *, void *, int))0x80034D60u)
#define queue_receive ((int (*)(void *, void *, int))0x8002DFA0u)
#define dma_async ((void (*)(void *, void *, u32, u32, int, void *, void *, const char *, int))0x80026DCCu)
#define dma_sync ((int (*)(void *, u32, u32))0x80026B44u)
#else
extern void *af_v3_clothing_destination(u8 *);
extern void af_v3_clothing_queue_create(void *, void *, int);
extern int af_v3_clothing_queue_receive(void *, void *, int);
extern void af_v3_clothing_dma_async(void *, void *, u32, u32, int, void *, void *, const char *, int);
extern int af_v3_clothing_dma(void *, u32, u32);
#define destination af_v3_clothing_destination
#define queue_create af_v3_clothing_queue_create
#define queue_receive af_v3_clothing_queue_receive
#define dma_async af_v3_clothing_dma_async
#define dma_sync af_v3_clothing_dma
#endif

int af_v3_clothing_checked_index(u8 *item) {
    if (!item) return 0;
    u32 value = ((u32)item[0] << 8) | item[1];
    if (value >= 0x2400 && value <= 0x24FF) return value - 0x2400;
    if (value == 0x34BF && af_v3_clothing_source(0x10BF, 0)) return 0x10BF;
    item[0] = 0x24;
    item[1] = 0;
    return 0;
}

static int transfer(u8 *slot, int index, u32 palette, int synchronous) {
    u32 source = af_v3_clothing_source(index, palette);
    if (!slot || !source) return 0;
    u8 *bank = slot + (palette ? 0x5C : 8);
    void *out = destination(bank);
    u32 bytes = palette ? 32 : 512;
    if (!out) return 0;
    if (synchronous) return dma_sync(out, source, bytes) == 0;
    if (*(u32 *)(bank + 0x14)) return queue_receive(bank + 0x34, 0, 0) == 0;
    queue_create(bank + 0x34, bank + 0x4C, 1);
    dma_async(bank + 0x14, out, source, bytes, 0, bank + 0x34, 0, "V3 clothing", 1);
    return 0;
}

int af_v3_npc_cloth_texture(u8 *slot, int index) { return transfer(slot, index, 0, 0); }
int af_v3_npc_cloth_palette(u8 *slot, int index) { return transfer(slot, index, 1, 0); }
void af_v3_npc_cloth_texture_sync(u8 *slot, int index) { transfer(slot, index, 0, 1); }
void af_v3_npc_cloth_palette_sync(u8 *slot, int index) { transfer(slot, index, 1, 1); }
