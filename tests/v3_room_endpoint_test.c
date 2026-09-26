#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_TRIGGER_SOUND
#define AF_V3_ROOM_EFFECTS
#include "../overlays/v3/room_rigs.c"
RoomRigTable af_v3_test_room_rigs;
RoomSoundTable af_v3_test_room_sounds;
RoomNativeTrigger af_v3_test_room_triggers[6];
RoomRigClip *af_v3_test_room_clip;
RoomEffectClip *af_test_effect_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
u32 af_test_effect_scene;
static u8 model[1024];
static s16 *joint,*morph;
static int joints,plays,stopped,positioned,systems,flashes,wall=76,draws;
static RoomRig *expected_actor;
static RoomRigGame *expected_game;
void *Lib_SegmentedToVirtual(void *p) {return model+(uptr)p-0x06000000;}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    assert(s==model && a==model+32);joints=*(u8 *)s;joint=j;morph=m;memset(k,0,sizeof(*k));
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *k,void *a,void *d) {(void)k;(void)a;(void)d;assert(0);}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {
    assert(a==model+32 && !d);k->start=k->current.f=1;k->end=k->duration=10;k->speed.f=1;
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) {
    ++plays;k->current.f+=k->speed.f;
    for(int i=0;i<(joints+1)*3;++i) {joint[i]=(s16)(10+i);morph[i]=(s16)(20+i);}
    return stopped;
}
void sAdo_OngenTrgStart(u32 word,float *p) {assert(word==0x174 && p==expected_actor->position);++positioned;}
void sAdo_SysTrgStart(u32 word) {assert(word==0x817E);++systems;}
int af_v3_room_effect_wall(void) {return wall;}
static void request(int effect,EffectPosition p,int priority,s16 angle,void *game,u16 item,s16 a,s16 b) {
    assert(effect==112 && priority==2 && !angle && game==expected_game && item==0xFFFF && !a && !b);
    assert(p.x==1 && p.y==2 && p.z==3);++flashes;
}
void *_Matrix_to_Mtx_new(void *p) {RoomRigGraphics *g=p;g->tail-=64;return g->tail;}
void cKF_Si3_draw_R_SV(void *g,RoomKeyframe *k,void *m,void *before,void *after,void *arg) {
    assert(g==expected_game && k==&expected_actor->keyframe && !before && !after);
    assert(arg==&af_v3_test_room_rigs.rows[0]);
    memset(m,0x5A,4*64);++draws;
}
int main(void) {
    af_v3_test_room_rigs=(RoomRigTable){.magic=ROOM_RIG_MAGIC,.count=1,.stride=24};
    RoomRigRecord *r=&af_v3_test_room_rigs.rows[0];
    *r=(RoomRigRecord){.index=1262,.bytes=1024,.skeleton=0x06000000,.animation=0x06000020,
        .joints=7,.shown=4,.mode=ROOM_RIG_HIT,.first.bits=2,.last.f=.5f};
    af_v3_test_room_sounds=(RoomSoundTable){.magic=ROOM_SOUND_MAGIC,.count=1,.stride=8,
        .rows={{.index=1262,.word=0x174,.wall=76,.effect=112,.system=0x817E}}};
    RoomEffectClip clip={.request=request};af_test_effect_clip=&clip;
    struct {u32 first[4];RoomRig actor;u32 last[4];} guarded;
    _Alignas(16) u8 commands[1024],translucent[64];RoomRigGraphics gfx={0};RoomRigGame game={.gfx=&gfx};
    expected_game=&game;expected_actor=&guarded.actor;
    for(int count=7;count<=8;++count) {
        memset(&guarded,0xA5,sizeof(guarded));RoomRig *a=&guarded.actor;
        a->index=1262;a->changed=1;a->state=0;a->position[0]=1;a->position[1]=2;a->position[2]=3;
        model[0]=r->joints=(u8)count;model[1]=4;plays=stopped=0;
        af_v3_room_rig_ct(a,model);
        assert(plays==1 && a->keyframe.current.f==1.5f && a->keyframe.speed.f==.5f && a->changed==1);
        for(int i=0;i<8;++i) {af_v3_room_rig_mv(a,0,&game,model);assert(!positioned && !systems && !flashes);}
        assert(plays==17 && a->keyframe.speed.f==.5f);
        stopped=1;af_v3_room_rig_mv(a,0,&game,model);
        assert(positioned==1 && systems==1 && flashes==1 && a->keyframe.current.f==1.5f);
        af_v3_test_room_triggers[0].word=0x817E;
        af_v3_room_rig_mv(a,0,&game,model);
        assert(positioned==2 && systems==1 && flashes==2); /* Only audio is singleton. */
        af_v3_test_room_triggers[0].word=0;
        for(int w=-1;w<=77;++w) if(w!=76) {
            wall=w;af_v3_room_rig_mv(a,0,&game,model);assert(systems==1 && flashes==2);
        }
        wall=76;int prior=positioned;
        const int excluded[]={5,6,13,15};
        for(unsigned i=0;i<4;++i) {a->state=excluded[i];af_v3_room_rig_mv(a,0,&game,model);}
        assert(positioned==prior && systems==1 && flashes==2);
        a->state=0;a->changed=0;int prior_plays=plays;
        af_v3_room_rig_mv(a,0,&game,model);assert(plays==prior_plays+1 && positioned==prior);
        a->index=2286;a->changed=1;af_v3_room_rig_mv(a,0,&game,model);
        assert(positioned==prior+1 && systems==2 && flashes==3);
        gfx.head=(RoomCommand *)commands;gfx.tail=commands+sizeof(commands);
        gfx.xlu_head=(RoomCommand *)translucent;gfx.xlu_tail=translucent+sizeof(translucent);
        af_v3_room_rig_dw(a,0,&game,model);assert(draws==count-6);
        for(int i=0;i<4;++i)assert(guarded.first[i]==0xA5A5A5A5 && guarded.last[i]==0xA5A5A5A5);
        for(int i=0;i<0x30;++i)assert(a->tail[i]==0xA5);
        positioned=systems=flashes=0;
    }
    puts("endpoint-hit animation, full morph capacity, conditional sounds/effects and bounds pass");
}
