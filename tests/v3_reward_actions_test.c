#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_requests.c"
#undef native
#undef FN
#define AF_V3_REWARD_EVENT 0x804B25E0u
#include "../overlays/v3/reward_wait.c"

static alignas(16) u8 actor[0x1400],game[16],before[0x1400];
static char calls[64];static int count,allowed,missing,wanted_action,wanted_priority,upper,part,continued;
static void log_call(char c) { assert(count<63);calls[count++]=c;calls[count]=0; }
static void clear_calls(void) { count=0;calls[0]=0; }
static void actor_check(void *p) { assert(p==actor); }
static void game_check(void *p) { assert(p==game); }
static int able(void *g,int action,int priority) {
    game_check(g);assert(action==wanted_action && priority==wanted_priority);log_call('C');return allowed;
}
static void *get(void *g) { game_check(g);log_call('G');return missing?0:actor; }
static void request(void *g,int action,int priority) {
    game_check(g);assert(action==wanted_action && priority==wanted_priority);log_call('Q');
    WORD(actor,0xD00)=action;WORD(actor,0xD04)=priority;WORD(actor,0xD08)=1;
}
void *af_test_reward_route_function(u32 address) {
    switch(address) {
    case 0x808B8874:return able;
    case 0x800B1C84:return get;
    case 0x808B3334:return request;
    default:assert(!"Unexpected request API");return 0;
    }
}
static void item_setup(void *p,int anim,float morph,int *u,int *mask) {
    actor_check(p);assert(anim==0 && morph==-5);*u=upper;*mask=part;log_call('I');
}
static void animation(void *p,void *g,int low,int up,float f0,float f1,float speed,float morph,int mask) {
    actor_check(p);game_check(g);assert(low==0 && up==upper && speed==1 && mask==part);
    assert(f0==(continued?7.0f:1.0f) && f1==(continued?13.0f:1.0f) && morph==(continued?0.0f:-5.0f));log_call('A');
}
static void setup(void *p,void *g) { actor_check(p);game_check(g);log_call('S'); }
static void reinput(void *p,void *g) { actor_check(p);game_check(g);log_call('R'); }
static int calc(void *p) { actor_check(p);log_call('C');return 0; }
static void lean(void *p) { actor_check(p);log_call('L'); }
static void eyes(void *p) { actor_check(p);log_call('E'); }
static void stand(void *p,void *g) { actor_check(p);game_check(g);log_call('S'); }
static void background(void *p) { actor_check(p);log_call('B'); }
static void held(void *p,void *g) { actor_check(p);game_check(g);log_call('H'); }
static int event(void *g,int type) { assert(type==0);log_call('V');return af_v3_reward_event(g,type); }
void *af_test_reward_wait_function(u32 address) {
    switch(address) {
    case 0x808B846C:return item_setup;
    case 0x808B4924:return animation;
    case 0x808B3BD0:return setup;
    case 0x808B61E4:return reinput;
    case 0x808B482C:return calc;
    case 0x808B5310:return lean;
    case 0x808B36F4:return eyes;
    case 0x808B4DAC:return stand;
    case 0x808B5FB0:return background;
    case 0x808BF410:return held;
    case AF_V3_REWARD_EVENT:return event;
    default:assert(!"Unexpected wait API");return 0;
    }
}
int main(void) {
    for(wanted_action=118;wanted_action<=120;wanted_action++) for(int type=0;type<(wanted_action==120?1:4);type++)
        for(allowed=0;allowed<2;allowed++) for(missing=0;missing<2;missing++) {
            memset(actor,0xA5,sizeof(actor));memcpy(before,actor,sizeof(actor));wanted_priority=34;clear_calls();
            int accepted=allowed && !missing;
            assert(af_v3_reward_request(game,wanted_action,type,wanted_priority)==accepted);
            assert(!strcmp(calls,!allowed?"C":missing?"CG":"CGQ"));
            if(accepted) {
                WORD(before,0xD00)=wanted_action;WORD(before,0xD04)=wanted_priority;WORD(before,0xD08)=1;
                if(wanted_action!=120) WORD(before,0xD58)=type;
            }
            assert(!memcmp(actor,before,sizeof(actor)));
        }
    allowed=1;missing=0;wanted_action=119;wanted_priority=34;clear_calls();
    assert(af_v3_reward_event(game,2)==1 && WORD(actor,0xD58)==2);
    wanted_action=120;wanted_priority=33;clear_calls();
    assert(af_v3_reward_axe_wait_request(game)==1 && WORD(actor,0xD58)==2);
    wanted_action=118;wanted_priority=31;clear_calls();
    af_v3_reward_submenu(actor,game);assert(WORD(actor,0xD58)==3 && !strcmp(calls,"CGQ"));
    clear_calls();memcpy(before,actor,sizeof(actor));
    assert(!af_v3_reward_request(0,118,0,1));assert(!af_v3_reward_request(game,117,0,1));
    assert(!af_v3_reward_request(game,121,0,1));assert(!af_v3_reward_request(game,118,-1,1));
    assert(!af_v3_reward_request(game,119,4,1));assert(!af_v3_reward_request(game,120,1,1));
    assert(!count && !memcmp(actor,before,sizeof(actor)));
    for(int variant=0;variant<6;variant++) {
        memset(actor,0xA5,sizeof(actor));upper=variant==5?9:0;part=variant==5?3:0;
        REAL(actor,0x194)=variant==1?1.0f:0.0f;WORD(actor,0xDAC)=variant==2?1:0;
        WORD(actor,0xDB0)=variant==3?7:upper;
        if(variant==4) { upper=9;WORD(actor,0xDB0)=9; }
        REAL(actor,0x184)=7;REAL(actor,0x1F4)=13;continued=variant==0 || variant==5;
        memcpy(before,actor,sizeof(actor));clear_calls();af_v3_reward_wait_setup(actor,game);
        REAL(before,0xD10)=0;assert(!strcmp(calls,"IAS") && !memcmp(actor,before,sizeof(actor)));
    }
    wanted_action=119;wanted_priority=34;
    for(int frame=0;frame<160;frame++) {
        clear_calls();af_v3_reward_wait_main(actor,game);
        assert(!strcmp(calls,"RCLESBH") && REAL(actor,0xD10)==2.0f*(frame+1));
    }
    allowed=0;clear_calls();af_v3_reward_wait_main(actor,game);
    assert(!strcmp(calls,"RCLESBHVC") && REAL(actor,0xD10)==320);
    allowed=1;clear_calls();af_v3_reward_wait_main(actor,game);
    assert(!strcmp(calls,"RCLESBHVCGQ") && WORD(actor,0xD00)==119 && WORD(actor,0xD58)==0);
    clear_calls();af_v3_reward_wait_setup(0,game);af_v3_reward_wait_setup(actor,0);
    af_v3_reward_wait_main(0,game);af_v3_reward_wait_main(actor,0);assert(!count);
    puts("pass: source request priorities, bounded writes, idle continuity, complete axe wait and retry");
}
