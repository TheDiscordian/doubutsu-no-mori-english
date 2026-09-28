#include "decoration_actor.h"

static const AFDecorActorRecord *record(const ACTOR *a) {
    if (!a) return 0;
    for (u32 i=0;i<18;++i) if (af_decor_actor_records[i].native_name==a->npc_id)
        return af_decor_actor_records+i;
    return 0;
}
static int ready(const AFDecorActorRecord *r) {
    if (!r || (r->dependencies&af_decor_actor_services.ready)!=r->dependencies) return 0;
    const AFDecorActorServices *s=&af_decor_actor_services;
    if ((r->dependencies&AF_DECOR_IDENTITIES) && (!s->resolve || !r->native_dummy)) return 0;
    if ((r->dependencies&AF_DECOR_DEMO) && !s->demo) return 0;
    if ((r->dependencies&AF_DECOR_EFFECT) && !s->effect) return 0;
    if ((r->dependencies&AF_DECOR_HARVEST) && !s->pocket) return 0;
    if ((r->dependencies&AF_DECOR_FISH) && (!s->fish_save || !s->fish_size || !s->fish_npc_size ||
        !s->event_npc || !s->npc_name || !s->random_name || !s->fish_record ||
        !s->message || !s->number || !s->string)) return 0;
    return 1;
}
void *af_decor_actor_descriptor(int profile) {
    for (u32 i=0;i<18;++i) if (af_decor_actor_records[i].profile==profile)
        return af_decor_actor_descriptors[af_decor_actor_records[i].owner];
    return af_decor_previous_descriptor(profile);
}
ACTOR *af_decor_actor_setup(GAME *game,u16 name,float x,float z,s16 params) {
    const AFDecorActorRecord *r=0;
    for (u32 i=0;i<18;++i) if (af_decor_actor_records[i].native_name==name) {
        r=af_decor_actor_records+i;break;
    }
    if (!r) return af_decor_previous_setup(game,name,x,z,params);
    /* These models are already resident. Do not index original structure-bank
       tables with additive names or borrow an unrelated native palette. */
    if (!game || !ready(r) || !af_decor_native_structure_clip) return 0;
    xyz_t pos={x,0.0f,z};pos.y=af_decor_native_ground(pos,0.0f);
    ACTOR *a=af_decor_native_make((u8*)game+0x1C78,game,r->profile,pos.x,pos.y,pos.z,0,0,0,
        ((signed char*)game)[0xE4],((signed char*)game)[0xE5],-1,name,params,-1,-1);
    if (!a || !a->mv_proc) return 0;
    af_decor_native_fg_set(0xFFFF,pos,0);
    return a;
}
void af_decor_actor_free(ACTOR *a) {
    const AFDecorActorRecord *r=record(a);
    u8 *descriptor=r?af_decor_actor_descriptors[r->owner]:0;
    if (descriptor && (*(u16*)a!=r->profile ||
            *(u8**)((u8*)a+0x170)!=descriptor)) descriptor=0;
    /* Preserve the structure pool's actual release, including original actors.
       Native deletion skips reference accounting for resident descriptors. */
    const u32 *clip=af_decor_native_structure_clip;
    if (clip) ((void (*)(ACTOR*))(uptr)clip[0x10/4])(a);
    if (descriptor && descriptor[0x1E]) --descriptor[0x1E];
}
static void effect(int id,xyz_t pos,int count,s16 angle,GAME *game,u16 name,int a,int b) {
    if (af_decor_actor_services.effect)
        af_decor_actor_services.effect(id,pos,count,angle,game,name,a,b);
}
static AFDecorEffectClip const effect_clip={effect};
static int clock_read(void) {
    lbRTC_time_c t=af_decor_native_rtc;
    if (!t.month || t.month>12 || !t.day || t.day>31 || t.hour>=24 || t.min>=60 || t.sec>=60) return 0;
    af_decor_actor_context.time.rtc_time=t;
    af_decor_actor_context.time.now_sec=t.hour*3600+t.min*60+t.sec;
    af_decor_actor_context.clip.effect_clip=(AFDecorEffectClip*)&effect_clip;
    return 1;
}
int af_decor_actor_call(ACTOR *a,GAME *game,unsigned int phase) {
    const AFDecorActorRecord *r=record(a);
    if (!game || !r || phase>3) return 0;
    u32 *initialized=(u32*)((u8*)a+0x2A4);
    if (phase && *initialized!=0x41464443u) return 0;
    /* Destruction must release owned clips even after the event stops. */
    if (phase!=1 && (!ready(r) || !clock_read() || !af_decor_native_player(game))) return 0;
    AFDecorDraw f=phase==0?r->ctor:phase==1?r->dtor:phase==2?r->init:r->move;
    if (f) f(a,game);
    /* Source controllers advance at 60 Hz, native actors at 30 Hz. Init
       already performs one movement step. Keep both ordered source steps,
       but never initialize twice or advance an actor deleted by step one. */
    if ((phase==2 || phase==3) && a->mv_proc && r->move) r->move(a,game);
    if (phase==0) *initialized=0x41464443u;
    else if (phase==1) *initialized=0;
    return 1;
}
void af_decor_actor_ctor(ACTOR *a,GAME *g) {
    if (!af_decor_actor_call(a,g,0)) af_decor_native_delete(a);
}
void af_decor_actor_dtor(ACTOR *a,GAME *g) { (void)af_decor_actor_call(a,g,1); }
void af_decor_actor_init(ACTOR *a,GAME *g) {
    if (!af_decor_actor_call(a,g,2)) af_decor_native_delete(a);
}
void af_decor_actor_move(ACTOR *a,GAME *g) {
    if (!af_decor_actor_call(a,g,3)) af_decor_native_delete(a);
}
void af_decor_actor_draw(ACTOR *a,GAME *g) {
    const AFDecorActorRecord *r=record(a);
    if (ready(r) && af_decor_draw(a,g,r->source_name)) af_decor_source_draw_tick(a);
}
u16 af_decor_source_name(ACTOR *a) { const AFDecorActorRecord *r=record(a);return r?r->source_name:0; }
void af_decor_source_move_install(ACTOR *a,AFDecorDraw source_move) {
    const AFDecorActorRecord *r=record(a);
    /* The donor init assigns its movement callback even after deletion.
       Keep native deletion final, and keep all later moves inside the adapter. */
    if (r && r->move==source_move && a->mv_proc) a->mv_proc=af_decor_actor_move;
}
void af_decor_source_collision(ACTOR *a) {
    const AFDecorActorRecord *r=record(a);
    if (r) (void)af_decor_collision(a,r->source_name);
}
static int destination(u16 source) {
    if (source==0 || source==0xFFFF) return source;
    if (af_decor_actor_services.resolve) return af_decor_actor_services.resolve(source);
    return -1;
}
int af_decor_source_fg(u16 source,xyz_t pos,int flag) {
    int name=destination(source);
    return name>=0?af_decor_native_fg_set(name,pos,flag):0;
}
void af_decor_source_unit_set(u16 source,int x,int z,int flag) {
    xyz_t pos;
    if (mFI_UtNum2CenterWpos(&pos,x,z)) (void)af_decor_source_fg(source,pos,flag);
}
u16 *af_decor_source_get_fg(xyz_t pos) {
    /* Source callers only compare the knife/fork here. Translate into a
       separately owned value, never rewrite the native foreground in place. */
    extern u16 af_decor_fg_result;
    u16 *p=af_decor_native_fg(pos);
    if (!p) return 0;
    int knife=destination(0x2530);
    af_decor_fg_result=(knife>=0 && *p==knife)?0x2530:0;
    return &af_decor_fg_result;
}
int af_decor_source_demo(int source,ACTOR *a) {
    return af_decor_actor_services.demo?af_decor_actor_services.demo(source,a):0;
}
int af_decor_actor_demo(int source,ACTOR *a) {
    if (source==1 || source==5) return af_decor_native_demo(source,a);
    /* Donor 16 is exclusively the boat-boarding acre transition. The native
       engine has no boat transition; do not pass 16 into its shorter enum.
       Imported resident houses do not add island/boat travel. */
    return 0;
}
int af_decor_actor_resolve(u16 source) {
    if (!source || source==0xFFFF) return source;
    for (u32 i=0;i<18;++i) {
        const AFDecorActorRecord *r=af_decor_actor_records+i;
        if (source==r->source_name) return r->native_name;
        if (source==r->source_dummy && r->native_dummy) return r->native_dummy;
    }
    return -1;
}
void af_decor_actor_effect(int id,xyz_t pos,int priority,s16 angle,GAME *game,u16 name,int a,int b) {
    /* The native aerobics radio uses this exact effect, angle, and arguments.
       Its effect implementation already uses native-rate movement/lifetime;
       only the source radio's request cadence needs the controller substeps. */
    AFDecorNativeEffectClip *clip=af_decor_native_effect_clip;
    if (id==32 && name==0x582C && a==1 && b==0 && game && clip && clip->request)
        clip->request(32,pos,priority,angle,game,0x582B,1,0);
}
int af_decor_source_status(int source,int status) {
    int native=af_holiday_native_type(source);
    return native>=0?af_decor_native_status(native,status):0;
}
static u32 rig_base(cKF_Skeleton_R_c *skeleton) {
    for (u32 i=0;i<18;++i)
        if (af_decor_records[i].skeleton==(u32)(uptr)skeleton) return af_decor_records[i].rig_base;
    return 0;
}
void af_decor_source_rig_ct(cKF_SkeletonInfo_R_c *key,cKF_Skeleton_R_c *skel,void *animation,s_xyz *work,s_xyz *morph) {
    u32 base=rig_base(skel);if (!base) return;
    u32 old=af_decor_segments[6];af_decor_segments[6]=base&0x1FFFFFFF;
    af_decor_native_rig_ct(key,skel,animation,work,morph);af_decor_segments[6]=old;
}
void af_decor_source_rig_init(cKF_SkeletonInfo_R_c *key,cKF_Skeleton_R_c *skel,void *animation,
                            float start,float end,float current,float speed,float morph,int mode,void *table) {
    u32 base=rig_base(skel);if (!base) return;
    u32 old=af_decor_segments[6];af_decor_segments[6]=base&0x1FFFFFFF;
    af_decor_native_rig_init(key,skel,animation,start,end,current,speed,morph,mode,table);
    af_decor_segments[6]=old;
}
int af_decor_source_rig_play(cKF_SkeletonInfo_R_c *key) {
    u32 base=rig_base(key->skeleton);if (!base) return 0;
    u32 old=af_decor_segments[6];af_decor_segments[6]=base&0x1FFFFFFF;
    int result=af_decor_native_rig_play(key);af_decor_segments[6]=old;return result;
}
void af_decor_source_copy(void *dst,const void *src,int n) {
    for (int i=0;i<n;++i) ((u8*)dst)[i]=((const u8*)src)[i];
}
void af_decor_source_zero(void *p,unsigned int n) { for (u32 i=0;i<n;++i) ((u8*)p)[i]=0; }
void af_decor_source_land(u8 *p) { for (u32 i=0;i<8;++i) p[i]=0x20; }
void af_decor_source_personal(PersonalID_c *dst,const PersonalID_c *src) { *dst=*src; }
void af_decor_noop(void *a,void *b) { (void)a;(void)b; }
