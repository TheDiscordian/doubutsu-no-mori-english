/* Donor-faithful joint attachments, without persistent per-actor allocations. */
#include "accessory.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned int u32;
typedef __UINTPTR_TYPE__ uptr;
struct Row { u16 actor, bank; u32 address, display; u8 joint, enabled; u16 bytes; };
struct Gfx { u32 w0, w1; };
struct Graph { u8 padding[0x298]; struct Gfx *p, *d; };
typedef int (*Callback)(void *, void *, int, void *, void *, void *, void *, void *);
struct Context {
    void *actor;
    Callback before, after;
    const struct Row *row;
    u32 captured;
    float matrix[16];
};
_Static_assert(sizeof(struct Row) == 16, "Accessory registry row");

#ifdef __mips__
#define rows ((const struct Row *)(AF_V3_ACCESSORY_RAM+0x1000u))
#define ready (*(volatile const u32 *)0x8019ACD0u == 1u)
#define installed_draw ((const u16 *)0x80462000u)
#define draw_skeleton ((void (*)(void *, void *, void *, Callback, Callback, void *))0x800530D8u)
#define matrix_push ((void (*)(void))0x800E020Cu)
#define matrix_pop ((void (*)(void))0x800E0244u)
#define matrix_get ((void (*)(float *))0x800E0260u)
#define matrix_put ((void (*)(const float *))0x800E0284u)
#define matrix_scale ((void (*)(float, float, float, u8))0x800E041Cu)
#define matrix_new ((void *(*)(struct Graph *))0x800E13C4u)
#define setup_npc ((void (*)(struct Graph *))0x800BD5E8u)
#define segments ((const u32 *)0x801458A0u)
_Static_assert(__builtin_offsetof(struct Graph, d) == 0x29C, "Native opaque arena offsets");
#else
extern struct Row af_accessory_rows[20];
extern u16 af_accessory_draws[1040];
extern int af_accessory_ready;
extern u32 af_accessory_segments[16];
extern void af_accessory_skeleton(void *, void *, void *, Callback, Callback, void *);
extern void af_accessory_push(void), af_accessory_pop(void), af_accessory_get(float *);
extern void af_accessory_put(const float *), af_accessory_scale(float, float, float, u8);
extern void *af_accessory_matrix(struct Graph *);
extern void af_accessory_setup(struct Graph *);
#define rows af_accessory_rows
#define ready af_accessory_ready
#define installed_draw af_accessory_draws
#define draw_skeleton af_accessory_skeleton
#define matrix_push af_accessory_push
#define matrix_pop af_accessory_pop
#define matrix_get af_accessory_get
#define matrix_put af_accessory_put
#define matrix_scale af_accessory_scale
#define matrix_new af_accessory_matrix
#define setup_npc af_accessory_setup
#define segments af_accessory_segments
#endif

static int before(void *game, void *skeleton, int joint, void *shape, void *flags,
                  void *argument, void *rotation, void *position) {
    struct Context *context = argument;
    return context->before ? context->before(game, skeleton, joint, shape, flags,
                                             context->actor, rotation, position) : 1;
}

static int after(void *game, void *skeleton, int joint, void *shape, void *flags,
                 void *argument, void *rotation, void *position) {
    struct Context *context = argument;
    int result = context->after ? context->after(game, skeleton, joint, shape, flags,
                                                context->actor, rotation, position) : 1;
    if (joint == context->row->joint) {
        float scale = *(const float *)((const u8 *)context->actor+0x5C);
        if (scale > 0.0f && scale <= 1.0f) {
            scale = 1.0f / (scale * 100.0f);
            matrix_push();
            matrix_scale(scale, scale, scale, 1);
            matrix_get(context->matrix);
            matrix_pop();
            context->captured = 1;
        }
    }
    return result;
}

void af_v3_accessory_draw(void *game, void *skeleton, void *matrices,
                          Callback original_before, Callback original_after, void *actor) {
    const struct Row *row = 0;
    u32 id = actor ? *(const u16 *)((const u8 *)actor+6) : 0;
    if (ready && id >= 0xE0DAu && id < 0xE0EEu) {
        row = rows+id-0xE0DAu;
        if (row->actor != id || row->enabled != 1 || row->bank < 432 || row->bank >= 448
                || (row->joint != 13 && row->joint != 25) || row->bytes < 8 || row->bytes > 0x1400
                || row->address < AF_V3_ACCESSORY_RAM+0x2000u || (row->address & 31)
                || row->address > AF_V3_ACCESSORY_RAM+AF_V3_ACCESSORY_BYTES-16u-row->bytes
                || (row->display & 0xFF000007u) != 0x06000000u
                || (row->display & 0xFFFFFFu) > (u32)row->bytes-8u
                || installed_draw[(id-0xE0DAu)*52] != id) row = 0;
    }
    if (!row) {
        draw_skeleton(game, skeleton, matrices, original_before, original_after, actor);
        return;
    }
    struct Context context;
    context.actor = actor;
    context.before = original_before;
    context.after = original_after;
    context.row = row;
    context.captured = 0;
    draw_skeleton(game, skeleton, matrices, before, after, &context);
    if (context.captured) {
        struct Graph *graph = *(struct Graph **)game;
        /* Seven commands plus one 64-byte matrix; retain a small aligned gap. */
        if ((uptr)graph->d < (uptr)graph->p || (uptr)graph->d-(uptr)graph->p < 128u) return;
        matrix_push();
        matrix_put(context.matrix);
        void *matrix = matrix_new(graph);
        matrix_pop();
        if (!matrix) return;
        setup_npc(graph);
        struct Gfx *p = graph->p;
        p[0] = (struct Gfx){0xDB060018u, row->address & 0x1FFFFFFFu};
        p[1] = (struct Gfx){0xDA380003u, (u32)(uptr)matrix};
        p[2] = (struct Gfx){0xDE000000u, row->display};
        p[3] = (struct Gfx){0xDB060018u, segments[6]};
        graph->p = p+4;
    }
}
