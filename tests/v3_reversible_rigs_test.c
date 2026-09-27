#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_reversible.c"

static unsigned native_plays,donor_plays,native_sounds,donor_sounds,comparisons;
static s16 *native_joint,*native_morph;
static unsigned joint_count=11;
static RoomRig *native_actor;
static int skeleton_token,animation_token;
static int step(float start,float end,float speed,float *current) {
    if (start>end) {*current-=speed;if (*current<=end) {*current=end;return 1;}}
    else {*current+=speed;if (*current>=end) {*current=end;return 1;}}
    return 0;
}
static void fill(s16 *joint,s16 *morph,float frame) {
    for (unsigned i=0;i<3*(joint_count+1);++i) {joint[i]=(s16)(frame+i);morph[i]=(s16)(frame-i);}
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *key,void *skeleton,void *animation,void *joint,void *morph) {
    assert(skeleton==&skeleton_token && animation==&animation_token);
    native_joint=joint;native_morph=morph;memset(key,0,sizeof(*key));
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *key,void *animation,void *unused) {
    assert(animation==&animation_token && !unused);key->current.f=1;key->speed.f=1;key->start=1;key->end=46;
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *key) {
    ++native_plays;fill(native_joint,native_morph,key->current.f);
    return step(key->start,key->end,key->speed.f,&key->current.f);
}
void sAdo_OngenTrgStart(u32 sound,float *position) {
    assert(sound==0x7A && position==native_actor->position);++native_sounds;
}

/* Use the actual donor lifecycle definitions. Only the native keyframe engine
   and audio are stubbed; comparing these stubs does not test native synthesis. */
typedef struct {s16 x,y,z;} s_xyz;
typedef struct {float x,y,z;} xyz_t;
typedef struct {struct {float start_frame,end_frame,speed,current_frame;} frame_control;
    s16 *joint,*morph;} cKF_SkeletonInfo_R_c;
typedef struct {s16 frames;} cKF_Animation_R_c;
typedef int cKF_Skeleton_R_c;
typedef struct {cKF_SkeletonInfo_R_c keyframe;s_xyz joint[17],morph[17];
    s16 dynamic_work_s[1];u8 switch_bit,switch_changed_flag;xyz_t position;} FTR_ACTOR;
typedef int ACTOR;
typedef int GAME;
#define TRUE 1
#define FALSE 0
#define cKF_STATE_STOPPED 1
static cKF_Animation_R_c cKF_ba_r_int_ike_jny_rosia01={46};
static cKF_Skeleton_R_c cKF_bs_r_int_ike_jny_rosia01;
static FTR_ACTOR *donor_actor;
static void donor_ct(cKF_SkeletonInfo_R_c *key,void *skeleton,void *animation,void *joint,void *morph) {
    assert(skeleton==&cKF_bs_r_int_ike_jny_rosia01 && animation==&cKF_ba_r_int_ike_jny_rosia01);
    memset(key,0,sizeof(*key));key->joint=joint;key->morph=morph;
}
static void donor_init(cKF_SkeletonInfo_R_c *key,void *animation,void *unused) {
    assert(animation==&cKF_ba_r_int_ike_jny_rosia01 && !unused);
    key->frame_control.current_frame=1;key->frame_control.speed=.5f;
    key->frame_control.start_frame=1;key->frame_control.end_frame=46;
}
static int donor_play(cKF_SkeletonInfo_R_c *key) {
    ++donor_plays;fill(key->joint,key->morph,key->frame_control.current_frame);
    return step(key->frame_control.start_frame,key->frame_control.end_frame,
        key->frame_control.speed,&key->frame_control.current_frame);
}
static void donor_trigger(u32 sound,xyz_t *position) {
    assert(sound==0x7A && position==&donor_actor->position);++donor_sounds;
}
#define cKF_SkeletonInfo_R_ct donor_ct
#define cKF_SkeletonInfo_R_init_standard_stop donor_init
#define cKF_SkeletonInfo_R_play donor_play
#define sAdo_OngenTrgStart donor_trigger
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wparentheses"
#include "donor_reversible.inc"
#pragma GCC diagnostic pop
#undef cKF_SkeletonInfo_R_ct
#undef cKF_SkeletonInfo_R_init_standard_stop
#undef cKF_SkeletonInfo_R_play
#undef sAdo_OngenTrgStart

static void compare(RoomRig *actor,FTR_ACTOR *donor) {
    RoomReversible *w=work(actor);RoomKeyframe *key=&actor->keyframe;
    assert(key->start==donor->keyframe.frame_control.start_frame);
    assert(key->end==donor->keyframe.frame_control.end_frame);
    assert(key->speed.f==donor->keyframe.frame_control.speed);
    assert(key->current.f==donor->keyframe.frame_control.current_frame);
    assert(w->state==donor->dynamic_work_s[0] && actor->switched==donor->switch_bit);
    assert(native_plays==donor_plays && native_sounds==donor_sounds);
    assert(!memcmp(w->joint,donor->joint,3*(joint_count+1)*2));
    assert(!memcmp(w->morph,donor->morph,3*(joint_count+1)*2));
    ++comparisons;
}
int main(void) {
    struct {u8 front[16];RoomRig actor;u8 back[16];} guard;
    unsigned switches[]={0,1,2,255};
    for (unsigned initial=0;initial<4;++initial) {
        memset(&guard,0xA7,sizeof(guard));RoomRig *actor=&guard.actor;native_actor=actor;
        FTR_ACTOR donor={0};donor_actor=&donor;
        actor->switched=donor.switch_bit=switches[initial];RoomRig before=*actor;
        af_v3_room_reverse_ct(actor,&skeleton_token,&animation_token,46);
        aIkeJnyRosia01_ct(&donor,NULL);compare(actor,&donor);
        for (unsigned frame=0;frame<360;++frame) {
            /* Presses during motion, both directions, repeated idle presses,
               all sixteen native states, and any-nonzero pulse values. */
            actor->state=(s16)(frame%16);
            for (unsigned tick=0;tick<2;++tick) {
                int pressed=!tick && (frame%61==0 || (frame>=150 && frame<164)) ? (int)(frame+1) : 0;
                donor.switch_changed_flag=(u8)pressed;
                af_v3_room_reverse_step(actor,46,0x7A,(u8)pressed);
                aIkeJnyRosia01_mv(&donor,NULL,NULL,NULL);compare(actor,&donor);
            }
            /* Actual drawer uses one matrix per displayed shape, not per joint.
               Even six matrices at either parity must preserve all large work. */
            RoomReversible saved=*work(actor);
            memset(actor->matrices[frame&1],0x22,6*64);
            assert(!memcmp(&saved,work(actor),sizeof(saved)));
            af_v3_room_reverse_dt(actor);aIkeJnyRosia01_dt(&donor,NULL);compare(actor,&donor);
            for (unsigned i=0;i<16;++i)assert(guard.front[i]==0xA7 && guard.back[i]==0xA7);
        }
        assert(!memcmp(actor->joint,before.joint,sizeof(actor->joint)));
        assert(!memcmp(actor->morph,before.morph,sizeof(actor->morph)));
        assert(!memcmp(actor->tail,before.tail,sizeof(actor->tail)));
        u8 *spare=(u8 *)work(actor)+sizeof(RoomReversible);
        for (u8 *p=spare;p<actor->matrices[1][0];++p)assert(*p==0xA7);
        assert(native_sounds>0);
    }
    printf("%u donor reversible comparisons; full hidden joints, idle-only switching, sound, persistence, and bounds pass\n",comparisons);
}
