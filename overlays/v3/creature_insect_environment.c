/* One environment/update/catch/destruction path for all eight added insects.
 * Ordinary species return to the native slot loop without touching their state.
 */
#include "creature_insect_engine.h"

PLAYER_ACTOR *af_insect_player(GAME *game) {return af_insect_native_player(game);}
int af_insect_same_block(const ACTOR *actor,const GAME *game) {
    const AfInsectGameView *view=(const AfInsectGameView *)game;
    return actor->block_x==view->acre_x && actor->block_z==view->acre_z;
}
u32 af_insect_source_frame(const GAME *game) {
    return ((const AfInsectGameView *)game)->frame*2u+af_insect_step();
}

void af_insect_position_integrate(ACTOR *actor) {
    AfInsectGameView *game=(AfInsectGameView *)af_insect_game;
    /* Native nature callbacks and object displacement run at native rate.
     * Apply nature once, and divide collision displacement over both substeps.
     * Never change the shared engine frame multiplier around a callback. */
    if (!af_insect_step()) game->nature(actor);
    const xyz_t *push=&actor->status_data.displacement;
    actor->world.position.x+=(actor->position_speed.x+push->x)*0.5f;
    actor->world.position.y+=(actor->position_speed.y+push->y)*0.5f;
    actor->world.position.z+=(actor->position_speed.z+push->z)*0.5f;
}

static f32 stress(const ACTOR *insect,const AfInsectGameView *game) {
    static const f32 rates[]={0.3f,1.0f,2.0f,5.0f,10.0f};
    f32 result=0.0f;
    /* All added entries have zero source catch-distance adjustment. Do not
     * index the old 32-species native sensitivity table with a new identity. */
    for (unsigned part=1;part<=4;part++) {
        for (ACTOR *a=game->lists[part].head;a;a=a->next_actor) {
            f32 distance=af_insect_distance(&insect->world.position,&a->world.position);
            if (distance<120.0f) {
                f32 beyond=distance-40.0f;
                if (beyond<0.0f) beyond=0.0f;
                int index=(int)(80.0f-beyond)/20;
                if (index>4) index=4;
                /* Other actors moved for a whole native frame, not one GC
                 * substep. Their displacement needs the same rate conversion. */
                f32 movement=af_insect_distance_xz(&a->world.position,&a->last_world_position)*0.5f;
                f32 value=movement*rates[index];
                if (value>result) result=value;
            }
        }
    }
    return result;
}

void af_insect_environment(aINS_INSECT_ACTOR *insect,GAME *game) {
    ACTOR *actor=(ACTOR *)insect;
    PLAYER_ACTOR *player=af_insect_player(game);
    if (player) {
        const xyz_t *pos=&player->actor_class.world.position;
        f32 xz=af_insect_distance_xz(&actor->world.position,pos);
        f32 y=pos->y-actor->world.position.y;
        actor->player_distance_xz=xz;actor->player_distance_y=y;
        actor->player_distance=SQ(xz)+SQ(y);
        actor->player_angle_y=af_insect_angle(&actor->world.position,pos);
    } else {
        actor->player_distance=actor->player_distance_xz=actor->player_distance_y=0;
        actor->player_angle_y=0;
    }
    AfInsectExtra *extra=af_insect_extra(insect);
    if (insect->bg_type==1 || insect->bg_type==2)
        af_insect_native_bg(NULL,actor,extra->bg_range,insect->bg_height,insect->bg_type==1,0,1);
    else if (insect->bg_type==3 || insect->bg_type==4)
        af_insect_directed_bg(actor,extra->bg_range,insect->bg_height,insect->bg_type==3,
                             extra->ut_x,extra->ut_z);
    if (!insect->insect_flags.bit_2 && insect->insect_flags.bit_4)
        af_insect_acre_wall(actor,extra->bg_range);
    f32 value=stress(actor,(const AfInsectGameView *)game);
    insect->patience+=F32_IS_ZERO(value)?-0.5f:value*0.5f;
    if (insect->patience<0.0f) insect->patience=0.0f;
    if (insect->patience>100.0f) insect->patience=100.0f;
}

static void destruct(aINS_INSECT_ACTOR *insect,GAME *game) {
    if (!insect->exist_flag) return;
    insect->exist_flag=0;
#ifdef AF_INSECT_CARRIED
    af_carried_insect_light_delete(insect,game);
#endif
    af_insect_pipe_destroy(game,insect->col_pipe);
}

/* Hook before the old slot update/cull: 0 = execute original instructions;
 * 1 = this added slot is handled; -1 = invalid added-slot ownership. */
int af_v3_insect_slot(aINS_INSECT_ACTOR *insect,GAME *game) {
    if (!insect || (unsigned)insect->type-32u>=AF_IMPORTED_INSECT_COUNT) return 0;
    if (!game || !af_insect_extra(insect)) return -1;
    if (insect->exist_flag!=1) return 1;
    ACTOR *actor=(ACTOR *)insect;
    actor->state_bitfield&=~0x01000000u;
    if (actor->state_bitfield&0x50u) {
        int result=af_v3_insect_tick(insect,game);
        if (result!=1) return -1;
        af_insect_world_to_eye(actor,0.0f);
        PLAYER_ACTOR *player=af_insect_player(game);
        f32 range=af_v3_insect_catch_range(insect);
        if (player && range>0.008f) af_insect_register_catch(player,game,actor,range);
    }
    af_insect_project(((AfInsectGameView *)game)->projection,&actor->world.position,
                      &actor->camera_position,&actor->camera_w);
    int caught=mPlib_Get_item_net_catch_label()==(uintptr_t)actor;
    if (insect->insect_flags.destruct && !caught) {
        destruct(insect,game);return 1;
    }
    if (af_insect_visible(actor)) actor->state_bitfield|=0x40u;
    else if (!caught) {
        if (actor->actor_specific==1 ||
                (actor->player_distance_xz>600.0f && !af_insect_same_block(actor,game)))
            destruct(insect,game);
        else actor->state_bitfield&=~0x40u;
    }
    return 1;
}
