/* Complete switched joint motion and source-ordered translucent redraws. */
#include "room_rigs.h"
#include "room_motion.h"
extern void add_calc(float *,float,float,float,float);
extern void sAdo_OngenPos(u32,u8,float *);
extern void sAdo_OngenTrgStart(u32,float *);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);
#ifdef __mips__
#define joint_clock ((const volatile u8 *)0x80136FBCu)
#else
extern u8 af_v3_test_joint_clock[8];
#define joint_clock af_v3_test_joint_clock
#endif

void af_v3_room_joint_ct(RoomRig *actor,const RoomRigRecord *r) {
    u32 kind=r->first.bits&255u;
    actor->motion_power=actor->switched==1 ? 1.0f : 0.0f;
    actor->motion_phase=kind==2 ? (float)(joint_clock[1]*60u+joint_clock[0])/600.0f : 0.0f;
    actor->keyframe.speed.f=.5f;
    cKF_SkeletonInfo_R_play(&actor->keyframe);
    actor->keyframe.speed.f=actor->motion_power*(kind==3 ? .5f : 1.0f);
}

void af_v3_room_joint_mv(RoomRig *actor,const RoomRigRecord *r) {
    u32 kind=r->first.bits&255u;
    float target=actor->switched==1 ? 1.0f : 0.0f;
    for (u32 i=0;i<2;++i) {
        if (kind==3) {
            if (actor->motion_power<target) {
                actor->motion_power+=.01f;
                if (actor->motion_power>target) actor->motion_power=target;
            } else if (actor->motion_power>target) {
                actor->motion_power-=.01f;
                if (actor->motion_power<target) actor->motion_power=target;
            }
            actor->keyframe.speed.f=actor->motion_power*.5f;
        } else {
            add_calc(&actor->motion_power,target,.3f,.3f,.0001f);
            actor->keyframe.speed.f=actor->motion_power*.5f*2.0f;
        }
        cKF_SkeletonInfo_R_play(&actor->keyframe);
        if (kind==2) {
            actor->motion_phase+=1.8204445f;
            if (actor->motion_phase>=65535.0f) actor->motion_phase=0.0f;
        }
    }
    if (kind==3 && !room_transition_state(actor->state)) {
        if (actor->changed) sAdo_OngenTrgStart(actor->switched==1 ? r->last.bits>>16 : r->last.bits&65535u,actor->position);
        if (actor->switched==1 && actor->motion_power>=.01f)
            sAdo_OngenPos((u32)(uptr)actor,(r->first.bits>>8)&127u,actor->position);
    }
}

typedef struct {
    RoomRig *actor;
    u8 *allocation;
    void *hidden;
    u32 kind;
} JointDraw;

static int joint_before(void *game,RoomKeyframe *key,int joint,void *list,
                        void *flags,void *arg,s16 *rotation,void *position) {
    (void)game;(void)key;(void)flags;(void)position;
    JointDraw *d=arg;
    if (d->kind==2) {
        if (joint==1) rotation[2]=(s16)((u16)rotation[2]+(int)d->actor->motion_phase);
    } else if (joint==3 || joint==(d->kind==1 ? 7 : 4)) {
        d->hidden=*(void **)list;
        *(void **)list=0;
    }
    return 1;
}

static int joint_after(RoomRigGame *game,RoomKeyframe *key,int joint,void *list,
                       void *flags,void *arg,void *rotation,void *position) {
    (void)key;(void)list;(void)flags;(void)rotation;(void)position;
    JointDraw *d=arg;
    if (d->kind==2 || !(joint==3 || joint==(d->kind==1 ? 7 : 4))) return 1;
    RoomRigGraphics *g=game->gfx;
    void *matrix=d->allocation+(joint==3 ? 64 : 128);
    _Matrix_to_Mtx(matrix);
    u32 level=(u8)(int)(d->actor->motion_power*255.0f);
    if (d->kind==1 && joint==7) *g->xlu_head++=(RoomCommand){0xFA000000|level,0xFFFF96FF};
    *g->xlu_head++=(RoomCommand){0xDA380003,(u32)(uptr)matrix};
    if (d->kind==3 && joint==4) {
        *g->xlu_head++=(RoomCommand){0xFA0000FF,0xFFFFFF00|level};
        *g->xlu_head++=(RoomCommand){0xDB060024,(u32)(uptr)(d->allocation+192)};
    }
    *g->xlu_head++=(RoomCommand){0xDE000000,(u32)(uptr)d->hidden};
    return 1;
}

void af_v3_room_joint_dw(RoomRig *actor,RoomRigGame *game,const RoomRigRecord *r) {
    if (!game || !game->gfx) return;
    RoomRigGraphics *g=game->gfx;u32 kind=r->first.bits&255u;
    uptr opa=(uptr)g->head,end=(uptr)g->tail,xlu=(uptr)g->xlu_head,xend=(uptr)g->xlu_tail;
    u32 commands=(2u+2u*r->shown)*8u;
    if (((opa|xlu|end|xend)&7) || end<opa || xend<xlu || end-opa<240u+commands+15u ||
            xend-xlu<commands+64u) return;
    uptr allocation=(end-240u)&~(uptr)15;
    g->tail=(u8 *)allocation;
    if (kind==3) {
        RoomCommand *scroll=(RoomCommand *)(allocation+192);
        u32 frame=actor->ctr_type==1 ? *(u32 *)((u8 *)game+0x1EA0) : game->frame;
        for (u32 i=0;i<2;++i) {
            u32 y=i ? 0 : ((frame*16u)&0x3FFFu)>>2;
            scroll[i*2]=(RoomCommand){0xE8000000,0};
            scroll[i*2+1]=(RoomCommand){0xF2000000|y,(i<<24)|(28u<<12)|((y+124u)&0xFFFu)};
        }
        scroll[4]=(RoomCommand){0xDF000000,0};
    }
    _Matrix_to_Mtx((void *)allocation);
    *g->head++=(RoomCommand){0xDA380003,(u32)allocation};
    JointDraw draw={actor,(u8 *)allocation,0,kind};
    void *matrices=actor->matrices[game->frame&1];
    cKF_Si3_draw_R_SV(game,&actor->keyframe,matrices,(void *)joint_before,(void *)joint_after,&draw);
    osWritebackDCache((void *)allocation,232);
    osWritebackDCache(matrices,r->shown*64);
}
