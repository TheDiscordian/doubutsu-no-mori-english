#include <assert.h>
#include <stdio.h>
#include <string.h>
#include <stdalign.h>
#define AF_V3_REWARD_MESSAGE_FIRST 12011
#include "../overlays/v3/player_reward_messages.c"

static alignas(16) unsigned char actor[0x1400], snapshot[0x1400], window[0x300], choice[32];
static int calls, requests, active, unlocked, message_id, display, camera, listening, cleared;
static void (*begin_callback)(void *);
static unsigned char colour[4];
static void *get_window(void) { calls++;return window; }
static void *get_choice(void) { calls++;return choice; }
static void set_id(int value) { calls++;message_id=value; }
static void set_display(int value) { calls++;display=value; }
static void set_camera(int value) { calls++;camera=value; }
static void listen(void) { calls++;listening++; }
static void lock(void *p) { assert(p==window);calls++;window[0x2D0]=1; }
static void unlock(void *p) { assert(p==window);calls++;unlocked++;window[0x2D0]=0; }
static void set_colour(const u8 *p) { calls++;memcpy(colour,p,4); }
static void clear(void *p) { assert(p==choice);calls++;cleared++; }
static int check(int type,void *p) { assert(type==9 && p==actor);calls++;return active; }
static int request(int type,void *p,void (*callback)(void *)) {
    assert(type==9 && p==actor);calls++;requests++;begin_callback=callback;return 0;
}
void *af_test_reward_function(u32 address) {
    switch(address) {
    case 0x80065040:return get_choice;
    case 0x80065508:return clear;
    case 0x8007B5C0:return set_id;
    case 0x8007B79C:return set_display;
    case 0x8007B980:return set_colour;
    case 0x8007BA1C:return set_camera;
    case 0x8007CDD8:return request;
    case 0x8007CF00:return check;
    case 0x8007D098:return listen;
    case 0x8009D1F0:return get_window;
    case 0x8009E9E8:return lock;
    case 0x8009E9F8:return unlock;
    default:assert(!"Unexpected engine call");return 0;
    }
}
static void guard(void) {
    assert(!memcmp(actor,snapshot,0xD10));
    assert(!memcmp(actor+0xD1C,snapshot+0xD1C,sizeof(actor)-0xD1C));
}
int main(void) {
    const int ids[]={12013,12011,12012,12014};
    memset(actor,0xA5,sizeof(actor));memcpy(snapshot,actor,sizeof(actor));
    assert(af_v3_reward_message_id(-1)==-1 && af_v3_reward_message_id(4)==-1);
    assert(!af_v3_reward_message_reset(0,0));af_v3_reward_message_begin(0);
    assert(!af_v3_reward_message_update(0,1));
    assert(!af_v3_reward_message_reset(actor,-1) && !af_v3_reward_message_reset(actor,4));
    assert(!memcmp(actor,snapshot,sizeof(actor)) && calls==0);
    for(int type=0;type<4;type++) {
        calls=requests=active=unlocked=listening=cleared=0;display=camera=-1;
        memset(window,0,sizeof(window));
        assert(af_v3_reward_message_id(type)==ids[type]);
        assert(af_v3_reward_message_reset(actor,type));
        assert(state(actor)->timer==0 && state(actor)->mode==0 && state(actor)->type==type);
        for(int i=0;i<21;i++) {
            assert(!af_v3_reward_message_update(actor,1));
            assert(state(actor)->timer==(i+1)*2.0f && calls==0);
        }
        assert(!af_v3_reward_message_update(actor,0) && requests==1);
        assert(!af_v3_reward_message_update(actor,0) && requests==2);
        assert(begin_callback==af_v3_reward_message_begin);
        begin_callback(actor);active=1;
        assert(message_id==ids[type] && display==0 && camera==5 && listening==1 && cleared==1);
        assert(!memcmp(colour,(unsigned char[]){185,245,80,255},4));
        assert(window[0x2D0]==1 && unlocked==0);
        assert(!af_v3_reward_message_update(actor,1) && state(actor)->mode==1);
        assert(window[0x2D0]==1);
        assert(!af_v3_reward_message_update(actor,0) && state(actor)->mode==1 && unlocked==0);
        assert(!af_v3_reward_message_update(actor,1) && state(actor)->mode==2 && unlocked==1);
        assert(!window[0x2D0]);
        assert(!af_v3_reward_message_update(actor,1) && state(actor)->mode==2);
        active=0;
        assert(!af_v3_reward_message_update(actor,1) && state(actor)->mode==3);
        int before=calls;
        assert(af_v3_reward_message_update(actor,1) && af_v3_reward_message_update(actor,0));
        assert(calls==before && requests==2 && unlocked==1);guard();
    }
    state(actor)->type=4;memcpy(snapshot,actor,sizeof(actor));int before=calls;
    af_v3_reward_message_begin(actor);assert(!af_v3_reward_message_update(actor,1));
    assert(calls==before && !memcmp(actor,snapshot,sizeof(actor)));
    puts("pass: all reward types, delayed request, continuation lock, completion, and actor guards");
}
