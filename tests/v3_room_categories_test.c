#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_TRIGGER_SOUND
#include "../overlays/v3/room_rigs.c"

RoomRigTable af_v3_test_room_rigs;
RoomSoundTable af_v3_test_room_sounds;
RoomNativeTrigger af_v3_test_room_triggers[6];
static u32 last_sound,sound_calls;
static float *last_position;
void sAdo_OngenTrgStart(u32 word,float *position) {
    last_sound=word;last_position=position;++sound_calls;
}
RoomRigClip *af_v3_test_room_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
static u8 model[9216];
static unsigned constructs,plays,draws,storage_calls;
static RoomRig *expected_actor;
static RoomRigGame *expected_game;
static float expected_end;
static int expected_mode;
static unsigned expected_joints;
static int stopped;

void *Lib_SegmentedToVirtual(void *value) {
    uptr at=(uptr)value;
    assert(at>=0x06000000 && at<0x06000000+sizeof(model));
    return model+at-0x06000000;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *key,void *skeleton,void *animation,void *joint,void *morph) {
    assert(((u8 *)skeleton)[0]==expected_joints && animation==model+0x200);
    assert(joint==expected_actor->joint && morph==expected_actor->morph);
    memset(key,0,sizeof(*key));++constructs;
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *key,void *animation,void *diff) {
    assert(animation==model+0x200 && !diff);key->mode=1;key->current.f=1;
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *key,void *animation,void *diff) {
    assert(animation==model+0x200 && !diff);key->mode=0;key->current.f=1;key->speed.f=1;
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *key) {
    ++plays;key->current.f+=key->speed.f;
    /* The shared runtime cannot overwrite unused work or native actor state. */
    for (unsigned i=0;i<(expected_joints+1)*3;++i) {
        ((s16 *)expected_actor->joint)[i]=(s16)i;
        ((s16 *)expected_actor->morph)[i]=(s16)i;
    }
    return stopped;
}
static void storage(RoomRig *actor,void *room,RoomRigGame *game,float start,float end) {
    assert(actor==expected_actor && room==(void *)0x1234 && game==expected_game);
    assert(start==1 && end==expected_end);++storage_calls;
}
void *_Matrix_to_Mtx_new(void *value) {
    RoomRigGraphics *gfx=value;gfx->tail-=64;return gfx->tail;
}
void cKF_Si3_draw_R_SV(void *value,RoomKeyframe *key,void *matrices,void *before,void *after,void *arg) {
    RoomRigGame *game=value;
    assert(key==&expected_actor->keyframe && matrices==expected_actor->matrices[game->frame&1]);
    assert(!after && arg);++draws;
    if (expected_mode!=1) { assert(!before);return; }
    assert(before);
    typedef int (*Callback)(void *,RoomKeyframe *,int,void *,void *,void *,s16 *,void *);
    for (int joint=0;joint<5;++joint) {
        s16 rot[3]={123,-321,32760};
        assert(((Callback)before)(game,key,joint,0,0,arg,rot,0)==1);
        assert(rot[0]==123 && rot[1]==-321);
        u16 angle=joint==3 ? af_v3_test_room_hour : joint==4 ? af_v3_test_room_minute : 0;
        assert((u16)rot[2]==(u16)(32760-angle));
    }
}
int main(void) {
    struct { u8 front[16];RoomSoundActor actor;u8 back[16]; } sound_guard;
    memset(&sound_guard,0xA7,sizeof(sound_guard));
    af_v3_test_room_sounds=(RoomSoundTable){ROOM_SOUND_MAGIC,2,8,0,{{1070,0x816B,0},{1071,0x44E,0}}};
    for (int variant=0;variant<2;++variant) for (int state=-1;state<17;++state) for (int changed=0;changed<3;++changed) {
        RoomSoundActor *actor=&sound_guard.actor;
        actor->index=(u16)(1070+variant*1024);actor->state=(s16)state;actor->changed=(u8)changed;
        unsigned before=sound_calls;RoomSoundActor saved=*actor;
        af_v3_room_sound_mv(actor,0,0,0);
        unsigned added=changed==1 && !(state==5 || state==6 || state==13 || state==15);
        assert(sound_calls==before+added && !memcmp(actor,&saved,sizeof(saved)));
        if (added)assert(last_sound==0x816B && last_position==actor->position);
    }
    for (int i=0;i<16;++i)assert(sound_guard.front[i]==0xA7 && sound_guard.back[i]==0xA7);
    sound_guard.actor.index=1070;sound_guard.actor.state=0;sound_guard.actor.changed=1;
    for (int i=0;i<6;++i) {
        unsigned before=sound_calls;af_v3_test_room_triggers[i].word=0x816B;
        af_v3_room_sound_mv(&sound_guard.actor,0,0,0);assert(sound_calls==before);
        af_v3_test_room_triggers[i].word=0x016B;
        af_v3_room_sound_mv(&sound_guard.actor,0,0,0);assert(sound_calls==before+1);
        af_v3_test_room_triggers[i].word=0;
    }
    sound_guard.actor.index=1071;sound_guard.actor.state=0;sound_guard.actor.changed=1;
    af_v3_room_sound_mv(&sound_guard.actor,0,0,0);assert(last_sound==0x44E);
    unsigned before=sound_calls;
    af_v3_test_room_sounds.rows[1].reserved=1;af_v3_room_sound_mv(&sound_guard.actor,0,0,0);
    af_v3_test_room_sounds.count=65;af_v3_room_sound_mv(&sound_guard.actor,0,0,0);
    af_v3_room_sound_mv(0,0,0,0);assert(sound_calls==before);
    struct { u8 front[16];RoomRig actor;u8 back[16]; } guarded;
    RoomRig *actor=&guarded.actor;expected_actor=actor;
    _Alignas(16) u8 opa[1024],xlu[64];
    RoomRigGraphics gfx={0};RoomRigGame game={.gfx=&gfx};expected_game=&game;
    RoomRigClip clip={.open_close=storage};
    af_v3_test_room_rigs=(RoomRigTable){ROOM_RIG_MAGIC,25,24,0,{{0}}};
    for (u32 i=0;i<25;++i) {
        RoomRigRecord *r=af_v3_test_room_rigs.rows+i;
        *r=(RoomRigRecord){(u16)(1024+i),4096,0x06000100,0x06000200,5,3,1,0,{.bits=3},{.bits=4}};
    }
    for (int mode=0;mode<3;++mode) for (int variant=0;variant<2;++variant) {
        memset(&guarded,0xA7,sizeof(guarded));actor->index=(u16)(1048+variant*1024);
        RoomRigRecord *r=af_v3_test_room_rigs.rows+24;r->mode=(u8)mode;
        r->first.bits=mode==1 ? 3 : mode==2 ? 0x3F800000 : 0;
        r->last.bits=mode==1 ? 4 : mode==2 ? (variant ? 0x41400000 : 0x41200000) : 0;
        expected_end=variant ? 12 : 10;expected_mode=mode;
        expected_joints=r->joints=(mode==2 && !variant) ? 3 : 5;
        model[0x100]=r->joints;model[0x101]=r->shown;
        unsigned old=plays;af_v3_room_rig_ct(actor,model);
        assert(plays==old+1 && actor->keyframe.mode==(mode==2 ? 0 : 1));
        assert(actor->keyframe.speed.f==(mode==1 ? .5f : 0));
        actor->changed=0;old=plays;unsigned old_storage=storage_calls;
        af_v3_test_room_clip=&clip;
        af_v3_room_rig_mv(actor,(void *)0x1234,&game,model);
        if (mode==2) {
            assert(storage_calls==old_storage+1 && plays==old);
            af_v3_test_room_clip=0;af_v3_room_rig_mv(actor,(void *)0x1234,&game,model);
            af_v3_test_room_clip=&clip;clip.open_close=0;
            af_v3_room_rig_mv(actor,(void *)0x1234,&game,model);
            assert(storage_calls==old_storage+1 && plays==old);clip.open_close=storage;
        } else assert(plays==old+2);
        if (mode==1) assert(actor->keyframe.current.f==2.5f);
        if (mode==0) assert(actor->speed.f==.02f);
        gfx.head=(RoomCommand *)opa;gfx.tail=opa+sizeof(opa)-variant*8;
        gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);game.frame=(u32)variant;
        af_v3_test_room_hour=65500;af_v3_test_room_minute=32770;
        af_v3_room_rig_dw(actor,0,&game,model);
        for (int i=0;i<16;++i)assert(guarded.front[i]==0xA7 && guarded.back[i]==0xA7);
        for (int i=0;i<0x30;++i)assert(actor->tail[i]==0xA7);
        for (int i=0;i<4;++i)assert(actor->unused_morph[i]==0xA7);
    }
    assert(constructs==6 && draws==6 && storage_calls==2);
    RoomRigRecord good=af_v3_test_room_rigs.rows[24];
    for (unsigned bad=0;bad<6;++bad) {
        RoomRigRecord *r=af_v3_test_room_rigs.rows+24;*r=good;
        if (bad==0)r->mode=4;
        if (bad==1)r->reserved=1;
        if (bad==2)r->last.bits=0x7FC00000;
        if (bad==3)r->first.bits=r->last.bits;
        if (bad==4) { r->mode=1;r->first.bits=3;r->last.bits=3; }
        if (bad==5)r->joints=7;
        RoomRig before=*actor;
        af_v3_room_rig_ct(actor,model);af_v3_room_rig_mv(actor,0,&game,model);
        assert(!memcmp(actor,&before,sizeof(before)));
    }
    /* The complete hit category shares the drawer and sound dependency table.
       Compare source call order for idle, moving, stopped, and repeated hits. */
    af_v3_test_room_sounds=(RoomSoundTable){ROOM_SOUND_MAGIC,1,8,0,{{1048,0x175,0}}};
    RoomRigRecord *r=af_v3_test_room_rigs.rows+24;
    *r=(RoomRigRecord){1048,4096,0x06000100,0x06000200,3,3,ROOM_RIG_HIT,0,{.bits=0},{.bits=0}};
    expected_mode=ROOM_RIG_HIT;expected_joints=3;model[0x100]=3;model[0x101]=3;
    for (int variant=0;variant<2;++variant) {
        memset(&guarded,0xA7,sizeof(guarded));actor->index=(u16)(1048+variant*1024);
        af_v3_room_rig_ct(actor,model);
        assert(actor->keyframe.current.f==1.5f && actor->keyframe.speed.f==0 && !actor->changed);
        for (int done=0;done<2;++done) for (int moving=0;moving<2;++moving)
        for (int changed=0;changed<3;++changed) for (int state=-1;state<17;++state) {
            stopped=done;actor->state=(s16)state;actor->changed=(u8)changed;
            float speed=moving ? .5f : 0;actor->keyframe.speed.f=speed;actor->keyframe.current.f=7;
            unsigned old=plays,sounds=sound_calls;int running=!done && moving;
            af_v3_room_rig_mv(actor,0,&game,model);
            assert(plays==old+1+(unsigned)running+(changed!=0));
            assert(actor->keyframe.current.f==(changed ? 1+(running ? .5f : speed) : 7+speed*(1+running)));
            assert(actor->keyframe.speed.f==((changed || running) ? .5f : speed));
            int audible=changed && state!=5 && state!=6 && state!=13 && state!=15;
            assert(sound_calls==sounds+(unsigned)audible && actor->changed==changed);
            if(audible)assert(last_sound==0x175 && last_position==actor->position);
        }
        gfx.head=(RoomCommand *)opa;gfx.tail=opa+sizeof(opa)-variant*8;
        gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);game.frame=(u32)variant;
        af_v3_room_rig_dw(actor,0,&game,model);
        for (int i=0;i<16;++i)assert(guarded.front[i]==0xA7 && guarded.back[i]==0xA7);
        for (int i=0;i<0x30;++i)assert(actor->tail[i]==0xA7);
    }
    r->first.bits=1;RoomRig saved=*actor;
    af_v3_room_rig_ct(actor,model);af_v3_room_rig_mv(actor,0,&game,model);
    assert(!memcmp(actor,&saved,sizeof(saved)));
    puts("Shared clock/storage/switch/hit categories preserve dispatch, time, limits, sound, and actor guards");
}
