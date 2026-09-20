#include "balloon_actor.h"

void af_v3_balloon_draw(Balloon *b,void *game) {
    if (b->mode!=1 || !b->ready) return;
    u8 *g=*(u8 **)game;
    u32 **head=(u32 **)(g+0x298),*tail=*(u32 **)(g+0x29C);
    u32 **xlu=(u32 **)(g+0x2A8),*xlu_tail=*(u32 **)(g+0x2AC);
    /* Parent matrix, state/reflection, four skeletal matrices and lists,
       both segment bindings, and their restores, before any partial draw. */
    if (((uptr)*head&7) || ((uptr)tail&7) || (uptr)tail<(uptr)*head ||
            (uptr)tail-(uptr)*head<1024 || ((uptr)*xlu&7) ||
            (uptr)xlu_tail<(uptr)*xlu || (uptr)xlu_tail-(uptr)*xlu<32) return;
    u32 saved=BSEG;
    BSEG=(u32)(uptr)b->model&0x1FFFFFFFu;
    *(*head)++=0xDB060018;*(*head)++=BSEG;
    BFN(0x800E020Cu,void,void)();
    BalloonPosition p=BPOS(b,0x28);
    BFN(0x800E0314u,void,float,float,float,int)(p.x,p.y,p.z,0);
    BFN(0x800E0698u,void,int,int)(BSHORT(b,0xDE),1);
    BFN(0x800E0500u,void,int,int)((s16)(BSHORT(b,0xDC)-0x4000),1);
    BFN(0x800E0834u,void,int,int)(0x4000,1);
    BFN(0x800E0500u,void,int,int)(b->lean,1);
    BFN(0x800E041Cu,void,float,float,float,int)(BREAL(b,0x5C),BREAL(b,0x60),BREAL(b,0x64),1);
    u32 matrix=BFN(0x800E13C4u,u32,void *)(g);
    *(*head)++=0xDA380003;*(*head)++=matrix;
    BFN(0x800BD4E8u,void,void *)(g);
    BFN(0x800588B8u,void,void *,void *)((u8 *)b+0x28,game);
    /* GX-only TexEdgeAlpha is not an N64 opcode. Complete converted balloon
       materials already use native AA/CVG_X_ALPHA, as in the held drawer. */
    BFN(0x800530D8u,void,void *,void *,void *,void *,void *,void *)
        (game,b->keyframe,b->matrices[BWORD(game,0xA0)&1],0,0,b);
    BFN(0x800E0244u,void,void)();
    BSEG=saved;
    *(*head)++=0xDB060018;*(*head)++=saved;
    *(*xlu)++=0xDB060018;*(*xlu)++=saved;
}
