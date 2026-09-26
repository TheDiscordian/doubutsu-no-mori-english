/* Source-defined envelope and waveform evaluation, with N64 motor transport.
   The caller serializes entry/step/clear across game and controller threads.
   Transport may block on SI and must run outside that short critical section. */
#include "room_rumble.h"

static int valid_bank(const RoomRumbleBank *bank) {
    if (!bank || bank->magic!=ROOM_RUMBLE_MAGIC || bank->count!=ROOM_RUMBLE_WAVES ||
            bank->reserved || bank->bytes<sizeof(*bank) || bank->bytes>1024) return 0;
    for (u32 i=0;i<ROOM_RUMBLE_WAVES;++i) {
        const RoomRumbleWave *w=bank->waves+i;
        if (!w->count || w->count>60 || w->offset<sizeof(*bank) ||
                w->offset>bank->bytes || w->count>bank->bytes-w->offset) return 0;
    }
    return 1;
}

void af_v3_rumble_clear(RoomRumbleEnvelope *state) {
    if (!state) return;
    *state=(RoomRumbleEnvelope){0};
}

int af_v3_rumble_entry(RoomRumbleEnvelope *state,const RoomRumbleBank *bank,
        int percent,int attack,int sustain,int release,
        int attack_frames,int sustain_frames,int release_frames,float distance) {
    if (!state || !valid_bank(bank) || state->count>=ROOM_RUMBLE_ELEMENTS ||
            (unsigned)attack>=ROOM_RUMBLE_WAVES || (unsigned)sustain>=ROOM_RUMBLE_WAVES ||
            (unsigned)release>=ROOM_RUMBLE_WAVES || attack_frames<0 || sustain_frames<0 ||
            release_frames<0 || !(attack_frames || sustain_frames || release_frames) ||
            !(distance<640.0f)) return 0;
    RoomRumbleElement *e=state->elements+state->count;
    *e=(RoomRumbleElement){0};
    e->phases[0]=(RoomRumblePhase){attack,attack_frames,attack_frames>0 ? 1.0f/attack_frames : -1.0f};
    e->phases[1]=(RoomRumblePhase){sustain,sustain_frames,sustain_frames>0 ? 1.0f/sustain_frames : -1.0f};
    e->phases[2]=(RoomRumblePhase){release,release_frames,release_frames>0 ? 1.0f/release_frames : -1.0f};
    e->phase=attack_frames ? 0 : sustain_frames ? 1 : 2;
    e->intensity=percent*0.01f;
    e->attenuation=distance<41.0f ? 1.0f : 1.0f/(distance-40.0f);
    ++state->count;
    return 1;
}

u32 af_v3_rumble_step(RoomRumbleEnvelope *state,const RoomRumbleBank *bank) {
    if (!state) return 0;
    if (!valid_bank(bank) || state->count>ROOM_RUMBLE_ELEMENTS) {
        af_v3_rumble_clear(state);return 0;
    }
    for (u32 i=0;i<state->count;++i) {
        RoomRumbleElement *e=state->elements+i;
        if ((unsigned)e->phase>=3) { af_v3_rumble_clear(state);return 0; }
        const RoomRumblePhase *p=e->phases+e->phase;
        if ((unsigned)p->wave>=ROOM_RUMBLE_WAVES || p->frames<0 ||
                e->frame<0 || e->frame==0x7FFFFFFF ||
                (unsigned)e->cursor>=bank->waves[p->wave].count) {
            af_v3_rumble_clear(state);return 0;
        }
        const RoomRumbleWave *w=bank->waves+p->wave;
        ++e->frame;
        e->strength=e->intensity*e->attenuation;
        if (!e->phase) e->strength*=e->frame*p->step;
        else if (e->phase==2) e->strength*=p->step*(p->frames-e->frame);
        u32 command=((const u8 *)bank)[w->offset+e->cursor];
        if (command>2) { af_v3_rumble_clear(state);return 0; }
        if (command==1) {
            e->accumulated+=e->strength;
            command=e->accumulated>=1.0f;
            if (command) e->accumulated-=1.0f;
        }
        e->command=command;
        if (++e->cursor>=w->count) e->cursor=0;
        if (e->frame>=p->frames) { ++e->phase;e->frame=0;e->cursor=0; }
    }
    /* Source ordering removes completed elements before choosing the first
       strongest remaining element. Ties never replace the earlier request. */
    u32 remaining=0,command=0;
    float strongest=-10000.0f;
    for (u32 i=0;i<state->count;++i) {
        RoomRumbleElement e=state->elements[i];
        if (e.phase>=3) continue;
        state->elements[remaining++]=e;
        if (e.strength>strongest) { strongest=e.strength;command=e.command; }
    }
    for (u32 i=remaining;i<state->count;++i) state->elements[i]=(RoomRumbleElement){0};
    state->count=remaining;
    return command;
}

void af_v3_rumble_motor(RoomRumbleMotor *motor,void *queue,u32 command,
        u32 connected,u32 changed) {
    if (!motor || !queue) return;
    /* A replacement Pak is never written as though it were the old motor.
       osMotorInit must recognise it before any start/stop transfer. */
    if (!connected || changed) {
        motor->ready=0;motor->on=0;motor->retry=0;
        if (!connected) return;
    }
    u32 on=command==1; /* N64 has no separate active-braking command. */
    if (motor->retry) { --motor->retry;return; }
    if (!motor->ready) {
        if (!on && !motor->on) return;
        int result=af_rumble_motor_init(queue,motor->pfs,0);
        if (result) {
            /* A positively identified other accessory cannot be our still-on
               motor. Do not keep probing it after the request ends. */
            if (result==11) motor->on=0; /* PFS_ERR_DEVICE */
            motor->retry=30;return;
        }
        motor->ready=1;
        /* Always explicitly drive a newly detected device, even if its
           previous state is unknown. Successful recognition is not a start. */
        motor->on=2;
    }
    if (on==motor->on) return;
    if (af_rumble_motor_access(motor->pfs,on)) {
        /* A failed stop does not prove that the motor stopped. Retain an
           unknown state so idle retraces retry recognition and stopping. */
        motor->ready=0;motor->on=2;motor->retry=30;
    } else motor->on=on;
}
