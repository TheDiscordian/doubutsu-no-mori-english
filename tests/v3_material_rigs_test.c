#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_MATERIAL_RIG
#include "../overlays/v3/room_rigs.c"
RoomRigTable af_v3_test_room_rigs;
RoomRigClip *af_v3_test_room_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
static _Alignas(16) u8 model[9216],original[9216];
static RoomRigRecord *record;
static RoomRig *expected_actor;
static s16 *joints,*morphs;
static unsigned plays,draws,loops;
void *Lib_SegmentedToVirtual(void *p) {
    uptr at=(uptr)p;assert(at>=0x06000000u && at<0x06000000u+record->bytes);
    return model+at-0x06000000;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    assert(((u8 *)s)[0]==record->joints && ((u8 *)s)[1]==record->shown);
    assert(a==model+record->animation-0x06000000);memset(k,0,sizeof(*k));joints=j;morphs=m;
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *k,void *a,void *d) {
    assert(a && !d);k->current.f=1;k->speed.f=1;k->mode=1;
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {
    (void)k;(void)a;(void)d;assert(0);
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) {
    assert(k->mode==1);++plays;k->current.f+=k->speed.f;
    for (unsigned i=0;i<(record->joints+1u)*3u;++i) {joints[i]=(s16)i;morphs[i]=(s16)(i+100);}
    return 0;
}
void sAdo_OngenPos(u32 id,u8 sound,float *position) {
    const RoomRigMaterial *p=(void *)(model+record->first.bits-0x06000000);
    assert(id==(u32)(uptr)expected_actor && sound==p->sound && position==expected_actor->position);++loops;
}
void *_Matrix_to_Mtx_new(void *p) {
    RoomRigGraphics *gfx=p;gfx->tail-=64;memset(gfx->tail,0x19,64);return gfx->tail;
}
void cKF_Si3_draw_R_SV(void *p,RoomKeyframe *k,void *matrices,void *before,void *after,void *arg) {
    RoomRigGame *game=p;assert(k==&expected_actor->keyframe && !before && !after && arg==expected_actor);
    assert(matrices==expected_actor->matrices[game->frame&1]);++draws;
    memset(matrices,0x28,record->shown*64);
    for (unsigned i=0;i<1u+2u*record->shown;++i)*game->gfx->head++=(RoomCommand){0xDA380003,0};
    *game->gfx->xlu_head++=(RoomCommand){0xDB060034,0};
}
static u32 word(FILE *f,unsigned bytes) {
    u32 v=0;while(bytes--) {int c=fgetc(f);assert(c!=EOF);v=(v<<8)|(unsigned)c;}return v;
}
int main(int argc,char **argv) {
    assert(argc==3);FILE *input=fopen(argv[1],"rb");assert(input);
    assert(word(input,4)==ROOM_RIG_MAGIC && word(input,4)==1 && word(input,4)==24 && word(input,4)==0);
    af_v3_test_room_rigs=(RoomRigTable){.magic=ROOM_RIG_MAGIC,.count=1,.stride=24};
    record=af_v3_test_room_rigs.rows;
    record->index=word(input,2);record->bytes=word(input,2);
    record->skeleton=word(input,4);record->animation=word(input,4);
    record->joints=word(input,1);record->shown=word(input,1);record->mode=word(input,1);record->reserved=word(input,1);
    record->first.bits=word(input,4);record->last.bits=word(input,4);fclose(input);
    assert(record->mode==8 && record->bytes<=sizeof(model));
    input=fopen(argv[2],"rb");assert(input);
    assert(fread(model,1,record->bytes,input)==record->bytes && fgetc(input)==EOF);fclose(input);
    memcpy(original,model,sizeof(model));
    struct {u8 front[16];RoomRig actor;u8 back[16];} guarded;
    RoomRig *actor=&guarded.actor;expected_actor=actor;
    _Alignas(16) u8 opaque[1024],translucent[64];
    RoomRigGraphics gfx={0};RoomRigGame game={.gfx=&gfx};
    for (unsigned alias=0;alias<2;++alias) {
        memset(&guarded,0xA7,sizeof(guarded));actor->index=record->index+alias*1024;
        unsigned ct=plays;af_v3_room_rig_ct(actor,model);
        assert(plays==ct+1 && actor->keyframe.current.f==1.5f && actor->keyframe.speed.f==.5f);
        for (unsigned tick=0;tick<300;++tick) {
            actor->state=(s16)(tick%16);actor->changed=(u8)tick;actor->switched=(u8)(tick&1);
            unsigned count=plays,sounds=loops;float frame=actor->keyframe.current.f;
            af_v3_room_rig_mv(actor,actor,&game,model);
            assert(plays==count+2 && loops==sounds+1 && actor->keyframe.current.f==frame+2 && actor->keyframe.speed.f==1);
            game.frame=tick<297 ? tick : tick==297 ? 0x3FFFFFFFu : tick==298 ? 0x40000000u : 0xFFFFFFFFu;
            gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+sizeof(opaque)-(tick&1)*8;
            gfx.xlu_head=(RoomCommand *)translucent;gfx.xlu_tail=translucent+sizeof(translucent);
            memset(opaque,0x42,sizeof(opaque));RoomRig before=*actor;count=draws;
            af_v3_room_rig_dw(actor,actor,&game,model);
            const RoomRigMaterial *p=rig_material(record,model);assert(p);
            u32 selected=((game.frame*2u)/5u)%2u;
            RoomCommand *commands=(void *)opaque;
            assert(draws==count+1 && commands[0].a==0xDA380003 && commands[1].a==0xDB060020);
            assert(commands[1].b==((u32)(uptr)(model+rig_frame_u16(p->offsets[selected]))&0x1FFFFFFF));
            assert(gfx.head==(RoomCommand *)opaque+3+2*record->shown);
            for (u8 *v=(u8 *)gfx.head;v<gfx.tail;++v)assert(*v==0x42);
            memcpy(before.matrices[game.frame&1],actor->matrices[game.frame&1],record->shown*64);
            assert(!memcmp(actor,&before,sizeof(before)));
            for (unsigned i=0;i<16;++i)assert(guarded.front[i]==0xA7 && guarded.back[i]==0xA7);
            for (unsigned i=(record->joints+1u)*3u;i<27;++i) {
                assert(((u16 *)actor->joint)[i]==0xA7A7 && ((u16 *)actor->morph)[i]==0xA7A7);
            }
        }
    }
    for (unsigned bad=0;bad<14;++bad) {
        RoomRigMaterial *p=(void *)(model+record->first.bits-0x06000000);
        if (bad==0)p->segment=7;
        if (bad==1)p->frames=0;
        if (bad==2)p->frames=9;
        if (bad==3)p->sound=128;
        if (bad==4)p->reserved=1;
        if (bad==5)memset(p->divisor,0,2);
        if (bad==6)memset(p->frame_bytes,255,2);
        if (bad==7)memset(p->offsets[0],255,2);
        if (bad==8)p->offsets[7][1]=1;
        if (bad==9)p->padding[7]=1;
        gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+sizeof(opaque);
        gfx.xlu_head=(RoomCommand *)translucent;gfx.xlu_tail=translucent+sizeof(translucent);
        if (bad==10)gfx.tail=opaque+160;
        if (bad==11)gfx.tail-=4;
        if (bad==12)gfx.head=0;
        if (bad==13)gfx.xlu_head=0;
        RoomRig before=*actor;unsigned old_plays=plays,old_draws=draws,old_loops=loops;
        if (bad<10) {af_v3_room_rig_ct(actor,model);af_v3_room_rig_mv(actor,actor,&game,model);}
        af_v3_room_rig_dw(actor,actor,&game,model);
        assert(plays==old_plays && draws==old_draws && loops==old_loops && !memcmp(actor,&before,sizeof(before)));
        memcpy(model,original,sizeof(model));
    }
    assert(!memcmp(model,original,sizeof(model)));
    puts("Material rigs pass 600 combined motion/draw frames, source rates, full joint writes, sound, and bounds");
}
