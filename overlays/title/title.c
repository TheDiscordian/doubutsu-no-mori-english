/* English title artwork and keyframes; native start/save transitions stay native. */
#include <PR/mbi.h>

typedef struct { s16 x, y, z; } TitleVec;
typedef struct {
    float start, end, duration, speed, frame;
    s32 mode;
} TitleFrame;
typedef struct {
    TitleFrame frame;
    void *skeleton, *animation;
    float morph;
    TitleVec *work, *morph_work, *difference;
    u8 movement[64];
} TitleSkeleton;
typedef struct {
    u32 magic, phase, draws, error;
    u32 background_alpha;
    TitleSkeleton skeleton[3];
    TitleVec work[3][22], morph[3][22];
    u32 guard;
} TitleState;

_Static_assert(sizeof(TitleSkeleton) == 0x70, "Native skeleton ABI");
_Static_assert(sizeof(TitleVec) == 6, "Native joint ABI");
_Static_assert(sizeof(TitleState) == 1152, "Explicit title actor extension");

extern const u32 af_title_assets[];
extern u32 SegmentBaseAddress[16];
extern void af_title_native_constructor(void *, void *);
extern void cKF_SkeletonInfo_R_ct(TitleSkeleton *, void *, void *, TitleVec *, TitleVec *);
extern void cKF_SkeletonInfo_R_init(TitleSkeleton *, void *, void *, float, float, float, float, float, s32, void *);
extern s32 cKF_SkeletonInfo_R_play(TitleSkeleton *);
extern void cKF_Si3_draw_SV_R_child(void *, TitleSkeleton *, s32 *, void *, void *, void *, Mtx **);
extern void Matrix_push(void);
extern void Matrix_pull(void);
extern void Matrix_translate(float, float, float, s32);
extern void Matrix_scale(float, float, float, s32);
extern Mtx *_Matrix_to_Mtx(Mtx *);

#define STATE_AT 0x330
#define MAGIC 0x41465453u
#define GUARD 0xC17E5AFEu
#define SEGMENT 11
#define U32(p, at) (*(u32 *)((u8 *)(p)+(at)))
#define PTR(p, at) (*(void **)((u8 *)(p)+(at)))

static TitleState *state(void *actor) { return (TitleState *)((u8 *)actor+STATE_AT); }
static u32 bind_assets(void) {
    u32 previous = SegmentBaseAddress[SEGMENT];
    SegmentBaseAddress[SEGMENT] = (u32)af_title_assets & 0x1FFFFFFFu;
    return previous;
}
static int valid(TitleState *s) {
    return s->magic == MAGIC && s->guard == GUARD && s->phase <= 2 && s->background_alpha <= 220;
}

void af_title_constructor(void *actor, void *game) {
    TitleState *s = state(actor);
    u32 i, previous;
    af_title_native_constructor(actor, game);
    for (i = 0; i < sizeof(*s)/4; ++i) ((u32 *)s)[i] = 0;
    if (af_title_assets[0] != 0x41465447u || af_title_assets[1] != 1 ||
        af_title_assets[2] != 280224 || af_title_assets[3] != SEGMENT ||
        af_title_assets[4] != 23 || af_title_assets[5] != 3) {
        s->error = 1;
        return;
    }
    previous = bind_assets();
    for (i = 0; i < 3; ++i) {
        void *skeleton = (void *)af_title_assets[6+i*3];
        void *animation = (void *)af_title_assets[7+i*3];
        cKF_SkeletonInfo_R_ct(&s->skeleton[i], skeleton, animation, s->work[i], s->morph[i]);
        /* Native animation units are 1/30 second; GC advances 0.5 at 60 Hz. */
        cKF_SkeletonInfo_R_init(&s->skeleton[i], skeleton, animation, 1.0f, 121.0f,
                               1.0f, 1.0f, 0.0f, 0, 0);
        cKF_SkeletonInfo_R_play(&s->skeleton[i]);
    }
    SegmentBaseAddress[SEGMENT] = previous;
    s->magic = MAGIC;
    s->guard = GUARD;
}

