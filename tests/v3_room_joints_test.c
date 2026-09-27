#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_ROOM_RIG_PACKET
#define AF_V3_ROOM_JOINT
#include "../overlays/v3/room_rigs.c"
#include "../overlays/v3/room_joints.c"
RoomRigTable af_v3_test_room_rigs;
RoomRigClip *af_v3_test_room_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
u8 af_v3_test_joint_clock[8]={59,23};
static u8 model[9216];
static s16 *joints,*morphs;
static unsigned plays,draws,clicks,loops;
static u32 click;
static RoomRigRecord *record;
static s16 rotation;

void *Lib_SegmentedToVirtual(void *p) {
    uptr a=(uptr)p;assert(a>=0x06000000 && a<0x06000000+sizeof(model));
    return model+a-0x06000000;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    assert(((u8 *)s)[0]==record->joints && a);memset(k,0,sizeof(*k));joints=j;morphs=m;
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *k,void *a,void *d) {
    assert(a && !d);k->speed.f=1;k->current.f=1;k->mode=1;
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {
    cKF_SkeletonInfo_R_init_standard_repeat(k,a,d);k->mode=0;
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) {
    assert(k->mode==1);++plays;k->current.f+=k->speed.f;
    /* Simulate complete native root+joint writes, including all eight joints. */
    for (unsigned i=0;i<(record->joints+1u)*3u;++i) {joints[i]=(s16)i;morphs[i]=(s16)(i+100);}
    return 0;
}
static float reference_ease(float value,float target) {
    float diff=target-value,step=.3f*diff;
    if (step>.0001f || step<-.0001f) {
        if (step>.3f)step=.3f;
        if (step<-.3f)step=-.3f;
        value+=step;
    } else if (diff>=0) {value+=.0001f;if (value>target)value=target;}
    else {value-=.0001f;if (value<target)value=target;}
    return value;
}
float add_calc(float *v,float target,float rate,float maximum,float minimum) {
    assert(rate==.3f && maximum==.3f && minimum==.0001f);*v=reference_ease(*v,target);return target-*v;
}
void sAdo_OngenTrgStart(u32 word,float *position) {assert(position);++clicks;click=word;}
void sAdo_OngenPos(u32 owner,u8 sound,float *position) {assert(owner && sound==0x51 && position);++loops;}
void *_Matrix_to_Mtx(void *matrix) {memset(matrix,0xA2,64);return matrix;}
void *_Matrix_to_Mtx_new(void *value) {
    RoomRigGraphics *g=value;g->tail-=64;return _Matrix_to_Mtx(g->tail);
}
void osWritebackDCache(void *p,int n) {assert(p && n>0);}
typedef int (*Callback)(void *,RoomKeyframe *,int,void *,void *,void *,s16 *,void *);
void cKF_Si3_draw_R_SV(void *value,RoomKeyframe *k,void *matrices,void *pre,void *post,void *arg) {
    RoomRigGame *game=value;RoomRigGraphics *g=game->gfx;++draws;
    *g->head++=(RoomCommand){0xDB060034,(u32)(uptr)matrices};
    *g->xlu_head++=(RoomCommand){0xDB060034,(u32)(uptr)matrices};
    unsigned shown=0;
    for (unsigned j=0;j<record->joints;++j) {
        void *shape=j ? (void *)(uptr)(0x06000200+j*32) : 0,*original=shape;
        /* Snowcone's original joint two is not drawn. */
        if ((record->first.bits&255)==3 && j==2)shape=original=0;
        s16 rot[3]={0,0,100};u8 flags=0;
        assert(((Callback)pre)(game,k,j,&shape,&flags,arg,rot,0)==1);
        if (j==1)rotation=rot[2];
        if (original) {
            _Matrix_to_Mtx((u8 *)matrices+shown*64);++shown;
            *g->head++=(RoomCommand){0xDA380003,0};
            if (shape)*g->head++=(RoomCommand){0xDE000000,(u32)(uptr)shape};
        }
        assert(((Callback)post)(game,k,j,&shape,&flags,arg,rot,0)==1);
    }
    assert(shown==record->shown);
}

int main(void) {
    struct {u8 front[16];RoomRig actor;u8 back[16];} guard;
    RoomRig *a=&guard.actor;
    _Alignas(16) u8 opa[2048],xlu[2048];
    union {_Alignas(16) u8 raw[0x1EA4];RoomRigGame game;} state;
    RoomRigGame *game=&state.game;RoomRigGraphics gfx={0};
    memset(&state,0,sizeof(state));game->gfx=&gfx;
    af_v3_test_room_rigs=(RoomRigTable){ROOM_RIG_MAGIC,1,24,0,{{0}}};
    record=af_v3_test_room_rigs.rows;
    for (u32 kind=1;kind<=3;++kind)for (u32 initial=0;initial<=1;++initial) {
        *record=(RoomRigRecord){.index=1024,.bytes=8192,.skeleton=0x06000100,.animation=0x06000180,
            .joints=kind==1 ? 8 : kind==2 ? 2 : 6,.shown=kind==1 ? 7 : kind==2 ? 1 : 4,.mode=6,
            .first={.bits=kind==3 ? 0x5103 : kind},.last={.bits=kind==3 ? 0x00160017 : 0}};
        model[256]=record->joints;model[257]=record->shown;
        memset(&guard,0x79,sizeof(guard));a->index=1024;a->switched=initial;
        af_v3_room_rig_ct(a,model);
        assert(a->motion_power==initial && a->keyframe.current.f==1.5f);
        float expected=initial,phase=kind==2 ? (23*60+59)/600.0f : 0;
        assert(a->motion_phase==phase);
        for (u32 frame=0;frame<1600;++frame) {
            a->switched=(frame/127)&1;a->changed=frame%127==0;a->state=frame%80==0 ? 5 : 0;
            float target=(float)a->switched;
            for (unsigned tick=0;tick<2;++tick) {
                if (kind!=3)expected=reference_ease(expected,target);
                else if (expected<target) {expected+=.01f;if(expected>target)expected=target;}
                else if (expected>target) {expected-=.01f;if(expected<target)expected=target;}
                if (kind==2) {phase+=1.8204445f;if(phase>=65535)phase=0;}
            }
            unsigned before_clicks=clicks,before_loops=loops,before_plays=plays;
            af_v3_room_rig_mv(a,0,game,model);
            assert(plays==before_plays+2 && a->motion_power==expected && a->motion_phase==phase);
            assert(clicks-before_clicks==(kind==3 && a->changed && a->state!=5));
            assert(loops-before_loops==(kind==3 && a->switched && expected>=.01f && a->state!=5));
            if(clicks>before_clicks)assert(click==(a->switched ? 0x16u : 0x17u));
            for(unsigned j=0;j<(record->joints+1u)*3u;++j)assert(((s16 *)a->morph)[j]==(s16)(j+100));
            game->frame=frame;a->ctr_type=(frame&1);
            *(u32 *)(state.raw+0x1EA0)=frame+17;
            memset(opa,0x6A,sizeof(opa));memset(xlu,0x6B,sizeof(xlu));
            gfx.head=(RoomCommand *)opa;gfx.tail=opa+sizeof(opa)-8*(frame&1);
            gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+sizeof(xlu);
            af_v3_room_rig_dw(a,0,game,model);
            assert(a->motion_power==expected && a->motion_phase==phase);
            assert((u8 *)gfx.head<gfx.tail && (u8 *)gfx.xlu_head<gfx.xlu_tail);
            RoomCommand *c=(RoomCommand *)xlu;
            if(kind==2)assert(gfx.xlu_head==c+1 && rotation==(s16)(100+(int)phase));
            else {
                assert(c[1].a==0xDA380003 && c[2].a==0xDE000000 && c[2].b==0x06000260);
                unsigned level=(u8)(int)(expected*255.0f);
                if(kind==1)assert(c[3].a==(0xFA000000|level) && c[3].b==0xFFFF96FF && c[5].b==0x060002E0);
                else {
                    assert(c[4].a==0xFA0000FF && c[4].b==(0xFFFFFF00|level) && c[5].a==0xDB060024 && c[6].b==0x06000280);
                    RoomCommand *scroll=(RoomCommand *)(gfx.tail+192);
                    u32 counter=frame+(a->ctr_type ? 17u : 0u),y=((counter*16u)&0x3FFFu)>>2;
                    assert(scroll[1].a==(0xF2000000|y) && scroll[1].b==((28u<<12)|((y+124u)&0xFFFu)));
                    assert(scroll[3].b==0x0101C07C && scroll[4].a==0xDF000000);
                }
            }
            for(unsigned i=0;i<16;++i)assert(guard.front[i]==0x79 && guard.back[i]==0x79);
            for(unsigned i=0;i<sizeof(a->tail);++i)assert(a->tail[i]==0x79);
        }
        for (unsigned variant=0;variant<3;++variant) {
            gfx.head=(RoomCommand *)opa;gfx.tail=opa+(variant==0 ? 128 : sizeof(opa));
            gfx.xlu_head=(RoomCommand *)xlu;gfx.xlu_tail=xlu+(variant==1 ? 16 : sizeof(xlu));
            if(variant==2)gfx.tail-=4;
            unsigned before=draws;af_v3_room_rig_dw(a,0,game,model);
            assert(draws==before && gfx.head==(RoomCommand *)opa && gfx.xlu_head==(RoomCommand *)xlu);
        }
        if(kind==2) {
            a->motion_phase=65534;af_v3_room_rig_mv(a,0,game,model);assert(a->motion_phase==1.8204445f);
        }
    }
    assert(draws==9600);puts("Complete switched joint motion, redraws, eight-joint work, audio, clock, and arena guards pass");
}
