/* Actual carrying/needle adapters, with native evaluator/graphics stubs. */
#include "../overlays/v3/room_rigs.c"
#include "../overlays/v3/room_joints.c"
#include "../overlays/v3/room_needle.c"
RoomRigTable af_v3_test_room_rigs;
RoomRigClip *af_v3_test_room_clip;
u16 af_v3_test_room_hour,af_v3_test_room_minute;
u8 af_v3_test_joint_clock[8];
static _Alignas(4) u8 needle_model[3008],needle_debug_bytes[0x1C94];
u8 *af_v3_room_debug=needle_debug_bytes;
static unsigned needle_plays,needle_draws;
static RoomRig *needle_actor;

void *Lib_SegmentedToVirtual(void *p) {
    uptr a=(uptr)p;assert(a>=0x06000000 && a<0x06000000+sizeof(needle_model));
    return needle_model+a-0x06000000;
}
void cKF_SkeletonInfo_R_ct(RoomKeyframe *k,void *s,void *a,void *j,void *m) {
    assert(s==needle_model+256 && a==needle_model+512 && j && m);memset(k,0,sizeof(*k));
}
void cKF_SkeletonInfo_R_init_standard_stop(RoomKeyframe *k,void *a,void *d) {
    assert(a && !d);k->speed.f=1;k->current.f=1;k->mode=0;
}
void cKF_SkeletonInfo_R_init_standard_repeat(RoomKeyframe *k,void *a,void *d) {
    (void)k;(void)a;(void)d;assert(!"needle must use the stopped initializer");
}
int cKF_SkeletonInfo_R_play(RoomKeyframe *k) {
    assert(k->mode==0);++needle_plays;k->current.f+=k->speed.f;return 0;
}
float add_calc(float *v,float target,float rate,float maximum,float minimum) {
    float diff=target-*v,step=rate*diff;
    if (step>maximum)step=maximum;
    if (step< -maximum)step=-maximum;
    if (fabsf(step)<minimum)step=diff>=0 ? minimum : -minimum;
    if (fabsf(step)>fabsf(diff))step=diff;
    *v+=step;return target-*v;
}
void sAdo_OngenTrgStart(u32 word,float *p) {(void)word;(void)p;assert(!"unexpected needle sound");}
void sAdo_OngenPos(u32 id,u8 sound,float *p) {(void)id;(void)sound;(void)p;assert(!"unexpected needle loop");}
void *_Matrix_to_Mtx(void *p) {memset(p,0xA5,64);return p;}
void *_Matrix_to_Mtx_new(void *p) {RoomRigGraphics *g=p;g->tail-=64;return _Matrix_to_Mtx(g->tail);}
void osWritebackDCache(void *p,int n) {assert(p && n>0);}
typedef int (*NeedleCallback)(void *,RoomKeyframe *,int,void *,void *,void *,s16 *,void *);
void cKF_Si3_draw_R_SV(void *g,RoomKeyframe *key,void *matrices,void *pre,void *post,void *arg) {
    assert(key==&needle_actor->keyframe);needle_draws++;
    for (int j=0;j<5;j++) {
        s16 r[3]={17,123,45};void *shape=(void *)(uptr)(0x06000280+j*32),*before=shape;
        assert(((NeedleCallback)pre)(g,key,j,&shape,0,arg,r,0)==1);
        s16 wanted=j==3 ? af_v3_room_needle_angle(&needle_actor->needle,123,
            needle_actor->s_angle_y,af_v3_carry_angle(needle_actor)) : 123;
        assert(r[0]==17 && r[1]==wanted && r[2]==45 && shape==before);
        assert(((NeedleCallback)post)(g,key,j,&shape,0,arg,r,0)==1 && shape==before);
    }
    memset(matrices,0xAB,8*64);
}
static void draw_needle(RoomRig *actor,unsigned frame) {
    _Alignas(16) u8 opa[2048],xlu[2048];
    RoomRigGraphics gfx={.head=(RoomCommand *)opa,.tail=opa+sizeof(opa),
        .xlu_head=(RoomCommand *)xlu,.xlu_tail=xlu+sizeof(xlu)};
    RoomRigGame g={.gfx=&gfx,.frame=frame};RoomNeedle before=actor->needle;
    needle_actor=actor;af_v3_room_rig_dw(actor,0,&g,needle_model);
    assert(!memcmp(&before,&actor->needle,sizeof(before)));
    assert(gfx.xlu_head==(RoomCommand *)xlu);
}
static void test_needle_binding(void) {
    af_v3_test_room_rigs=(RoomRigTable){ROOM_RIG_MAGIC,1,24,0,{{0}}};
    af_v3_test_room_rigs.rows[0]=(RoomRigRecord){.index=1049,.bytes=3008,
        .skeleton=0x06000100,.animation=0x06000200,.joints=5,.shown=4,.mode=6,.first={.bits=4}};
    needle_model[256]=5;needle_model[257]=4;
    for (int direction=-1;direction<=1;direction+=2) {
        setup(0);RoomRig *child=actors+1;child->index=1049;fg[34]=0x3064;
        af_v3_room_rig_ct(child,needle_model);
        assert(child->keyframe.mode==0 && child->keyframe.speed.f==0 && child->keyframe.current.f==1.5f);
        RoomNeedle expected=child->needle;RoomKeyframe key=child->keyframe;
        assert(af_v3_carry_permit_rotate_ac(actors));
        assert(af_v3_carry_parent(child)==actors);
        for (unsigned frame=0;frame<14;frame++) {
            actors[0].state=frame==0 ? (direction>0 ? 8 : 7) : (direction>0 ? 3 : 4);
            actors[0].s_angle_y=direction*frame*1000;
            af_v3_carry_after_move(actors,&owner);
            s16 *regs=(s16 *)(needle_debug_bytes+0x14);
            regs[11*96+80]=frame>8 ? -90 : 0;regs[11*96+81]=frame>8 ? 7 : 0;
            unsigned start=needle_plays;
            af_v3_room_rig_mv(child,&owner,&game,needle_model);
            assert(needle_plays==start+2);
            for (unsigned i=0;i<2;i++) af_v3_room_needle_step(&expected,&key,child->state,
                &actors[0].state,regs[11*96+80],regs[11*96+81]);
            assert(!memcmp(&expected,&child->needle,sizeof(expected)));
            if (frame==4)assert(direction>0 ? child->needle.amplitude< -44 : child->needle.amplitude>44);
            draw_needle(child,frame);
        }
        actors[0].state=0;actors[0].s_angle_y=direction*16384;
        af_v3_carry_after_move(actors,&owner);
        assert(!af_v3_carry_parent(child) && child->s_angle_y==direction*16384);
        draw_needle(child,14);expected_child=34;af_v3_carry_destruct(&owner);
        RoomRig preview=*child;preview.index=2073;
        af_v3_room_rig_ct(&preview,needle_model);draw_needle(&preview,15);
        assert(!af_v3_carry_parent(&preview) && preview.needle.amplitude==0);
    }
    assert(needle_draws==32);
    puts("shared needle dispatcher: real carrying parent, both turns, release, debug inputs, preview, and matrix lifetime pass");
}
