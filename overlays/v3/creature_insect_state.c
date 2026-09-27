/* Per-controller donor-only fields and the shared player-action event latch.
 * Constructor/destructor hooks own this state; no saved data changes here.
 */
#include "creature_insects.h"
static AfInsectController *controller;
static AfInsectExtra extra[AF_INSECT_SLOTS];
static AfInsectEvents events;
static unsigned substep;

void af_insect_begin_step(unsigned step) {substep=step&1u;}
unsigned af_insect_step(void) {return substep;}

void af_v3_insect_events_reset(void) {
    substep=0;
    events.pl_action=aINS_PL_ACT_NONE;
    events.pl_action_ut_x=events.pl_action_ut_z=-1;
    events.position_move_proc=af_v3_insect_position;
}

void af_v3_insect_bind_controller(AfInsectController *owner) {
    controller=owner;
    for (unsigned i=0;i<AF_INSECT_SLOTS;i++) extra[i]=(AfInsectExtra){-1,-1,12.0f};
    af_v3_insect_events_reset();
}

void af_v3_insect_unbind_controller(AfInsectController *owner) {
    if (controller==owner) af_v3_insect_bind_controller(NULL);
}

AfInsectExtra *af_insect_extra(aINS_INSECT_ACTOR *insect) {
    if (controller)
        for (unsigned i=0;i<AF_INSECT_SLOTS;i++) if (insect==controller->insects+i) return extra+i;
    return NULL;
}

int af_insect_occupied_acre(int x,int z) {
    if (controller) for (unsigned i=0;i<AF_INSECT_WILD_SLOTS;i++) {
        const aINS_INSECT_ACTOR *insect=controller->insects+i;
        const ACTOR *actor=&insect->tools_actor.actor_class;
        if (insect->exist_flag==1 && actor->block_x==x && actor->block_z==z) return 1;
    }
    return 0;
}

const AfInsectEvents *af_insect_events(void) {return &events;}

/* The event stays available to all slots and both substeps. Reset once after
 * the complete controller update, never after one insect consumes the event. */
int af_v3_insect_event(int action,int x,int z) {
    if (!controller || action<1 || action>aINS_PL_ACT_SHAKE_TREE ||
            x<0 || z<0 || x>32767 || z>32767) return 0;
    events.pl_action=action;events.pl_action_ut_x=x;events.pl_action_ut_z=z;
    return 1;
}

float af_v3_insect_catch_range(const aINS_INSECT_ACTOR *insect) {
    if (!insect || (unsigned)insect->type-32u>=8) return -1.0f;
    /* All eight use the donor's ordinary 8-unit range. A source action sets
     * bit_1 while uncatchable (hidden tree insects, escape, dive, or drowning). */
    return insect->insect_flags.bit_1?0.0f:8.0f;
}
