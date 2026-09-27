#include <assert.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/player_exercise.c"

typedef float f32;
typedef int8_t s8;
typedef uint32_t u32;
enum { FALSE=0, TRUE=1, mPlayer_RADIO_EXERCISE_COMMAND_RING_BUFFER_SIZE=8,
       mPlayer_RADIO_EXERCISE_CMD_NUM=18, mPlayer_REQUEST_PRIORITY_4=4,
       mPlayer_REQUEST_PRIORITY_1=1, mPlayer_STATUS_FOR_BEE_ATTACK=1 };
#define ARRAY_COUNT(a) ((int)(sizeof(a)/sizeof(*(a))))
typedef struct { float start_frame, end_frame, duration, speed, current_frame; } cKF_FrameControl_c;
typedef struct { cKF_FrameControl_c frame_control; } cKF_SkeletonInfo_R_c;
typedef struct { int cmd, _04, _08, _0C; } mPlayer_main_radio_exercise_c;
typedef struct {
    s8 radio_exercise_command_ring_buffer[8], radio_exercise_ring_buffer_cmd_timer;
    int radio_exercise_command_ring_buffer_index, radio_exercise_continue_cmd_idx;
    float radio_exercise_cmd_timer;
    u32 old_sound_frame_counter;
    cKF_SkeletonInfo_R_c keyframe0, keyframe1;
    struct { mPlayer_main_radio_exercise_c radio_exercise; } main_data;
} PLAYER_ACTOR;
typedef PLAYER_ACTOR ACTOR;
typedef struct { PLAYER_ACTOR *player; } GAME;
typedef struct { int tempo; } Radio_c;
#define GET_PLAYER_ACTOR_GAME_ACTOR(g) ((g)->player)
static int able, input, request_ok, status, tempo;
static u32 now;
typedef struct { int request, command, priority, wait, flags, settle, bee; float speed, morph; } Events;
static Events donor_events, port_events;
static int Player_actor_Check_AbleRadioExercise(ACTOR *a) { (void)a; return able; }
static int Player_actor_CheckController_forRadio_exercise(GAME *g) { (void)g; return input; }
static int Player_actor_request_main_radio_exercise_all(GAME *g,int cmd,float speed,int priority) {
    (void)g; donor_events.request++; donor_events.command=cmd;
    donor_events.speed=speed; donor_events.priority=priority; return request_ok;
}
static void Player_actor_SettleRequestMainIndexPriority(ACTOR *a) { (void)a; donor_events.settle++; }
static void Player_actor_Set_status_for_bee(ACTOR *a,int kind) { (void)a; assert(kind==1); donor_events.bee++; }
static int Player_actor_request_main_wait_all(GAME *g,float morph,float delay,int flags,int priority) {
    (void)g; assert(delay==0); donor_events.wait++; donor_events.morph=morph;
    donor_events.flags=flags; donor_events.priority=priority; return 1;
}
static u32 sAdo_GetSoundFrameCounter(void) { return now; }
static int sAdos_GetRadioCounter(Radio_c *r) { r->tempo=tempo; return status; }
static void add_calc2(float *value,float target,float fraction,float maximum) {
    if (*value!=target) {
        float step=fraction*(target-*value);
        if(step>maximum)step=maximum;else if(step < -maximum)step=-maximum;
        *value+=step;
    }
}
static int Player_actor_CulcAnimation_Base3(ACTOR *a,float *dummy) { (void)a; *dummy=0; return 1; }
#include "donor_player_exercise.inc"
#include "exercise_patterns.inc"

static int request(void *context,int cmd,float speed,int priority) {
    (void)context; port_events.request++;port_events.command=cmd;
    port_events.speed=speed;port_events.priority=priority;return request_ok;
}
static void wait_action(void *context,float morph,int flags,int priority) {
    (void)context;port_events.wait++;port_events.morph=morph;
    port_events.flags=flags;port_events.priority=priority;
}
static void settle(void *context) { (void)context;port_events.settle++; }
static void bee(void *context) { (void)context;port_events.bee++; }
static const AFExerciseCalls calls={0,request,wait_action,settle,bee};
static unsigned int comparisons;
static void load(PLAYER_ACTOR *a,const AFExercise *s) {
    memset(a,0,sizeof(*a));
    memcpy(a->radio_exercise_command_ring_buffer,s->ring,8);
    a->radio_exercise_command_ring_buffer_index=s->head;
    a->radio_exercise_ring_buffer_cmd_timer=s->hold;
    a->radio_exercise_continue_cmd_idx=s->continuation;
    a->radio_exercise_cmd_timer=s->timer;
    a->old_sound_frame_counter=s->old_sound_frame;
    a->main_data.radio_exercise=(mPlayer_main_radio_exercise_c){s->command,s->skip,s->settled,s->late};
    memset(&donor_events,0,sizeof(donor_events));memset(&port_events,0,sizeof(port_events));
}
static void compare(const PLAYER_ACTOR *a,const AFExercise *s) {
    assert(!memcmp(a->radio_exercise_command_ring_buffer,s->ring,8));
    assert(a->radio_exercise_command_ring_buffer_index==s->head);
    assert(a->radio_exercise_ring_buffer_cmd_timer==s->hold);
    assert(a->radio_exercise_continue_cmd_idx==s->continuation);
    assert(a->radio_exercise_cmd_timer==s->timer);
    assert(a->main_data.radio_exercise._08==s->settled);
    assert(a->main_data.radio_exercise._0C==s->late);
    assert(!memcmp(&donor_events,&port_events,sizeof(port_events)));comparisons++;
}
static u32 rng=1;
static u32 random_value(void) { rng=rng*1664525u+1013904223u;return rng; }

