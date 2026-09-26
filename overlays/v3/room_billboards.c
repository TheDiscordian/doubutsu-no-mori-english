/* Parameterised complete rig drawing, reusing installed camera-facing helpers. */
#include "room_rigs.h"
extern int af_v3_fire_before(void *,void *,int,void *,void *,void *,void *,void *);
extern int af_v3_fire_after(void *,void *,int,void *,void *,void *,void *,void *);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);
typedef struct { RoomRig *actor;void *matrix;u32 flame; } BillboardDraw;

void af_v3_room_billboard_dw(RoomRig *actor,void *room,RoomRigGame *game,
                           const RoomRigRecord *r,const RoomBillboard *p) {
    RoomRigGraphics *g=game->gfx;
    uptr opa=(uptr)g->head,end=(uptr)g->tail,xlu=(uptr)g->xlu_head,xend=(uptr)g->xlu_tail;
    u32 commands=(2u+2u*r->shown)*8u;
    if (((opa|xlu)&7) || end<opa || xend<xlu || end-opa<176u+commands ||
            xend-xlu<commands+16u) return;
    uptr allocation=(end-176u)&~(uptr)15;
    if (allocation<opa+commands) return;
    g->tail=(u8 *)allocation;
    RoomCommand *scroll=(RoomCommand *)(allocation+128);
    u32 frame=room ? *(u32 *)((u8 *)game+0x1EA0) : game->frame;
    for (u32 i=0;i<2;++i) {
        /* Source doubles its rates into 14-bit sixteenth-texel coordinates. */
        u32 x=((frame*(u32)(int)p->rates[i][0]*2u)&0x3FFFu)>>2;
        u32 y=((frame*(u32)(int)p->rates[i][1]*2u)&0x3FFFu)>>2;
        scroll[i*2]=(RoomCommand){0xE8000000,0};
        scroll[i*2+1]=(RoomCommand){0xF2000000|(x<<12)|y,
            (i<<24)|(((x+(p->dimensions[i][0]-1u)*4u)&0xFFFu)<<12)|
            ((y+(p->dimensions[i][1]-1u)*4u)&0xFFFu)};
    }
    scroll[4]=(RoomCommand){0xDF000000,0};
    _Matrix_to_Mtx((void *)allocation);
    *g->head++=(RoomCommand){0xDA380003,(u32)allocation};
    *g->xlu_head++=(RoomCommand){0xDA380003,(u32)allocation};
    *g->xlu_head++=(RoomCommand){0xDB060024,(u32)(allocation+128)};
    BillboardDraw draw={actor,(void *)(allocation+64),p->flame};
    void *matrices=actor->matrices[game->frame&1];
    cKF_Si3_draw_R_SV(game,&actor->keyframe,matrices,(void *)af_v3_fire_before,(void *)af_v3_fire_after,&draw);
    osWritebackDCache((void *)allocation,168);
    osWritebackDCache(matrices,r->shown*64);
}
