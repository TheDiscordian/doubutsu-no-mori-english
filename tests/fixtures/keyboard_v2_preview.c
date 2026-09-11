/* Checkpoint-restored visual fixture, never installed into a game cartridge. */
#include <PR/mbi.h>
#define WORD(p,n) (*(u32 *)((u8 *)(p)+(n)))
#define META ((volatile u32 *)0x80503000)
typedef void (*Draw)(void *,void *,void *);

void af_keyboard_v2_preview(void *actor,void *game) {
    static const Vp viewport={{{640,480,511,0},{640,480,511,0}}};
    void *graph=*(void **)game;
    Gfx *g=(Gfx *)WORD(graph,0x298);
    (void)actor;
    if (WORD(graph,0x29C)<(u32)g+0x7000) {META[4]=1;return;}
    gDPPipeSync(g++);
    gDPSetScissor(g++,G_SC_NON_INTERLACE,0,0,320,240);
    gDPSetColorImage(g++,G_IM_FMT_RGBA,G_IM_SIZ_16b,320,WORD(graph,0x2E4));
    gDPSetCycleType(g++,G_CYC_FILL);
    gDPSetRenderMode(g++,G_RM_NOOP,G_RM_NOOP2);
    gDPSetFillColor(g++,0xBDF7BDF7);
    gDPFillRectangle(g++,0,0,319,239);
    gDPPipeSync(g++);
    gSPViewport(g++,&viewport);
    WORD(graph,0x298)=(u32)g;
    META[5]=(u32)g;
    ((Draw)META[0])((void *)META[1],(void *)META[2],game);
    META[6]=WORD(graph,0x298);
    META[7]=WORD(graph,0x29C);
    META[8]=WORD(graph,0x2E4);
    ++META[3];
}
