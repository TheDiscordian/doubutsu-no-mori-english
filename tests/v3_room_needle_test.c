#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_needle.c"

static unsigned native_plays,donor_plays,comparisons;
int cKF_SkeletonInfo_R_play(RoomKeyframe *key) {
    ++native_plays;key->current.f+=key->speed.f;return 0;
}
float sin_s(s16 angle) {
    return sinf((float)angle*(6.2831853071795864769f/65536.0f));
}

/* Compile the actual donor functions, not a second handwritten motion model.
   Graphics submission is outside this test; DrawBefore's arithmetic is real. */
typedef float f32;
typedef struct { float x,y,z; } xyz_t;
typedef struct { s16 x,y,z; } s_xyz;
typedef struct { struct {float speed;} frame_control;float frame; } cKF_SkeletonInfo_R_c;
typedef int cKF_Animation_R_c;
typedef int cKF_Skeleton_R_c;
typedef int GAME;
typedef int Gfx;
typedef struct {
    int id;
    s16 state,s_angle_y,dynamic_work_s[3];
    float dynamic_work_f[2];
    cKF_SkeletonInfo_R_c keyframe;
    s_xyz joint[5],morph[5];
} FTR_ACTOR;
typedef struct {
    struct {int ftrID;s16 angle_y;struct {int ftr_ID;} fit_ftr_table[4];} parent_ftr;
} MY_ROOM_ACTOR;
typedef MY_ROOM_ACTOR ACTOR;
static struct {FTR_ACTOR *ftr_actor_list;} l_aMR_work;
typedef struct {ACTOR *my_room_actor_p;} TestClip;
static struct {TestClip *my_room_clip;} clip;
static s16 debug_regs[82];
#define GETREG(group,index) debug_regs[index]
#define Common_Get(field) field
#define FALSE 0
#define TRUE 1
enum {aFTR_STATE_STOP,aFTR_STATE_WAIT_PUSH,aFTR_STATE_WAIT_PUSH2,aFTR_STATE_WAIT_PUSH3,
    aFTR_STATE_PUSH,aFTR_STATE_WAIT_PULL,aFTR_STATE_WAIT_PULL2,aFTR_STATE_PULL,
    aFTR_STATE_WAIT_LROTATE,aFTR_STATE_LROTATE,aFTR_STATE_WAIT_RROTATE,aFTR_STATE_RROTATE,
    aFTR_STATE_BIRTH_WAIT,aFTR_STATE_BIRTH,aFTR_STATE_BYE,aFTR_STATE_DEATH};
cKF_Animation_R_c cKF_ba_r_int_ike_jny_houi01;
cKF_Skeleton_R_c cKF_bs_r_int_ike_jny_houi01;
static void donor_ct(cKF_SkeletonInfo_R_c *key,void *skeleton,void *motion,void *joint,void *morph) {
    assert(skeleton && motion && joint && morph);memset(key,0,sizeof(*key));key->frame=1;
}
static void donor_init(cKF_SkeletonInfo_R_c *key,void *motion,void *unused) {
    assert(motion && !unused);key->frame_control.speed=.5f;
}
static int donor_play(cKF_SkeletonInfo_R_c *key) {
    ++donor_plays;key->frame+=key->frame_control.speed;return 0;
}
#define cKF_SkeletonInfo_R_ct donor_ct
#define cKF_SkeletonInfo_R_init_standard_stop donor_init
#define cKF_SkeletonInfo_R_play donor_play
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#include "donor_needle.inc"
#pragma GCC diagnostic pop
#undef cKF_SkeletonInfo_R_ct
#undef cKF_SkeletonInfo_R_init_standard_stop
#undef cKF_SkeletonInfo_R_play

