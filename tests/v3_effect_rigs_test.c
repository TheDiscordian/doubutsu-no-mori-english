#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_TRIGGER_SOUND
#define AF_V3_ROOM_REVERSIBLE
#define AF_V3_ROOM_EFFECT_RIG
#include "../overlays/v3/room_rigs.c"
#include "../overlays/v3/room_reversible.c"
#include "../overlays/v3/room_effect_rigs.c"

RoomRigTable af_v3_test_room_rigs;
RoomSoundTable af_v3_test_room_sounds;
RoomNativeTrigger af_v3_test_room_triggers[6];
RoomRigClip *af_v3_test_room_clip;
RoomEffectClip *af_test_effect_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
static _Alignas(16) u8 model[9216];
static RoomRigRecord *record;
static RoomRig *actor;
static s16 *joint_work,*morph_work;
static unsigned native_plays,donor_plays,native_events,donor_events,draws,checks,emissions;
static u32 native_rng,donor_rng;
static float random_value(u32 *seed) { *seed=*seed*1664525u+1013904223u;return (float)(*seed>>8)/16777216.0f; }
float af_effect_random(void) { return random_value(&native_rng); }
static void event(unsigned *events,u32 kind) { *events=(*events*33u)^kind; }
static int advance(float start,float end,float speed,float *current) {
    if (start>end) {*current-=speed;if (*current<=end) {*current=end;return 1;}}
    else {*current+=speed;if (*current>=end) {*current=end;return 1;}}
    return 0;
}
static void vectors(s16 *j,s16 *m,float current) {
    for (unsigned i=0;i<3u*(record->joints+1u);++i) {j[i]=(s16)(current+i);m[i]=(s16)(current-i);}
}
void *Lib_SegmentedToVirtual(void *p) {
    uptr at=(uptr)p;assert(at>=0x06000000u && at<0x06000000u+record->bytes);
    return model+at-0x06000000u;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    assert(((u8 *)s)[0]==record->joints && ((u8 *)s)[1]==record->shown);
    assert(a==model+record->animation-0x06000000u);memset(k,0,sizeof(*k));joint_work=j;morph_work=m;
    assert(j==work(actor)->joint && m==work(actor)->morph);
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {
    assert(a && !d);k->current.f=1;k->speed.f=1;
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *k,void *a,void *d) { (void)k;(void)a;(void)d;assert(0); }
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) {
    ++native_plays;vectors(joint_work,morph_work,k->current.f);
    return advance(k->start,k->end,k->speed.f,&k->current.f);
}
void sAdo_OngenTrgStart(u32 sound,float *pos) {
    assert((sound==0x16 || sound==0x17) && pos==actor->position);event(&native_events,sound);
}
void sAdo_OngenPos(u32 id,u8 sound,float *pos) {
    assert(id==(u32)(uptr)actor && sound==0x50 && pos==actor->position);event(&native_events,sound);
}
static void emit(int effect,EffectPosition pos,int priority,s16 angle,void *game,u16 item,s16 spread,s16 arg) {
    assert(effect==113 && pos.x==actor->position[0] && pos.y==actor->position[1]+18 && pos.z==actor->position[2]);
    assert(priority==1 && !angle && game && item==0xFFFF && spread==6 && !arg);
    event(&native_events,113);++emissions;
}
void *_Matrix_to_Mtx_new(void *g) { (void)g;assert(0);return 0; }
void *_Matrix_to_Mtx(void *p) { memset(p,0x19,64);return p; }
void osWritebackDCache(void *p,int n) { assert(p && (n==128 || n==record->shown*64)); }
typedef int (*JointCallback)(void *,RoomKeyframe *,int,void *,void *,void *,void *,void *);
void cKF_Si3_draw_R_SV(void *p,RoomKeyframe *k,void *matrices,void *before,void *after,void *arg) {
    RoomRigGame *game=p;assert(k==&actor->keyframe && before && after && arg);
    assert(matrices==actor->matrices[game->frame&1]);++draws;
    memset(matrices,0x28,record->shown*64);
    *game->gfx->head++=(RoomCommand){0xDB060034,0};
    *game->gfx->xlu_head++=(RoomCommand){0xDB060034,0};
    for (unsigned j=0;j<record->joints;++j) {
        void *list=j ? (void *)(uptr)(0x06000100+8*j) : NULL;void *expected=list;
        assert(((JointCallback)before)(game,k,j,&list,NULL,arg,NULL,NULL)==1);
        assert(list==(j==2 ? NULL : expected));
        if (list) { *game->gfx->head++=(RoomCommand){0xDA380003,0};*game->gfx->head++=(RoomCommand){0xDE000000,(u32)(uptr)list}; }
        assert(((JointCallback)after)(game,k,j,&list,NULL,arg,NULL,NULL)==1);
    }
}

