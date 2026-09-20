#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/balloon_actor.c"
#include "../overlays/v3/balloon_release.c"
#include "../overlays/v3/balloon_look.c"
#include "../overlays/v3/balloon_fall.c"
#include "../overlays/v3/reward_deferred.c"

static alignas(16) u8 player[0x13B0],game[16],private_data[0x400],change[0x30];
u8 *af_test_balloon_private=private_data;
u32 af_test_balloon_segment;
static Balloon balloon,other;
static void *owned,*requested,*released;
static int selected=255,accepted=1,demo,requests,settled,waits,rewards,old_look,old_setup;
static int priority_seen,type_seen,recovery_kind,recoveries,setup_calls,base_calls,head_calls,atan_calls;
static int targets[4],steps[4];static float ratios[4];
static s16 atan_y,atan_x;
static float distance_result=50;

void *af_test_balloon_pointer(void *p,u32 at) {
    assert(p==player);
    if(at==0x13A0)return owned;
    if(at==0xD6C)return requested;
    if(at==0xD14)return released;
    assert(!"Unexpected pointer read");return 0;
}
void af_test_balloon_set_pointer(void *p,u32 at,void *value) {
    assert(p==player && at==0xD14);released=value;
}
int af_v3_player_selected_equipment(u32 item) {
    unsigned shape=item-0x2244;
    return shape<8u && (selected&(1<<shape))?(int)(91+shape):-1;
}
void af_v3_balloon_draw(Balloon *b,void *g) {(void)b;(void)g;}
static void *get_player(void *g) {assert(g==game);return player;}
static void *get_change(void) {return change;}
static int native_request(void *g,int type,const void *data,void *existing,int priority) {
    assert(g==game);requests++;priority_seen=priority;type_seen=type;
    if(accepted) {BWORD(player,0xD58)=type;memcpy(player+0xD5C,data,16);requested=existing;BWORD(player,0xD70)=0;}
    return accepted;
}
static float sine(s16 a) {assert(a==123);return .6f;}
static float cosine(s16 a) {assert(a==123);return .8f;}
static void item_setup(void *p,int anim,float morph,int *animation,int *part) {
    assert(p==player && anim==0 && morph==-5);*animation=13;*part=3;setup_calls++;
}
static void animation_setup(void *p,void *g,int a,int b,float s,float e,float speed,float morph,int part) {
    assert(p==player && g==game && a==0 && b==13 && s==1 && e==1 && speed==1 && morph==-5 && part==3);
    setup_calls++;
}
static void setup_base(void *p,void *g) {assert(p==player && g==game);base_calls++;}
static void settle(void *p) {assert(p==player);settled++;}
static int wait(void *g,float morph,int flags,int priority) {
    assert(g==game && morph==-5 && !flags && priority==1);waits++;return accepted;
}
int af_v3_reward_request(void *g,int action,int type,int priority) {
    assert(g==game && action==118 && type==3 && priority==34);rewards++;return accepted;
}
static void native_look(void *p) {assert(p==player);old_look++;}
static void native_setup(void *p,void *g) {assert(p==player && g==game);old_setup++;}
static float distance(float x,float z) {assert(x==20 && z==30);return distance_result;}
static s16 atan2short(float a,float b) {
    if(atan_calls++%2==0) {assert(a==30 && b==20);return atan_y;}
    assert(a==distance_result && b==80);return atan_x;
}
static void smooth(s16 *p,s16 target,float ratio,s16 maximum,s16 minimum) {
    assert(head_calls<4 && p==&BSHORT(player,head_calls%2?0x1138:0x1136) && !minimum);
    targets[head_calls]=target;ratios[head_calls]=ratio;steps[head_calls]=maximum;head_calls++;
}
static int title_demo(void) {return demo;}
void af_v3_tool_getup(void *p,void *g,int kind,float morph) {
    assert(p==player && g==game && morph==-5);recovery_kind=kind;recoveries++;
}
void *af_test_balloon_function(u32 at) {
    switch(at) {
    case 0x800B1C84:return get_player;
    case 0x800B1F74:return get_change;
    case 0x808D71F8:return native_request;
    case 0x80099A94:return sine;
    case 0x80099A54:return cosine;
    case 0x808B846C:return item_setup;
    case 0x808B4924:return animation_setup;
    case 0x808B3BD0:return setup_base;
    case 0x808B3648:return settle;
    case 0x808C1064:return wait;
    case 0x808D7570:return native_look;
    case 0x808D72E0:return native_setup;
    case 0x800DADC4:return distance;
    case 0x800E0008:return atan2short;
    case 0x8009A974:return smooth;
    case 0x8007D90C:return title_demo;
    default:assert(!"Unexpected balloon consumer API");return 0;
    }
}
void *af_test_deferred_function(u32 at) {return af_test_balloon_function(at);}

