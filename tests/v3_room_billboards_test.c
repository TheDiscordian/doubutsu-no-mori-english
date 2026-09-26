#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_BILLBOARD
#include "../overlays/v3/room_rigs.c"
#include "../overlays/v3/room_billboards.c"

RoomRigTable af_v3_test_room_rigs;
RoomRigClip *af_v3_test_room_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
static _Alignas(16) u8 model[8192],opa[4096],xlu[2048],context[0x2000];
static RoomRigGraphics gfx;
static RoomRigGame *game=(void *)context;
static struct { u8 front[16];RoomRig actor;u8 back[16]; } guarded;
static RoomRig *actor=&guarded.actor;
static RoomRigRecord *row=&af_v3_test_room_rigs.rows[0];
static RoomBillboard *params=(void *)(model+0x300);
static unsigned sound_calls,draws,plays,flushes;

void *Lib_SegmentedToVirtual(void *p) {
    uptr n=(uptr)p;assert(n>=0x06000000 && n<0x06002000);return model+n-0x06000000;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *key,void *bones,void *motion,void *joint,void *morph) {
    assert(key==&actor->keyframe && bones==model+0x100 && motion==model+0x200);
    assert(joint==actor->joint && morph==actor->morph);memset(key,0,sizeof *key);
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *key,void *motion,void *diff) {
    assert(key==&actor->keyframe && motion==model+0x200 && !diff);
    key->speed.f=1;key->current.f=1;key->mode=1;
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *key,void *motion,void *diff) {
    (void)key;(void)motion;(void)diff;assert(0);
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *key) { ++plays;key->current.f+=key->speed.f;return 0; }
void sAdo_OngenPos(u32 id,u8 sound,float *pos) {
    assert(id==(u32)(uptr)actor && pos==actor->position && sound==params->sound);++sound_calls;
}
void *_Matrix_to_Mtx(void *target) { assert(!((uptr)target&15));memset(target,0xBB,64);return target; }
void *_Matrix_to_Mtx_new(void *graph) { (void)graph;assert(0);return 0; }
void osWritebackDCache(void *at,int bytes) {
    assert((at==gfx.tail && bytes==168) || (at==actor->matrices[game->frame&1] && bytes==row->shown*64));
    ++flushes;
}
/* The unchanged installed camera helpers have separate full-code bindings.
   These stubs verify the new caller's complete argument and graphics contract. */
