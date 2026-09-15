#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/camper_trade.h"
#include "../overlays/v3/furniture_rewards.c"
#undef items
#undef rare
struct Item af_test_reward_records[1024];
u16 af_test_reward_rare;
static struct TradePrivate priv;
const struct TradePrivate *native_private = &priv;
struct TradeState native_trade_state;
int native_scene;
u16 camper_last_gift, native_rare_item;
static const u16 tent[10] = {0x335C,0x3360,0x3364,0x336C,0x3370,0x339C,0x33A4,0x33A8,0x33AC,0x33B0};
static unsigned enabled, winter_enabled;
static float rolls[32];
static int nrolls, used, houses, original_calls, goods, names;
static u16 house_item, name_items[5], excluded_items[3][3];
static int goods_category[3], goods_list[3], excluded_count[3];
static const int categories[3] = {0,3,4};
float native_random(void) { assert(used<nrolls); return rolls[used++]; }
u32 native_item_kind(u32 item,u32 mode) {
    assert(mode==2);
    if (item==0x34BF) return 2;
    if (item==0x3260) return 1;
    if (item==0x31A8) return winter_enabled ? 1:3;
    for(int i=0;i<10;++i) if(item==tent[i]) return enabled>>i&1 ? 1:3;
    return item>>12;
}
int af_v3_furniture_import_profile(u32 index) {
    assert(index>=1024 && index<2048);
    return native_item_kind(af_test_reward_records[index-1024].item,2)==1;
}
float af_v3_reward_random(void) { return native_random(); }
void af_v3_native_reward_goods(void *game,u16 *out,int n,const u16 *existing,int count,int cat,int list) {
    native_random_goods(game,out,n,existing,count,cat,list);
}
u16 native_house_item(const void *animal) { assert(animal==&priv); ++houses; return house_item; }
void native_goods_priority(u8 *p,int category) { assert(category==3 || category==4); p[0]=2;p[1]=0;p[2]=1; }
void native_random_goods(void *game,u16 *out,int n,const u16 *existing,int count,int cat,int list) {
    assert(!game && n==1 && goods<3 && count<=3);
    goods_category[goods]=cat;goods_list[goods]=list;excluded_count[goods]=count;
    for(int i=0;i<count;++i) excluded_items[goods][i]=existing[i];
    ++goods;*out=(u16)(0x2600+cat);
}
void native_item_name(u16 item,int slot) { assert(slot>=0 && slot<5); name_items[slot]=item; ++names; }
u16 native_other_fruit(void) { return 0x2802; }
void native_trade_original(PocketPicker p,const void *a,const int *c,int n,int mode) {
    assert(p==af_v3_camper_pocket && a==&priv && c==categories && n==3 && mode==1);++original_calls;
}
static void reset(void) {
    memset(&priv,0,sizeof(priv));memset(&native_trade_state,0,sizeof(native_trade_state));
    memset(name_items,0,sizeof(name_items));native_private=&priv;
    enabled=1023;native_scene=35;camper_last_gift=native_rare_item=house_item=0;
    winter_enabled=0;af_test_reward_rare=0;
    memset(af_test_reward_records,0,sizeof(af_test_reward_records));
    for (int i=0;i<11;++i) {
        u16 item=i==10 ? 0x31A8:tent[i];unsigned slot=(item-0x3000)/4;
        af_test_reward_records[slot]=(struct Item){.index=1024+slot,.item=item,.enabled=1,.reward=i==10 ? 19:23};
    }
    nrolls=used=houses=original_calls=goods=names=0;
}
static void roll(float r) { rolls[nrolls++]=r; }
static int picker(u16 *out) { *out=priv.items[0]; return *out ? 0:-1; }
static void trade(int mode) {
    af_test_reward_rare=native_rare_item;
    af_v3_camper_trade(picker,&priv,categories,3,mode);
    assert(used==nrolls);
    for(int i=1;i<5;++i) assert(name_items[i]==native_trade_state.items[i]);
}
int main(void) {
    /* First/middle/last slot selection and complete original/import eligibility. */
    for(int slot=0;slot<15;++slot) {
        reset();priv.items[slot]=slot%3==0 ? 0x3260 : slot%3==1 ? 0x2601:0x2702;
        roll(0.999f);u16 item=0;
        assert(af_v3_camper_pocket(&item)==slot && item==priv.items[slot]);assert(used==1);
    }
    reset();priv.items[0]=0x1000;priv.items[1]=0x3260;priv.items[2]=0x2701;
    for(int i=0;i<3;++i) { roll((i+0.25f)/3);u16 out=0;assert(af_v3_camper_pocket(&out)==i); }
    reset();priv.items[0]=0x3260;priv.items[1]=0x34BF;priv.items[2]=0x3FFC;
    priv.items[3]=tent[0];enabled=0;camper_last_gift=0x3260;
    u16 out=0xBEEF;assert(af_v3_camper_pocket(&out)==-1 && out==0xBEEF && used==0);
    for(int condition=1;condition<=3;++condition) {
        reset();priv.items[14]=0x3260;priv.conditions=(u32)condition<<28;
        assert(af_v3_camper_pocket(&out)==-1 && out==0xBEEF);
    }
    reset();native_private=0;assert(af_v3_camper_pocket(&out)==-1 && out==0xBEEF);
    reset();native_scene=0;priv.items[0]=camper_last_gift=0x3260;roll(0);
    assert(af_v3_camper_pocket(&out)==0 && out==0x3260);
    af_v3_camper_trade(af_v3_camper_pocket,&priv,categories,3,1);
    assert(original_calls==1 && goods==0 && names==0);
    /* All ten actual camping rewards; tent list persists for carpet/wall A. */
    for(int i=0;i<10;++i) {
        reset();priv.items[0]=0x3260;roll(.8f);roll(.1f);roll((i+.25f)/10);roll(0);
        trade(0);assert(native_trade_state.items[1]==tent[i] && native_trade_state.items[4]==tent[i]);
        assert(goods==2 && goods_list[0]==2 && goods_list[1]==2 && names==5);
        assert(goods_category[0]==3 && goods_category[1]==4 && houses==0);
    }
    /* 79%/80% threshold, house override, and house-empty fallback order. */
    reset();roll(.799f);roll(.1f);trade(1);
    assert(goods==3 && goods_list[0]==8 && goods_list[1]==8 && goods_list[2]==8 && native_trade_state.items[4]==0x2512);
    reset();house_item=0x3260;roll(.8f);roll(.099f);trade(1);
    assert(houses==1 && goods==2 && native_trade_state.items[1]==0x3260 && goods_list[0]==2);
    reset();roll(.8f);roll(.099f);roll(.999f);trade(1);
    assert(houses==1 && native_trade_state.items[1]==tent[9]);
    /* Selected-only stock: single/two-item duplicate allowances match donor. */
    reset();enabled=1<<4;priv.items[0]=native_rare_item=tent[4];roll(.9f);roll(.5f);roll(.2f);trade(1);
    assert(native_trade_state.items[1]==tent[4]);
    reset();enabled=(1<<0)|(1<<9);priv.items[0]=tent[0];native_trade_state.items[1]=tent[9];
    roll(.9f);roll(.5f);roll(.99f);trade(1);assert(native_trade_state.items[1]==tent[9]);
    /* With three available, reject both existing items; reject rare items too. */
    reset();enabled=7;priv.items[0]=tent[0];native_trade_state.items[1]=tent[1];
    roll(.9f);roll(.5f);roll(.01f);roll(.34f);roll(.99f);trade(1);
    assert(native_trade_state.items[1]==tent[2]);
    reset();enabled=7;native_rare_item=tent[0];roll(.9f);roll(.5f);roll(.01f);roll(.34f);trade(1);
    assert(native_trade_state.items[1]==tent[1]);
    reset();enabled=0;roll(.9f);roll(.5f);trade(1);
    assert(goods==3 && goods_list[0]==8);
    reset();enabled=7;priv.items[0]=tent[0];native_trade_state.items[1]=tent[1];native_rare_item=tent[2];
    roll(.9f);roll(.5f);trade(1);assert(goods==3); /* no endless rejection */
    /* Fish/bug category set retains clothes, stationery, fruit, and exclusions. */
    reset();const int other[3]={2,1,5};priv.items[0]=0x2300;priv.shirt=0x34BF;roll(.5f);
    af_v3_camper_trade(picker,&priv,other,3,0);
    assert(goods==2 && goods_category[0]==2 && goods_category[1]==1 && goods_list[0]==8 && houses==0);
    assert(excluded_count[0]==3 && excluded_items[0][0]==0x2300 && excluded_items[0][2]==0x34BF);
    assert(native_trade_state.items[3]==0x2802 && native_trade_state.items[4]==0x2601);
    assert(used==nrolls);
    /* Winter only opts into donor logic when a winter import is selected. */
    reset();native_scene=31;
    af_v3_camper_trade(af_v3_camper_pocket,&priv,categories,3,1);
    assert(original_calls==1 && !used && !goods);
    reset();native_scene=31;winter_enabled=1;roll(.899f);roll(.1f);trade(1);
    assert(goods==3 && goods_list[0]==8 && houses==0);
    reset();native_scene=31;winter_enabled=1;roll(.9f);roll(.1f);roll(.5f);trade(1);
    assert(native_trade_state.items[1]==0x31A8 && goods==2 && goods_list[0]==2);
    reset();native_scene=31;winter_enabled=1;house_item=0x3260;roll(.9f);roll(.099f);trade(1);
    assert(native_trade_state.items[1]==0x3260 && houses==1 && goods==2 && goods_list[0]==2);
    reset();native_scene=31;winter_enabled=1;roll(.9f);roll(.099f);roll(.5f);trade(1);
    assert(native_trade_state.items[1]==0x31A8 && houses==1);
    puts("pass: full-ID pocket search, actual camping rewards, optional profiles, exclusions, donor rolls, and retained categories");
}
