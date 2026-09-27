/* Shared stopped/reversible motion; source timing is one explicit step. */
#include "room_reversible.h"
extern void sAdo_OngenTrgStart(u32,float *);

static RoomReversible *work(RoomRig *actor) {
    return (RoomReversible *)(void *)actor->matrices[0][6];
}

void af_v3_room_reverse_ct(RoomRig *actor,void *skeleton,void *animation,float duration) {
    RoomReversible *state=work(actor);
    RoomKeyframe *key=&actor->keyframe;
    cKF_SkeletonInfo_R_ct(key,skeleton,animation,state->joint,state->morph);
    cKF_SkeletonInfo_R_init_standard_stop(key,animation,(void *)0);
    key->speed.f=0;
    key->start=1;
    key->end=duration;
    state->state=actor->switched==1;
    state->reserved=0;
    if (!state->state) key->current.f=duration;
    cKF_SkeletonInfo_R_play(key);
}

void af_v3_room_reverse_step(RoomRig *actor,float duration,u32 sound,int pressed) {
    RoomReversible *state=work(actor);
    RoomKeyframe *key=&actor->keyframe;
    if (pressed && key->speed.f==0) {
        state->state=(state->state+1)&1;
        key->speed.f=.5f;
        key->start=state->state ? duration : 1;
        key->end=state->state ? 1 : duration;
        sAdo_OngenTrgStart(sound,actor->position);
    }
    if (cKF_SkeletonInfo_R_play(key)==1) key->speed.f=0;
}

void af_v3_room_reverse_dt(RoomRig *actor) {
    actor->switched=work(actor)->state!=0;
}
