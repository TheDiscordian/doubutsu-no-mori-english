/* Source-bound camera flashes use the native effect pool and scene lifetime.
 * Native updates cover two donor ticks. Keep particle timers in donor ticks;
 * the native owner supplies the second decrement after the move callback.
 */
#include "room_effects.h"
extern void Matrix_translate(float,float,float,u8);
extern void Matrix_mult(float *,int);
extern void Matrix_scale(float,float,float,u8);
extern void *_Matrix_to_Mtx(void *);
extern void osWritebackDCache(void *,int);
extern void _texture_z_light_fog_prim_xlu(void *);
#ifndef AF_EFFECT_FLASH_MODEL
#define AF_EFFECT_FLASH_MODEL 0x06000140u
#endif

void af_v3_flash_init(EffectPosition pos,int priority,s16 angle,void *game,u16 item,s16 arg0,s16 arg1) {
    (void)arg1;
    RoomEffectClip *clip=room_effect_clip;
    if (clip) clip->create(ROOM_EFFECT_FLASH,pos,0,game,0,item,priority,arg0,angle);
}

void af_v3_flash_ct(RoomEffect *effect,void *game,void *arg) {
    (void)game;(void)arg;
    s16 length=(s16)(3.0f+af_effect_random()*7.0f);
    if (effect->arg0==1 && room_effect_clip) {
        /* Integer native light endpoints round up by less than one frame. */
        room_effect_clip->light((EffectColour){27,27,27,255},(length+1)/2,((length>>1)+1)/2,1);
    }
    effect->timer=5;
    effect->acceleration.x=0.3f+af_effect_random()*0.7f;
}

void af_v3_flash_mv(RoomEffect *effect,void *game) {
    (void)game;
    s16 elapsed=5-effect->timer;
    RoomEffectClip *clip=room_effect_clip;
    if (clip) {
        float scale=elapsed<=4 ? clip->adjust(elapsed,0,2,effect->acceleration.x*0.005f,0.01f)
                              : clip->adjust(elapsed,3,4,effect->acceleration.x*0.01f,0.0f);
        effect->scale=(EffectPosition){scale,scale,scale};
    }
    if (effect->timer>0) --effect->timer;
}

void af_v3_flash_dw(RoomEffect *effect,RoomRigGame *game) {
    RoomRigGraphics *g=game->gfx;
    uptr head=(uptr)g->xlu_head,tail=(uptr)g->xlu_tail;
    /* The native setup uses one command; the complete draw uses three more. */
    if ((head&7u) || tail<head || tail-head<32u+64u+15u) return;
    uptr matrix=(tail-64u)&~(uptr)15u;
    if (matrix<head+32u) return;
    g->xlu_tail=(u8 *)matrix;
    Matrix_translate(effect->position.x,effect->position.y,effect->position.z,0);
    Matrix_mult((float *)((u8 *)game+0x1E5C),1);
    Matrix_scale(effect->scale.x,effect->scale.y,effect->scale.z,1);
    _Matrix_to_Mtx((void *)matrix);
    osWritebackDCache((void *)matrix,64);
    _texture_z_light_fog_prim_xlu(g);
    *g->xlu_head++=(RoomCommand){0xDA380003,(u32)matrix};
    *g->xlu_head++=(RoomCommand){0xFA0000FF,0xFFFFFFC8};
    /* Complete donor list has its own render mode; segment 8 is unused. */
    *g->xlu_head++=(RoomCommand){0xDE000000,AF_EFFECT_FLASH_MODEL};
}

void af_v3_flash_controller_init(EffectPosition pos,int priority,s16 angle,void *game,u16 item,s16 arg0,s16 arg1) {
    (void)arg1;
    RoomEffectClip *clip=room_effect_clip;
    if (clip) clip->create(ROOM_EFFECT_FLASH_CONTROLLER,pos,0,game,0,item,priority,arg0,angle);
}

void af_v3_flash_controller_ct(RoomEffect *effect,void *game,void *arg) {
    (void)game;(void)arg;
    effect->timer=240;
    effect->specific[0]=0;
}

void af_v3_flash_controller_mv(RoomEffect *effect,void *game) {
    if (!(effect->timer&7)) {
        u32 scene=room_effect_scene;
        int size=scene==20u ? 4 : (scene==6u || scene==21u) ? 6 : scene==22u ? 8 : -1;
        if (size!=-1 && room_effect_clip) {
            EffectPosition pos;
            pos.z=43.0f;
            pos.x=40.0f+(af_effect_random()*(float)size)*40.0f;
            pos.y=-10.0f+af_effect_random()*20.0f+75.0f;
            room_effect_clip->request(ROOM_EFFECT_FLASH,pos,effect->priority,0,game,effect->item,
                                     effect->specific[0]&1,0);
            ++effect->specific[0];
        }
    }
    if (effect->timer>0) --effect->timer;
}

void af_v3_flash_controller_dw(RoomEffect *effect,void *game) {
    (void)effect;(void)game;
}
