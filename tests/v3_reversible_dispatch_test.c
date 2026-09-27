#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_TRIGGER_SOUND
#define AF_V3_ROOM_REVERSIBLE
#include "../overlays/v3/room_rigs.c"
#include "../overlays/v3/room_reversible.c"
#ifdef AF_V3_ROOM_DUAL_MOTION
#include "../overlays/v3/room_dual_motion.c"
u32 af_v3_test_dual_scene;
void *af_v3_test_dual_owner;
static struct {u8 prefix[0x1A0];int direction;} contact_owner;
#endif

RoomRigTable af_v3_test_room_rigs;
RoomSoundTable af_v3_test_room_sounds;
RoomNativeTrigger af_v3_test_room_triggers[6];
RoomRigClip *af_v3_test_room_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
static _Alignas(16) u8 model[9216];
static RoomRigRecord *record;
static RoomRig *actor;
static s16 *joints,*morphs;
static unsigned plays,sounds,draws;
void *Lib_SegmentedToVirtual(void *p) {
    uptr at=(uptr)p;assert(at>=0x06000000u && at<0x06000000u+record->bytes);
    return model+at-0x06000000;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    assert(((u8 *)s)[0]==record->joints && ((u8 *)s)[1]==record->shown);
    assert(a==model+record->animation-0x06000000
#ifdef AF_V3_ROOM_DUAL_MOTION
        || a==model+record->first.bits-0x06000000
#endif
    );memset(k,0,sizeof(*k));joints=j;morphs=m;
    assert(j==work(actor)->joint && m==work(actor)->morph);
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {
    assert(a && !d);k->current.f=1;k->speed.f=1;k->mode=0;
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *k,void *a,void *d) {
    (void)k;(void)a;(void)d;assert(0);
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) {
    ++plays;assert(k->mode==0);
    for (unsigned i=0;i<3u*(record->joints+1u);++i) {joints[i]=(s16)i;morphs[i]=(s16)(100+i);}
    if (k->start>k->end) {k->current.f-=k->speed.f;if (k->current.f<=k->end) {k->current.f=k->end;return 1;}}
    else {k->current.f+=k->speed.f;if (k->current.f>=k->end) {k->current.f=k->end;return 1;}}
    return 0;
}
void sAdo_OngenTrgStart(u32 sound,float *p) {
#ifdef AF_V3_ROOM_DUAL_MOTION
    assert(sound==(work(actor)->state ? record->last.bits>>16 : record->last.bits&65535));
#else
    assert(sound==0x7A);
#endif
    assert(p==actor->position);++sounds;
}
#ifdef AF_V3_ROOM_DUAL_MOTION
void sAdo_OngenPos(u32 id,u8 sound,float *p) {
    assert(id==(u32)(uptr)actor && sound==record->reserved && p==actor->position);
}
void *_Matrix_to_Mtx(void *p) {memset(p,0x19,64);return p;}
void osWritebackDCache(void *p,int n) {assert(p && (n==184 || n==record->shown*64));}
#endif
void *_Matrix_to_Mtx_new(void *p) {RoomRigGraphics *g=p;g->tail-=64;memset(g->tail,0x19,64);return g->tail;}
void cKF_Si3_draw_R_SV(void *p,RoomKeyframe *k,void *matrices,void *before,void *after,void *arg) {
    RoomRigGame *game=p;assert(k==&actor->keyframe && !before && !after && !arg);
    assert(matrices==actor->matrices[game->frame&1]);++draws;memset(matrices,0x28,record->shown*64);
    for (unsigned i=0;i<1u+2u*record->shown;++i)*game->gfx->head++=(RoomCommand){0xDA380003,0};
    *game->gfx->xlu_head++=(RoomCommand){0xDB060034,0};
}
static u32 read_word(FILE *f,unsigned n) {u32 v=0;while(n--) {int c=fgetc(f);assert(c!=EOF);v=v<<8|(unsigned)c;}return v;}
int main(int argc,char **argv) {
    assert(argc==3);FILE *f=fopen(argv[1],"rb");assert(f);
    assert(read_word(f,4)==ROOM_RIG_MAGIC && read_word(f,4)==1 && read_word(f,4)==24 && !read_word(f,4));
    af_v3_test_room_rigs=(RoomRigTable){.magic=ROOM_RIG_MAGIC,.count=1,.stride=24};record=af_v3_test_room_rigs.rows;
    record->index=read_word(f,2);record->bytes=read_word(f,2);
    record->skeleton=read_word(f,4);record->animation=read_word(f,4);
    record->joints=read_word(f,1);record->shown=read_word(f,1);record->mode=read_word(f,1);record->reserved=read_word(f,1);
    record->first.bits=read_word(f,4);record->last.bits=read_word(f,4);fclose(f);
#ifdef AF_V3_ROOM_DUAL_MOTION
    assert(record->mode==11 && record->joints==6 && record->shown==5);
    unsigned contexts=2;
#else
    assert(record->mode==9 && record->joints==11 && record->shown==5);
    unsigned contexts=1;
#endif
    f=fopen(argv[2],"rb");assert(f);assert(fread(model,1,record->bytes,f)==record->bytes && fgetc(f)==EOF);fclose(f);
    af_v3_test_room_sounds=(RoomSoundTable){.magic=ROOM_SOUND_MAGIC,.count=1,.stride=8};
    af_v3_test_room_sounds.rows[0]=(RoomSoundRecord){.index=record->index,.word=0x7A};
    struct {u8 front[16];RoomRig actor;u8 back[16];} guard;
    _Alignas(16) u8 opaque[1024],xlu[64];RoomRigGraphics gfx={0};RoomRigGame game={.gfx=&gfx};
    unsigned saved[]={0,1,2,255};actor=&guard.actor;
    for (unsigned context=0;context<contexts;++context)
    for (unsigned alias=0;alias<2;++alias) for (unsigned initial=0;initial<4;++initial) {
        memset(&guard,0xA7,sizeof(guard));actor->index=record->index+alias*1024;actor->switched=saved[initial];
#ifdef AF_V3_ROOM_DUAL_MOTION
        af_v3_test_dual_scene=context ? 6 : 20;
        af_v3_test_dual_owner=&contact_owner;contact_owner.direction=0;
#endif
        unsigned before=plays;af_v3_room_rig_ct(actor,model);
#ifdef AF_V3_ROOM_DUAL_MOTION
        assert(plays==before+1 && actor->switched==(!context && initial==1) && actor->keyframe.speed.f==0);
        assert(actor->keyframe.current.f==51);
#else
        assert(plays==before+1 && actor->switched==(initial==1) && actor->keyframe.speed.f==0);
        assert(actor->keyframe.current.f==(initial==1 ? 1 : record->first.f));
#endif
        for (unsigned tick=0;tick<180;++tick) {
            actor->state=(s16)(tick%16);actor->changed=tick%61==0 ? 1 : tick%7==0 ? 3 : 0;
            unsigned accepted=work(actor)->state;int press=actor->changed && actor->keyframe.speed.f==0;
#ifdef AF_V3_ROOM_DUAL_MOTION
            af_v3_test_dual_owner=tick%17==0 ? NULL : &contact_owner;
            contact_owner.direction=tick%13==0 ? 2 : 0;
            press=press && af_v3_test_dual_owner && !contact_owner.direction;
#endif
            if (actor->changed)actor->switched=!actor->switched; /* Native input toggles before the callback. */
            unsigned audio=sounds;before=plays;af_v3_room_rig_mv(actor,actor,&game,model);
            accepted^=press;assert(plays==before+2 && sounds==audio+(unsigned)press);
            assert((unsigned)work(actor)->state==accepted && actor->switched==accepted); /* Save capture precedes destruction. */
            RoomReversible work_before=*work(actor);RoomRig actor_before=*actor;game.frame=tick;
            gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+sizeof(opaque);
            gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);
            before=draws;af_v3_room_rig_dw(actor,actor,&game,model);assert(draws==before+1);
            assert(!memcmp(work(actor),&work_before,sizeof(work_before)));
            memcpy(actor_before.matrices[tick&1],actor->matrices[tick&1],record->shown*64);
            assert(!memcmp(actor,&actor_before,sizeof(*actor)));
            af_v3_room_rig_dt(actor,model);assert(actor->switched==accepted);
            for (unsigned j=0;j<16;++j)assert(guard.front[j]==0xA7 && guard.back[j]==0xA7);
            for (unsigned j=0;j<27;++j)assert(((u16 *)actor->joint)[j]==0xA7A7 && ((u16 *)actor->morph)[j]==0xA7A7);
        }
    }
    for (unsigned bad=0;bad<5;++bad) {
        RoomRigRecord keep=*record;RoomRig before=*actor;
        if (bad==0)record->joints=17;
        if (bad==1)record->shown=7;
        if (bad==2)record->first.bits=0x7F800000;
        if (bad==3)record->last.bits=1;
        if (bad==4)record->reserved=255;
        unsigned p=plays,d=draws,s=sounds;
        af_v3_room_rig_ct(actor,model);af_v3_room_rig_mv(actor,actor,&game,model);
        af_v3_room_rig_dw(actor,actor,&game,model);af_v3_room_rig_dt(actor,model);
        assert(p==plays && d==draws && s==sounds && !memcmp(actor,&before,sizeof(before)));*record=keep;
    }
#ifdef AF_V3_ROOM_DUAL_MOTION
    /* A resource-only staging record and damaged motion cannot dispatch. */
    for (unsigned bad=0;bad<3;++bad) {
        RoomRigRecord keep=*record;RoomRig before=*actor;
        unsigned at=record->first.bits-0x06000000+16;u8 saved=model[at];
        if (bad==0)record->last.bits=0;
        if (bad==1)model[at]=0;
        if (bad==2)record->first.bits=record->animation;
        unsigned p=plays,d=draws,s=sounds;
        af_v3_room_rig_ct(actor,model);af_v3_room_rig_mv(actor,actor,&game,model);
        af_v3_room_rig_dw(actor,actor,&game,model);af_v3_room_rig_dt(actor,model);
        assert(p==plays && d==draws && s==sounds && !memcmp(actor,&before,sizeof(before)));
        *record=keep;model[at]=saved;
    }
    puts("2880 dual-motion dispatch frames; aliases, room/contact readers, both sounds, drawing, native save ordering, and bounds pass");
#else
    puts("1440 reversible dispatch frames; aliases, full joint work, drawing, native save ordering, audio, and bounds pass");
#endif
}
