/* Parent-sensitive joint motion; native owner/attachment binding is separate. */
#include "room_needle.h"
extern float sin_s(s16);
extern float add_calc(float *,float,float,float,float);

void af_v3_room_needle_ct(RoomNeedle *work,RoomKeyframe *key,s16 state) {
    *work=(RoomNeedle){.previous_state=state};
    key->speed.f=.5f;
    cKF_SkeletonInfo_R_play(key);
    key->speed.f=0;
}

static void rotation_kick(RoomNeedle *work,s16 state) {
    /* The N64 enum differs from the donor: native 3 increases the room angle
       (donor LROTATE), native 4 decreases it (donor RROTATE). */
    if (state==7 || state==8) work->rotation_ticks=0;
    else if (state==3 || state==4) {
        work->rotation_ticks=(s16)((u16)work->rotation_ticks+1u);
        if (work->rotation_ticks==8) {
            work->phase=0;
            float previous=work->amplitude*sin_s(work->phase);
            if (state==3) {
                work->amplitude=previous-45.0f;
                if (work->amplitude< -45.0f) work->amplitude=-45.0f;
            } else {
                work->amplitude=45.0f+previous;
                if (work->amplitude>45.0f) work->amplitude=45.0f;
            }
        }
    }
}

void af_v3_room_needle_step(RoomNeedle *work,RoomKeyframe *key,s16 state,
                           const s16 *parent_state,s16 phase_adjust,s16 decay_adjust) {
    /* Run twice per native update, preserving source ordering when both the
       object and its parent contribute to the same rotation counter. */
    rotation_kick(work,state);
    if (parent_state) rotation_kick(work,*parent_state);
    cKF_SkeletonInfo_R_play(key);
    float decay=.2f+.01f*decay_adjust;
    if (work->amplitude>0) {
        work->amplitude-=decay;
        if (work->amplitude<0) work->amplitude=0;
    } else if (work->amplitude<0) {
        work->amplitude+=decay;
        if (work->amplitude>0) work->amplitude=0;
    }
    if (work->amplitude!=0)
        work->phase=(s16)((u16)work->phase+0x320u+(u16)phase_adjust);
    else work->phase=0;
    add_calc(&work->smoothed,work->amplitude*sin_s(work->phase),.3f,100.0f,.0001f);
    work->previous_state=state;
}

s16 af_v3_room_needle_angle(const RoomNeedle *work,s16 joint,s16 own_angle,s16 parent_offset) {
    /* Keep both source multiplications and truncation, including angle wrap. */
    int offset=10430.378f*(.017453292f*work->smoothed);
    return (s16)((int)joint-own_angle-parent_offset-offset);
}
