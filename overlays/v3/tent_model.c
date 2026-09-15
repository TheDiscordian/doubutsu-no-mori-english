/* Native light-switch callbacks for the complete GC tent model.
 * The profile must have no generic rig/texture animation. Its unused joint
 * storage holds one private fade float. Submitted palettes belong to the
 * graphics frame, not to a mutable actor or heap allocation.
 */
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
typedef union { float f; u32 bits; } FloatWord;
typedef struct {
    u8 before_switch[0x12C];
    u8 switch_bit;
    u8 before_fade[0x1A4 - 0x12D];
    FloatWord fade;
    u8 rest[0x740 - 0x1A8];
} Tent;
typedef struct { u32 a, b; } Command;
typedef struct {
    u8 before_opaque_head[0x298];
    Command *head;
    u8 *tail;
} TentGfx;
typedef struct { TentGfx *gfx; } TentGame;
typedef struct {
    u32 magic;
    u16 bytes, count;
    u32 on, off, models[4];
} PaletteLayout;
_Static_assert(sizeof(PaletteLayout) == 32, "Complete immutable palette-fade layout");
#ifdef AF_V3_SHARED_PALETTE_FADE
extern const PaletteLayout af_v3_legacy_tent_layout;
#endif
_Static_assert(sizeof(Tent) == 0x740, "Native furniture stride");
_Static_assert(__builtin_offsetof(Tent, switch_bit) == 0x12C, "Native switch state");
_Static_assert(__builtin_offsetof(Tent, fade) == 0x1A4, "Tent-owned unused joint storage");
#ifdef __mips__
_Static_assert(sizeof(uptr) == 4, "N64 pointer width");
_Static_assert(__builtin_offsetof(TentGfx, head) == 0x298, "Native opaque command head");
_Static_assert(__builtin_offsetof(TentGfx, tail) == 0x29C, "Native opaque allocation tail");
#endif
extern void *_Matrix_to_Mtx(void *destination);
extern void osWritebackDCache(void *address, int bytes);

void af_v3_tent_model_ct(Tent *actor, u8 *data) {
    (void)data;
    actor->fade.bits = actor->switch_bit == 1 ? 0x3F800000u : 0;
}

void af_v3_tent_model_mv(Tent *actor, void *room, void *game, u8 *data) {
    FloatWord target, step;
    float now = actor->fade.f;
    (void)room; (void)game; (void)data;
    target.bits = actor->switch_bit == 1 ? 0x3F800000u : 0;
    step.bits = 0x3DCCCCCDu; /* Donor float 0.1, not a rounded frame counter. */
    if (now > target.f) {
        now -= step.f;
        if (now < target.f) now = target.f;
    } else if (now < target.f) {
        now += step.f;
        if (now > target.f) now = target.f;
    }
    actor->fade.f = now;
}

void af_v3_tent_model_dt(Tent *actor, u8 *data) {
    (void)data;
    actor->fade.bits = 0;
    /* There is no heap allocation to release. Prior submitted frames keep
     * their palettes after the actor is destroyed or reused. */
}

#ifdef AF_V3_SHARED_PALETTE_FADE
static void draw(Tent *actor, TentGame *game, u8 *data, const PaletteLayout *layout) {
#else
void af_v3_tent_model_dw(Tent *actor, void *room, TentGame *game, u8 *data) {
#endif
    TentGfx *gfx = game->gfx;
    uptr head = (uptr)gfx->head, tail = (uptr)gfx->tail, allocation;
    Command *commands = gfx->head;
    const u16 *on, *off;
    u16 *palette;
#ifdef AF_V3_SHARED_PALETTE_FADE
    u32 count = layout->count;
    if (layout->magic != 0x41465031u || count < 1 || count > 4 ||
            layout->bytes < 96 || layout->bytes > 9216 ||
            (layout->on & 31) || (layout->off & 31) ||
            layout->on > (u32)layout->bytes - 32 || layout->off > (u32)layout->bytes - 32) return;
    for (u32 i = 0; i < count; ++i)
        if ((layout->models[i] & 7) || layout->models[i] < 0x06000000u ||
                layout->models[i] > 0x06000000u + layout->bytes - 8) return;
#else
    (void)room;
    const u32 count = 4;
#endif
    /* Six commands, a 64-byte matrix, and a 32-byte palette. Round the shared
     * allocation down to 32 bytes, keeping both resources properly aligned.
     * Do not modify either arena end or issue a draw if there is no room. */
    if (!data || (head & 7) || (tail & 15) || tail < head || tail - head < 96+(count+2)*8) return;
    allocation = (tail - 96) & ~(uptr)31;
    if (allocation < head + (count+2)*8) return;
    gfx->tail = (u8 *)allocation;
    gfx->head = commands + count+2;
    palette = (u16 *)(allocation + 64);
#ifdef AF_V3_SHARED_PALETTE_FADE
    on = (const u16 *)(data + layout->on);
    off = (const u16 *)(data + layout->off);
#else
    on = (const u16 *)(data + 0x20);
    off = (const u16 *)(data + 0x40);
#endif
    for (u32 i = 0; i < 16; ++i) {
        u32 result = off[i] & 1u;
        for (u32 shift = 1; shift <= 11; shift += 5) {
            float a = (float)((off[i] >> shift) & 31u);
            float b = (float)((on[i] >> shift) & 31u);
            result |= ((u32)(a + actor->fade.f * (b - a)) & 31u) << shift;
        }
        palette[i] = result;
    }
    _Matrix_to_Mtx((void *)allocation);
    osWritebackDCache((void *)allocation, 96);
    commands[0] = (Command){0xDA380003, (u32)allocation};
    commands[1] = (Command){0xDB060020, (u32)(allocation + 64)};
#ifdef AF_V3_SHARED_PALETTE_FADE
    for (u32 i = 0; i < count; ++i) commands[i+2] = (Command){0xDE000000, layout->models[i]};
#else
    commands[2] = (Command){0xDE000000, 0x06000C50};
    commands[3] = (Command){0xDE000000, 0x06000D18};
    commands[4] = (Command){0xDE000000, 0x06000E00};
    commands[5] = (Command){0xDE000000, 0x06000FF0};
#endif
}

#ifdef AF_V3_SHARED_PALETTE_FADE
void __attribute__((section(".text.layout_entry")))
af_v3_tent_model_dw(Tent *actor, void *room, TentGame *game, u8 *data) {
    (void)room;
    if (data) draw(actor, game, data, &af_v3_legacy_tent_layout);
}

void __attribute__((section(".text.layout_entry")))
af_v3_palette_fade_dw(Tent *actor, void *room, TentGame *game, u8 *data) {
    (void)room;
    if (data) draw(actor, game, data, (const PaletteLayout *)data);
}
#endif
