#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_pickup.c"

u8 af_test_reward_players[4*0xBD0], *af_test_reward_active;
static alignas(16) u8 actor[0x1400], game[32];
static int flags[4][4], selected, allowed, calls;
static char log_calls[32];
static void log_call(char c) { assert(calls<31);log_calls[calls++]=c;log_calls[calls]=0; }
static void reset(void) { calls=0;log_calls[0]=0; }
int af_v3_reward_flag(u32 player,u32 category,u32 index,u32 mark) {
    assert(player<4 && category==1 && index<4 && mark==0);log_call('F');return flags[player][index];
}
int af_v3_player_selected_equipment(u32 item) {
    assert(item==0x223B);log_call('S');return selected?90:-1;
}
int af_v3_reward_request(void *g,int action,int type,int priority) {
    assert(g==game && action==118 && type==3 && priority==34);log_call('R');return allowed;
}
static void settle(void *p) { assert(p==actor);log_call('P'); }
static int wait(void *g,float morph,int mask,int priority) {
    assert(g==game && morph==-5.0f && mask==0 && priority==1);log_call('W');return 1;
}
void *af_test_reward_pickup_function(u32 address) {
    switch(address) {
    case 0x808B3648:return settle;
    case 0x808C1064:return wait;
    default:assert(!"Unexpected pickup API");return 0;
    }
}
int main(void) {
    for(u32 player=0;player<4;player++) for(u32 type=0;type<4;type++) for(int done=0;done<2;done++) {
        af_test_reward_active=af_test_reward_players+player*0xBD0;
        memset(flags,0,sizeof(flags));flags[player][type]=done;reset();
        assert(af_v3_reward_completed(type)==done && !strcmp(log_calls,"F"));
    }
    af_test_reward_active=af_test_reward_players;
    reset();assert(af_v3_reward_completed(4)==-1 && af_v3_reward_completed((u32)-1)==-1 && !calls);
    for(int invalid=0;invalid<3;invalid++) {
        af_test_reward_active=invalid==0?0:af_test_reward_players+(invalid==1?1:4*0xBD0);
        reset();assert(af_v3_reward_completed(3)==-1 && !calls);
    }
    af_test_reward_active=af_test_reward_players;
    for(int first=0;first<2;first++) for(int golden=0;golden<2;golden++)
      for(selected=0;selected<2;selected++) for(int done=0;done<2;done++) for(allowed=0;allowed<2;allowed++) {
        flags[0][3]=done;reset();af_v3_reward_pickup(actor,game,golden?0x223B:0x2202,first);
        const char *want=golden?(selected?(done?(first?"PSFW":"SFPW"):(first?"PSFR":"SFR")):
                                                        (first?"PSW":"SPW")):"PW";
        assert(!strcmp(log_calls,want));
    }
    selected=1;af_test_reward_active=0;reset();af_v3_reward_pickup(actor,game,0x223B,0);
    assert(!strcmp(log_calls,"SPW"));
    reset();af_v3_reward_pickup(0,game,0x223B,1);af_v3_reward_pickup(actor,0,0x223B,1);assert(!calls);
    for(u32 i=0;i<sizeof(actor);i++) assert(actor[i]==0);
    for(u32 i=0;i<sizeof(game);i++) assert(game[i]==0);
    puts("pass: four-player completion queries, source priority ordering, selection, repeat suppression and rejection");
}
