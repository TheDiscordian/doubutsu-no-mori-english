/* Checkpoint-restored visual fixture, never installed into a game cartridge. */
#include <PR/mbi.h>
#define WORD(p,n) (*(u32 *)((u8 *)(p)+(n)))
#define META ((volatile u32 *)0x80503000)
typedef void (*Draw)(void *,void *,void *);
typedef void (*Matrix)(void *,int);

void af_keyboard_v2_preview(void *actor,void *game) {
    static const Vp viewport={{{640,480,511,0},{640,480,511,0}}};
    void *graph=*(void **)game;
    Gfx *branch=(Gfx *)WORD(graph,0x298), *g=branch+1;
    Gfx *overlay=(Gfx *)WORD(graph,0x288);
    (void)actor;
    if (WORD(graph,0x29C)<(u32)g+0x7000 || WORD(graph,0x28C)<(u32)overlay+32) {
        META[4]=1;return;
    }
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
    /* The title uses a perspective camera; ordinary menus establish this
       native orthographic projection before calling the keyboard. */
    ((Matrix)0x80090F10)(graph,0);
    META[5]=WORD(graph,0x298);
    ((Draw)META[0])((void *)META[1],(void *)META[2],game);
    ((Matrix)0x8009104C)(graph,0);
    META[6]=WORD(graph,0x298);
    META[7]=WORD(graph,0x29C);
    META[8]=WORD(graph,0x2E4);
    /* Store commands/vertices in the large opaque arena, but execute this
       fixture after the title world through the final overlay stream. The
       ordinary keyboard caller already supplies its correct menu ordering. */
    g=(Gfx *)WORD(graph,0x298);
    gSPEndDisplayList(g++);
    gSPBranchList(branch,g);
    gSPDisplayList(overlay++,branch+1);
    WORD(graph,0x298)=(u32)g;
    WORD(graph,0x288)=(u32)overlay;
    ++META[3];
}
