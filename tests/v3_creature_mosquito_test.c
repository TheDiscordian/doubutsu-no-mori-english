/* Controlled native services exercise the complete player response, silently. */
#include "creature_insect_player.h"
#include "creature_insect_engine.h"
#include <assert.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_EXTENDED_PLAYER_FACES
#include "../overlays/v3/player_faces.c"
u32 af_test_native_eye[130],af_test_native_mouth[130],af_test_player_faces[320];

static union {max_align_t align;u8 data[0x13E0];} storage;
#define WORD(n) (*(u32 *)(storage.data+(n)))
#define REAL(n) (*(float *)(storage.data+(n)))
GAME *af_insect_game=(GAME *)(uintptr_t)0x1234;
const void *af_insect_demo_clip;
const u32 af_insect_mosquito_message=12032;
static int has_player=1,title,demo,status=1,able=1,requested,priority,animation,upper,setup;
static int loops,steps,ending,brakes,forced,collisions,items,settled,waiting,turned;
static int reporting,report_requests,message_id,starts,stops;
static void (*report_callback)(void *);
PLAYER_ACTOR *af_insect_native_player(GAME *g) {
    assert(g==af_insect_game);return has_player?(PLAYER_ACTOR *)storage.data:NULL;
}
static void actor(void *p) {assert(p==storage.data);}
static int is_title(void) {return title;}
static int is_demo(int index) {assert(index==(int)WORD(0xCF0));return demo;}
static int bee_status(void *p) {actor(p);return status;}
static int eligible(GAME *g,int index,int prio) {
    assert(g==af_insect_game && (index==107 || index==108));
    assert(prio==(index==107?25:26));return able;
}
static void request(GAME *g,int index,int prio) {assert(g==af_insect_game);requested=index;priority=prio;}
static void item_setup(void *p,int anim,float morph,int *out_upper,int *part) {
    actor(p);assert(morph==-5 && (anim==262 || anim==263));*out_upper=upper;*part=4;
}
static void init(void *p,GAME *g,int lower,int up,float a,float b,float speed,float morph,int mode,int part) {
    actor(p);assert(g==af_insect_game && up==upper && a==1 && b==1 && speed==.5f && morph==-5 && part==2);
    animation=lower;loops=mode;
}
static void init_loop(void *p,GAME *g,int low,int up,float a,float b,float speed,float morph,int part) {
    init(p,g,low,up,a,b,speed,morph,1,part);
}
static void base(void *p,GAME *g) {actor(p);assert(g==af_insect_game);setup++;}
static int brake(void *p,float amount) {actor(p);assert(amount==0.32625001f*2);brakes++;return 1;}
static void force(void *p,GAME *g) {actor(p);assert(g==af_insect_game);forced++;}
static int animate(void *p,float *last) {actor(p);*last=1;steps++;return ending;}
static void simple(void *p) {actor(p);}
static void collide(void *p,GAME *g) {actor(p);assert(g==af_insect_game);collisions++;}
static int item(void *p,GAME *g) {actor(p);assert(g==af_insect_game);items++;return 0;}
static void eye(void *p,int i) {actor(p);assert(i==4);WORD(0xCE8)=i;}
static void mouth(void *p,int i) {actor(p);assert(i==4);WORD(0xCEC)=i;}
static s16 turn(s16 *angle,s16 target,float rate,s16 max,s16 min) {
    assert(angle==(s16 *)(storage.data+0xDE) && !target && rate==0.2928932188f && max==2500 && min==50);
    *angle-=10;turned++;return *angle;
}
static int check(int type,void *p) {actor(p);assert(type==9);return reporting;}
static void demo_request(int type,void *p,void (*cb)(void *)) {
    actor(p);assert(type==9);report_callback=cb;report_requests++;
}
static void msg(int id) {message_id=id;}
static void name(int enabled) {assert(!enabled);}
static void camera(int mode) {assert(mode==5);}
static void listen(void) {}
static void colour(void *p) {assert(!memcmp(p,(u8[]){225,165,255,255},4));}
static void start(int track,int fade) {assert(track==68 && fade==0x168);starts++;}
static void stop(int track,int fade) {assert(track==68 && fade==0x168);stops++;}
static void settle(void *p) {actor(p);settled++;}
static int wait_action(GAME *g,float morph,int flags,int prio) {
    assert(g==af_insect_game && morph==-5 && !flags && prio==1);waiting++;return 1;
}
void *af_insect_player_resolve(u32 address) {
    switch(address) {
        case 0x8007D90C:return is_title;case 0x808B6424:return is_demo;case 0x808B3AE4:return bee_status;
        case 0x808B8874:return eligible;case 0x808B3334:return request;
        case 0x808B846C:return item_setup;case 0x808B4A44:return init;case 0x808B4924:return init_loop;
        case 0x808B3BD0:return base;case 0x808B3C10:return brake;case 0x808B61E4:return force;
        case 0x808B48F0:return animate;case 0x808B36F4:case 0x808B5310:case 0x808B5FB0:return simple;
        case 0x808B4DAC:return collide;case 0x808BF410:return item;
        case 0x808B36E8:return eye;case 0x808B37F8:return mouth;case 0x8009A974:return turn;
        case 0x8007CF00:return check;case 0x8007CDD8:return demo_request;
        case 0x8007B5C0:return msg;case 0x8007B79C:return name;case 0x8007BA1C:return camera;
        case 0x8007D098:return listen;case 0x8007B980:return colour;
        case 0x8005DF70:return start;case 0x8005E58C:return stop;
        case 0x808B3648:return settle;case 0x808C1064:return wait_action;
        default:assert(!"Unexpected mosquito binding");return NULL;
    }
}
int main(void) {
    af_test_native_eye[1]=123;af_test_native_mouth[1]=456;
    assert(af_v3_player_eye_sequence(1)==123 && af_v3_player_mouth_sequence(1)==456);
    u32 *face_words=af_test_player_faces;face_words[0]=0x41465046;face_words[1]=2;face_words[2]=157;face_words[3]=8;
    face_words[318]=0x80671000;face_words[319]=0x80671117;
    face_words[4+132*2]=0x80671010;face_words[5+132*2]=0x80671030;
    assert(af_v3_player_eye_sequence(262)==0x80671010 && af_v3_player_mouth_sequence(262)==0x80671030);
    face_words[4+132*2]=0x80671117;assert(!af_v3_player_eye_sequence(262));
    face_words[318]=0;assert(!af_v3_player_mouth_sequence(262));face_words[1]=1;
    face_words[4+132*2]=0x804B4C10;assert(af_v3_player_eye_sequence(262)==0x804B4C10);
    void *label=(void *)(uintptr_t)0x80400120,*p=storage.data;
    WORD(0xCF0)=7;WORD(0xD58)=0xF1234567;
    has_player=0;assert(!mPlib_request_main_stung_mosquito_type1(label));has_player=1;
    title=1;assert(!mPlib_request_main_stung_mosquito_type1(label));title=0;
    af_insect_demo_clip=p;assert(!mPlib_request_main_stung_mosquito_type1(label));af_insect_demo_clip=NULL;
    demo=1;assert(!mPlib_request_main_stung_mosquito_type1(label));demo=0;
    status=0;assert(!mPlib_request_main_stung_mosquito_type1(label));status=1;
    able=0;assert(!mPlib_request_main_stung_mosquito_type1(label));able=1;
    assert(!requested && WORD(0xD58)==0xF1234567);
    WORD(0xCF0)=51;WORD(0xD10)=0;
    assert(!mPlib_request_main_stung_mosquito_type1(label) && WORD(0xD10)==1 && !requested);
    WORD(0xCF0)=7;assert(mPlib_request_main_stung_mosquito_type1(label));
    assert(requested==107 && priority==25 && WORD(0xD58)==(u32)(uintptr_t)label);
    assert(!mPlib_Check_stung_mosquito(label));WORD(0xCF0)=107;
    assert(mPlib_Check_stung_mosquito(label) && !mPlib_Check_stung_mosquito((void *)(uintptr_t)1));
    upper=9;af_insect_mosquito_setup(p,af_insect_game);
    assert(animation==262 && !loops && setup==1 && WORD(0xD10)==(u32)(uintptr_t)label);
    af_insect_mosquito_main(p,af_insect_game);
    assert(requested==107 && steps==2 && brakes==1 && collisions==1 && forced==1 && items==1);
    ending=1;af_insect_mosquito_main(p,af_insect_game);assert(requested==108 && priority==26);
    WORD(0xCF0)=108;assert(mPlib_Check_stung_mosquito(label));
    af_insect_mosquito_notice_setup(p,af_insect_game);
    assert(animation==263 && loops && setup==2 && WORD(0xD10)==(u32)(uintptr_t)label);
    assert(!REAL(0xD14) && !WORD(0xD18) && WORD(0xCE8)==4 && WORD(0xCEC)==4);
    af_insect_mosquito_notice_main(p,af_insect_game);
    assert(WORD(0xD18)==1 && report_requests==1 && !waiting && turned==2);
    report_callback(p);assert(message_id==12032 && starts==1);
    reporting=1;af_insect_mosquito_notice_main(p,af_insect_game);assert(WORD(0xD18)==2 && !waiting);
    reporting=0;af_insect_mosquito_notice_main(p,af_insect_game);
    assert(WORD(0xD18)==3 && waiting==1 && settled==1);
    af_insect_mosquito_settle(p,af_insect_game);assert(stops==1);
    WORD(0xCF0)=7;assert(!mPlib_Check_stung_mosquito(label));
    assert(steps==10 && brakes==5 && collisions==5 && forced==5 && items==5);
    /* Existing player extensions beyond the native action unions stay untouched. */
    for (unsigned i=0x12D8;i<sizeof storage.data;i++) assert(!storage.data[i]);
    puts("Complete mosquito request, fishing interruption, motions, message, and cleanup: passed");
}
