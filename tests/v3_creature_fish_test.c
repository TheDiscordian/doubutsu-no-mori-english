#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/creature_fish.c"
const u32 af_test_fish_values[96]={
    [0]=0x3F800000,[1]=0x3FA00000,[2]=0x3FA00000,[3]=0x3FC00000,
    [4]=0x3FE00000,[5]=0x40000000,[6]=0x400CCCCD,
    [48]=0xC1000000,[49]=0xC1200000,[50]=0xC1400000,[51]=0xC1400000,
    [52]=0xC1700000,[53]=0xC1A00000,[54]=0xC1C80000
};
static _Alignas(16) u8 storage[0x2A0];
float af_fish_sin(s16 angle) {assert(angle==1234);return 0.25f;}
float af_fish_cos(s16 angle) {assert(angle==1234);return -0.5f;}
int main(void) {
    const float speed[]={1,1.25f,1.25f,1.5f,1.75f,2,2.2f};
    const float distance[]={-8,-10,-12,-12,-15,-20,-25};
    void *actor=storage+16;
    for(unsigned original=0;original<2;original++)for(unsigned index=0;index<45;index++)
    for(unsigned size=0;size<8;size++) {
        memset(storage,0xA5,sizeof(storage));
        U32(actor,0x1D4)=index;U16(actor,0x1D8)=size;
        ((u8 *)actor)[0x1DA]=!original;U16(actor,0x23C)=0x400;
        U16(actor,0x36)=1234;F32(actor,0x28)=100;F32(actor,0x2C)=200;F32(actor,0x30)=300;
        af_v3_fish_near_init(actor);
        assert(F32(actor,0x74)==(!original && size<7?speed[size]:index==31?2.0f:1.25f));
        assert(F32(actor,0x7C)==12 && U16(actor,0x23C)==0x402);
        af_v3_fish_position(actor);
        float correction=!original && size<7?distance[size]:-20;
        assert(F32(actor,0x28)==100+correction*0.25f);
        assert(F32(actor,0x30)==300-correction*0.5f && F32(actor,0x2C)==200);
        for(unsigned n=0;n<16;n++)assert(storage[n]==0xA5 && storage[sizeof(storage)-1-n]==0xA5);
    }
    puts("fish position/approach readers pass, including native values and bounds");
}
