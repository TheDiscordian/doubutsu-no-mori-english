#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/room_rigs.c"
RoomRigTable af_v3_test_room_rigs;
static u8 model[9216];
static s16 *joint_work,*morph_work;
static unsigned plays,draws,constructs;
static void *last_matrices;

void *Lib_SegmentedToVirtual(void *value) {
    uptr address=(uptr)value;
    assert(address>=0x06000000u && address<0x06000000u+sizeof(model));
    return model+address-0x06000000u;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *key,void *skeleton,void *animation,void *joint,void *morph) {
    assert(((u8 *)skeleton)[0]==6 && ((u8 *)skeleton)[1]==5);
    assert((u8 *)animation>=model && (u8 *)animation<model+sizeof(model));
    memset(key,0,sizeof(*key));joint_work=joint;morph_work=morph;++constructs;
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *key,void *motion,void *diff) {
    assert(motion && !diff);key->start=1;key->end=61;key->duration=61;key->current.f=1;key->mode=1;
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *key) {
    assert(key->mode==1);++plays;
    /* The native evaluator uses root plus six joints, never nine vectors. */
    for (int i=0;i<21;++i)joint_work[i]=(s16)i;
    for (int i=0;i<21;++i)morph_work[i]=(s16)(i+1);
    key->current.f+=key->speed.f;
    if (key->current.f>61)key->current.f=key->current.f-61+1;
    return 0;
}
void *_Matrix_to_Mtx_new(void *value) {
    RoomRigGraphics *gfx=value;gfx->tail-=64;memset(gfx->tail,0x19,64);return gfx->tail;
}
void cKF_Si3_draw_R_SV(void *value,RoomKeyframe *key,void *matrices,void *before,void *after,void *arg) {
    RoomRigGame *game=value;(void)key;
    assert(!before && !after && !arg);++draws;last_matrices=matrices;
    memset(matrices,0x28,5*64);
    for (int i=0;i<11;++i)*game->gfx->head++=(RoomCommand){0xDA380003,0};
    *game->gfx->xlu_head++=(RoomCommand){0xDB060034,0};
}
static void source_step(float *speed,float *target,float *frame,int changed) {
    if (changed)*target=1.25f;
    else if (*speed>=1.25f)*target=.5f;
    if (*speed<*target) { *speed+=.01f;if(*speed>*target)*speed=*target; }
    else if (*speed>*target) { *speed-=.01f;if(*speed<*target)*speed=*target; }
    *frame+=*speed;if(*frame>61)*frame=*frame-61+1;
}
int main(void) {
    struct { u8 front[16];RoomRig actor;u8 back[16]; } guarded;
    RoomRig *actor=&guarded.actor;
    af_v3_test_room_rigs=(RoomRigTable){ROOM_RIG_MAGIC,8,16,0,{{0}}};
    for (u32 i=0;i<8;++i) {
        RoomRigRecord *r=af_v3_test_room_rigs.rows+i;
        *r=(RoomRigRecord){(u16)(1024+i),4096,0x06000100+i*8,0x06000200+i*20,6,5};
        model[r->skeleton-0x06000000]=6;model[r->skeleton-0x06000000+1]=5;
    }
    _Alignas(16) u8 opaque[1024],translucent[64];
    RoomRigGraphics gfx={0};RoomRigGame game={.gfx=&gfx};
    for (u32 n=0;n<8;++n) {
        memset(&guarded,0xA7,sizeof(guarded));actor->index=(u16)(1024+n);
        af_v3_room_rig_ct(actor,model);
        assert(actor->speed.f==0 && actor->target.f==.5f && actor->keyframe.current.f==1);
        unsigned initial=plays;float speed=0,target=.5f,frame=1;
        for (int i=0;i<8000;++i) {
            actor->changed=(i%97==0 || i%137==0);
            int changed=actor->changed;
            source_step(&speed,&target,&frame,changed);source_step(&speed,&target,&frame,0);
            af_v3_room_rig_mv(actor,0,&game,model);
            assert(actor->speed.f==speed && actor->target.f==target && actor->keyframe.current.f==frame);
            assert(actor->changed==changed);
        }
        assert(plays==initial+16000);
        for (int i=0;i<16;++i)assert(guarded.front[i]==0xA7 && guarded.back[i]==0xA7);
        for (int i=0;i<4;++i)assert(actor->unused_morph[i]==0xA7);
        for (int i=0;i<0x30;++i)assert(actor->tail[i]==0xA7);
        for (int i=0;i<6;++i)assert(((u8 *)actor->joint)[42+i]==0xA7);
        for (u32 parity=0;parity<2;++parity) {
            gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+sizeof(opaque);
            gfx.xlu_head=(RoomCommand *)translucent;gfx.xlu_tail=translucent+sizeof(translucent);
            game.frame=parity;af_v3_room_rig_dw(actor,0,&game,model);
            assert(last_matrices==actor->matrices[parity]);
            assert(gfx.head==(RoomCommand *)opaque+12 && gfx.tail==opaque+sizeof(opaque)-64);
            assert(gfx.xlu_head==(RoomCommand *)translucent+1);
        }
        for (u32 parity=0;parity<2;++parity)
            for (int i=5*64;i<10*64;++i)assert(actor->matrices[parity][i/64][i%64]==0xA7);
    }
    assert(constructs==8 && draws==16);
    RoomRig before=*actor;
    unsigned drawn=draws;
    gfx.head=(RoomCommand *)opaque;gfx.tail=opaque+144;
    af_v3_room_rig_dw(actor,0,&game,model);assert(draws==drawn && gfx.head==(RoomCommand *)opaque);
    gfx.tail=opaque+sizeof(opaque);gfx.xlu_tail=(u8 *)gfx.xlu_head;
    af_v3_room_rig_dw(actor,0,&game,model);assert(draws==drawn);
    actor->index=900;before=*actor;
    af_v3_room_rig_ct(actor,model);af_v3_room_rig_mv(actor,0,&game,model);
    assert(!memcmp(actor,&before,sizeof(before)));
    actor->index=1024;before=*actor;
    for (u32 bad=0;bad<4;++bad) {
        RoomRigTable original=af_v3_test_room_rigs;
        if (bad==0)af_v3_test_room_rigs.magic^=1;
        if (bad==1)af_v3_test_room_rigs.count=25;
        if (bad==2)af_v3_test_room_rigs.rows[0].joints=7;
        if (bad==3)af_v3_test_room_rigs.rows[0].animation=0x06010000;
        af_v3_room_rig_ct(actor,model);af_v3_room_rig_mv(actor,0,&game,model);
        assert(!memcmp(actor,&before,sizeof(before)));af_v3_test_room_rigs=original;
    }
    puts("Room rigs retain source timing, switch pulses, independent state, complete drawing, and bounds");
    return 0;
}
