#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_deferred.c"
static alignas(16) u8 actor[0x1400],game[16],change[0x50];
static int accepted,calls;static char events[32];
static void log_call(char c) { assert(calls<31);events[calls++]=c;events[calls]=0; }
static void reset(void) { calls=0;events[0]=0; }
static void *get_change(void) { log_call('C');return change; }
static int bury_request(void *g,const void *p,int item,int priority) {
    assert(g==game && p==change+8 && item==0x1234 && priority==31);log_call('B');
    if(accepted) WORD(actor,0xD70)=0;
    return accepted;
}
static int release_request(void *g,int type,const void *p,void *existing,int priority) {
    assert(g==game && type==1 && p==change+12 && !existing && priority==31);log_call('R');
    if(accepted) WORD(actor,0xD70)=0;
    return accepted;
}
static void setup_bury(void *p,void *g) { assert(p==actor && g==game);WORD(actor,0xD20)=99;log_call('b'); }
static void setup_release(void *p,void *g) { assert(p==actor && g==game);WORD(actor,0xD20)=99;log_call('r'); }
static void fill(void *p,void *g,int ended) { assert(p==actor && g==game && (ended==0 || ended==1));log_call('F'); }
static void settle(void *p) { assert(p==actor);log_call('P'); }
static int wait(void *g,float morph,int mask,int priority) {
    assert(g==game && morph==-5 && !mask && priority==1);log_call('W');return accepted;
}
int af_v3_reward_request(void *g,int action,int type,int priority) {
    assert(g==game && action==118 && type==3 && priority==34);log_call('G');return accepted;
}
void *af_test_deferred_function(u32 address) {
    switch(address) {
    case 0x800B1F74:return get_change;
    case 0x808D2458:return bury_request;
    case 0x808D71F8:return release_request;
    case 0x808D251C:return setup_bury;
    case 0x808D72E0:return setup_release;
    case 0x808D10D8:return fill;
    case 0x808B3648:return settle;
    case 0x808C1064:return wait;
    default:assert(!"Unexpected deferred API");return 0;
    }
}
int main(void) {
    WORD(change,8)=1;HALF(change,0x14)=0x1234;
    for(int flag=0;flag<2;flag++) for(accepted=0;accepted<2;accepted++) {
        WORD(change,0x20)=flag;WORD(actor,0xD70)=77;reset();af_v3_reward_bury_submenu(actor,game);
        assert(!strcmp(events,"CB") && WORD(actor,0xD70)==(accepted?flag:77));
        WORD(actor,0xD70)=77;reset();af_v3_reward_release_submenu(actor,game);
        assert(!strcmp(events,"CR") && WORD(actor,0xD70)==(accepted?flag:77));
        WORD(actor,0xD70)=flag;reset();af_v3_reward_bury_setup(actor,game);
        assert(!strcmp(events,"b") && WORD(actor,0xD20)==flag);
        reset();af_v3_reward_release_setup(actor,game);assert(!strcmp(events,"r") && WORD(actor,0xD20)==flag);
        for(int ended=0;ended<2;ended++) {
            reset();af_v3_reward_bury_transition(actor,game,ended);
            assert(!strcmp(events,flag?(ended?"PG":""):"F"));
        }
        REAL(actor,0xD18)=0;
        for(int frame=0;frame<41;frame++) {
            reset();af_v3_reward_release_transition(actor,game);assert(!calls && REAL(actor,0xD18)==frame+1);
        }
        reset();af_v3_reward_release_transition(actor,game);
        assert(!strcmp(events,flag?"PG":"PW") && REAL(actor,0xD18)==42);
        reset();af_v3_reward_release_transition(actor,game);
        assert(!strcmp(events,flag?"PG":"PW") && REAL(actor,0xD18)==42);
    }
    reset();af_v3_reward_bury_submenu(0,game);af_v3_reward_release_submenu(actor,0);
    af_v3_reward_bury_setup(0,game);af_v3_reward_release_setup(actor,0);
    af_v3_reward_bury_transition(0,game,1);af_v3_reward_release_transition(actor,0);assert(!calls);
    puts("pass: deferred requests, rejected writes, native setups, bury interruption rules and full release delay");
}
