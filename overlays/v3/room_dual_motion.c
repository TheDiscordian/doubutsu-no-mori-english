/* Full source-order dual-animation contact behaviour and three scroll layers.
   Environment/contact readers and mapped sounds belong to checked dispatch. */
#include "room_dual_motion.h"
#include "room_motion.h"
extern void sAdo_OngenPos(u32,u8,float *);
extern void sAdo_OngenTrgStart(u32,float *);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);

static RoomReversible *dual_work(RoomRig *actor) {
    return (RoomReversible *)(void *)actor->matrices[0][6];
}

#ifdef AF_V3_ROOM_DUAL_MOTION
int af_v3_room_dual_resolve(const RoomRigRecord *r,u8 *data,RoomDualMotion *out) {
    if (!r || !data || !out || r->mode!=ROOM_RIG_DUAL || r->bytes<32 || r->bytes>9216 ||
            (r->bytes&15) || !r->last.bits ||
            r->animation==r->first.bits || !r->reserved || r->reserved>127) return 0;
    u32 headers[2]={r->first.bits,r->animation};
    for (u32 i=0;i<2;++i) {
        u32 at=headers[i];u16 sound=(u16)(r->last.bits>>(i*16));
        if ((at&3) || at<0x06000000u || at>0x06000000u+r->bytes-20u ||
                !sound || (sound&0x8080u) || (sound>>8)!=1) return 0;
        u8 *a=data+at-0x06000000u;u32 frames=(u32)a[18]*256u+a[19];
        if (a[16]!=255 || a[17]!=255 || !frames || frames>32767) return 0;
        out->animation[i]=Lib_SegmentedToVirtual((void *)(uptr)at);
        out->duration[i]=(float)frames;out->click[i]=sound;
    }
    out->loop=r->reserved;return 1;
}

int af_v3_room_dual_front(void) {
#ifdef __mips__
    void **clip=*(void **volatile *)0x80136F2Cu;
    void *owner=clip ? *clip : (void *)0;
#else
    void *owner=af_v3_test_dual_owner;
#endif
    return owner && *(int *)((u8 *)owner+0x1A0)==0;
}
#endif

void af_v3_room_dual_ct(RoomRig *actor,void *skeleton,const RoomDualMotion *motion,int force_closed) {
    RoomReversible *w=dual_work(actor);RoomKeyframe *key=&actor->keyframe;
    if (force_closed) actor->switched=0;
    w->state=force_closed ? 0 : actor->switched==1;w->reserved=0;
    void *animation=motion->animation[w->state];float end=motion->duration[w->state];
    cKF_SkeletonInfo_R_ct(key,skeleton,animation,w->joint,w->morph);
    cKF_SkeletonInfo_R_init_standard_stop(key,animation,(void *)0);
    key->speed.f=0;key->start=1;key->end=end;key->current.f=end;
    cKF_SkeletonInfo_R_play(key);
}

void af_v3_room_dual_step(RoomRig *actor,const RoomDualMotion *motion,int pressed,int front_contact) {
    RoomReversible *w=dual_work(actor);RoomKeyframe *key=&actor->keyframe;
    if (pressed && front_contact && key->speed.f==0) {
        w->state=(w->state+1)&1;
        cKF_SkeletonInfo_R_init_standard_stop(key,motion->animation[w->state],(void *)0);
        key->start=1;key->end=motion->duration[w->state];key->speed.f=.5f;
        sAdo_OngenTrgStart(motion->click[w->state],actor->position);
    }
    if (!room_transition_state(actor->state) &&
            (w->state ? key->current.f>25.0f : key->current.f<25.0f))
        sAdo_OngenPos((u32)(uptr)actor,motion->loop,actor->position);
    if (cKF_SkeletonInfo_R_play(key)==1) key->speed.f=0;
}

void af_v3_room_dual_dt(RoomRig *actor) { actor->switched=dual_work(actor)->state!=0; }

void af_v3_room_dual_dw(RoomRig *actor,RoomRigGame *game,u32 shown,int stop_scroll) {
    if (!actor || !game || !game->gfx || !shown || shown>6) return;
    RoomRigGraphics *g=game->gfx;
    uptr head=(uptr)g->head,end=(uptr)g->tail,xlu=(uptr)g->xlu_head,xend=(uptr)g->xlu_tail;
    if (!head || !end || !xlu || !xend || ((head|end|xlu|xend)&7) || end<head || xend<xlu ||
            end-head<184u+15u+8u*(5u+2u*shown) || xend-xlu<8) return;
    uptr allocation=(end-184u)&~(uptr)15u;
    g->tail=(u8 *)allocation;
    RoomCommand *scroll=(RoomCommand *)(allocation+64);
    u32 frame=2u*(actor->ctr_type==1 ? *(u32 *)((u8 *)game+0x1EA0) : game->frame);
    static const u8 phases[3]={0,5,15};
    for (u32 i=0;i<3;++i) {
        u32 source=stop_scroll ? 0u : 0u-2u*(frame+phases[i]);
        u32 s=((source<<1)&0x3FFFu)>>2;
        scroll[i*5]=(RoomCommand){0xE8000000,0};
        scroll[i*5+1]=(RoomCommand){0xF2000000u|(s<<12),(((s+124u)&0xFFFu)<<12)|28u};
        scroll[i*5+2]=(RoomCommand){0xE8000000,0};
        scroll[i*5+3]=(RoomCommand){0xF2000000,0x01000000u|(124u<<12)|28u};
        scroll[i*5+4]=(RoomCommand){0xDF000000,0};
    }
    _Matrix_to_Mtx((void *)allocation);
    *g->head++=(RoomCommand){0xDA380003,(u32)allocation};
    for (u32 i=0;i<3;++i)
        *g->head++=(RoomCommand){0xDB060020u+i*4u,(u32)(uptr)(scroll+i*5)&0x1FFFFFFFu};
    void *matrices=actor->matrices[game->frame&1];
    cKF_Si3_draw_R_SV(game,&actor->keyframe,matrices,(void *)0,(void *)0,(void *)0);
    osWritebackDCache((void *)allocation,184);
    osWritebackDCache(matrices,shown*64);
}
