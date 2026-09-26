#ifndef AF_V3_ROOM_MOTION_H
#define AF_V3_ROOM_MOTION_H
/* Native state-table identities, not the GameCube enum values. */
static inline int room_push_state(int state) {
    return state==9 || state==11 || state==14 || state==1;
}
static inline int room_pull_state(int state) {
    return state==10 || state==12 || state==2;
}
static inline int room_transition_state(int state) {
    return state==5 || state==6 || state==13 || state==15;
}
#endif