static void reset_counters(void) {
    requests=settled=waits=rewards=old_look=old_setup=setup_calls=base_calls=head_calls=atan_calls=recoveries=0;
}
static void request_checks(void) {
    int data[4]={0,2,3,4};owned=&balloon;
    for(int shape=0;shape<8;shape++) for(int flag=0;flag<2;flag++) for(accepted=0;accepted<2;accepted++) {
        reset_counters();data[0]=shape;BWORD(player,0xD70)=77;requested=&other;
        assert(af_v3_balloon_request(game,2,flag,data,0,31)==accepted);
        assert(requests==1 && priority_seen==31 && type_seen==2 && BWORD(player,0xD70)==(accepted?flag:77));
        if(accepted) assert(!memcmp(player+0xD5C,data,16) && requested==0);
        else assert(requested==&other);
    }
    accepted=1;data[0]=7;
    for(int mode=0;mode<4;mode++) {
        reset_counters();owned=mode==0?0:&balloon;selected=mode==1?127:255;data[0]=mode==2?8:7;
        u8 before[sizeof(player)];memcpy(before,player,sizeof(player));
        assert(!af_v3_balloon_request(game,2,0,data,mode==3?&other:0,30));
        assert(!requests && !memcmp(before,player,sizeof(player)));
    }
    selected=255;owned=&balloon;data[0]=7;reset_counters();
    assert(af_v3_balloon_request(game,2,0,data,&balloon,30) && requested==&balloon && priority_seen==30);
    for(int type=0;type<2;type++) {
        BWORD(change,8)=type;BWORD(change,0x20)=1;memcpy(change+12,data,16);reset_counters();
        af_v3_balloon_submenu(player,game);
        assert(requests==1 && type_seen==type && BWORD(player,0xD70)==1);
        af_v3_balloon_release_setup(player,game);assert(old_setup==1 && BWORD(player,0xD20)==1);
        BWORD(player,0xD10)=type;af_v3_balloon_look(player);assert(old_look==1 && !head_calls);
        BREAL(player,0xD18)=41;af_v3_balloon_release_transition(player,game);
        assert(settled==1 && rewards==1 && !waits);
    }
}
static void queue_checks(void) {
    for(int shape=0;shape<8;shape++) for(int flag=0;flag<2;flag++) {
        memset(change,0xA5,sizeof(change));owned=&balloon;selected=255;
        assert(af_v3_balloon_queue(game,0x2244+shape,flag)==1);
        assert(BWORD(change,0)==81 && BWORD(change,4)==1 && BWORD(change,8)==2 && BWORD(change,12)==shape);
        for(int at=16;at<32;at+=4)assert(!BWORD(change,at));
        assert(BWORD(change,0x20)==flag && BWORD(change,0x24)==(int)0xA5A5A5A5u);
    }
    for(int mode=0;mode<4;mode++) {
        memset(change,0xA5,sizeof(change));owned=mode==0?0:&balloon;selected=mode==1?127:255;
        assert(!af_v3_balloon_queue(mode==2?0:game,mode==3?0x224C:0x224B,1));
        for(unsigned i=0;i<sizeof(change);i++)assert(change[i]==0xA5);
    }
    owned=&balloon;selected=255;
}
static void setup_checks(void) {
    BWORD(player,0xD58)=2;BSHORT(player,0xDE)=123;BPOS(player,0x28)=(BalloonPosition){100,200,300};
    for(int shape=0;shape<8;shape++) {
        BWORD(player,0xD5C)=shape;BWORD(player,0xD70)=1;requested=0;owned=&balloon;reset_counters();
        af_v3_balloon_release_setup(player,game);
        assert(released==&balloon && balloon.type==shape && balloon.pending==1);
        assert(balloon.angle.x==0 && balloon.angle.y==123 && balloon.angle.z==0 && balloon.lean==0);
        assert(balloon.position.x==115.5f && balloon.position.y==217.5f && balloon.position.z==300.5f);
        assert(balloon.frame==-1 && balloon.speed==7 && BWORD(player,0xD1C)==1 && BWORD(player,0xD20)==1);
        assert(BWORD(player,0xD10)==2 && !BREAL(player,0xD18) && !BWORD(player,0x13A4));
        assert(setup_calls==2 && base_calls==1 && !old_setup);
    }
    requested=&balloon;balloon.frame=13;af_v3_balloon_release_setup(player,game);
    assert(!BWORD(player,0xD1C) && balloon.frame==13 && released==&balloon);
    owned=0;requested=0;af_v3_balloon_release_setup(player,game);
    assert(!released && BWORD(player,0x13A4)==1);owned=&balloon;
}
static void look_checks(void) {
    BWORD(player,0xD10)=2;BPOS(player,0x48)=(BalloonPosition){10,20,30};
    BPOS(&balloon,0x28)=(BalloonPosition){30,50,60};BSHORT(player,0xDC)=0;BSHORT(player,0xDE)=0;
    for(int mode=0;mode<5;mode++) {
        reset_counters();released=mode==0?0:&balloon;balloon.mode=mode==1?1:0;balloon.pending=mode==2?1:-1;
        if(mode==4)balloon.pending=0;
        atan_y=20000;atan_x=-12000;BREAL(player,0xD18)=0;
        af_v3_balloon_look(player);
        int live=mode==1 || mode==2 || mode==4;
        assert(BWORD(player,0x13A4)==!live && head_calls==4 && !old_look);
        assert(released==(live?&balloon:0));
        for(int i=0;i<4;i++) {
            assert(targets[i]==(live?(i%2?-0x1555:0x2AAA):0));
            assert(steps[i]==(live || i%2==0?500:200));
            assert(ratios[i]==(live?.1339745962f:.2928932309f));
        }
    }
    released=&balloon;balloon.mode=1;BSHORT(player,0xDE)=32760;BSHORT(player,0xDC)=-32760;
    atan_y=-32760;atan_x=32760;reset_counters();af_v3_balloon_look(player);
    assert(targets[0]==16 && targets[1]==-16);
    for(int mode=0;mode<2;mode++) {
        reset_counters();BREAL(player,0xD18)=mode?0:30;distance_result=mode?9:50;
        af_v3_balloon_look(player);assert(!atan_calls && !targets[0] && !targets[1]);
    }
    for(int flag=0;flag<2;flag++) {
        reset_counters();BWORD(player,0xD20)=flag;BREAL(player,0xD18)=40;BWORD(player,0x13A4)=1;
        af_v3_balloon_release_transition(player,game);assert(!settled);
        BWORD(player,0x13A4)=0;
        for(int i=0;i<60;i++)af_v3_balloon_release_transition(player,game);
        assert(!settled && BREAL(player,0xD18)==101);
        BWORD(player,0x13A4)=1;af_v3_balloon_release_transition(player,game);
        assert(settled==1 && waits==!flag && rewards==flag && BREAL(player,0xD18)==42);
    }
}
static void fall_checks(void) {
    BSHORT(player,0x1370)=100;BSHORT(player,0x1372)=-10;BSHORT(player,0x1388)=20;
    BSHORT(player,0x1376)=-70;BSHORT(player,0xDE)=80;BREAL(player,0xA28)=12.5f;
    BPOS(player,0x103C)=(BalloonPosition){14,25,36};
    for(int shape=0;shape<8;shape++) for(int mode=0;mode<4;mode++) {
        reset_counters();owned=mode==0?0:&balloon;selected=mode==1?0:255;demo=mode==3;
        BSHORT(private_data,0x3EC)=(s16)(0x2244+shape);balloon.pending=-1;
        af_v3_balloon_getup(player,game,91+shape,-5);
        int flies=mode>=2;
        assert(recoveries==1 && recovery_kind==(flies?-1:91+shape));
        assert(BWORD(player,0x13A8)==(flies?shape:-1));
        assert(BSHORT(private_data,0x3EC)==(mode==2?0:0x2244+shape));
        if(flies) {
            assert(balloon.pending==1 && balloon.type==shape && balloon.frame==12.5f && balloon.speed==7);
            assert(balloon.angle.x==110 && balloon.angle.y==80 && !balloon.angle.z && balloon.lean==-70);
            assert(!memcmp(&balloon.position,player+0x103C,sizeof(BalloonPosition)));
        } else assert(balloon.pending==-1);
        af_v3_balloon_getup_transition(player,game,0);assert(!requests && !settled);
        af_v3_balloon_getup_transition(player,game,1);
        assert(requests==flies && settled==!flies && waits==!flies);
        if(flies) assert(requested==&balloon && priority_seen==30 && BWORD(player,0xD5C)==shape && !BWORD(player,0xD70));
    }
    for(int kind=-1;kind<100;kind++) if(kind<91 || kind>98) {
        af_v3_balloon_getup(player,game,kind,-5);assert(recovery_kind==kind && BWORD(player,0x13A8)==-1);
    }
}
int main(void) {
    request_checks();queue_checks();setup_checks();look_checks();fall_checks();
    puts("pass: all balloon shapes, original creatures, source pose, head tracking, timing, fall loss and rejection");
}
