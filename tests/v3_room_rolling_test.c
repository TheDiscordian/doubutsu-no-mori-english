#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_ROLLING
#include "../overlays/v3/room_rigs.c"
RoomRigTable af_v3_test_room_rigs;
RoomRigClip *af_v3_test_room_clip;
RoomMotionClip *af_v3_test_motion_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
static u8 object[4096];
static unsigned plays;
void *Lib_SegmentedToVirtual(void *p) { return object+(uptr)p-0x06000000u; }
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    (void)s;(void)a;(void)j;(void)m;memset(k,0,sizeof *k);
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *k,void *a,void *d) {
    (void)a;(void)d;k->start=1;k->end=k->duration=100;k->current.f=k->speed.f=1;k->mode=1;
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {(void)k;(void)a;(void)d;assert(0);}
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) { ++plays;k->current.f+=k->start<k->end ? k->speed.f : -k->speed.f;return 0; }
void *_Matrix_to_Mtx_new(void *p) { return p; }
void cKF_Si3_draw_R_SV(void *g,RoomKeyframe *k,void *m,void *b,void *a,void *d) {
    (void)g;(void)k;(void)m;(void)b;(void)a;(void)d;
}
int main(void) {
    af_v3_test_room_rigs=(RoomRigTable){ROOM_RIG_MAGIC,1,24,0,{{1030,4096,0x06000100,0x06000200,3,2,5,0,{.f=100},{.bits=0}}}};
    object[0x100]=3;object[0x101]=2;
    RoomMotionOwner owner={0};RoomMotionClip clip={&owner};
    struct { u8 first[16];RoomRig actor;u8 last[16]; } guarded;
    for (int alias=0;alias<2;++alias) for (int state=-1;state<18;++state)
        for (int direction=-1;direction<5;++direction) for (int present=0;present<3;++present) {
            memset(&guarded,0xA7,sizeof guarded);RoomRig *a=&guarded.actor;
            a->index=1030+alias*1024;a->position[0]=10;a->position[1]=3;a->position[2]=20;
            af_v3_room_rig_ct(a,object);
            assert(a->speed.f==10 && a->target.f==20 && a->keyframe.speed.f==0 && a->keyframe.current.f==1.5f);
            a->state=state;owner.direction=direction;clip.owner=present==2 ? &owner : NULL;
            af_v3_test_motion_clip=present ? &clip : NULL;
            a->position[0]+=6;a->position[2]+=8;
            /* Mirror the actual native owner: last_position already equals position. */
            memcpy((u8 *)a+0x14,a->position,12);
            unsigned before=plays;af_v3_room_rig_mv(a,0,0,object);
            int push=state==9 || state==11 || state==14 || state==1;
            int pull=state==10 || state==12 || state==2;
            int active=present==2 && (push || pull) && (direction==1 || direction==3);
            float speed=active ? (0.1f+5.0f/1.55f)*.5f : 0;
            int forward=push ? direction==3 : direction==1;
            assert(plays==before+2 && fabsf(a->keyframe.speed.f-speed)<0.000001f);
            if(active)assert(a->keyframe.start==(forward ? 1 : 100) && a->keyframe.end==(forward ? 100 : 1));
            assert(a->speed.f==16 && a->target.f==28);
            af_v3_room_rig_mv(a,0,0,object);
            assert(a->keyframe.speed.f==(active ? .05f : 0));
            for(unsigned i=0;i<16;++i)assert(guarded.first[i]==0xA7 && guarded.last[i]==0xA7);
            for(unsigned i=0;i<4;++i)assert(a->unused_morph[i]==0xA7);
    }
    puts("Rolling motion preserves native states, direction, displacement, donor timing, and instance guards");
}
