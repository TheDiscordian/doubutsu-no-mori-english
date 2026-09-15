#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/furniture_rewards.c"

struct Item af_test_reward_records[1024];
u16 af_test_reward_rare;
static unsigned char enabled[1024];
static float rolls[8];
static unsigned roll, calls;
static void *last_game;
static u16 *last_out, *last_existing;
static int last_count, last_existing_count, last_kind, last_list;
int af_v3_furniture_import_profile(u32 index) {
    assert(index >= 1024 && index < 2048);
    return enabled[index - 1024];
}
float af_v3_reward_random(void) { assert(roll < 8); return rolls[roll++]; }
void af_v3_native_reward_goods(void *game, u16 *out, int count, u16 *existing,
        int existing_count, int kind, int list) {
    ++calls; last_game=game; last_out=out; last_existing=existing;
    last_count=count; last_existing_count=existing_count; last_kind=kind; last_list=list;
    if (out && count>0) *out=0x1234;
}
static void add(unsigned slot, unsigned route) {
    struct Item *row=items+slot;
    row->item=(u16)(0x3000+slot*4); row->index=(u16)(1024+slot);
    row->enabled=1;row->reward=(u8)route;enabled[slot]=1;
}
static u16 gift(int encoded) {
    u16 out=0xFFFF;roll=0;calls=0;
    af_v3_furniture_reward_goods(0,&out,1,0,0,0,encoded);
    return out;
}
int main(void) {
    assert(gift(0x0C02)==0x1234 && calls==1 && !roll && last_list==2);
    add(5,12);add(129,12);add(1023,12);add(70,13);
    assert(gift(0x0C02)==0x3014 && !calls && roll==1);
    rolls[0]=.5f;assert(gift(0x0C02)==0x3204);
    rolls[0]=.99999f;assert(gift(0x0C02)==0x3FFC);
    rolls[0]=1.f;assert(gift(0x0C02)==0x3FFC);
    assert(gift(0x0D01)==0x3118 && !calls);
    enabled[129]=0;items[1023].enabled=0;
    assert(gift(0x0C02)==0x3014);
    items[5].index=0;assert(gift(0x0C02)==0x1234 && calls==1);
    items[5].index=1029;items[5].item=0x3015;
    assert(gift(0x0C02)==0x1234 && calls==1);
    items[5].item=0x3014;af_test_reward_rare=0x3014;
    assert(gift(0x0C02)==0x1234 && calls==1 && !roll);
    enabled[129]=1;rolls[0]=0.f;rolls[1]=.75f;
    assert(gift(0x0C02)==0x3204 && roll==2 && !calls);
    u16 out[3]={0},existing[2]={1,2};int game=0;
    af_v3_furniture_reward_goods(&game,out,3,existing,2,4,0x0C02);
    assert(last_game==&game && last_out==out && last_existing==existing &&
        last_count==3 && last_existing_count==2 && last_kind==4 && last_list==2);
    assert(gift(5)==0x1234 && last_list==5);
    assert(gift(-1)==0x1234 && last_list==-1);
    af_v3_furniture_reward_goods(&game,0,1,0,0,0,0x0C02);
    assert(last_out==0 && last_list==2);
    puts("Reward categories, sparse profiles, exclusions, bounds, and seven-argument fallbacks pass");
}
