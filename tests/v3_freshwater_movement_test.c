#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/creature_freshwater.c"
typedef float f32;
typedef struct {struct {struct {s16 y;} angle;} world;struct {struct {s16 y;} rotation;} shape_info;
    float speed,max_velocity_y;} ACTOR;
typedef struct {struct {ACTOR actor_class;} tools_class;int action,work0;
    float fwork3;short swork0,swork2,swork3;unsigned short gyo_flags;unsigned char swim_flag;} aGYO_CTRL_ACTOR;
typedef void GAME;
enum {aGTT_ACTION_SWIM,aGTT_ACTION_WAIT,aGTT_ACTION_ESCAPE,aGTT_ACTION_NEAR};
#define TRUE 1
#define FALSE 0
#define ABS(x) ((x)<0?-(x):(x))
#define DEG2SHORT_ANGLE2(x) ((int)((x)*(65536.0f/360.0f)))
#define DECREMENT_TIMER(x) ((x)?--(x):0)
static float roll=0.5f;
static int player,bobber,wall,player_calls,search_calls,flow_calls,setup_calls;
static s16 current=1000;
#define RANDOM_F(n) (roll*(n))
#define RANDOM2_F(n) (0.25f*(n))
float af_patrol_random(void) {return roll;}
float af_patrol_random2(void) {return 0.25f;}
float af_patrol_sin(s16 a) {return sinf((float)a*(6.283185307179586f/65536.0f));}
static float sin_s(s16 a) {return af_patrol_sin(a);}
int af_patrol_chase_float(float *p,float target,float step) {
    if (step) {
        if (*p>target) step=-step;
        *p+=step;
        if (step*(*p-target)>=0.0f) {*p=target;return 1;}
    } else if (*p==target) return 1;
    return 0;
}
static int chase_f(float *p,float t,float s) {return af_patrol_chase_float(p,t,s);}
int af_patrol_chase_angle(s16 *p,s16 target,s16 step) {
    if (step) {
        if ((s16)(*p-target)>0) step=-step;
        *p=(s16)(*p+step);
        if ((s16)(*p-target)*step>=0) {*p=target;return 1;}
    } else if (*p==target) return 1;
    return 0;
}
static int chase_angle(s16 *p,s16 t,s16 s) {return af_patrol_chase_angle(p,t,s);}
s16 af_fresh_flow_reverse(void *a) {(void)a;return current;}
static s16 aGTT_Get_flow_angle_rv(ACTOR *a) {(void)a;return current;}
int af_fresh_wall(void *a) {(void)a;return wall;}
static int aGYO_check_wall(ACTOR *a) {(void)a;return wall;}
int af_fresh_player_near(void *a,void *g) {(void)a;(void)g;player_calls++;return player;}
int af_fresh_search(void *a,void *g) {(void)a;(void)g;search_calls++;return bobber;}
static int aGTT_player_near(ACTOR *a,GAME *g) {(void)a;(void)g;player_calls++;return player;}
static int aGTT_search_Uki(ACTOR *a,GAME *g) {(void)a;(void)g;search_calls++;return bobber;}
static void aGTT_setupAction(aGYO_CTRL_ACTOR *,int);
/* This header is extracted from the verified local donor, not a handwritten
 * model of its movement. Only explicit frame-rate wrappers are supplied below. */