/* Actual donor lifecycle, with deterministic engine/audio/effect boundaries.
   These comparisons test control flow, not native synthesis or GPU execution. */
typedef struct {s16 x,y,z;} s_xyz;
typedef struct {float x,y,z;} xyz_t;
typedef struct {struct {float start_frame,end_frame,speed,current_frame;} frame_control;
    s16 *joint,*morph;} cKF_SkeletonInfo_R_c;
typedef struct {s16 frames;} cKF_Animation_R_c;
typedef int cKF_Skeleton_R_c;
typedef struct {cKF_SkeletonInfo_R_c keyframe;s_xyz joint[17],morph[17];
    s16 dynamic_work_s[4],state;u8 switch_bit,switch_changed_flag;xyz_t position;} FTR_ACTOR;
typedef int ACTOR;
typedef RoomRigGame GAME;
#define TRUE 1
#define FALSE 0
static cKF_Animation_R_c cKF_ba_r_int_nog_nabe={8};
static cKF_Skeleton_R_c cKF_bs_r_int_nog_nabe;
static FTR_ACTOR *donor_actor;
static void donor_ct(cKF_SkeletonInfo_R_c *k,void *s,void *a,void *j,void *m) {
    assert(s==&cKF_bs_r_int_nog_nabe && a==&cKF_ba_r_int_nog_nabe);
    memset(k,0,sizeof(*k));k->joint=j;k->morph=m;
}
static void donor_init(cKF_SkeletonInfo_R_c *k,void *a,void *d) {
    assert(a==&cKF_ba_r_int_nog_nabe && !d);k->frame_control.current_frame=1;k->frame_control.speed=.5f;
}
static int donor_play(cKF_SkeletonInfo_R_c *k) {
    ++donor_plays;vectors(k->joint,k->morph,k->frame_control.current_frame);
    return advance(k->frame_control.start_frame,k->frame_control.end_frame,k->frame_control.speed,&k->frame_control.current_frame);
}
static void donor_trigger(u32 sound,xyz_t *pos) { assert(pos==&donor_actor->position);event(&donor_events,sound); }
static void donor_loop(u32 id,u8 sound,xyz_t *pos) {
    assert(id==(u32)(uptr)donor_actor && pos==&donor_actor->position && sound==0x50);event(&donor_events,sound);
}
static void donor_emit(int effect,xyz_t pos,int priority,s16 angle,GAME *game,u16 item,s16 spread,s16 arg) {
    assert(effect==113 && pos.x==donor_actor->position.x && pos.y==donor_actor->position.y+18 && pos.z==donor_actor->position.z);
    assert(priority==1 && !angle && game && item==0xFFFF && spread==6 && !arg);event(&donor_events,113);
}
static struct {void (*effect_make_proc)(int,xyz_t,int,s16,GAME *,u16,s16,s16);} donor_clip={donor_emit};
static struct {void *unused;typeof(donor_clip) *effect_clip;} donor_common={NULL,&donor_clip};
#define Common_Get(field) donor_common
#define aFTR_CAN_PLAY_SE(a) ((a)->state!=13 && (a)->state!=14 && (a)->state!=15 && (a)->state!=12)
#define RANDOM_F(maximum) (random_value(&donor_rng)*(maximum))
#define cKF_SkeletonInfo_R_ct donor_ct
#define cKF_SkeletonInfo_R_init_standard_stop donor_init
#define cKF_SkeletonInfo_R_play donor_play
#define sAdo_OngenTrgStart donor_trigger
#define sAdo_OngenPos donor_loop
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wpointer-to-int-cast"
#include "donor_effect_rig.inc"
#pragma GCC diagnostic pop
#undef cKF_SkeletonInfo_R_ct
#undef cKF_SkeletonInfo_R_init_standard_stop
#undef cKF_SkeletonInfo_R_play
#undef sAdo_OngenTrgStart
#undef sAdo_OngenPos

