#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/player_exercise_native.h"
#include "exercise_patterns.inc"
typedef struct {float x,y,z;} Position;
typedef struct {unsigned char prefix[0x28];struct {Position position;} world;} ACTOR;
static union {double align;unsigned char bytes[AF_EXERCISE_PLAYER_BYTES+16];} storage;
static void *player=storage.bytes,*game=(void *)0x1234;
static unsigned int clock_value,held;
static unsigned short count=4;
static unsigned char handle=1,test_field_type=1;
static union {double align;unsigned char bytes[4*0x160];} audio;
static int events[2],held_item,shrine=1,block=1,px=2,pz=3,bgm=27;
static int demo,pickup,shake,request_able=1,requests,waits,settles,bees;
static int updates,wait_updates,wait_setups,physics,animations,eyes,inits,camera_calls;
static float stick;
#define WORD(n) (*(int *)(storage.bytes+(n)))
#define REAL(n) (*(float *)(storage.bytes+(n)))
#define STATE ((AFExercise *)(storage.bytes+AF_EXERCISE_STATE_OFFSET))

void *af_test_exercise_memory(unsigned int address) {
    switch(address) {
        case 0x8014BDA0:return &clock_value;
        case 0x80113848:return &handle;
        case 0x8014BD60:return &count;
        case 0x80136EA1:return &test_field_type;
    }
    assert(address>=0x8014CB90u && address<0x8014CB90u+sizeof(audio.bytes));
    return audio.bytes+address-0x8014CB90u;
}
static int event(int id,int status) {assert(status==16);assert(id==16||id==8);return events[id==8];}
static int shrine_block(int *x,int *z,int kind) {assert(kind==4);*x=2;*z=3;return shrine;}
static int player_block(int *x,int *z,Position p) {assert(p.x==50.0f);*x=px;*z=pz;return block;}
static int current_bgm(void) {return bgm;}
static int title_demo(void) {return demo;}
static float old_stick(void) {return stick;}
static int get_pickup(void *g) {assert(g==game);return pickup;}
static int get_shake(void *g) {assert(g==game);return shake;}
static int get_button(int mask) {return (held&(unsigned int)mask)!=0;}
static int able_request(void *g,int action,int priority) {assert(g==game&&action==111&&priority==4);return request_able;}
static void request_action(void *g,int action,int priority) {
    assert(g==game&&action==111&&priority==4);assert(WORD(0xD58)>=0&&WORD(0xD58)<18);++requests;
}
static int request_wait(void *g,float morph,int flags,int priority) {
    assert(g==game&&morph==-5.0f&&flags==4&&priority==1);++waits;return 1;
}
static void settle(void *p) {assert(p==player);++settles;}
static void bee(void *p,int status) {assert(p==player&&status==1);++bees;}
static void init(void *p,void *g) {assert(p==player&&g==game);++inits;}
static void after(void *p,void *g) {assert(p==player&&g==game);++updates;}
static int camera(void *p) {assert(p==player);++camera_calls;return 7;}
static void wait_setup(void *p,void *g) {assert(p==player&&g==game);++wait_setups;}
static void native_wait(void *p,void *g) {assert(p==player&&g==game);++wait_updates;}
static void animation_init(void *p,void *g,int a,int b,float x,float y,float speed,float morph,int mode,int part) {
    assert(p==player&&g==game&&a==b&&a>=274&&a<=285);
    assert(x==1.0f&&y==1.0f&&speed==0.0f&&morph==-5.0f&&mode==0&&part==0);
    REAL(0x184)=REAL(0x1F4)=1.0f;REAL(0x178)=a==277?161.0f:81.0f;
}
static void base(void *p,void *g) {assert(p==player&&g==game);}
static void brake(void *p) {assert(p==player);++physics;}
static void actor_noop(void *p) {assert(p==player);}
static void eye(void *p) {assert(p==player);++eyes;}
static int animate(void *p,float *last) {
    assert(p==player);assert(REAL(0x180)==REAL(0x1F0));++animations;
    *last=REAL(0x184);REAL(0x184)+=REAL(0x180);
    if (REAL(0x184)>=REAL(0x178)) {REAL(0x184)=REAL(0x178);return 1;}
    return 0;
}
void *af_test_exercise_resolve(unsigned int address) {
    switch(address) {
        case 0x8007FF08:return event;
        case 0x80089440:return shrine_block;
        case 0x80088710:return player_block;
        case 0x8005EAFC:return current_bgm;
        case 0x8007D90C:return title_demo;
        case 0x808B32C4:return old_stick;
        case 0x808B2D50:return get_pickup;
        case 0x808B3010:return get_shake;
        case 0x80078D30:return get_button;
        case 0x808B8874:return able_request;
        case 0x808B3334:return request_action;
        case 0x808C1064:return request_wait;
        case 0x808B3648:return settle;
        case 0x808B3AF0:return bee;
        case 0x804AC8AC:return init;
        case 0x808BD218:return after;
        case 0x808BBDE8:return camera;
        case 0x808C1118:return wait_setup;
        case 0x808C1370:return native_wait;
        case 0x808B4A44:return animation_init;
        case 0x808B3BD0:case 0x808B61E4:case 0x808B4DAC:case 0x808BF410:return base;
        case 0x808B3C74:return brake;
        case 0x808B48F0:return animate;
        case 0x808B5310:case 0x808B5FB0:return actor_noop;
        case 0x808B36F4:return eye;
    }
    assert(!"Unexpected native dependency");return 0;
}

