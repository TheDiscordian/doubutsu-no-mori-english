/* Complete campfire/bonfire callbacks for the native furniture owner.
 * The full rig owns the logs and flame anchor. Only the flame shape is replaced
 * by a camera-facing draw; submitted scroll commands and matrices are immutable.
 */
typedef unsigned char u8;
typedef unsigned int u32;
typedef signed short s16;
typedef __UINTPTR_TYPE__ uptr;
typedef union { float f; u32 bits; } FloatWord;
typedef struct {
    float start, end, duration;
    FloatWord speed, current;
    int mode;
    u8 rest[0x58];
} Keyframe;
typedef struct {
    u8 before_position[8];
    float position[3];
    u8 before_state[0x3C - 0x14];
    s16 state;
    u8 before_keyframe[0x134 - 0x3E];
    Keyframe keyframe;
    s16 joint[9][3], morph[9][3];
    u8 matrices[2][10][64];
    u8 texture_animation[4];
    float scale[3];
    u8 rest[0x20];
} Fire;
typedef struct { u32 a, b; } Command;
typedef struct {
    u8 before_opaque[0x298];
    Command *opa_head;
    u8 *opa_tail;
    u8 before_translucent[8];
    Command *xlu_head;
    u8 *xlu_tail;
} FireGfx;
typedef struct {
    FireGfx *gfx;
    u8 before_frame[0xA0 - sizeof(FireGfx*)];
    u32 frame;
    u8 before_billboard[0x1E5C - 0xA4];
    float billboard[16];
    u8 before_play_frame[4];
    u32 play_frame;
} FireGame;
typedef struct { Fire *actor; void *matrix; u32 flame; } FireDraw;
typedef int (*JointCallback)(FireGame*, Keyframe*, int, Command**, u8*, void*, s16*, float*);
#define CHECK(type, field, at) \
    _Static_assert(__builtin_offsetof(type, field) == (at), #type "." #field)
CHECK(Fire, position, 8); CHECK(Fire, state, 0x3C);
CHECK(Fire, keyframe, 0x134); CHECK(Fire, joint, 0x1A4);
CHECK(Fire, morph, 0x1DA); CHECK(Fire, matrices, 0x210);
CHECK(Fire, scale, 0x714);
CHECK(FireGame, frame, 0xA0); CHECK(FireGame, billboard, 0x1E5C);
CHECK(FireGame, play_frame, 0x1EA0);
_Static_assert(sizeof(Fire) == 0x740, "Native furniture stride");
_Static_assert(sizeof(Keyframe) == 0x70, "Native keyframe size");
#ifdef __mips__
CHECK(FireGfx, opa_head, 0x298); CHECK(FireGfx, opa_tail, 0x29C);
CHECK(FireGfx, xlu_head, 0x2A8); CHECK(FireGfx, xlu_tail, 0x2AC);
#endif
extern void cKF_SkeletonInfo_R_ct(Keyframe*, void*, void*, void*, void*);
extern void cKF_SkeletonInfo_R_init_standard_repeat(Keyframe*, void*, void*);
extern int cKF_SkeletonInfo_R_play(Keyframe*);
extern void cKF_Si3_draw_R_SV(FireGame*, Keyframe*, void*, JointCallback, JointCallback, void*);
extern void *Lib_SegmentedToVirtual(void*);
extern void sAdo_OngenPos(u32, u8, float*);
extern void Matrix_Position_Zero(float*);
extern void Matrix_push(void);
extern void Matrix_pull(void);
extern void Matrix_translate(float, float, float, u8);
extern void Matrix_mult(float*, int);
extern void Matrix_RotateY(s16, int);
extern void Matrix_scale(float, float, float, u8);
extern void *_Matrix_to_Mtx(void*);
extern void osWritebackDCache(void*, int);

static void fire_ct(Fire *actor, uptr skeleton, uptr animation) {
    Keyframe *key = &actor->keyframe;
    void *rig = Lib_SegmentedToVirtual((void*)skeleton);
    void *motion = Lib_SegmentedToVirtual((void*)animation);
    cKF_SkeletonInfo_R_ct(key, rig, motion, actor->joint, actor->morph);
    cKF_SkeletonInfo_R_init_standard_repeat(key, motion, (void*)0);
    key->speed.bits = 0x3F000000; /* 0.5, retaining donor evaluation order. */
    cKF_SkeletonInfo_R_play(key);
}
void af_v3_campfire_ct(Fire *actor, u8 *data) {
    (void)data; fire_ct(actor, 0x06001F38, 0x06001F00);
}
void af_v3_bonfire_ct(Fire *actor, u8 *data) {
    (void)data; fire_ct(actor, 0x06001780, 0x06001748);
}
static void fire_mv(Fire *actor, u8 sound) {
    cKF_SkeletonInfo_R_play(&actor->keyframe);
    actor->keyframe.speed.bits = 0x3F000000;
    /* Native birth, bye, death, and birth-wait differ from the GC enum. The
     * positional sound manager expires sources that are no longer refreshed. */
    if (actor->state != 5 && actor->state != 6 && actor->state != 13 && actor->state != 15)
        sAdo_OngenPos((u32)(uptr)actor, sound, actor->position);
}
void af_v3_campfire_mv(Fire *actor, void *room, FireGame *game, u8 *data) {
    (void)room; (void)game; (void)data; fire_mv(actor, 0x5D);
}
void af_v3_bonfire_mv(Fire *actor, void *room, FireGame *game, u8 *data) {
    (void)room; (void)game; (void)data; fire_mv(actor, 0x5C);
}
static int fire_before(FireGame *game, Keyframe *key, int joint, Command **shape,
        u8 *flags, void *arg, s16 *rotation, float *translation) {
    (void)game; (void)key; (void)flags; (void)arg; (void)rotation; (void)translation;
    if (joint == 2) *shape = (void*)0;
    return 1; /* Keep the complete joint transform even with no shape. */
}
static int fire_after(FireGame *game, Keyframe *key, int joint, Command **shape,
        u8 *flags, void *arg, s16 *rotation, float *translation) {
    (void)key; (void)shape; (void)flags; (void)rotation; (void)translation;
    if (joint == 2) {
        FireDraw *draw = arg;
        float position[3];
        FloatWord factor; factor.bits = 0x3C23D70A; /* 0.01 */
        Matrix_Position_Zero(position);
        Matrix_push();
        Matrix_translate(position[0], position[1], position[2], 0);
        Matrix_mult(game->billboard, 1);
        Matrix_RotateY(0x4000, 1);
        Matrix_scale(draw->actor->scale[0] * factor.f, draw->actor->scale[1] * factor.f,
                     draw->actor->scale[2] * factor.f, 1);
        _Matrix_to_Mtx(draw->matrix);
        Matrix_pull();
        Command *command = game->gfx->xlu_head;
        command[0] = (Command){0xDA380003, (u32)(uptr)draw->matrix};
        command[1] = (Command){0xDE000000, draw->flame};
        game->gfx->xlu_head = command + 2;
    }
    return 1;
}
static void fire_dw(Fire *actor, void *room, FireGame *game, u8 *data, int large) {
    FireGfx *gfx = game->gfx;
    uptr opa = (uptr)gfx->opa_head, tail = (uptr)gfx->opa_tail;
    uptr xlu = (uptr)gfx->xlu_head, xend = (uptr)gfx->xlu_tail;
    /* Full rig: five commands on each head, two joint matrices in the actor.
     * Frame arena: shared identical base matrix, flame matrix, five scroll
     * commands, and eight padding bytes. Check both heads before any write. */
    if (!data || ((opa | xlu) & 7) || tail < opa || xend < xlu
            || tail - opa < 216 || xend - xlu < 40) return;
    uptr allocation = (tail - 176) & ~(uptr)15;
    if (allocation < opa + 40) return;
    gfx->opa_tail = (u8*)allocation;
    Command *scroll = (Command*)(allocation + 128);
    u32 frame = room ? game->play_frame : game->frame;
    /* GC has 1/16-texel tile origins; N64 has 1/4. Convert the GC's doubled
     * arguments before packing, with unsigned wrapping and explicit floor.
     * Odd bonfire frames quantise by 1/8 texel, with no accumulated drift. */
    u32 y = large ? (((0u - frame * 6u) & 0x3FFFu) >> 2) : ((0u - frame * 3u) & 0xFFFu);
    u32 x = large ? (0u - frame) & 0xFFFu : 0;
    scroll[0] = (Command){0xE8000000, 0};
    scroll[1] = (Command){0xF2000000 | y, (124u << 12) | ((y + 252u) & 0xFFFu)};
    scroll[2] = (Command){0xE8000000, 0};
    scroll[3] = (Command){0xF2000000 | (x << 12),
        0x01000000 | (((x + (large ? 252u : 124u)) & 0xFFFu) << 12) | 124u};
    scroll[4] = (Command){0xDF000000, 0};
    _Matrix_to_Mtx((void*)allocation);
    *gfx->opa_head++ = (Command){0xDA380003, (u32)allocation};
    *gfx->xlu_head++ = (Command){0xDA380003, (u32)allocation};
    *gfx->xlu_head++ = (Command){0xDB060024, (u32)(allocation + 128)};
    FireDraw draw = {actor, (void*)(allocation + 64), large ? 0x06001660 : 0x06001E20};
    void *matrices = actor->matrices[game->frame & 1];
    cKF_Si3_draw_R_SV(game, &actor->keyframe, matrices, fire_before, fire_after, &draw);
    osWritebackDCache((void*)allocation, 168);
    osWritebackDCache(matrices, 128);
}
void af_v3_campfire_dw(Fire *actor, void *room, FireGame *game, u8 *data) {
    fire_dw(actor, room, game, data, 0);
}
void af_v3_bonfire_dw(Fire *actor, void *room, FireGame *game, u8 *data) {
    fire_dw(actor, room, game, data, 1);
}
