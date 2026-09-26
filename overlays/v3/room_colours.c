#include "room_colours.h"
#include "room_motion.h"

static RoomColourState *colour_state(void) {
    RoomColourState *s=room_colour_state;
    if (s->magic!=ROOM_COLOUR_MAGIC) {
        *s=(RoomColourState){0};s->magic=ROOM_COLOUR_MAGIC;
    }
    return s;
}

void af_v3_room_colour_ct(RoomRig *actor) {
    if (actor) ((u8 *)actor)[0x12C]=0;
}

static void same_switch_off(RoomRig *actor,void *room) {
    /* The room is relocated; its linked globals are not callable/live RAM.
       Resolve the verified three-field work through its actual overlay owner. */
    RoomColourOverlay *overlay=*(RoomColourOverlay **)((u8 *)room+0x170);
    if (!overlay || overlay->vrom_start!=0x0082D7F0u ||
            overlay->vram_start!=0x80936710u || overlay->vram_end<0x8094756Cu || !overlay->loaded) return;
    RoomColourInstances *work=(RoomColourInstances *)(overlay->loaded+0x10E50);
    if (!work->actors || !work->used || work->count<=0 || work->count>48) return;
    for (int i=0;i<work->count;++i) {
        RoomRig *other=work->actors+i;
        if (work->used[i] && other->index==actor->index) {
            ((u8 *)other)[0x12C]=0;other->changed=1;
        }
    }
}

void af_v3_room_colour_mv(RoomRig *actor,void *room,RoomRigGame *game,u8 sound) {
    if (!actor || !room || !game || room_transition_state(actor->state)) return;
    u8 *on=(u8 *)actor+0x12C;
    if (*on==1) {
        sAdo_OngenPos((u32)(uptr)actor,sound,actor->position);
        RoomColourState *s=colour_state();void *player=af_reaction_player(game);
        if (player) {
            if (s->player!=player) { s->player=player;s->active=0;s->timer=0; }
            s->request=1;
        }
    }
    if (actor->changed && *on==1) { same_switch_off(actor,room);*on=1; }
}

void af_v3_room_colour_update(void *actor,RoomRigGame *game,RoomColourOriginal original) {
    /* Preserve the complete native pre-action update before consuming requests. */
    original(actor,game);
    RoomColourState *s=colour_state();
    if (s->player!=actor) { s->request=0;s->active=0;return; }
    if (!s->request) { s->active=0;return; }
    s->request=0;
    for (u32 i=0;i<2;++i) {
        if (!s->active) { s->active=1;s->timer=0; }
        else { s->timer+=1.0f;if (s->timer>=79.68f) s->timer=0; }
    }
}

void af_v3_room_colour_draw(RoomRigGame *game,RoomKeyframe *key,void *matrix,
                            void *before,void *after,void *actor) {
    RoomColourState *s=colour_state();RoomRigGraphics *gfx=game->gfx;
    int enabled=s->active && s->player==actor && gfx && gfx->head && gfx->tail &&
        (uptr)gfx->head+4*sizeof(RoomCommand)<=(uptr)gfx->tail;
    RoomCommand *effect=enabled ? gfx->head : 0;
    if (enabled) {
        int near=1,far=1,frame=(int)(s->timer/9.96f);
        if (!(frame&1) && frame>=0 && frame<8) {
            /* Exact bounded form of the donor binary's stride-three indexing. */
            static const u8 rgb[4][3]={{255,100,255},{255,255,255},{100,100,100},{100,255,255}};
            for (u32 i=0;i<3;++i) s->rgb[i]=rgb[frame/2][i];
            const float *eye=(const float *)((u8 *)game+0x1960);
            const float *centre=(const float *)((u8 *)game+0x196C);
            const float *position=(const float *)((u8 *)actor+0x28);
            float x=centre[0]-eye[0],y=centre[1]-eye[1],z=centre[2]-eye[2];
            float length=sqrtf(x*x+y*y+z*z);
            if (length>0.0f) {
                float projected=((position[0]-eye[0])*x+(position[1]-eye[1])*y+(position[2]-eye[2])*z)/length;
                near=(int)(210.0f+(length-projected)/length);
                far=near+(int)(780.0f+(length-352.0f)*0.07092198729515076f+
                               (length*0.25f)*0.07092198729515076f);
            }
        }
        gfx->head=gfx_set_fog_nosync(gfx->head,s->rgb[0],s->rgb[1],s->rgb[2],255,near,far);
    }
    cKF_Si3_draw_R_SV(game,key,matrix,before,after,actor);
    if (enabled) {
        const u8 *light=(const u8 *)game+0x1C60;
        /* The skeleton callbacks may allocate matrices from the tail. Never
           restore an old tail pointer over those live allocations. If they
           consume the remaining command space, disable our initial effect
           instead of spilling commands or tinting everything drawn afterward. */
        int space=(uptr)gfx->head+2*sizeof(RoomCommand)<=(uptr)gfx->tail;
        RoomCommand *end=gfx_set_fog_nosync(space ? gfx->head : effect,
            light[7],light[8],light[9],0,*(const s16 *)(light+10),*(const s16 *)(light+12));
        if (space) gfx->head=end;
    }
}
