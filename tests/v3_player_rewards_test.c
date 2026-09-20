#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#define AF_V3_REWARD_BGMS 73,75,76,74
#define AF_V3_REWARD_RESET 0x804B237Cu
#define AF_V3_REWARD_UPDATE 0x804B23A8u
#include "../overlays/v3/player_rewards.c"

static alignas(16) u8 actor[0x1400],game[16],before[0x1400];
static char calls[64];static int count,kind,animation_end,message_end,expected_type;
static const int bgms[]={73,75,76,74};
static void log_call(char c) { assert(count<63);calls[count++]=c;calls[count]=0; }
static void actor_check(void *p) { assert(p==actor); }
static void game_check(void *p) { assert(p==game); }
static int get_kind(void *p,int action) { actor_check(p);assert(action==118);log_call('K');return kind; }
static int reset(void *p,int type) {
    actor_check(p);assert(type==expected_type);log_call('R');
    memset(actor+0xD10,0,8);WORD(actor,0xD18)=type;return 1;
}
static void item_setup(void *p,int anim,float morph,int *upper,int *part) {
    actor_check(p);assert(anim==258 && morph==-5.0f);*upper=kind<0?258:777;*part=6;log_call('I');
}
static void animation(void *p,void *g,int lower,int upper,float f0,float f1,float speed,float morph,int mode,int part) {
    actor_check(p);game_check(g);int balloon=kind>=91 && kind<99;
    assert(lower==(balloon?260:258) && upper==(balloon?260:kind<0?258:777));
    assert(f0==1 && f1==1 && speed==1 && morph==-5 && mode==0 && part==(balloon?0:3));log_call('A');
}
static void setup(void *p,void *g) { actor_check(p);game_check(g);log_call('S'); }
static void start(int bgm,int stop) { assert(bgm==bgms[expected_type] && stop==0x168);log_call('B'); }
static void stop(int bgm,int type) { assert(bgm==bgms[expected_type] && type==0x168);log_call('D'); }
static int calc(void *p,float *last) { actor_check(p);*last=52;log_call('C');return animation_end; }
static void turn(s16 *angle,int target,float speed,int maximum,int minimum) {
    assert(angle==(s16 *)(actor+0xDE) && target==0 && speed==0.2928932188134524f && maximum==2500 && minimum==50);
    *angle-=7;log_call('T');
}
static int brake(void *p) { actor_check(p);log_call('B');return 0; }
static void reinput(void *p,void *g) { actor_check(p);game_check(g);log_call('R'); }
static void lean(void *p) { actor_check(p);log_call('L'); }
static void normal_eye(void *p) { actor_check(p);log_call('N'); }
static void face(void *p) { actor_check(p);log_call('F'); }
static void stand(void *p,void *g) { actor_check(p);game_check(g);log_call('S'); }
static void background(void *p) { actor_check(p);log_call('G'); }
static void item(void *p,void *g) { actor_check(p);game_check(g);log_call('I'); }
static int message(void *p,int end) { actor_check(p);assert(end==animation_end);log_call('M');return message_end; }
static void priority(void *p) { actor_check(p);log_call('P'); }
static int wait_request(void *g,float morph,int flags,int prio) {
    game_check(g);assert(morph==-5.0f && flags==0 && prio==1);log_call('W');return 1;
}
void *af_test_player_reward_function(u32 address) {
    switch(address) {
    case AF_V3_REWARD_RESET:return reset;
    case AF_V3_REWARD_UPDATE:return message;
    case 0x8005DC9C:return start;
    case 0x8005E494:return stop;
    case 0x8009A974:return turn;
    case 0x808B3648:return priority;
    case 0x808B36F4:return normal_eye;
    case 0x808B3828:return face;
    case 0x808B3BD0:return setup;
    case 0x808B3C74:return brake;
    case 0x808B488C:return calc;
    case 0x808B4A44:return animation;
    case 0x808B4DAC:return stand;
    case 0x808B5310:return lean;
    case 0x808B5FFC:return background;
    case 0x808B61E4:return reinput;
    case 0x808B846C:return item_setup;
    case 0x808BD5C4:return get_kind;
    case 0x808BF410:return item;
    case 0x808C1064:return wait_request;
    default:assert(!"Unexpected reward control call");return 0;
    }
}
static void clear_calls(void) { count=0;calls[0]=0; }
int main(void) {
    assert(af_v3_reward_bgm(-1)==-1 && af_v3_reward_bgm(4)==-1);
    for(expected_type=0;expected_type<4;expected_type++) {
        assert(af_v3_reward_bgm(expected_type)==bgms[expected_type]);
        for(kind=-1;kind<115;kind++) {
            memset(actor,0xA5,sizeof(actor));WORD(actor,0xD00)=118;WORD(actor,0xD58)=expected_type;
            memcpy(before,actor,sizeof(actor));clear_calls();af_v3_reward_setup(actor,game);
            assert(!strcmp(calls,"KRIASB"));memset(before+0xD10,0,8);WORD(before,0xD18)=expected_type;
            assert(!memcmp(before,actor,sizeof(actor)));
        }
        clear_calls();af_v3_reward_stop_fanfare(actor);assert(!strcmp(calls,"D"));
        assert(!memcmp(before,actor,sizeof(actor)));
        for(animation_end=0;animation_end<2;animation_end++) for(message_end=0;message_end<2;message_end++) {
            SHORT(actor,0xDE)=1000;memcpy(before,actor,sizeof(actor));clear_calls();
            af_v3_reward_main(actor,game);
            const char *expected=animation_end?(message_end?"CTTBRLNSGIMPW":"CTTBRLNSGIM"):
                (message_end?"CTTBRLFSGIMPW":"CTTBRLFSGIM");
            assert(!strcmp(calls,expected));SHORT(before,0xDE)=986;SHORT(before,0x36)=986;
            assert(!memcmp(before,actor,sizeof(actor)));
        }
    }
    clear_calls();af_v3_reward_setup(0,game);af_v3_reward_setup(actor,0);
    af_v3_reward_stop_fanfare(0);af_v3_reward_main(0,game);af_v3_reward_main(actor,0);
    WORD(actor,0xD18)=WORD(actor,0xD58)=4;memcpy(before,actor,sizeof(actor));
    af_v3_reward_setup(actor,game);af_v3_reward_stop_fanfare(actor);af_v3_reward_main(actor,game);
    assert(!count && !memcmp(before,actor,sizeof(actor)));
    puts("pass: reward setup, all held kinds, frame order, facial/exit gates, audio, and bounded state");
}
