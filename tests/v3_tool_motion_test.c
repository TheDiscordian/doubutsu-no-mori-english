#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/tool_motion.c"
#include "../overlays/v3/tool_recovery.c"

static union { int align; unsigned char bytes[0x13A0]; } player;
static int kind, loads, setups, seen_kind, seen_animation, seen_main, seen_mode;
static float seen_speed, seen_morph, seen_frame;
static int get_kind(void *p, int action) {
    assert(p == player.bytes && action == 44);
    return kind;
}
static int check_animation(int k, int a) {
    if (k == 0 || (k >= 2 && k < 34) || k == 35) return a < 0;
    if (k == 1) return (a >= 2 && a <= 8) || (a >= 23 && a <= 29);
    if (k == 34) return (a >= 10 && a <= 15) || (a >= 32 && a <= 37);
    return 0;
}
static void load(void *p, int k, int a, float speed, float morph, float frame, int mode) {
    assert(p == player.bytes);
    ++loads; seen_kind=k; seen_animation=a; seen_speed=speed;
    seen_morph=morph; seen_frame=frame; seen_mode=mode;
}
static int basic_animation(int k) { assert(k == kind); return 1000; }
static void setup(void *p, int a, int item, float speed, float morph, float frame, int *out, int *part) {
    assert(p == player.bytes);
    ++setups; seen_main=a; seen_animation=item; seen_speed=speed; seen_morph=morph; seen_frame=frame;
    *out=270; *part=3;
}
void *af_test_tool_motion_function(u32 at) {
    switch (at) {
        case 0x808BD5C4u: return get_kind;
        case 0x808BDF6Cu: return check_animation;
        case 0x808BDDB4u: return load;
        case 0x808BD6E0u: return basic_animation;
        case 0x808BD690u: return basic_animation;
        case 0x808B83B4u: return setup;
    }
    assert(0); return 0;
}
static void action(int actual, int requested, int animation, int expected_animation, int accept) {
    kind=actual; loads=0;
    memset(player.bytes,0xA5,sizeof(player.bytes)); WORD(player.bytes,0xD00)=44;
    unsigned char before[sizeof(player.bytes)]; memcpy(before,player.bytes,sizeof(before));
    af_v3_tool_action_setup(player.bytes,requested,animation,13,-4.0f,7.0f,1);
    assert(loads == accept);
    if (accept) {
        assert(seen_kind == actual && seen_animation == expected_animation);
        assert(seen_speed == 1.0f && seen_morph == -4.0f && seen_frame == 7.0f && seen_mode == 1);
        assert(WORD(player.bytes,0xCFC) == 13 && (signed char)player.bytes[0x1117] == actual);
        memcpy(player.bytes+0xCFC,before+0xCFC,4);player.bytes[0x1117]=before[0x1117];
    }
    assert(memcmp(before,player.bytes,sizeof(before)) == 0);
}
int main(void) {
    for (int a=2;a<=8;++a) {
        action(1,1,a,a,1);
        for (int k=45;k<=46;++k) { action(k,1,a,a+21,1); action(k,k,a,a+21,1); }
    }
    for (int a=10;a<=15;++a) {
        action(34,34,a,a,1);
        for (int k=87;k<=88;++k) { action(k,34,a,a+22,1); action(k,k,a,a+22,1); }
    }
    for (int k=36;k<=44;++k) action(k,0,-1,-1,1);
    for (int k=89;k<=90;++k) action(k,35,-1,-1,1);
    action(46,34,10,0,0); action(88,1,2,0,0); action(46,1,10,0,0); action(88,34,2,0,0);
    action(44,0,2,0,0); action(90,35,10,0,0); action(-1,1,2,0,0);
    action(INT_MIN,1,2,0,0); action(INT_MAX,34,10,0,0);
    action(46,1,INT_MAX,0,0); action(88,34,INT_MIN,0,0);
    for (int k=-1;k<115;++k) {
        int out=-1, part=-1;
        kind=k; setups=0;WORD(player.bytes,0xD00)=44;
        af_v3_tool_moving_setup(player.bytes,72,1.75f,-3.5f,&out,&part);
        assert(setups == 1 && seen_main == 72 && out == 270 && part == 3);
        assert(seen_frame == -1.0f && seen_morph == -3.5f);
        assert(seen_animation == (k==34 ? 11 : k==87 || k==88 ? 33 : 1000));
        assert(seen_speed == (k==34 || k==87 || k==88 ? 1.75f : 1.0f));
        for (int getup=0;getup<2;++getup) {
            unsigned char before[sizeof(player.bytes)];memcpy(before,player.bytes,sizeof(before));
            int imported_net=k==45 || k==46, net=k==1 || imported_net;
            loads=0;
            if (getup) af_v3_tool_getup(player.bytes,0,k,-5.0f);
            else af_v3_tool_tumble(player.bytes,0,k,-5.0f);
            assert(loads==1 && seen_kind==k && seen_speed==1.0f && seen_morph==-5.0f && seen_frame==-1.0f);
            assert(seen_mode==!net);
            assert(seen_animation==(net ? (getup ? 5 : 6)+(imported_net ? 21 : 0) : 1000));
            assert(WORD(player.bytes,0xCFC)==(net ? (getup ? 6 : 5) : 1000));
            assert((signed char)player.bytes[0x1117]==k);
            memcpy(player.bytes+0xCFC,before+0xCFC,4);player.bytes[0x1117]=before[0x1117];
            assert(memcmp(player.bytes,before,sizeof(before))==0);
        }
    }
    puts("Shared tool motions preserve actual kinds, timing, original tools, and bounded state: pass");
}