static s16 donor_state(int native) {
    static const s16 map[16]={0,4,7,9,11,13,14,10,8,1,5,2,6,15,3,12};
    assert(native>=0 && native<16);return map[native];
}
static void compare(RoomNeedle *work,FTR_ACTOR *donor,RoomKeyframe *key,MY_ROOM_ACTOR *owner,
                    int self_state,int parent_state,int joint,int angle,int parent_angle) {
    donor->state=donor_state(self_state);donor->s_angle_y=(s16)angle;
    FTR_ACTOR *parent=parent_state<0 ? NULL : aMR_GetParentFactor(donor,owner);
    s16 native_parent=(s16)parent_state;
    if(parent) {parent->state=donor_state(parent_state);parent->s_angle_y=(s16)parent_angle;}
    unsigned plays=native_plays;
    af_v3_room_needle_step(work,key,(s16)self_state,parent ? &native_parent : NULL,
        debug_regs[80],debug_regs[81]);
    fIJHOUI_mv(donor,owner,NULL,NULL);
    assert(native_plays==plays+1 && native_plays==donor_plays);
    assert(work->amplitude==donor->dynamic_work_f[0]);
    assert(work->smoothed==donor->dynamic_work_f[1]);
    assert(work->rotation_ticks==donor->dynamic_work_s[1]);
    assert(work->phase==donor->dynamic_work_s[2]);
    assert(donor_state(work->previous_state)==donor->dynamic_work_s[0]);
    assert(key->speed.f==donor->keyframe.frame_control.speed && key->current.f==donor->keyframe.frame);
    s_xyz rot={231,(s16)joint,-719};
    int offset=parent ? aMR_GetParentAngleOffset(donor,owner) : 0;
    s16 actual=af_v3_room_needle_angle(work,rot.y,(s16)angle,(s16)offset);
    assert(fIJHOUI_DrawBefore(NULL,&donor->keyframe,3,NULL,NULL,donor,&rot,NULL)==1);
    assert(rot.x==231 && rot.z==-719 && actual==rot.y);
    s_xyz unchanged=rot;
    assert(fIJHOUI_DrawBefore(NULL,&donor->keyframe,2,NULL,NULL,donor,&rot,NULL)==1);
    assert(!memcmp(&rot,&unchanged,sizeof(rot)));
    ++comparisons;
}

int main(void) {
    struct {u32 front[4];RoomNeedle work;u32 back[4];} guarded;
    FTR_ACTOR actors[5];MY_ROOM_ACTOR owner;
    TestClip owner_clip={&owner};clip.my_room_clip=&owner_clip;
    l_aMR_work.ftr_actor_list=actors;
    for(unsigned child=0;child<4;++child) for(int direction=3;direction<=4;++direction) {
        memset(&guarded,0x6B,sizeof(guarded));memset(actors,0,sizeof(actors));memset(&owner,0,sizeof(owner));
        RoomNeedle *work=&guarded.work;RoomKeyframe key={.current={.f=1}};
        FTR_ACTOR *donor=actors+child+1;donor->id=(int)child+1;
        owner.parent_ftr.ftrID=0;owner.parent_ftr.angle_y=32760;
        for(unsigned i=0;i<4;++i) owner.parent_ftr.fit_ftr_table[i].ftr_ID=(int)i+1;
        af_v3_room_needle_ct(work,&key,0);fIJHOUI_ct(donor,NULL);
        assert(key.current.f==1.5f && work->amplitude==0 && work->smoothed==0);
        /* Self rotation; then a parent's rotation, wrap, both contributors,
           interrupted waits, counter wrap, debug controls, and full decay. */
        for(unsigned frame=0;frame<1200;++frame) {
            int self=0,parent=0;
            if(frame==0)self=direction==3 ? 8 : 7;
            if(frame>0 && frame<20)self=direction;
            if(frame==160)parent=direction==3 ? 8 : 7;
            if(frame>160 && frame<180)parent=direction;
            if(frame==320)self=parent=8;
            if(frame>320 && frame<340)self=parent=direction;
            if(frame==480) {work->rotation_ticks=32767;donor->dynamic_work_s[1]=32767;self=direction;}
            if(frame>=600 && frame<616)self=(int)(frame-600);
            debug_regs[80]=frame>=640 && frame<720 ? -90 : 0;
            debug_regs[81]=frame>=640 && frame<720 ? 7 : 0;
            for(unsigned tick=0;tick<2;++tick)
                compare(work,donor,&key,&owner,self,parent,(int)(frame*97),
                    (int)(frame*311),(int)(frame*503));
            if(frame==4) assert(direction==3 ? work->amplitude<0 : work->amplitude>0);
            for(unsigned i=0;i<4;++i)assert(guarded.front[i]==0x6B6B6B6Bu && guarded.back[i]==0x6B6B6B6Bu);
        }
        assert(work->amplitude==0 && work->smoothed==0 && work->phase==0);
        /* Genuine no-parent cases: inactive owner, unrelated child, no room,
           no clip, and a clip without a room. None is an installed stub. */
        owner.parent_ftr.ftrID=-1;
        compare(work,donor,&key,&owner,8,-1,110,-230,0);
        owner.parent_ftr.ftrID=0;donor->id=99;
        compare(work,donor,&key,&owner,3,-1,-310,420,0);
        owner_clip.my_room_actor_p=NULL;
        compare(work,donor,&key,NULL,4,-1,170,-390,0);
        clip.my_room_clip=NULL;
        compare(work,donor,&key,NULL,0,-1,0,-32768,0);
        clip.my_room_clip=&owner_clip;
        owner_clip.my_room_actor_p=&owner;
    }
    printf("%u donor needle comparisons; parent states, angle wrapping, decay, and instance guards pass\n",comparisons);
}
