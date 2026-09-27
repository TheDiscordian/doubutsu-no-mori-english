/* Category dispatch and source-rate stepping. The controller hook must bypass
 * native movement/lifetime updates for these objects; originals stay native. */
#include "creature_insects.h"

int af_v3_insect_init(aINS_INSECT_ACTOR *insect,GAME *game) {
    static const mActor_proc init[8]={
        aITT_actor_init,aIKR_actor_init,aIAB_actor_init,aIMN_actor_init,
        aIDG_actor_init,aIMN_actor_init,aIDG_actor_init,aIKA_actor_init
    };
    if (!insect || (unsigned)insect->type-32u>=8) return 0;
    AfInsectExtra *extra=af_insect_extra(insect);
    if (!extra) return -1;
    extra->ut_x=extra->ut_z=-1;
    insect->move_proc=af_v3_insect_position;
    insect->life_time=216000;
    insect->alpha0=255;
    insect->insect_flags.bit_4=1;
    init[insect->type-32]((ACTOR *)insect,game);
    return 1;
}

void af_v3_insect_position(ACTOR *actor) {
    aINS_INSECT_ACTOR *insect=(aINS_INSECT_ACTOR *)actor;
    xyz_t_move(&actor->last_world_position,&actor->world.position);
    chase_f(&actor->speed,insect->target_speed,insect->speed_step*0.5f);
    actor->position_speed.x=actor->speed*sin_s(actor->world.angle.y);
    actor->position_speed.z=actor->speed*cos_s(actor->world.angle.y);
    if (insect->type!=aINS_INSECT_TYPE_MOSQUITO)
        chase_f(&actor->position_speed.y,actor->max_velocity_y,actor->gravity*0.5f);
    af_insect_position_integrate(actor);
}

int af_v3_insect_tick(aINS_INSECT_ACTOR *insect,GAME *game) {
    if (!insect || (unsigned)insect->type-32u>=8) return 0;
    ACTOR *actor=(ACTOR *)insect;
    if (!insect->move_proc || !actor->mv_proc || !af_insect_extra(insect)) return -1;
    /* GC bodies have both half-speed floating increments and 60-Hz integer
     * timers. Run two full ordered substeps, not blanket constant replacement. */
    for (unsigned step=0;step<2;step++) {
        if (!insect->exist_flag || insect->insect_flags.destruct) break;
        if (!insect->tools_actor.init_matrix) insect->move_proc(actor);
        af_insect_environment(insect,game);
        if (insect->life_time>0) insect->life_time--;
        if (!insect->life_time) {
            insect->insect_flags.bit_3=1;
            if (insect->alpha_time>0 && --insect->alpha_time<24) {
                insect->alpha0-=11;
                if (insect->alpha0<=0) {
                    insect->alpha0=0;
                    insect->insect_flags.destruct=1;
                }
            }
        }
        actor->mv_proc(actor,game);
    }
    return 1;
}