void af_title_step(void *actor) {
    TitleState *s = state(actor);
    u32 previous, i, done = 1, skip;
    void *game = *(void **)0x8010EF90;
    if (!valid(s)) return;
    skip = *(u8 *)0x80137950 && (*(u16 *)((u8 *)game+0x20) & 0x1000);
    previous = bind_assets();
    if (!s->phase || skip) {
        for (i = 0; i < 3; ++i) {
            if (skip) s->skeleton[i].frame.frame = 121.0f;
            if (cKF_SkeletonInfo_R_play(&s->skeleton[i]) != 1) done = 0;
        }
        if (done || skip) s->phase = 1;
    } else if (s->phase == 1) {
        /* Match the reference's 20/60-second tick at the native 30-Hz rate. */
        s->background_alpha += 40;
        if (s->background_alpha >= 220) s->background_alpha = 220;
    }
    SegmentBaseAddress[SEGMENT] = previous;
    if (skip) {
        s->background_alpha = 220;
        U32(actor, 0x2A8) = 255; /* Native skip completes the copyright fade. */
    }
    if (s->phase == 1 && s->background_alpha == 220) {
        s->phase = 2;
        for (i = 0; i < 6; ++i) ((u8 *)actor)[0x31C+i] = 1;
    }
    ++U32(actor, 0x2A4); /* Retain the native introduction counter. */
}

static const Gfx letter_mode[] = {
    gsDPPipeSync(),
    gsSPLoadGeometryMode(G_CULL_BACK),
    gsDPSetOtherMode(G_AD_NOTPATTERN | G_CD_MAGICSQ | G_CK_NONE | G_TC_FILT |
        G_TF_BILERP | G_TT_NONE | G_TL_TILE | G_TD_CLAMP | G_TP_PERSP |
        G_CYC_1CYCLE | G_PM_NPRIMITIVE, G_AC_NONE | G_ZS_PRIM | G_RM_XLU_SURF | G_RM_XLU_SURF2),
    gsDPSetCombineMode(G_CC_DECALRGBA, G_CC_DECALRGBA),
    gsSPEndDisplayList(),
};
static const Gfx background_mode[] = {
    gsDPPipeSync(),
    gsSPLoadGeometryMode(G_CULL_BACK),
    gsDPSetOtherMode(G_AD_DISABLE | G_CD_DISABLE | G_CK_NONE | G_TC_FILT |
        G_TF_BILERP | G_TT_NONE | G_TL_TILE | G_TD_CLAMP | G_TP_PERSP |
        G_CYC_1CYCLE | G_PM_NPRIMITIVE, G_AC_NONE | G_ZS_PRIM | G_RM_XLU_SURF | G_RM_XLU_SURF2),
    gsDPSetCombineLERP(0, 0, 0, PRIMITIVE, TEXEL0, 0, PRIMITIVE, 0,
                      0, 0, 0, PRIMITIVE, TEXEL0, 0, PRIMITIVE, 0),
    gsSPEndDisplayList(),
};
static const Gfx trademark_mode[] = {
    gsDPPipeSync(),
    gsSPLoadGeometryMode(G_CULL_BACK),
    gsDPSetOtherMode(G_AD_DISABLE | G_CD_DISABLE | G_CK_NONE | G_TC_FILT |
        G_TF_BILERP | G_TT_NONE | G_TL_TILE | G_TD_CLAMP | G_TP_PERSP |
        G_CYC_1CYCLE | G_PM_NPRIMITIVE, G_AC_NONE | G_ZS_PRIM | G_RM_XLU_SURF | G_RM_XLU_SURF2),
    gsDPSetCombineLERP(0, 0, 0, PRIMITIVE, 0, 0, 0, TEXEL0,
                      0, 0, 0, PRIMITIVE, 0, 0, 0, TEXEL0),
    gsSPEndDisplayList(),
};