/* These two functions are read from the actual GAFE01 source. Their event
   names are mapped to the independently checked native calendar IDs. */
#define VER_GAFE01_00 0
#define VERSION 0
#define mEv_EVENT_MORNING_AEROBICS 16
#define mEv_EVENT_SPORTS_FAIR_AEROBICS 8
#define mEv_STATUS_RUN 16
#define mRF_BLOCKKIND_SHRINE 4
#define mFI_FIELDTYPE2_FG 0
#define TRUE 1
#define FALSE 0
#define mEv_check_status event
#define mFI_BlockKind2BkNum shrine_block
#define mFI_Wpos2BlockNum player_block
#define Common_Get(name) test_field_type
#define aMR_RadioBgmNow() (bgm==27)
#define mPlib_Check_now_handin_item() held_item
#include "donor_player_exercise_native.inc"

int main(void) {
    memset(storage.bytes,0xA5,sizeof(storage.bytes));REAL(0x28)=50.0f;
    storage.bytes[0x1117]=255;clock_value=10;
    af_v3_exercise_native_init(player,game);assert(inits==1&&STATE->old_sound_frame==10);
    for(int i=0;i<8;++i)assert(STATE->ring[i]==-1);
    unsigned comparisons=0;
    for(int bits=0;bits<256;++bits) {
        events[0]=bits&1;events[1]=bits&2;shrine=!!(bits&4);block=!!(bits&8);
        px=bits&16?2:1;test_field_type=!!(bits&32);bgm=bits&64?27:0;
        held_item=!!(bits&128);storage.bytes[0x1117]=held_item?1:255;
        assert(af_v3_exercise_native_able(player)==Player_actor_Check_AbleRadioExercise(player));++comparisons;
    }
    events[0]=events[1]=0;test_field_type=1;bgm=27;storage.bytes[0x1117]=255;
    assert(af_v3_exercise_native_camera(player)==0&&camera_calls==0);
    bgm=0;assert(af_v3_exercise_native_camera(player)==7&&camera_calls==1);bgm=27;
    for(unsigned int b=0;b<16;++b) {
        held=b;assert(af_v3_exercise_native_input(player,game)==af_v3_exercise_buttons(b,0));
        for(int j=0;j<5;++j) {
            demo=j==0;stick=j==1?1.0f:0.0f;pickup=j==2;shake=j==3;storage.bytes[0x1117]=j==4?0:255;
            assert(af_v3_exercise_native_input(player,game)==-1);
        }
        demo=pickup=shake=0;stick=0.0f;storage.bytes[0x1117]=255;
    }
    unsigned char *group=audio.bytes+0x160;group[0]=0x80;group[4]=181;
    *(unsigned short *)(group+8)=5760;int tempo=-9;
    assert(af_v3_exercise_native_tempo(&tempo)==0&&tempo==120);
    group[4]=180;assert(af_v3_exercise_native_tempo(&tempo)==-1);group[4]=181;
    group[0]=0;assert(af_v3_exercise_native_tempo(&tempo)==-1);group[0]=0x80;
    handle=4;assert(af_v3_exercise_native_tempo(&tempo)==-1);handle=1;
    /* All complete command patterns enter through the installed WAIT wrapper. */
    static const unsigned char buttons[9]={0,1,2,4,5,6,8,9,10};
    for(int cmd=0;cmd<18;++cmd) {
        af_v3_exercise_native_init(player,game);WORD(0xD5C)=0;
        af_v3_exercise_native_wait_setup(player,game);held=0;
        af_v3_exercise_native_wait(player,game);int previous=requests;
        const AFExercisePattern *pattern=af_v3_exercise_patterns+cmd;
        for(int j=0;j<pattern->length;++j) {held=buttons[(int)pattern->keys[j]];af_v3_exercise_native_wait(player,game);}
        for(int j=0;j<4;++j)af_v3_exercise_native_wait(player,game);
        assert(requests>previous);assert(WORD(0xD58)==cmd);
        WORD(0xD58)=cmd;REAL(0xD5C)=0.25f;
        af_v3_exercise_native_setup(player,game);assert(STATE->command==cmd&&REAL(0x180)==0.25f);
        held=0;int a=animations,b=physics,e=eyes,w=waits,s=settles;
        for(int frame=0;frame<300&&waits==w;++frame) {
            clock_value+=2;af_v3_exercise_native_main(player,game);af_v3_exercise_native_after(player,game);
            assert(STATE->old_sound_frame==clock_value);
        }
        assert(waits>w&&settles>s&&settles==bees);
        assert(animations-a==2*(physics-b)&&eyes-e==physics-b);
    }
    /* Re-entering an actor at the same address must not inherit gesture state. */
    memset(STATE,0xCC,sizeof(*STATE));clock_value=0xFFFFFFFFu;
    af_v3_exercise_native_init(player,game);assert(STATE->old_sound_frame==clock_value&&STATE->continuation==-1);
    clock_value=0;af_v3_exercise_native_after(player,game);assert(STATE->old_sound_frame==0);
    for(unsigned i=AF_EXERCISE_PLAYER_BYTES;i<sizeof(storage.bytes);++i)assert(storage.bytes[i]==0xA5);
    assert(wait_updates&&wait_setups==18&&updates);
    printf("%u donor eligibility comparisons; 18 native-adapter gesture/animation/exit paths\n",comparisons);
}