#include DONOR_HEADER
static int aGTT_swim_speed_check(aGYO_CTRL_ACTOR *a,f32 t,f32 s,f32 v) {
    int done=donor60_speed_check(a,t,s,v);
    if (!done) done=donor60_speed_check(a,t,s,v);
    return done;
}
static int aGTT_swim_speed_change(aGYO_CTRL_ACTOR *a,f32 t,f32 s,f32 v) {
    int done=donor60_speed_change(a,t,s,v);
    if (!done) done=donor60_speed_change(a,t,s,v);
    return done;
}
static void aGTT_setupAction(aGYO_CTRL_ACTOR *a,int action) {
    a->action=action;setup_calls++;
    if (action==0) aGTT_swim_init(a);
    if (action==1) {aGTT_wait_init(a);a->work0/=2;}
    if (action==2) {aGTT_escape_init(a);a->work0/=2;}
}
void af_fresh_setup(void *a,int action) {
    W(a,0x1DC)=action;setup_calls++;
    if (action==0) af_v3_freshwater_swim_init(a);
    if (action==1) af_v3_freshwater_wait_init(a);
    if (action==2) af_v3_freshwater_escape_init(a);
}
void af_fresh_flow(void *a) {
    flow_calls++;
    s16 angle=(s16)(H(a,0x36)-current);int distance=angle<0?-(int)angle:angle;
    af_patrol_chase_angle((s16 *)((u8 *)a+0x36),current,distance>0x4000?0x400:0x100);
    H(a,0xDE)=H(a,0x36);
}
static void to_native(void *a,const aGYO_CTRL_ACTOR *d) {
    memset(a,0xA5,0x280);
    H(a,0x36)=d->tools_class.actor_class.world.angle.y;
    H(a,0xDE)=d->tools_class.actor_class.shape_info.rotation.y;
    F(a,0x74)=d->tools_class.actor_class.speed;F(a,0x7C)=d->tools_class.actor_class.max_velocity_y;
    W(a,0x1DC)=d->action;W(a,0x214)=d->work0;F(a,0x224)=d->fwork3;
    H(a,0x228)=d->swork0;H(a,0x22C)=d->swork2;H(a,0x22E)=d->swork3;
    U(a,0x23C)=d->gyo_flags;((u8 *)a)[0x23E]=d->swim_flag;
}
static void equal(void *a,const aGYO_CTRL_ACTOR *d) {
    _Alignas(16) u8 want[0x280];to_native(want,d);
    if (memcmp(a,want,sizeof(want))) {
        for (unsigned i=0;i<sizeof(want);i++) if (((u8 *)a)[i]!=want[i])
            fprintf(stderr,"field %x: %02x != %02x\n",i,((u8 *)a)[i],want[i]);
        assert(!"complete donor/native actor differs");
    }
}
int main(void) {
    unsigned cases=0;
    _Alignas(16) u8 a[0x280];
    for (int action=0;action<3;action++) for (int kind=0;kind<3;kind++) {
        aGYO_CTRL_ACTOR d={0};d.swim_flag=kind;d.tools_class.actor_class.world.angle.y=32000;
        d.gyo_flags=0x42;d.swork0=12;to_native(a,&d);
        if (action==0) {aGTT_swim_init(&d);af_v3_freshwater_swim_init(a);}
        if (action==1) {aGTT_wait_init(&d);d.work0/=2;af_v3_freshwater_wait_init(a);}
        if (action==2) {aGTT_escape_init(&d);d.work0/=2;af_v3_freshwater_escape_init(a);}
        equal(a,&d);cases++;
    }
    for (int action=0;action<3;action++) for (int kind=0;kind<3;kind++)
    for (int scenario=0;scenario<10;scenario++) {
        roll=(kind+0.25f)/3.0f;player=scenario==1;bobber=scenario==2;wall=scenario==3;
        aGYO_CTRL_ACTOR d={0};d.action=action;d.swim_flag=kind;
        d.tools_class.actor_class.world.angle.y=32700;
        d.tools_class.actor_class.shape_info.rotation.y=32700;
        d.tools_class.actor_class.speed=scenario==7?0.03f:2.0f;
        d.fwork3=scenario==4?175.0f:scenario==5?355.0f:scenario==6?0.0f:90.0f;
        d.work0=scenario==0?1:20;d.swork0=12;d.swork2=400;d.swork3=-32700;
        d.gyo_flags=scenario==8?0x40:scenario==9?0x80:0;
        to_native(a,&d);player_calls=search_calls=setup_calls=flow_calls=0;
        if (action==0) aGTT_swim((ACTOR *)&d,NULL);
        if (action==1) aGTT_wait((ACTOR *)&d,NULL);
        if (action==2) aGTT_escape((ACTOR *)&d,NULL);
        int p=player_calls,s=search_calls,t=setup_calls;
        player_calls=search_calls=setup_calls=flow_calls=0;
        if (action==0) af_v3_freshwater_swim(a,NULL);
        if (action==1) af_v3_freshwater_wait(a,NULL);
        if (action==2) af_v3_freshwater_escape(a,NULL);
        assert(p==player_calls && s==search_calls && t==setup_calls);
        equal(a,&d);cases++;
    }
    printf("%u complete freshwater donor/port cases passed\n",cases);
}