static void compare(FTR_ACTOR *d) {
    RoomEffectRigState *w=effect_work(actor);RoomKeyframe *k=&actor->keyframe;
    assert(k->start==d->keyframe.frame_control.start_frame && k->end==d->keyframe.frame_control.end_frame);
    assert(k->current.f==d->keyframe.frame_control.current_frame && k->speed.f==d->keyframe.frame_control.speed);
    assert(w->reverse.state==d->dynamic_work_s[0] && w->delayed==d->dynamic_work_s[1]);
    assert(w->steam==d->dynamic_work_s[2] && w->delay==d->dynamic_work_s[3]);
    assert(actor->switched==d->switch_bit && native_plays==donor_plays);
    assert(native_events==donor_events && native_rng==donor_rng);
    assert(!memcmp(w->reverse.joint,d->joint,3*(record->joints+1)*2));
    assert(!memcmp(w->reverse.morph,d->morph,3*(record->joints+1)*2));++checks;
}
static u32 read_word(FILE *f,unsigned n) {u32 v=0;while(n--) {int c=fgetc(f);assert(c!=EOF);v=v<<8|(unsigned)c;}return v;}
int main(int argc,char **argv) {
    assert(argc==3);FILE *f=fopen(argv[1],"rb");assert(f);
    assert(read_word(f,4)==ROOM_RIG_MAGIC && read_word(f,4)==1 && read_word(f,4)==24 && !read_word(f,4));
    af_v3_test_room_rigs=(RoomRigTable){.magic=ROOM_RIG_MAGIC,.count=1,.stride=24};record=af_v3_test_room_rigs.rows;
    record->index=read_word(f,2);record->bytes=read_word(f,2);record->skeleton=read_word(f,4);record->animation=read_word(f,4);
    record->joints=read_word(f,1);record->shown=read_word(f,1);record->mode=read_word(f,1);record->reserved=read_word(f,1);
    record->first.bits=read_word(f,4);record->last.bits=read_word(f,4);fclose(f);
    assert(record->mode==10 && record->joints==4 && record->shown==3);
    f=fopen(argv[2],"rb");assert(f);assert(fread(model,1,record->bytes,f)==record->bytes && fgetc(f)==EOF);fclose(f);
    const RoomEffectRigParams *params=af_v3_room_effect_rig_params(record,model);assert(params);
    RoomEffectClip clip={.request=emit};af_test_effect_clip=&clip;
    struct {u8 front[16];RoomRig actor;u8 back[16];} guard;actor=&guard.actor;
    _Alignas(16) u8 opaque[1024],xlu[64],game_bytes[0x1EA8];memset(game_bytes,0,sizeof(game_bytes));
    RoomRigGraphics gfx={0};RoomRigGame *game=(RoomRigGame *)game_bytes;game->gfx=&gfx;
    unsigned saved[]={0,1,2,255};
    const s16 donor_states[]={0,1,2,3,4,13,14,5,6,7,8,9,10,15,11,12};
    for (unsigned context=0;context<2;++context) for (unsigned initial=0;initial<4;++initial) {
        memset(&guard,0xA7,sizeof(guard));actor->index=record->index+context*1024;actor->switched=saved[initial];
        actor->ctr_type=context ? 0 : 1;actor->state=0;
        FTR_ACTOR d={0};donor_actor=&d;d.switch_bit=saved[initial];
        actor->position[0]=d.position.x=19;actor->position[1]=d.position.y=27;actor->position[2]=d.position.z=-31;
        native_rng=donor_rng=17;af_v3_room_rig_ct(actor,model);fNNB_ct(&d,NULL);fNNB_dt(&d,NULL);compare(&d);
        for (unsigned frame=0;frame<500;++frame) {
            actor->state=frame/7%16;d.state=donor_states[actor->state];
            actor->changed=frame%61==0 ? 3 : frame%7==0 ? 1 : 0;d.switch_changed_flag=actor->changed;
            if (actor->changed)actor->switched=!actor->switched;
            af_v3_room_rig_mv(actor,NULL,game,model);
            fNNB_mv(&d,NULL,game,NULL);d.switch_changed_flag=0;fNNB_mv(&d,NULL,game,NULL);fNNB_dt(&d,NULL);compare(&d);
            game->frame=frame;*(u32 *)(game_bytes+0x1EA0)=frame+17;
            RoomEffectRigState before=*effect_work(actor);
            gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+sizeof(opaque);gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);
            unsigned prior=draws;af_v3_room_rig_dw(actor,NULL,game,model);assert(draws==prior+1);
            assert(!memcmp(effect_work(actor),&before,sizeof(before)));
            unsigned counter=context ? frame : frame+17;
            unsigned active=context ? d.keyframe.frame_control.end_frame==8 : d.dynamic_work_s[1]==1;
            unsigned selected=active ? (counter*2u)&3u : 4u;
            RoomCommand *commands=(RoomCommand *)xlu;
            assert(commands[0].a==0xDB060020 && commands[0].b==((u32)(uptr)(model+half(params->offsets[selected]))&0x1FFFFFFFu));
            assert(commands[2].a==0xDA380003 && commands[3].a==0xDE000000 && commands[3].b==word(params->model));
            assert(gfx.xlu_head==commands+4 && (uptr)gfx.head<=(uptr)gfx.tail);
            af_v3_room_rig_dt(actor,model);compare(&d);
            for (unsigned j=0;j<16;++j)assert(guard.front[j]==0xA7 && guard.back[j]==0xA7);
            for (unsigned j=0;j<27;++j)assert(((u16 *)actor->joint)[j]==0xA7A7 && ((u16 *)actor->morph)[j]==0xA7A7);
        }
    }
    /* Bad parameters and insufficient command/matrix room must not draw. */
    u8 *packed=model+record->first.bits-0x06000000u;
    unsigned bad_offsets[]={0,4,8,9,10,11,13,15,16,26};
    for (unsigned i=0;i<sizeof(bad_offsets)/sizeof(*bad_offsets);++i) {
        u8 old=packed[bad_offsets[i]];packed[bad_offsets[i]]=0xFF;
        assert(!af_v3_room_effect_rig_params(record,model));packed[bad_offsets[i]]=old;
    }
    for (unsigned side=0;side<2;++side) {
        gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+(side ? sizeof(opaque) : 128);
        gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+(side ? 24 : sizeof(xlu));
        RoomRigGraphics before=gfx;unsigned prior=draws;
        af_v3_room_rig_dw(actor,NULL,game,model);assert(prior==draws && !memcmp(&gfx,&before,sizeof(gfx)));
    }
    assert(emissions>0);printf("%u donor effect-rig comparisons; %u draw frames; %u steam requests; bounds pass\n",checks,draws,emissions);
}