int af_v3_fire_before(void *g,void *key,int joint,void *shape,void *flags,void *arg,void *rot,void *pos) {
    (void)g;(void)key;(void)flags;(void)arg;(void)rot;(void)pos;
    if(joint==2)*(void **)shape=0;
    return 1;
}
int af_v3_fire_after(void *g,void *key,int joint,void *shape,void *flags,void *arg,void *rot,void *pos) {
    (void)shape;(void)flags;(void)rot;(void)pos;
    BillboardDraw *d=arg;
    assert(g==game && key==&actor->keyframe && d->actor==actor && d->flame==params->flame);
    if(joint==2) {
        assert(d->matrix==gfx.tail+64);_Matrix_to_Mtx(d->matrix);
        *gfx.xlu_head++=(RoomCommand){0xDA380003,(u32)(uptr)d->matrix};
        *gfx.xlu_head++=(RoomCommand){0xDE000000,d->flame};
    }
    return 1;
}
void cKF_Si3_draw_R_SV(void *g,RoomKeyframe *key,void *matrices,void *before,void *after,void *arg) {
    assert(g==game && key==&actor->keyframe && matrices==actor->matrices[game->frame&1]);
    assert(before==(void *)af_v3_fire_before && after==(void *)af_v3_fire_after);
    *gfx.head++=(RoomCommand){0xDB060034,(u32)(uptr)matrices};
    *gfx.xlu_head++=(RoomCommand){0xDB060034,(u32)(uptr)matrices};
    unsigned shown=0;
    for(int j=0;j<row->joints;++j) {
        void *shape=j==1 ? 0 : (void *)(uptr)(0x06000400+j*0x100);
        int has=shape!=0;u8 flags=j==2;
        af_v3_fire_before(g,key,j,&shape,&flags,arg,0,0);
        if(has) {
            RoomCommand **head=shape && flags ? &gfx.xlu_head : &gfx.head;
            *(*head)++=(RoomCommand){0xDA380003,(u32)(uptr)matrices+64*shown++};
            if(shape)*(*head)++=(RoomCommand){0xDE000000,(u32)(uptr)shape};
        }
        af_v3_fire_after(g,key,j,&shape,&flags,arg,0,0);
    }
    assert(shown==row->shown);memset(matrices,0xCC,shown*64);++draws;
}
static void arena(unsigned tail_offset) {
    memset(opa,0xA7,sizeof opa);memset(xlu,0xA7,sizeof xlu);
    gfx.head=(void *)(opa+32);gfx.tail=opa+sizeof opa-32-tail_offset;
    gfx.xlu_head=(void *)(xlu+32);gfx.xlu_tail=xlu+sizeof xlu-32;
}
int main(void) {
    const RoomBillboard cases[]={
        {0x06000600,{{32,32},{32,64}},{{0,0},{0,-8}},0x57,0,2,0},
        {0x06000600,{{32,64},{32,32}},{{0,-6},{0,0}},0x5D,1,2,0},
        {0x06000600,{{32,64},{64,32}},{{0,-3},{-2,0}},0x5C,1,2,0}};
    af_v3_test_room_rigs=(RoomRigTable){ROOM_RIG_MAGIC,1,24,0,{{0}}};game->gfx=&gfx;
    const u32 frames[]={0,1,2,3,63,127,1023,5461,0x7FFFFFFF,0xFFFFFFFF};
    for(unsigned variant=0;variant<3;++variant) for(unsigned catalogue=0;catalogue<2;++catalogue) {
        *params=cases[variant];unsigned joints=variant ? 3:4;
        *row=(RoomRigRecord){1177,8192,0x06000100,0x06000200,joints,joints-1,ROOM_RIG_BILLBOARD,0,
            {.bits=0x06000300},{.bits=0}};
        model[0x100]=joints;model[0x101]=joints-1;
        memset(&guarded,0xA7,sizeof guarded);actor->index=(u16)(1177+1024*catalogue);
        af_v3_room_rig_ct(actor,model);
        assert(actor->keyframe.speed.f==.5f && actor->keyframe.current.f==1.5f);
        for(int state=-1;state<18;++state) {
            actor->state=(s16)state;unsigned old=sound_calls,p=plays;
            af_v3_room_rig_mv(actor,0,game,model);
            int audible=!params->suppress_states || (state!=5 && state!=6 && state!=13 && state!=15);
            assert(sound_calls==old+(unsigned)audible && plays==p+1);
        }
        for(unsigned i=0;i<sizeof frames/sizeof *frames;++i) for(unsigned room=0;room<2;++room) {
            arena((i&1)*8);game->frame=frames[i];*(u32 *)(context+0x1EA0)=~frames[i];
            unsigned old=draws,f=flushes;af_v3_room_rig_dw(actor,room ? actor:0,game,model);
            assert(draws==old+1 && flushes==f+2);
            RoomCommand *scroll=(void *)(gfx.tail+128);u32 frame=room ? ~frames[i]:frames[i];
            for(unsigned tile=0;tile<2;++tile) {
                long long dx=(long long)frame*params->rates[tile][0];
                long long dy=(long long)frame*params->rates[tile][1];
                u32 x=(u32)((dx-(dx<0))/2)&4095,y=(u32)((dy-(dy<0))/2)&4095;
                assert(scroll[tile*2].a==0xE8000000 && !scroll[tile*2].b);
                assert(scroll[tile*2+1].a==(0xF2000000|x<<12|y));
                assert(scroll[tile*2+1].b==((tile<<24)|(((x+(params->dimensions[tile][0]-1)*4)&4095)<<12)|
                    ((y+(params->dimensions[tile][1]-1)*4)&4095)));
            }
            assert(scroll[4].a==0xDF000000 && !scroll[4].b);
            u8 retained[176];u8 *first=gfx.tail;memcpy(retained,first,sizeof retained);
            af_v3_room_rig_dw(actor,room ? actor:0,game,model);assert(!memcmp(retained,first,sizeof retained));
        }
        arena(0);gfx.tail=(u8 *)gfx.head+200;RoomRigGraphics before=gfx;unsigned old=draws;
        af_v3_room_rig_dw(actor,0,game,model);assert(draws==old && !memcmp(&gfx,&before,sizeof gfx));
        for(unsigned i=0;i<16;++i)assert(guarded.front[i]==0xA7 && guarded.back[i]==0xA7);
    }
    puts("Billboard rigs retain loop policy, full draw streams, scroll timing, and bounded immutable frames");
}