int main(void) {
    assert(sizeof(AFExercisePattern)==16);
    PLAYER_ACTOR actor;GAME game={&actor};AFExercise s;
    af_v3_exercise_init(&s,0);
    for(int round=0;round<2000;round++) {
        int cmd=round<110?6:(int)(random_value()%10)-1;
        load(&actor,&s);
        Player_actor_Set_RadioExerciseCommandRingBuffer(&actor,cmd);
        af_v3_exercise_push(&s,cmd);compare(&actor,&s);
        for(int continuation=-1;continuation<18;continuation++) {
            float a,b;s.continuation=continuation;load(&actor,&s);
            assert(Player_actor_Check_radio_exercise_command(&actor,continuation,&a)==af_v3_exercise_match(&s,patterns,&b));
            assert(a==b);comparisons++;
        }
    }
    for(int pattern=0;pattern<18;pattern++) {
        af_v3_exercise_init(&s,0);
        for(int k=0;k<patterns[pattern].length;k++)af_v3_exercise_push(&s,patterns[pattern].keys[k]);
        s.continuation=-1;float timer;
        /* A circle can match a shorter prefix first; compare the donor's exact
           table order, not an assumption that every gesture wins immediately. */
        load(&actor,&s);float reference;
        assert(af_v3_exercise_match(&s,patterns,&timer)==Player_actor_Check_radio_exercise_command(&actor,-1,&reference));
        assert(timer==reference);
        for(int t=0;t<8;t++)for(int skip=0;skip<2;skip++)for(int permitted=0;permitted<2;permitted++) {
            able=permitted;request_ok=t&1;s.timer=(float)t;s.continuation=-1;load(&actor,&s);
            int a=Player_actor_CheckAndRequest_main_radio_exercise_all(&game,skip);
            int b=af_v3_exercise_check(&s,patterns,able,skip,&calls);assert(a==b);compare(&actor,&s);
        }
        for(int step=0;step<220;step++) {
            able=step%5!=0;request_ok=1;s.command=pattern;
            s.continuation=step%19-1;s.timer=(float)(step%8);s.late=step%2;s.settled=step%3==0;
            load(&actor,&s);float frame=(float)step, end=pattern==3?161.0f:81.0f;
            actor.keyframe0.frame_control=(cKF_FrameControl_c){1,end,end,0.75f,frame};
            Player_actor_request_proc_index_fromRadio_exercise(&actor,&game,frame>=end);
            af_v3_exercise_finish(&s,patterns,able,frame,end,0.75f,frame>=end,&calls);compare(&actor,&s);
        }
        for(int tick=0;tick<80;tick++) {
            s.command=pattern;s.old_sound_frame=tick<40?(u32)tick:0xFFFFFFF0u;
            now=tick<40?(u32)(tick+tick%9):(u32)(tick-40);status=tick%3;tempo=tick%4?120:0;
            load(&actor,&s);float initial=(tick%12)*0.13f;actor.keyframe0.frame_control.speed=initial;
            assert(Player_actor_CulcAnimation_Radio_exercise(&actor)==1);
            float value=af_v3_exercise_speed(&s,patterns,initial,now,status,tempo);
            assert(fabsf(value-actor.keyframe0.frame_control.speed)<0.000001f);
            assert(actor.keyframe0.frame_control.speed==actor.keyframe1.frame_control.speed);comparisons++;
        }
    }
    const int buttons[16]={0,1,2,0,3,4,5,3,6,7,8,6,0,1,2,0};
    for(unsigned int i=0;i<16;i++) {
        assert(af_v3_exercise_buttons(i,0)==buttons[i]);assert(af_v3_exercise_buttons(i,1)==-1);
    }
    for(int flags=0;flags<8;flags++) {
        s.continuation=5;s.timer=3;af_v3_exercise_wait_setup(&s,flags);
        assert(s.skip==!(flags&4));assert(s.continuation==((flags&4)?5:-1));
        assert(s.timer==((flags&4)?3:0));
        int skip=s.skip;af_v3_exercise_input(&s,1,6);assert(s.ring[s.head]==(skip?-1:6));
    }
    for(int i=-2;i<20;i++) {
        unsigned int animation=af_v3_exercise_setup(&s,patterns,i);int expected=i>=0&&i<18?i:0;
        assert(animation==patterns[expected].animation && s.command==expected);
        assert(s.skip==1 && !s.settled && !s.late && s.continuation==-1 && s.timer==0);
    }
    printf("%u actual-donor exercise comparisons; C buttons, setup, and wait chaining pass\n",comparisons);
    return 0;
}
