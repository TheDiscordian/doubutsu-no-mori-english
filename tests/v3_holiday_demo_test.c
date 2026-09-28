#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "holiday_demo.h"
static AFHDNativeDemo data;
AFHDNativeDemo *af_hd_native_demo=&data;
AFHDDemoState af_hd_state;
static _Alignas(8) unsigned char game[0x2000],player[0x40],actor[0x40];
_Alignas(8) unsigned char af_hd_common[0xAB8];
void *af_hd_game=game;
volatile short af_hd_title_flags;
static int check_count,default_count,start_count,end_count,title,starts=1,ends,go=1;
static int request_callbacks,cameras,interpolations,shrine_shots,normal_shots,scene_calls,bgm_calls;
static int check(void) {check_count++;return 1;}
static int defaults(void) {default_count++;return 1;}
static int start(void) {start_count++;return starts;}
static int end(void) {end_count++;return ends;}
#define REPEAT14(f) f,f,f,f,f,f,f,f,f,f,f,f,f,f
int (*const af_hd_checks[14])(void)={REPEAT14(check)};
int (*const af_hd_defaults[14])(void)={REPEAT14(defaults)};
int (*const af_hd_starts[14])(void)={REPEAT14(start)};
int (*const af_hd_ends[14])(void)={REPEAT14(end)};
int af_hd_title_demo(void) {return title;}
int af_hd_trigger(unsigned int mask) {assert(mask==0x8000);return 1;}
float af_hd_weight(void *a) {assert(a==actor);return 0.5f;}
int af_hd_force_speak(void *g,void *a) {assert(g==game && a==actor);return 1;}
void *af_hd_player(void *g) {assert(g==game);return player;}
int af_hd_camera(int kind) {assert(kind>=0 && kind<=12);cameras++;return 1;}
int af_hd_demo_type(void) {return data.state?data.current.type:0;}
void af_hd_emsg_colour(void *a) {assert(!a);af_holiday_demo_colour((unsigned char[]){175,255,255,255});}
void af_hd_camera_angle(void *g,AFHolidayShortPosition *a,float *distance) {
    assert(g==game);*a=(AFHolidayShortPosition){1,2,3};*distance=300;
}
void af_hd_camera_simple(void *g,const AFHolidayPosition *p,const AFHolidayShortPosition *a,float d,int zero,int priority) {
    assert(g==game && p->x==1600 && p->z==2320 && p->y==100 && a->y==2 && d==300 && !zero && priority==6);
    shrine_shots++;
}
int af_hd_camera_inter(void *g,const AFHolidayPosition *center,const AFHolidayPosition *eye,
    const AFHolidayPosition *goal_center,const AFHolidayPosition *goal_eye,float s0,float s1,unsigned int flags,int ticks,int priority) {
    assert(g==game && center==goal_center && eye==goal_eye && center->x==420 && eye->x==220 && eye->z==180);
    assert(s0==0.6f && s1==0.3f && flags==1 && ticks==7 && priority==7);interpolations++;return 1;
}
void af_hd_camera_normal(void *g,int zero,int priority) {assert(g==game && !zero && priority==5);normal_shots++;}
int af_hd_landmark(int *x,int *z,unsigned int kind) {assert(kind==4);*x=2;*z=3;return 1;}
void af_hd_origin(float *x,float *z,int bx,int bz) {*x=bx*640;*z=bz*640;}
int af_hd_goto(void *g,const AFHolidayDoor *door,int flag) {
    assert(g==game && door==(AFHolidayDoor *)(af_hd_common+0x78C) && !flag);scene_calls++;return go;
}
void af_hd_bgm_end(void) {bgm_calls++;}
static void callback(void *a) {assert(a==actor);request_callbacks++;}
static void reset(void) {
    memset(&data,0,sizeof(data));memset(&af_hd_state,0,sizeof(af_hd_state));
    memset(game,0,sizeof(game));memset(af_hd_common,0,sizeof(af_hd_common));
    float height=100;memcpy(player+0x2C,&height,4);
    AFHolidayPosition eye={300,400,200},center={500,100,500};
    memcpy(game+0x1A60,&eye,sizeof(eye));memcpy(game+0x1A6C,&center,sizeof(center));
    starts=1;ends=title=0;
}
int main(void) {
    /* All original modes retain table dispatch and their own numeric identity. */
    for(int type=0;type<14;type++) {
        reset();assert(af_holiday_demo_request(type,actor,callback));
        assert(af_holiday_demo_choose()==0 && data.current.type==type && data.state==1);
        af_holiday_demo_run();assert(data.state==2);
        ends=1;af_holiday_demo_run();assert(data.state==9);
    }
    assert(check_count==14 && default_count==14 && start_count==14 && end_count==14 && request_callbacks==14);
    reset();title=-9;*(short *)actor=0x99;
    assert(af_holiday_demo_request(8,actor,callback) && af_holiday_demo_choose()==0);
    reset();title=-9;*(short *)actor=0x98;
    assert(af_holiday_demo_request(8,actor,callback) && af_holiday_demo_choose()==-1);
    reset();for(int i=0;i<32;i++)assert(af_holiday_demo_request(0,actor,callback));
    AFHDNativeDemo full=data;assert(!af_holiday_demo_request(0,actor,callback) && !memcmp(&full,&data,sizeof(full)));
    reset();assert(!af_holiday_demo_request(-1,actor,callback) && !af_holiday_demo_request(16,actor,callback));
    assert(!af_holiday_demo_request(AF_HD_SPEECH,0,callback));
    /* Whole alternate announcement -> speech -> retained announcement -> return. */
    *(int *)(af_hd_common+0x780)=AF_HD_EVENTMSG2;
    AFHolidayDoor *door=(AFHolidayDoor *)(af_hd_common+0x78C);door->wipe_type=6;
    af_holiday_demo_init();assert(!*(int *)(af_hd_common+0x780) && data.request_count==1);
    af_holiday_demo_main();assert(data.state==2 && data.current.type==AF_HD_EVENTMSG2);
    assert(af_hd_state.saved.type==AF_HD_EVENTMSG2 && af_hd_title_flags==2 && shrine_shots==1);
    assert(!af_holiday_demo_busy() && data.data.event.colour[0]==175);
    /* The engine clears its request queue between updates. */
    data.request_count=data.priority=0;
    assert(af_holiday_demo_request(AF_HD_SPEECH,actor,callback));
    starts=0;af_holiday_demo_main();assert(data.current.type==AF_HD_SPEECH && data.state==1);
    assert(data.camera==12 && data.speaker==player && data.listener==actor && data.speaker_able && !data.listener_able);
    assert(data.data.talk.name && data.data.talk.zoom && !data.data.talk.change_player && af_holiday_demo_busy());
    af_holiday_demo_message(1234);af_holiday_demo_set_name(-1);af_holiday_demo_set_turn(1);
    af_holiday_demo_set_zoom(0);af_holiday_demo_set_change_player(0);af_holiday_demo_set_return_wait(1);
    unsigned char colour[]={1,2,3,4};af_holiday_demo_colour(colour);
    void *speaker,*listener;
    assert(af_holiday_demo_talk_actor()==actor && af_holiday_demo_actors(&speaker,&listener));
    assert(speaker==player && listener==actor && data.data.talk.message==1234);
    assert(af_holiday_demo_get_name()==-1 && af_holiday_demo_get_turn()==1 && !af_holiday_demo_get_zoom());
    assert(!af_holiday_demo_get_change_player() && af_holiday_demo_get_return_wait()==1);
    assert(!memcmp(af_holiday_demo_colour_pointer(),colour,4));
    starts=1;af_holiday_demo_run();assert(data.state==2 && interpolations==1 && af_hd_state.speech_camera);
    *(int *)(game+0x1AC0)=10;*(int *)(game+0x1B14)=2;
    assert(af_holiday_demo_camera_reverse(game) && *(unsigned int *)(game+0x1B10)==4);
    af_holiday_demo_camera_counter(game);assert(*(int *)(game+0x1B14)==1);
    af_holiday_demo_camera_counter(game);af_holiday_demo_camera_counter(game);
    assert(shrine_shots==2 && !af_hd_state.speech_camera);
    data.request_count=data.priority=0;ends=1;af_holiday_demo_main();
    assert(data.current.type==AF_HD_EVENTMSG2 && data.state==2 && af_hd_state.saved.type==AF_HD_EVENTMSG2);
    assert(!af_holiday_demo_busy() && !af_holiday_demo_talk_actor());
    af_holiday_demo_run();assert(!scene_calls && data.state==2);
    af_hd_state.fading_title=1;go=0;af_holiday_demo_run();
    assert(scene_calls==1 && !bgm_calls && data.state==2 && af_hd_state.saved.type==AF_HD_EVENTMSG2);
    go=1;af_holiday_demo_run();assert(scene_calls==2 && bgm_calls==1 && data.state==9 && !af_hd_state.saved.type);
    assert(game[0x1EE0]==11 && game[0x1EE1]==6 && af_hd_common[0x14B]==6);
    af_holiday_demo_main();assert(!data.state && !data.current.type);
    /* Ordinary reverse interpolation remains the native normal-camera route. */
    *(unsigned int *)(game+0x1B10)=0;assert(af_holiday_demo_camera_reverse(game));
    assert(*(unsigned int *)(game+0x1B10)==2);af_holiday_demo_camera_counter(game);assert(normal_shots==1);
    puts("Event demo: 14 native modes, queue/credits gates, alternate speech/resume, all speech readers, both camera returns, and failed/successful scene returns pass");
    return 0;
}
