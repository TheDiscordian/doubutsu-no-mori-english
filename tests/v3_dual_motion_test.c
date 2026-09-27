#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_dual_motion.c"

static RoomRig *actor;
static int skeleton,opening,closing,native_animation,donor_animation;
static s16 *joint_work,*morph_work;
static unsigned native_events,donor_events,checks,draws;
static void event(unsigned *events,u32 kind) { *events=*events*33u^kind; }
static int advance(float end,float speed,float *current) {
    *current+=speed;if (*current>=end) {*current=end;return 1;}return 0;
}
static void vectors(s16 *j,s16 *m,float current) {
    for (unsigned i=0;i<21;++i) {j[i]=(s16)(current+i);m[i]=(s16)(current-i);}
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    assert(s==&skeleton && (a==&opening || a==&closing));memset(k,0,sizeof(*k));joint_work=j;morph_work=m;
    assert(j==dual_work(actor)->joint && m==dual_work(actor)->morph);
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {
    assert((a==&opening || a==&closing) && !d);native_animation=a==&opening;
    k->current.f=1;k->speed.f=1;
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) {
    event(&native_events,0x10000);vectors(joint_work,morph_work,k->current.f);
    return advance(k->end,k->speed.f,&k->current.f);
}
void sAdo_OngenTrgStart(u32 sound,float *pos) {
    assert((sound==0x16A || sound==0x16B) && pos==actor->position);event(&native_events,sound);
}
void sAdo_OngenPos(u32 id,u8 sound,float *pos) {
    assert(id==(u32)(uptr)actor && sound==0x52 && pos==actor->position);event(&native_events,sound);
}
void *_Matrix_to_Mtx(void *p) { memset(p,0x19,64);return p; }
void osWritebackDCache(void *p,int n) { assert(p && (n==184 || n==5*64)); }
void cKF_Si3_draw_R_SV(void *p,RoomKeyframe *k,void *matrices,void *before,void *after,void *arg) {
    RoomRigGame *game=p;assert(k==&actor->keyframe && !before && !after && !arg);
    assert(matrices==actor->matrices[game->frame&1]);++draws;memset(matrices,0x28,5*64);
    *game->gfx->head++=(RoomCommand){0xDB060034,0};*game->gfx->xlu_head++=(RoomCommand){0xDB060034,0};
    for (unsigned i=0;i<5;++i) {
        *game->gfx->head++=(RoomCommand){0xDA380003,0};*game->gfx->head++=(RoomCommand){0xDE000000,0x06000000+8*i};
    }
}

typedef struct {s16 x,y,z;} s_xyz;
typedef struct {float x,y,z;} xyz_t;
typedef struct {struct {float start_frame,end_frame,speed,current_frame;} frame_control;s16 *joint,*morph;} cKF_SkeletonInfo_R_c;
typedef struct {s16 frames;} cKF_Animation_R_c;
typedef int cKF_Skeleton_R_c;
typedef struct {cKF_SkeletonInfo_R_c keyframe;s_xyz joint[17],morph[17];s16 dynamic_work_s[4],state;
    u8 switch_bit,switch_changed_flag;xyz_t position;} FTR_ACTOR;
typedef int ACTOR;
typedef RoomRigGame GAME;
#define TRUE 1
#define FALSE 0
#define cKF_STATE_STOPPED 1
#define SCENE_NPC_HOUSE 100
#define SCENE_COTTAGE_NPC 101
#define aMR_CONTACT_DIR_FRONT 0
static int scene;
static struct {int contact_direction;} contact;
#define aMR_GetContactInfoLayer1() (&contact)
#define Save_Get(field) scene
static cKF_Animation_R_c cKF_ba_r_int_ike_island_hako01={51},cKF_ba_r_int_ike_island_hako02={51};
static cKF_Skeleton_R_c cKF_bs_r_int_ike_island_hako01;
static FTR_ACTOR *donor_actor;
static void donor_ct(cKF_SkeletonInfo_R_c *k,void *s,void *a,void *j,void *m) {
    assert(s==&cKF_bs_r_int_ike_island_hako01);
    assert(a==&cKF_ba_r_int_ike_island_hako01 || a==&cKF_ba_r_int_ike_island_hako02);
    memset(k,0,sizeof(*k));k->joint=j;k->morph=m;
}
static void donor_init(cKF_SkeletonInfo_R_c *k,void *a,void *d) {
    assert(!d && (a==&cKF_ba_r_int_ike_island_hako01 || a==&cKF_ba_r_int_ike_island_hako02));
    donor_animation=a==&cKF_ba_r_int_ike_island_hako01;k->frame_control.current_frame=1;k->frame_control.speed=1;
}
static int donor_play(cKF_SkeletonInfo_R_c *k) {
    event(&donor_events,0x10000);vectors(k->joint,k->morph,k->frame_control.current_frame);
    return advance(k->frame_control.end_frame,k->frame_control.speed,&k->frame_control.current_frame);
}
static void donor_trigger(u32 sound,xyz_t *pos) {assert(pos==&donor_actor->position);event(&donor_events,sound);}
static void donor_loop(u32 id,u8 sound,xyz_t *pos) {
    assert(id==(u32)(uptr)donor_actor && pos==&donor_actor->position && sound==0x52);event(&donor_events,sound);
}
#define aFTR_CAN_PLAY_SE(a) ((a)->state!=13 && (a)->state!=14 && (a)->state!=15 && (a)->state!=12)
#define cKF_SkeletonInfo_R_ct donor_ct
#define cKF_SkeletonInfo_R_init_standard_stop donor_init
#define cKF_SkeletonInfo_R_play donor_play
#define sAdo_OngenTrgStart donor_trigger
#define sAdo_OngenPos donor_loop
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-parameter"
#pragma GCC diagnostic ignored "-Wpointer-to-int-cast"
#include "donor_dual_motion.inc"
#pragma GCC diagnostic pop
#undef cKF_SkeletonInfo_R_ct
#undef cKF_SkeletonInfo_R_init_standard_stop
#undef cKF_SkeletonInfo_R_play
#undef sAdo_OngenTrgStart
#undef sAdo_OngenPos

static void compare(FTR_ACTOR *d) {
    RoomReversible *w=dual_work(actor);RoomKeyframe *k=&actor->keyframe;
    assert(k->start==d->keyframe.frame_control.start_frame && k->end==d->keyframe.frame_control.end_frame);
    assert(k->current.f==d->keyframe.frame_control.current_frame && k->speed.f==d->keyframe.frame_control.speed);
    assert(w->state==d->dynamic_work_s[0] && actor->switched==d->switch_bit);
    assert(native_animation==donor_animation && native_events==donor_events);
    assert(!memcmp(w->joint,d->joint,42) && !memcmp(w->morph,d->morph,42));++checks;
}
int main(void) {
    struct {u8 front[16];RoomRig actor;u8 back[16];} guard;actor=&guard.actor;
    _Alignas(16) u8 opaque[1024],xlu[64],game_bytes[0x1EA8];memset(game_bytes,0,sizeof(game_bytes));
    RoomRigGraphics gfx={0};RoomRigGame *game=(RoomRigGame *)game_bytes;game->gfx=&gfx;
    RoomDualMotion motion={.animation={&closing,&opening},.duration={51,51},.click={0x16B,0x16A},.loop=0x52};
    unsigned saved[]={0,1,2,255};const int scenes[]={0,SCENE_NPC_HOUSE,SCENE_COTTAGE_NPC};
    const s16 donor_states[]={0,1,2,3,4,13,14,5,6,7,8,9,10,15,11,12};
    for (unsigned context=0;context<3;++context) for (unsigned initial=0;initial<4;++initial) {
        memset(&guard,0xA7,sizeof(guard));actor->switched=saved[initial];scene=scenes[context];
        actor->ctr_type=context ? 0 : 1;actor->state=0;FTR_ACTOR d={0};donor_actor=&d;d.switch_bit=saved[initial];
        af_v3_room_dual_ct(actor,&skeleton,&motion,context!=0);fIIH_ct(&d,NULL);
        af_v3_room_dual_dt(actor);fIIH_dt(&d,NULL);compare(&d);
        for (unsigned frame=0;frame<400;++frame) {
            actor->state=frame/7%16;d.state=donor_states[actor->state];contact.contact_direction=frame%17==0 ? 2 : 0;
            int press=frame%61==0 ? 3 : frame%7==0 ? 1 : 0;
            for (int tick=0;tick<2;++tick) {
                d.switch_changed_flag=tick ? 0 : press;
                af_v3_room_dual_step(actor,&motion,d.switch_changed_flag,contact.contact_direction==0);
                fIIH_mv(&d,NULL,game,NULL);af_v3_room_dual_dt(actor);fIIH_dt(&d,NULL);compare(&d);
            }
            game->frame=frame;*(u32 *)(game_bytes+0x1EA0)=0x7FFFFF00u+frame;
            RoomReversible before=*dual_work(actor);memset(opaque,0xB8,sizeof(opaque));memset(xlu,0xB8,sizeof(xlu));
            gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+sizeof(opaque);gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);
            int stop=frame%11==0;af_v3_room_dual_dw(actor,game,5,stop);
            assert(!memcmp(&before,dual_work(actor),sizeof(before)));
            assert(gfx.head==(RoomCommand *)opaque+15 && gfx.xlu_head==(RoomCommand *)xlu+1);
            RoomCommand *commands=(RoomCommand *)opaque,*tiles=(RoomCommand *)(gfx.tail+64);
            assert(commands[0].a==0xDA380003);
            unsigned counter=actor->ctr_type==1 ? *(u32 *)(game_bytes+0x1EA0) : game->frame;
            const unsigned phases[]={0,5,15};
            for (unsigned i=0;i<3;++i) {
                unsigned scroll=stop ? 0 : (0u-(counter*2u+phases[i]))&0xFFFu;
                assert(commands[1+i].a==0xDB060020u+4*i && commands[1+i].b==((u32)(uptr)(tiles+5*i)&0x1FFFFFFFu));
                assert(tiles[5*i+1].a==(0xF2000000u|scroll<<12));
                assert(tiles[5*i+1].b==(((scroll+124u)&0xFFFu)<<12|28u));
                assert(tiles[5*i+3].a==0xF2000000 && tiles[5*i+3].b==0x0107C01C);
                assert(tiles[5*i+4].a==0xDF000000 && !tiles[5*i+4].b);
            }
            unsigned prior_draws=draws;gfx.tail=(u8 *)gfx.head+64;RoomRigGraphics snapshot=gfx;
            af_v3_room_dual_dw(actor,game,5,0);assert(!memcmp(&gfx,&snapshot,sizeof(gfx)) && prior_draws==draws);
            for (unsigned i=0;i<16;++i)assert(guard.front[i]==0xA7 && guard.back[i]==0xA7);
        }
    }
    assert(checks==9612 && draws==4800);printf("%u donor comparisons; %u draw frames\n",checks,draws);
    return 0;
}
