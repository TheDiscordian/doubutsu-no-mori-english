/* Field effects use their ordinary native loader, lifetime, and drawing. */
#include "creature_insect_effects.h"

void af_insect_effect(int type,xyz_t position,int priority,s16 angle,GAME *game,
                      mActor_name_t item,int arg0,int arg1) {
    AfInsectEffectClip *clip=af_insect_effect_clip;
    if (!clip) return;
    if (type==eEC_EFFECT_DIG_MUD) type=85;
    else if (type!=eEC_EFFECT_TURI_HAMON && type!=eEC_EFFECT_TURI_MIZU) return;
    clip->request(type,position,priority,angle,game,item,(s16)arg0,(s16)arg1);
}

AfInsectEffect *af_insect_mud_create(s16 type,xyz_t position,xyz_t *offset,GAME *game,
        void *argument,u16 item,int priority,s16 arg0,s16 arg1) {
    AfInsectEffectClip *clip=af_insect_effect_clip;
    if (!clip) return 0;
    int small=type==85 && (arg1&0x4000);
    /* The ordinary request loads the mud owner before reaching this bridge.
     * Clear only the GC size flag before the native constructor selects its
     * motion/lifetime. Keep the mole flag and every original mud variant. */
    AfInsectEffect *effect=clip->create(type,position,offset,game,argument,item,priority,
        arg0,small?(s16)(arg1&~0x4000):arg1);
    if (effect && small) {
        effect->scale.x=effect->scale.y=effect->scale.z=0.005f;
        effect->specific[2]=1;
        /* Both source and native late-life adjust calls discard their result;
         * neither writes a new scale. Keep that source behaviour. */
    }
    return effect;
}
