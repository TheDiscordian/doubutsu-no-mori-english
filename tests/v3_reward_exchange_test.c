#include <assert.h>
#include <stdalign.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/reward_exchange.c"
static alignas(16) u8 submenu[0x60],menu[0x60],overlay[16],hand[0x300],actor[0x1400],change[0x50],private_data[0x400],game_data[16];
u8 *af_test_exchange_game=game_data,*af_test_exchange_active=private_data;
static Pos dig;
static int empty,selected,completed,position_ok,drop_ok,has_dig,calls;
static char events[64];
static void log_call(char c) { assert(calls<63);events[calls++]=c;events[calls]=0; }
static void reset(void) { calls=0;events[0]=0;memset(change,0xA5,sizeof(change)); }
static void move_out(void *p,int mode) { assert(p==menu && mode==0);log_call('M'); }
void *af_test_exchange_pointer(void *p,u32 offset) {
    if(p==submenu && offset==0x2C) return overlay;
    if(p==overlay && offset==0x106D4) return hand;
    if(p==overlay && offset==0x106B0) return move_out;
    if(p==menu && offset==0x40) return has_dig?&dig:0;
    assert(!"Unexpected pointer read");return 0;
}
static void *get_actor(void *g) { assert(g==game_data);return actor; }
static void *get_change(void) { return change; }
static int hand_empty(void *p) { assert(p==submenu);return empty; }
static int position(void *p,Pos *out,int mode) {
    assert(p==actor && mode==0);out->x=11;out->y=22;out->z=33;log_call('P');return position_ok;
}
static int drop(void *g,u32 item,Pos *pos) {
    assert(g==game_data && item==af_v3_present_encode(HALF(hand,0x23C),WORD(hand,0x2E4)));
    assert(pos->x==11 && pos->y==22 && pos->z==33);log_call('D');return drop_ok;
}
static void fish(int angle,int item) {
    assert(angle==-123 && item==(s16)HALF(hand,0x23C));WORD(change,0)=81;WORD(change,4)=1;WORD(change,0x20)=0;log_call('F');
}
static void insect(u32 item) { assert(item==0x2D01);WORD(change,0)=81;WORD(change,4)=1;WORD(change,0x20)=0;log_call('I'); }
static void bury(const void *pos,u32 item) {
    assert(pos==&dig && item==0x1234);WORD(change,0)=63;WORD(change,4)=1;WORD(change,0x20)=0;log_call('B');
}
static void warning(void *s,void *m,int kind) { assert(s==submenu && m==menu && kind==11);log_call('X'); }
static void sound(int n) { assert(n==0x31);log_call('S'); }
void *af_test_exchange_function(u32 address,u32 context) {
    assert(context==0x80873AEC);
    switch(address) {
    case 0x800B1C84:return get_actor;
    case 0x800B1F74:return get_change;
    case 0x80871708:return hand_empty;
    case 0x80870C6C:return position;
    case 0x808715C8:return drop;
    case 0x800B2060:return fish;
    case 0x80873968:return insect;
    case 0x800B2008:return bury;
    case 0x80871570:return warning;
    case 0x800D1A9C:return sound;
    default:assert(!"Unexpected exchange API");return 0;
    }
}
int af_v3_reward_completed(u32 type) { assert(type==3);return completed; }
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223B);return selected?90:-1; }
u32 af_v3_present_encode(u32 item,u32 condition) { return item==0x223B && condition==1?0x2521:item; }
static void exchange(void) { af_v3_reward_exchange(submenu,menu,0x80873AEC); }
int main(void) {
    position_ok=drop_ok=1;HALF(menu,0x46)=(u16)-123;
    for(int incoming=0;incoming<2;incoming++) for(selected=0;selected<2;selected++) for(completed=0;completed<2;completed++) {
        WORD(menu,0x3C)=incoming?0x223B:0x1234;int flag=incoming && selected && !completed;
        empty=1;reset();exchange();assert(!strcmp(events,"MS") && WORD(change,0)==(flag?118:7));
        empty=0;HALF(hand,0x23C)=0x1234;reset();exchange();
        assert(!strcmp(events,flag?"PDMS":"PDM") && WORD(change,0)==(flag?118:7) && WORD(change,0x20)==0);
        HALF(hand,0x23C)=0x2301;reset();exchange();assert(!strcmp(events,"FMS") && WORD(change,0x20)==flag);
        HALF(hand,0x23C)=0x2D01;reset();exchange();assert(!strcmp(events,"IMS") && WORD(change,0x20)==flag);
        HALF(hand,0x23C)=0x223B;WORD(hand,0x2E4)=0;reset();exchange();assert(!strcmp(events,"PDM") && WORD(change,0)==7);
        WORD(hand,0x2E4)=1;reset();exchange();assert(!strcmp(events,flag?"PDMS":"PDM") && WORD(change,0)==(flag?118:7));
        WORD(hand,0x2E4)=0;
    }
    WORD(menu,0x3C)=0x223B;selected=1;completed=0;HALF(hand,0x23C)=0x1234;has_dig=1;
    for(int search=0;search<2;search++) for(int equipment=0;equipment<3;equipment++) {
        position_ok=search;drop_ok=0;HALF(private_data,0x3EC)=equipment==0?0x2202:equipment==1?0x223B:0x2200;
        reset();exchange();
        assert(!strcmp(events,equipment<2?(search?"PDBMS":"PBMS"):(search?"PDX":"PX")));
        if(equipment<2) assert(WORD(change,0)==63 && WORD(change,0x20)==1);
        else for(u32 i=0;i<sizeof(change);i++) assert(change[i]==0xA5);
    }
    reset();af_v3_reward_exchange(0,menu,0x80873AEC);af_v3_reward_exchange(submenu,0,0x80873AEC);assert(!calls);
    puts("pass: source reward conditions, native exchange/drop/empty-hand/bury/creature routes and warning/sound semantics");
}
