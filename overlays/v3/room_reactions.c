#include "room_reactions.h"

/* This state has its own reservation after the immutable CRC-checked packet.
   The packet loader clears its magic before publishing its ready/cache word.
   No saved, Controller Pak, native room, or actor allocation is enlarged. */
static RoomReactionState *state_locked(void) {
    RoomReactionState *s=room_reaction_state;
    if (s->magic!=ROOM_REACTION_STATE_MAGIC) {
        *s=(RoomReactionState){0};
        s->motor.on=2; /* Recognise and stop a motor left on across a reset. */
        s->magic=ROOM_REACTION_STATE_MAGIC;
    }
    return s;
}

void af_v3_room_reaction_ct(RoomRig *actor) {
    if (!actor) return;
    actor->joint[0][0]=0; /* donor dynamic_work_s[1], face */
    actor->joint[0][1]=0; /* donor dynamic_work_s[0], countdown */
}

void af_v3_room_reaction_mv(RoomRig *actor,void *room,RoomRigGame *game) {
    if (!actor || !room || !game) return; /* Catalogue previews never react. */
    u8 *player=af_reaction_player(game);
    if (!player) return;
    u32 mask=af_rumble_mask(1);
    RoomReactionState *s=state_locked();
    if (s->owner!=(uptr)room) {
        s->owner=(uptr)room;s->pending=0;
        af_v3_rumble_clear(&s->envelope);
    }
    s->heartbeat=s->tick;
    s16 *face=&actor->joint[0][0],*countdown=&actor->joint[0][1];
    for (u32 step=0;step<2;++step) {
        if (!*face) {
            if (!step && actor->changed) {
                s->angle=*(s16 *)(player+0xDE);s->pending=1;
                *countdown=50;*face=1;
            }
        } else {
            /* Normal constructed state is 0..50. A corrupt counter must not
               overflow signed arithmetic or escape the bounded reaction. */
            if (*countdown<0 || *countdown>50) { *countdown=0;*face=0;continue; }
            --*countdown;
            if (*countdown==20)
                af_v3_rumble_entry(&s->envelope,&af_v3_rumble_waves,100,1,1,13,0,7,7,0.0f);
            if (*countdown<0) { *countdown=0;*face=0; }
        }
    }
    int pending=s->pending;
    s16 angle=s->angle;
    if (pending && *(int *)(player+0xCF0)==0x61) { s->pending=0;pending=0; }
    af_rumble_mask(mask);
    /* Preserve the request until the player's priority system accepts shock.
       Native shock timers count 30-Hz updates rather than the donor's 60 Hz. */
    if (pending) af_reaction_shock(game,10.0f,angle,0);
}

void af_v3_room_rumble_retrace(void *queue,const u8 *pad) {
    if (!queue || !pad) return;
    u32 mask=af_rumble_mask(1);
    RoomReactionState *s=state_locked();
    ++s->tick;
    /* The normal item callback refreshes this at 30 Hz. Stop during loading,
       paused gameplay, scene exits, or pre-NMI rather than leaving a latch on.
       The elapsed comparison remains valid across unsigned tick rollover. */
    if (pad[0x47E] || s->tick-s->heartbeat>6u) af_v3_rumble_clear(&s->envelope);
    u32 command=af_v3_rumble_step(&s->envelope,&af_v3_rumble_waves);
    af_rumble_mask(mask);
    /* No interrupt mask is held across blocking libultra SI transfers. The
       call site owns padmgr's serial queue after the input/status reads. */
    u32 connected=pad[0x2C9]==1 && !pad[0x17] && (pad[0x16]&1u);
    af_v3_rumble_motor(&s->motor,queue,command,connected,pad[0x16]&2u);
}
