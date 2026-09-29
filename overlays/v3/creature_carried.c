/* Native layouts are bound to the original controller/light consumers by the
 * installer. Event state is supplied by the event owner, never a dummy flag. */
#include "creature_carried.h"
#include "creature_insect_engine.h"
#include "carried_items.h"
static AfSpiritCommon *spirit_common;
static const volatile u16 *spirit_status;
f32 af_carried_absf(f32 value) {return __builtin_fabsf(value);}

void af_carried_spirit_event_bind(AfSpiritCommon *common,const volatile u16 *status) {
    spirit_common=common;
    spirit_status=status;
}

AfSpiritCommon *af_carried_spirit_common(void) {return spirit_common;}

int af_carried_spirit_running(void) {
    /* Source ERROR masks RUN. Unbound/inactive events do not leave spirits
     * floating forever; the complete source lifecycle makes them escape. */
    return spirit_status && !(*spirit_status&0x20u) && (*spirit_status&0x10u)!=0;
}

void *af_carried_insect_light_context(GAME *game) {
    return (u8 *)game+0x1C60;
}

u32 af_carried_game_frame(const GAME *game) {
    /* GAME.frame_counter is distinct from GAME_PLAY.game_frame. */
    return *(const u32 *)((const u8 *)game+0xA0)*2u+af_insect_step();
}

int af_carried_creature_enabled(int type) {
    return type==aINS_INSECT_TYPE_SPIRIT && af_carried_quantity(ITM_SPIRIT0)==1;
}

void af_carried_insect_light_delete(aINS_INSECT_ACTOR *insect,GAME *game) {
    if (insect->type!=aINS_INSECT_TYPE_SPIRIT) return;
    if (insect->light_list)
        Global_light_list_delete(af_carried_insect_light_context(game),insect->light_list);
    insect->light_list=NULL;
    insect->light_flag=0;
}

void af_carried_insect_destruct(aINS_INSECT_ACTOR *insect,GAME *game) {
    /* The original clip destroy callback also runs during scene teardown;
     * handling lights only in the imported update loop would leak them. */
    if (insect->type==27 && insect->light_flag) {
        Global_light_list_delete(af_carried_insect_light_context(game),insect->light_list);
        insect->light_flag=0;
    } else af_carried_insect_light_delete(insect,game);
    insect->exist_flag=0;
    af_insect_pipe_destroy(game,insect->col_pipe);
}
