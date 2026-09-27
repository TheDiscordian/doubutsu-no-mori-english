/* Ground colonies use native actor ownership; carried/released ants use the
 * shared insect controller. Behaviour follows the pinned complete aANT source.
 */
#include "creature_insect_colony.h"
static AfInsectInit pending;
static int pending_valid,pending_x,pending_z;
enum { WAIT,CAUGHT,DISAPPEAR };

void af_insect_colony_reset(void) {pending_valid=0;pending.game=0;}

int af_insect_make_colony(AfInsectInit *init,int x,int z) {
    if (!init || !init->game || init->type!=38 || x<0 || x>127 || z<0 || z>127) return 0;
    /* The source has one deferred request, replaced by another request. Keep
     * it outside the native 16-byte clip, which has no extension storage. */
    pending=*init;pending_x=x;pending_z=z;pending_valid=1;return 1;
}

void af_insect_controller_end(GAME *game) {
    if (pending_valid && pending.game==game) {
        ACTOR *actor=af_insect_create_actor((u8 *)game+0x1C78,game,AF_INSECT_COLONY_ID,
            pending.position.x,pending.position.y,pending.position.z,0,0,0,
            (s8)pending_x,(s8)pending_z,-1,0,-1,-1,-1);
        if (actor) af_insect_colony_reset(); /* Allocation failure retries next tick. */
    }
    af_v3_insect_events_reset();
}

int af_insect_colony_present(int x,int z,GAME *game) {
    if (!game) return 0;
    for (const ACTOR *a=((AfInsectGameView *)game)->lists[AF_INSECT_COLONY_PART].head;
            a;a=a->next_actor)
        if (a->id==AF_INSECT_COLONY_ID && a->block_x==x && a->block_z==z) return 1;
    return 0;
}

int af_insect_net_index(const ACTOR *label,int type,int index) {
    if (type==0 && index>=0) return index;
    /* Native type 1 is a bee swarm. Only our distinct colony profile is an
     * ant; native bees keep index 8. This also covers the frame before the
     * colony hands its label to the newly created carried ant. */
    if (type==1 && label && label->id==AF_INSECT_COLONY_ID) return 38;
    return 8;
}

static void action(AfInsectColony *a,int next) {
    a->action=next;
    if (next==CAUGHT) a->failures=0;
    if (next==DISAPPEAR) a->actor.shape_info.rotation.x=a->actor.shape_info.rotation.z=0;
}

static void constructor(ACTOR *actor,GAME *game) {
    (void)game;
    AfInsectColony *a=(AfInsectColony *)actor;
    a->foreground=mFI_GetUnitFG(actor->world.position);
    actor->home.position.y=actor->world.position.y=
        mCoBG_GetBgY_OnlyCenter_FromWpos(actor->world.position,-10.0f);
    actor->shape_info.rotation.x=0x2000;
    a->alpha=255;action(a,WAIT);
}

static void destructor(ACTOR *actor,GAME *game) {
    /* If carried-slot creation failed, do not leave a freed colony pointer in
     * the native player. Successful transfers already point to the single ant. */
    PLAYER_ACTOR *player=af_insect_player(game);
    if (player && mPlib_Get_item_net_catch_label()==(uintptr_t)actor)
        af_insect_net_change(player,0,0);
}

static void move(ACTOR *actor,GAME *game) {
    AfInsectColony *a=(AfInsectColony *)actor;
    if (!(actor->state_bitfield&0x40u) && !af_insect_same_block(actor,game)) {
        af_insect_delete_actor(actor);return;
    }
    if (actor->world.position.x<0.0f && actor->world.position.z<0.0f) return;
    PLAYER_ACTOR *player=af_insect_player(game);
    /* Native actor dispatch has already updated distance. Run source actions
     * at 60 Hz, but register only once in the native eight-request catch list. */
    int registered=0;
    for (unsigned half=0;half<2;half++) {
        if (a->action==WAIT) {
            if (!a->foreground || (*a->foreground!=0x2806 && *a->foreground!=0x2F03))
                action(a,DISAPPEAR);
            else if (player && mPlib_Get_item_net_catch_label()==(uintptr_t)actor) action(a,CAUGHT);
            else if (player && !registered) {
                xyz_t stop;
                if ((af_insect_net_swing(player,game)>0.0f || mPlib_Check_StopNet(&stop)) &&
                        actor->player_distance_xz<40.0f)
                    af_insect_net_force(player,game,actor,1);
                else af_insect_net_request(player,game,actor,1,24.0f);
                registered=1;
            }
        } else if (a->action==CAUGHT) {
            AfInsectInit init={38,actor->world.position,0,game};
            a->insect=af_insect_native_clip && af_insect_native_clip->make ?
                af_insect_native_clip->make(&init,1):0;
            if (a->insect) {
                if (player && af_insect_net_change(player,a->insect,0)) action(a,DISAPPEAR);
            } else if (++a->failures>1) action(a,DISAPPEAR);
        } else if (a->action==DISAPPEAR) {
            a->alpha-=15;
            if (a->alpha<0) {a->alpha=0;af_insect_delete_actor(actor);break;}
            chase_f(&actor->scale.x,0.01f,0.05f);
            actor->scale.y=actor->scale.z=actor->scale.x;
        }
    }
    af_insect_world_to_eye(actor,0.0f);
}

const AfInsectProfile af_insect_colony_profile={
    AF_INSECT_COLONY_ID,AF_INSECT_COLONY_PART,0,0x10,0,3,sizeof(AfInsectColony),
    constructor,destructor,move,af_insect_colony_draw,0
};
