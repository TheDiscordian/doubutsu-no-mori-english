/* Test-only rendering callback. Never linked into a distributed cartridge. */
#include <PR/mbi.h>

#define WORD(p, n) (*(u32 *)((u8 *)(p) + (n)))
#define META ((volatile u32 *)0x80503000)
#define DEPTH ((void *)0x80600000)

static const Lights1 light = gdSPDefLights1(96, 96, 96, 159, 159, 159, 40, 90, 80);
static const u32 roots[] = {0x06093348, 0x06095440, 0x06022388};

void af_event_preview(void *actor, void *game) {
    void *graph = *(void **)game;
    Gfx *p = (Gfx *)WORD(graph, 0x288);
    Gfx *end = (Gfx *)WORD(graph, 0x28C);
    u32 mode = META[0];
    u32 arena = 0x801540C0 + (WORD(graph, 0x2E0) & 1) * 0x20410 + 0x18F08;
    (void)actor;
    META[3] = (u32)p;
    META[4] = (u32)end;
    META[5] = arena;
    if (mode > 2 || (u32)p < arena || (u32)end > arena + 0x2000 ||
        (u32)p + 2048 > (u32)end) {
        META[2] = 1;
        return;
    }
    gDPPipeSync(p++);
    gDPSetScissor(p++, G_SC_NON_INTERLACE, 0, 0, 320, 240);
    gDPSetCycleType(p++, G_CYC_FILL);
    gDPSetRenderMode(p++, G_RM_NOOP, G_RM_NOOP2);
    gDPSetColorImage(p++, G_IM_FMT_RGBA, G_IM_SIZ_16b, 320, DEPTH);
    gDPSetFillColor(p++, 0xFFFCFFFC);
    gDPFillRectangle(p++, 0, 0, 319, 239);
    gDPPipeSync(p++);
    gDPSetColorImage(p++, G_IM_FMT_RGBA, G_IM_SIZ_16b, 320, WORD(graph, 0x2E4));
    gDPSetFillColor(p++, 0xBDF7BDF7);
    gDPFillRectangle(p++, 0, 0, 319, 239);
    gDPPipeSync(p++);
    gDPSetDepthImage(p++, DEPTH);
    gDPSetOtherMode(p++, G_AD_NOTPATTERN | G_CD_MAGICSQ | G_CK_NONE | G_TC_FILT |
        G_TF_BILERP | G_TT_RGBA16 | G_TL_TILE | G_TD_CLAMP | G_TP_PERSP |
        G_CYC_2CYCLE | G_PM_NPRIMITIVE, G_AC_NONE | G_ZS_PIXEL |
        G_RM_FOG_SHADE_A | G_RM_AA_ZB_TEX_EDGE2);
    gSPLoadGeometryMode(p++, G_ZBUFFER | G_SHADE | G_FOG | G_LIGHTING |
        G_SHADING_SMOOTH | G_CULL_BACK);
    gSPFogPosition(p++, 990, 1000);
    gDPSetFogColor(p++, 192, 192, 192, 255);
    gSPSetLights1(p++, light);
    gSPPerspNormalize(p++, 0xFFFF);
    gSPSegment(p++, 6, 0x80510000);
    gSPMatrix(p++, 0x80503040, G_MTX_PROJECTION | G_MTX_LOAD | G_MTX_NOPUSH);
    gSPMatrix(p++, 0x80503080, G_MTX_MODELVIEW | G_MTX_LOAD | G_MTX_NOPUSH);
    gSPDisplayList(p++, roots[mode]);
    gDPPipeSync(p++);
    gDPSetDepthImage(p++, WORD(graph, 8));
    WORD(graph, 0x288) = (u32)p;
    META[1]++;
}
