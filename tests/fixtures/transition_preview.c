/* Isolated native transition draw, never installed in a release cartridge. */
#include <PR/mbi.h>
#define WORD(p,n) (*(u32 *)((u8 *)(p)+(n)))
#define META ((volatile u32 *)0x80503000)

void af_transition_preview(void *actor,void *game) {
    static const Vp viewport={{{640,480,511,0},{640,480,511,0}}};
    void *graph=*(void **)game;
    void *wipe=(void *)0x80503040;
    Gfx *p=(Gfx *)WORD(graph,0x288),*end=(Gfx *)WORD(graph,0x28C);
    (void)actor;
    if ((u32)p+2048>(u32)end) {META[2]=1;return;}
    if (!META[1]) {
        ((void *(*)(void *))0x80083CBC)(wipe);
        ((void (*)(void *,int))0x80084018)(wipe,META[0]==1 ? 0x80 : META[0]==2 ? 0x40 : 0);
        ((void (*)(void *))0x80083C00)(wipe);
        WORD(wipe,0)=META[4];
    }
    gDPPipeSync(p++);
    gDPSetScissor(p++,G_SC_NON_INTERLACE,0,0,320,240);
    gDPSetCycleType(p++,G_CYC_FILL);
    gDPSetRenderMode(p++,G_RM_NOOP,G_RM_NOOP2);
    gDPSetColorImage(p++,G_IM_FMT_RGBA,G_IM_SIZ_16b,320,(void *)0x80600000);
    gDPSetFillColor(p++,0xFFFFFFFF);
    gDPFillRectangle(p++,0,0,319,239);
    gDPPipeSync(p++);
    gDPSetOtherMode(p++,G_AD_DISABLE|G_CD_MAGICSQ|G_CK_NONE|G_TC_FILT|
        G_TF_BILERP|G_TT_NONE|G_TL_TILE|G_TD_CLAMP|G_TP_PERSP|
        G_CYC_1CYCLE|G_PM_1PRIMITIVE,G_AC_NONE|G_ZS_PIXEL|G_RM_AA_OPA_SURF|G_RM_AA_OPA_SURF2);
    gSPViewport(p++,&viewport);
    gSPSegment(p++,4,(void *)0x80510000);
    ((void (*)(void *,Gfx **))0x80083E08)(wipe,&p);
    gDPSetColorImage(p++,G_IM_FMT_RGBA,G_IM_SIZ_16b,320,WORD(graph,0x2E4));
    WORD(graph,0x288)=(u32)p;
    META[1]++;
    META[3]=0x80600000;
}