static Mtx *matrices(void *graph, u32 count, u32 font_space) {
    u32 head = U32(graph, 0x298), tail = U32(graph, 0x29C);
    u32 font = U32(graph, 0x2B8), end = U32(graph, 0x2BC);
    u32 size = count*sizeof(Mtx);
    /* Native graphics allocations can leave an eight-byte-aligned tail.
       Own the alignment padding as well as the matrices, without crossing head. */
    tail &= ~15u;
    if (head > tail || size > tail-head || font > end || font_space > end-font) return 0;
    U32(graph, 0x29C) = tail-size;
    return (Mtx *)(tail-size);
}

void af_title_draw(void *actor, void *game) {
    TitleState *s = state(actor);
    void *graph = PTR(game, 0);
    u32 previous, i;
    Gfx *gfx, *opaque;
    Mtx *matrix;
    if (!valid(s)) return;
    matrix = matrices(graph, 19, 2048);
    if (!matrix) { s->error = 2; return; }
    previous = bind_assets();
    gfx = PTR(graph, 0x2B8);
    gSPSegment(gfx++, SEGMENT, af_title_assets);
    Matrix_push();
    Matrix_translate(0.0f, 730.0f, 0.0f, 1);
    Matrix_scale(0.135f, 0.135f, 0.135f, 1);
    if (s->background_alpha) {
        _Matrix_to_Mtx(matrix);
        gSPMatrix(gfx++, matrix, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW);
        gSPDisplayList(gfx++, background_mode);
        gDPSetPrimColor(gfx++, 0, 255, 80, 60, 0, s->background_alpha);
        for (i = 0; i < 4; ++i) gSPDisplayList(gfx++, af_title_assets[15+i]);
    }
    ++matrix;
    gSPDisplayList(gfx++, letter_mode);
    opaque = PTR(graph, 0x298);
    PTR(graph, 0x298) = gfx;
    for (i = 0; i < 3; ++i) {
        s32 joint = 0;
        /* The child entry avoids the wrapper's unrelated segment-13/XLU writes. */
        cKF_Si3_draw_SV_R_child(game, &s->skeleton[i], &joint, 0, 0, 0, &matrix);
    }
    gfx = PTR(graph, 0x298);
    PTR(graph, 0x298) = opaque;
    gSPSegment(gfx++, SEGMENT, previous);
    PTR(graph, 0x2B8) = gfx;
    Matrix_pull();
    SegmentBaseAddress[SEGMENT] = previous;
    ++s->draws;
}

void af_title_trademark(void *actor, void *game) {
    TitleState *s = state(actor);
    void *graph = PTR(game, 0);
    Mtx *matrix;
    Gfx *gfx;
    u32 previous;
    if (!valid(s)) return;
    matrix = matrices(graph, 1, 512);
    if (!matrix) { s->error = 3; return; }
    previous = bind_assets();
    gfx = PTR(graph, 0x2B8);
    gSPSegment(gfx++, SEGMENT, af_title_assets);
    Matrix_push();
    Matrix_translate(1530.0f, 690.0f, 0.0f, 1);
    Matrix_scale(0.162082675f, 0.162082675f, 0.162082675f, 1);
    _Matrix_to_Mtx(matrix);
    gSPMatrix(gfx++, matrix, G_MTX_NOPUSH | G_MTX_LOAD | G_MTX_MODELVIEW);
    gSPDisplayList(gfx++, trademark_mode);
    gDPSetPrimColor(gfx++, 0, 255, 40, 40, 45, 255);
    gSPDisplayList(gfx++, af_title_assets[19]);
    gSPSegment(gfx++, SEGMENT, previous);
    PTR(graph, 0x2B8) = gfx;
    Matrix_pull();
    SegmentBaseAddress[SEGMENT] = previous;
}
