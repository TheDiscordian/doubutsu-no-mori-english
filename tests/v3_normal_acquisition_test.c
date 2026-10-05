#include <assert.h>
#include <string.h>
#include "../overlays/v3/normal_acquisition.c"

u16 af_normal_goods[31], af_normal_foreground[30][256];
const int af_normal_cedar_max[4] = {6, 4, 2, 0};
const u16 af_normal_diaries[3][7]={{0x2B11,0x2B14,0x2B17,0x2B1A,0x2B1D,0,0},
    {0x2B12,0x2B15,0x2B18,0x2B1B,0x2B1E,0,0},{0x2B13,0x2B16,0x2B19,0x2B1C,0x2B1F,0x2B10,0}};
static u16 diary_mask=0, stock_list[66];
static int paper_enabled=0;
static u8 priority[3]={0,1,2};
static float random_value=0.5f;
static int goods_power=0;
static int enabled=1, level=2, halloween=0, fruit_calls=0, random_calls=0;
int af_normal_category(unsigned item) { assert(item==0x290A || item==0x2040); return item==0x2040?(paper_enabled?49:0):(enabled?48:0); }
int af_normal_shop_level(void) { return level; }
int af_normal_halloween(void) { return halloween; }
float af_normal_random(void) { ++random_calls; return random_value; }
void af_normal_native_fruit(void) { ++fruit_calls; }
u16 af_normal_selected_diaries(void) { return diary_mask; }
void af_normal_priorities(u8 *out,int kind) { assert(kind==0); memcpy(out,priority,3); }
int af_normal_goods_power(void) { return goods_power; }
void af_normal_prior_select(void *game,u16 *items,int count,u16 *existing,int existing_count,int category,int list) {
    (void)game;(void)existing;(void)existing_count; assert(category==1 && list==8);
    for(int i=0;i<count;++i) items[i]=0x2000+i;
}
u16 *af_normal_prior_stock_list(void *lists,void *priorities,int type) {
    (void)lists;(void)priorities;(void)type;return stock_list;
}
void af_normal_native_plants(signed char *counts, const u8 *goods, int flowers) {
    memset(counts,0,10); counts[0]=goods[8]; counts[1]=flowers;
}

int main(void) {
    u8 goods[12]={0}; goods[8]=2;
    struct { unsigned before; signed char counts[10]; u16 shop_info; unsigned after; } plant;
    memset(&plant,0,sizeof(plant)); plant.before=0xabcdef01; plant.after=0x12345678; plant.shop_info=0x9a5b;
    for (level=0;level<4;++level) for(enabled=0;enabled<2;++enabled) for(halloween=0;halloween<2;++halloween) {
        memset(af_normal_goods,0,sizeof(af_normal_goods));
        for(int i=0;i<25;++i) af_normal_goods[i]=(u16)(0x1000+i);
        af_normal_shop_plants(plant.counts,goods,3);
        int added=level>=2 && enabled && !halloween;
        assert(af_normal_goods[25]==(added?0x290A:0));
        assert(plant.counts[0]==2-added && plant.counts[1]==3);
        assert(plant.shop_info==0x9a5b && plant.before==0xabcdef01 && plant.after==0x12345678);
        for(int i=0;i<25;++i) assert(af_normal_goods[i]==0x1000+i);
        for(int i=26;i<31;++i) assert(af_normal_goods[i]==0);
    }
    level=2; enabled=1; halloween=0;
    for(int i=0;i<31;++i) af_normal_goods[i]=0x1000;
    af_normal_shop_plants(plant.counts,goods,3);
    assert(plant.counts[0]==2); /* no stock space: never corrupt another item */
    for(enabled=0;enabled<2;++enabled) {
        random_calls=0;
        for(int acre=0;acre<30;++acre) for(int i=0;i<256;++i)
            af_normal_foreground[acre][i]=i<9?0x0804:0x7777;
        af_normal_new_town();
        assert(fruit_calls==enabled+1);
        for(int acre=0;acre<30;++acre) {
            int converted=0;
            for(int i=0;i<256;++i) {
                if(i>=9) assert(af_normal_foreground[acre][i]==0x7777);
                if(af_normal_foreground[acre][i]==0x0861) ++converted;
            }
            assert(converted==(enabled && acre<15?af_normal_cedar_max[acre/5]:0));
        }
        assert(random_calls==(enabled?60:0));
    }
    u16 few[256]={0}; few[255]=0x0804;
    af_normal_cedar_block(few,6); assert(few[255]==0x0861);
    /* Preserve the original eight-bit count, including its 256-tree wrap. */
    u16 full[256]; for(int i=0;i<256;++i) full[i]=0x0804;
    int prior_random=random_calls; af_normal_cedar_block(full,6);
    for(int i=0;i<256;++i) assert(full[i]==0x0804);
    assert(random_calls==prior_random);
    level=2; diary_mask=0xffff;
    af_normal_shop_select(0,af_normal_goods,3,0,0,1,8);
    assert(af_normal_goods[0]==0x2000 && af_normal_goods[1]==0x2001 && af_normal_goods[2]==0x2B17);
    diary_mask=0;
    af_normal_shop_select(0,af_normal_goods,3,0,0,1,8);
    assert(af_normal_goods[2]==0x2002);
    diary_mask=0xffff;
    u16 gift[3]; af_normal_shop_select(0,gift,3,0,0,1,8); assert(gift[2]==0x2002);
    level=1; af_normal_shop_select(0,af_normal_goods,3,0,0,1,8); assert(af_normal_goods[2]==0x2002);
    static const u8 permutations[6][3]={{0,1,2},{0,2,1},{1,0,2},{1,2,0},{2,0,1},{2,1,0}};
    for(unsigned p=0;p<6;++p) for(goods_power=-30;goods_power<=50;goods_power+=10)
        for(unsigned roll=0;roll<100;++roll) {
            memcpy(priority,permutations[p],3);random_value=(float)roll/100.0f;
            /* Original GetItemList chooses a rank; SelectListFromPriority
             * searches the A/B/C entries for that rank. */
            int actual_roll=(int)(random_value*100.0f);
            unsigned rank=actual_roll<(goods_power<0?5:goods_power+5)?2:
                actual_roll<goods_power+40?1:0;
            unsigned group=0;while(priority[group]!=rank) ++group;
            unsigned count=group==2?6:5;
            int before=random_calls;
            assert(select_diary(0xffff)==af_normal_diaries[group][(int)(random_value*count)]);
            assert(random_calls==before+2);
            before=random_calls;
            assert(select_diary((u16)(1u<<(af_normal_diaries[(group+1)%3][0]-0x2B10)))==0);
            assert(random_calls==before+2); /* empty selected group still draws */
        }
    random_value=0.5f;goods_power=0;memcpy(priority,permutations[0],3);
    for(paper_enabled=0;paper_enabled<2;++paper_enabled) {
        stock_list[0]=0x2001;stock_list[1]=0x2040;stock_list[2]=0x2002;stock_list[3]=0;
        assert(af_normal_stock_list(0,0,8)==stock_list);
        assert(stock_list[0]==0x2001 && stock_list[1]==(paper_enabled?0x2040:0x2002));
        assert(stock_list[paper_enabled?3:2]==0);
    }
    return 0;
}
