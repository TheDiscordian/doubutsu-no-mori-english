/* Complete delayed reversible material/effect lifecycle at the donor tick rate. */
#include "room_effect_rigs.h"
#include "room_effects.h"
#include "room_motion.h"
extern void sAdo_OngenPos(u32,u8,float *);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);

static u32 half(const u8 *p) { return ((u32)p[0]<<8)|p[1]; }
static u32 word(const u8 *p) { return (half(p)<<16)|half(p+2); }
static float duration(const RoomEffectRigParams *p) {
    FloatWord f;f.bits=word(p->duration);return f.f;
}
static RoomEffectRigState *effect_work(RoomRig *actor) {
    return (RoomEffectRigState *)(void *)actor->matrices[0][6];
}

const RoomEffectRigParams *af_v3_room_effect_rig_params(const RoomRigRecord *r,const u8 *data) {
    if (!data || ((uptr)data&7) || r->bytes<32 || (r->first.bits&3) || r->last.bits ||
            r->first.bits<0x06000000u || r->first.bits>0x06000000u+r->bytes-32u) return 0;
    const RoomEffectRigParams *p=(const RoomEffectRigParams *)(data+(r->first.bits-0x06000000u));
    u32 d=word(p->duration),model=word(p->model),size=half(p->frame_bytes);
    if (d<0x3F800000u || d>0x46FFFE00u || (model&7) || model<0x06000000u ||
            model>0x06000000u+r->bytes-8u || p->segment!=8 || p->frames!=5 || p->sound!=0x50 ||
            p->joint!=2 || r->joints<=p->joint || half(p->delay)!=19 || size!=128 || size>r->bytes) return 0;
    for (u32 i=0;i<5;++i) if ((half(p->offsets[i])&7) || half(p->offsets[i])>r->bytes-size) return 0;
    for (u32 i=0;i<6;++i) if (p->padding[i]) return 0;
    return p;
}

void af_v3_room_effect_rig_ct(RoomRig *actor,void *skeleton,void *animation,const RoomEffectRigParams *p) {
    /* This donor lifecycle intentionally uses the opposite saved-switch test
       to the plain reversible category. Do not normalise the two policies. */
    af_v3_room_reverse_init(actor,skeleton,animation,duration(p),actor->switched!=1);
    RoomEffectRigState *state=effect_work(actor);
    state->delayed=state->reverse.state;
    state->steam=state->delay=state->reserved=0;
}

void af_v3_room_effect_rig_step(RoomRig *actor,RoomRigGame *game,const RoomEffectRigParams *p,int pressed) {
    RoomEffectRigState *state=effect_work(actor);
    if (state->reverse.state==1 && !room_transition_state(actor->state)) {
        sAdo_OngenPos((u32)(uptr)actor,p->sound,actor->position);
        if (state->steam<0) {
            RoomEffectClip *clip=room_effect_clip;
            if (clip && game) {
                EffectPosition pos={actor->position[0],actor->position[1]+18.0f,actor->position[2]};
                clip->request(ROOM_EFFECT_STEAM,pos,1,0,game,0xFFFF,6,0);
            }
            state->steam=(int)(10.0f+af_effect_random()*20.0f);
        } else --state->steam;
    }
    int accepted=pressed && actor->keyframe.speed.f==0 && state->delay==0;
    /* Delayed state is observed before advancing the keyframe evaluator. */
    if (accepted) state->delay=(s16)half(p->delay);
    if (!state->delay) state->delayed=state->reverse.state;
    af_v3_room_reverse_step(actor,duration(p),state->reverse.state ? 0x16 : 0x17,accepted);
    if (state->delay>0) --state->delay;
}

typedef struct { const RoomEffectRigParams *params;u8 *allocation; } EffectRigDraw;
static int effect_before(void *game,RoomKeyframe *key,int joint,void *list,
        void *flags,void *arg,s16 *rotation,void *position) {
    (void)game;(void)key;(void)flags;(void)rotation;(void)position;
    EffectRigDraw *draw=arg;
    if (joint==draw->params->joint) *(void **)list=0;
    return 1;
}
static int effect_after(RoomRigGame *game,RoomKeyframe *key,int joint,void *list,
        void *flags,void *arg,void *rotation,void *position) {
    (void)key;(void)list;(void)flags;(void)rotation;(void)position;
    EffectRigDraw *draw=arg;
    if (joint==draw->params->joint) {
        void *matrix=draw->allocation+64;
        _Matrix_to_Mtx(matrix);
        *game->gfx->xlu_head++=(RoomCommand){0xDA380003,(u32)(uptr)matrix};
        *game->gfx->xlu_head++=(RoomCommand){0xDE000000,word(draw->params->model)};
    }
    return 1;
}

void af_v3_room_effect_rig_dw(RoomRig *actor,RoomRigGame *game,const RoomRigRecord *r,
        const RoomEffectRigParams *p,u8 *data) {
    RoomRigGraphics *g=game->gfx;
    uptr head=(uptr)g->head,end=(uptr)g->tail,xlu=(uptr)g->xlu_head,xend=(uptr)g->xlu_tail;
    u32 commands=(2u+2u*r->shown)*8u;
    if (!head || !end || !xlu || !xend || ((head|end|xlu|xend)&7) || end<head || xend<xlu ||
            end-head<128u+15u+commands || xend-xlu<32u) return;
    uptr allocation=(end-128u)&~(uptr)15;
    g->tail=(u8 *)allocation;
    u32 counter=actor->ctr_type==1 ? *(u32 *)((u8 *)game+0x1EA0) : game->frame;
    int active=actor->ctr_type==1 ? effect_work(actor)->delayed==1 : actor->keyframe.end==duration(p);
    u32 frame=active ? (counter*2u)&3u : 4u;
    _Matrix_to_Mtx((void *)allocation);
    *g->head++=(RoomCommand){0xDA380003,(u32)allocation};
    *g->xlu_head++=(RoomCommand){0xDB060000u+4u*p->segment,
        (u32)(uptr)(data+half(p->offsets[frame]))&0x1FFFFFFFu};
    EffectRigDraw draw={p,(u8 *)allocation};
    void *matrices=actor->matrices[game->frame&1];
    cKF_Si3_draw_R_SV(game,&actor->keyframe,matrices,(void *)effect_before,(void *)effect_after,&draw);
    osWritebackDCache((void *)allocation,128);
    osWritebackDCache(matrices,r->shown*64);
}
