#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/creature_water.c"
#include "../overlays/v3/creature_patrol.c"
u32 af_v3_fish_patrol_mode;
static unsigned unit=24,block_kind=0x800,attribute_calls,native_calls,last_native;
static float ground_y=0,water_y=40,random_value=0.5f;
static int coast=1,near_player,near_uki;
static _Alignas(16) unsigned char memory[0x280];
unsigned af_water_attribute(FishVector p,void *unused) {
    (void)unused;attribute_calls++;
    return coast && p.z< -50?0:24;
}
unsigned *af_water_unit(FishVector p) {(void)p;return &unit;}
int af_water_is_water(unsigned a) {return (a>=11 && a<=21) || a==24;}
unsigned af_water_block(int x,int z) {assert(x==2 && z==3);return block_kind;}
void af_water_centre(FishVector *p,int bx,int bz,int x,int z) {
    assert(bx==2 && bz==3);*p=(FishVector){(float)(x*40),0,(float)(z*40)};
}
float af_water_ground(void *a,FishVector p,float offset) {(void)a;(void)p;(void)offset;return ground_y;}
float af_water_height(FishVector p,const char *name,int line) {(void)p;(void)name;(void)line;return water_y;}
float af_patrol_random(void) {return random_value;}
float af_patrol_random2(void) {return 0.0f;}
float af_patrol_sin(s16 a) {return (float)a/32768.0f;}
int af_patrol_chase_float(float *p,float target,float step) {
    if (*p>target) step=-step;
    *p+=step;
    if (step*(*p-target)>=0) {*p=target;return 1;}
    return 0;
}
int af_patrol_chase_angle(s16 *p,s16 target,s16 step) {
    (void)step;*p=target;return 1;
}
int af_patrol_player_near(void *a,void *g) {(void)a;(void)g;return near_player;}
int af_patrol_search(void *a,void *g) {(void)a;(void)g;return near_uki;}
void af_patrol_setup(void *a,int action) {
    W(a,0x1DC)=action;
    if (action==0) af_v3_patrol_swim_init(a);
    if (action==1) af_v3_patrol_wait_init(a);
    if (action==2) af_v3_patrol_escape_init(a);
}
#define OLD(name,number) void name(void *a,void *g) {(void)a;(void)g;native_calls++;last_native=number;}
OLD(af_patrol_old_swim,0)
OLD(af_patrol_old_wait,1)
OLD(af_patrol_old_escape,2)
#define INIT(name,number) void name(void *a) {(void)a;native_calls++;last_native=number;}
INIT(af_patrol_old_swim_init,3)
INIT(af_patrol_old_wait_init,4)
INIT(af_patrol_old_escape_init,5)
static void *reset(void) {
    memset(memory,0xAB,sizeof(memory));void *a=memory+16;
    memset(a,0,0x250);((u8 *)a)[8]=2;((u8 *)a)[9]=3;
    FISH_VECTOR(a,0x28)=(FishVector){0,0,0};
    FISH_VECTOR(a,0x3C)=(FishVector){1,2,3};
    unit=24;coast=1;ground_y=0;water_y=40;block_kind=0x800;
    attribute_calls=0;near_player=near_uki=0;return a;
}
int main(void) {
    unsigned collision[256];for(unsigned i=0;i<256;i++)collision[i]=12;
    FishWaterBlock b={2,3,collision};
    for(unsigned fish=36;fish<=44;fish++) {
        int ocean=fish>=39 && fish<=42;
        assert(af_v3_water_site(&b,fish,5,7)==!ocean);
        collision[7*16+5]=24;unit=24;
        assert(af_v3_water_site(&b,fish,5,7));
        if (ocean) {
            water_y=19;assert(!af_v3_water_site(&b,fish,5,7));water_y=40;
            unit=37;assert(!af_v3_water_site(&b,fish,5,7));unit=24;
        }
        collision[7*16+5]=12;
    }
    collision[7*16+5]=13;assert(af_v3_water_site(&b,19,5,7));
    collision[7*16+5]=12;assert(!af_v3_water_site(&b,19,5,7));
    assert(!af_v3_water_site(&b,32,5,7) && !af_v3_water_site(&b,40,16,7));
    void *a=reset();assert(!af_v3_water_wall(a));
    coast=0;assert(af_v3_water_wall(a));
    assert(H(a,0x36)==-32768 && F(a,0x28)==1 && F(a,0x2C)==2 && F(a,0x30)==3);
    a=reset();unit=22;assert(af_v3_water_wall(a) && H(a,0x36)==0);
    a=reset();water_y=19;assert(af_v3_water_wall(a));
    a=reset();FISH_U32(a,0x98)=(1u<<21)|(1u<<18);H(a,0xA8)=1234;
    assert(af_v3_water_wall(a) && H(a,0x36)==1234 && !attribute_calls);
    a=reset();FISH_U32(a,0x98)=(1u<<21)|(7u<<18);assert(af_v3_water_wall(a));
    for(unsigned mode=0;mode<2;mode++)for(unsigned origin=0;origin<2;origin++) {
        if(mode && origin)continue;
        a=reset();af_v3_fish_patrol_mode=mode;((u8 *)a)[0x1DA]=(u8)origin;
        unsigned before=native_calls;
        af_v3_patrol_swim(a,0);assert(last_native==0);
        af_v3_patrol_wait(a,0);assert(last_native==1);
        af_v3_patrol_escape(a,0);assert(last_native==2);
        af_v3_patrol_swim_init(a);assert(last_native==3);
        af_v3_patrol_wait_init(a);assert(last_native==4);
        af_v3_patrol_escape_init(a);assert(last_native==5);
        assert(native_calls==before+6);
    }
    for(unsigned roll=0;roll<3;roll++) {
        a=reset();af_v3_fish_patrol_mode=1;((u8 *)a)[0x1DA]=1;
        random_value=((float)roll+0.5f)/3.0f;W(a,0x214)=1;
        af_v3_patrol_wait(a,0);
        assert(((u8 *)a)[0x23E]==(roll==1) && W(a,0x1DC)==0);
    }
    for(unsigned kind=0;kind<4;kind++) {
        a=reset();((u8 *)a)[0x1DA]=1;((u8 *)a)[0x23E]=(u8)kind;
        af_v3_patrol_swim_init(a);
        F(a,0x224)=kind==0?355.0f:175.0f;
        af_v3_patrol_swim(a,0);
        if(kind==2)assert(((u8 *)a)[0x23E]==3 && F(a,0x224)==5);
        else assert(W(a,0x1DC)==1);
    }
    a=reset();((u8 *)a)[0x1DA]=1;af_v3_patrol_escape_init(a);
    assert(W(a,0x214)==50 && F(a,0x74)==1);
    af_v3_patrol_escape(a,0);assert(W(a,0x214)==49 && F(a,0x74)==0.98f);
    W(a,0x214)=1;af_v3_patrol_escape(a,0);assert(W(a,0x1DC)==1);
    a=reset();((u8 *)a)[0x1DA]=1;near_uki=1;W(a,0x214)=10;
    af_v3_patrol_wait(a,0);assert(W(a,0x1DC)==3);
    for(unsigned i=0;i<16;i++) assert(memory[i]==0xAB && memory[sizeof(memory)-1-i]==0xAB);
    puts("all fish terrain, donor patrol states, native-mode fallbacks, and bounds pass");
}
