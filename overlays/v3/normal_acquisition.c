/* Source-bound normal acquisition, using existing saved stock and foreground.
 * Cedar stock occupies one ordinary sapling space, not an extra shop space. */
typedef unsigned short u16;
typedef unsigned char u8;
extern int af_normal_category(unsigned), af_normal_shop_level(void);
extern int af_normal_halloween(void);
extern void af_normal_native_plants(signed char *, const u8 *, int);
extern void af_normal_native_fruit(void);
extern float af_normal_random(void);
extern u16 af_normal_goods[31], af_normal_foreground[30][256];
extern u16 af_normal_selected_diaries(void);
extern void af_normal_prior_select(void *,u16 *,int,u16 *,int,int,int);
extern u16 *af_normal_prior_stock_list(void *,void *,int);
extern void af_normal_priorities(u8 *,int);
extern int af_normal_goods_power(void);
extern const u16 af_normal_diaries[3][7];

static u16 select_diary(u16 selected) {
    u8 priorities[3];
    af_normal_priorities(priorities,0); /* source diaries use furniture priority */
    int roll=(int)(af_normal_random()*100.0f), power=af_normal_goods_power();
    int rare=power<0?5:power+5, uncommon=power+40;
    unsigned rank=roll<rare?2:roll<uncommon?1:0,group=0;
    /* The table stores each A/B/C group's rank, not group numbers by rank. */
    while(group<3 && priorities[group]!=rank) ++group;
    if(group==3) return 0;
    u16 choices[6]; unsigned count=0;
    for(unsigned i=0;i<7 && af_normal_diaries[group][i];++i) {
        u16 item=af_normal_diaries[group][i];
        if(item-0x2B10u<16u && selected&(1u<<(item-0x2B10u))) choices[count++]=item;
    }
    int ordinal=(int)(af_normal_random()*(float)count);
    /* The donor consumes this random draw even when the chosen list is empty. */
    return count?choices[ordinal]:0;
}

void af_normal_shop_select(void *game,u16 *items,int count,u16 *existing,
        int existing_count,int category,int list) {
    u16 selected=af_normal_selected_diaries();
    unsigned long offset=(unsigned long)items-(unsigned long)af_normal_goods;
    int diary=category==1 && selected && af_normal_shop_level()>=2 &&
        count>0 && offset<62 && offset+(unsigned long)count*2<=62;
    /* The donor sells two papers + one diary in Nookway, four + one in
     * Nookington's. Those are the existing three/five native paper spaces.
     * Grab bags and raffle days do not call the ordinary paper selector. */
    af_normal_prior_select(game,items,count-diary,existing,existing_count,category,list);
    if(diary) items[count-1]=select_diary(selected);
}

u16 *af_normal_stock_list(void *lists,void *priorities,int type) {
    u16 *items=af_normal_prior_stock_list(lists,priorities,type);
    if(!items || (*items>>8)!=0x20) return items;
    unsigned count=0;
    while(count<65 && items[count]) {
        if((items[count]>>8)!=0x20) return 0;
        ++count;
    }
    if(count==65) return 0;
    if(af_normal_category(0x2040)!=49) {
        unsigned out=0;
        for(unsigned i=0;i<count;++i) if(items[i]-0x2040u>=4u) items[out++]=items[i];
        items[out]=0;
    }
    return items;
}

void af_normal_shop_plants(signed char *counts, const u8 *goods_count, int flowers) {
    af_normal_native_plants(counts, goods_count, flowers);
    if (af_normal_category(0x290A) != 48 || af_normal_shop_level() < 2 ||
        af_normal_halloween() || counts[0] <= 0) return;
    /* Native daily initialization clears unused saved stock to EMPTY_NO.
     * ShopSaleReport removes this identity from that same saved stock array. */
    for (int i = 0; i < 31; ++i) {
        if (af_normal_goods[i] == 0) {
            af_normal_goods[i] = 0x290A;
            --counts[0];
            return;
        }
    }
}

/* mAGrw_ChangeTree2OtherBlock + mAGrw_ChangeItemBlock. Preserve the donor's
 * count, ordinal RNG selection, scanning order, and decrement per conversion. */
void af_normal_cedar_block(u16 *items, int maximum) {
    u8 count = 0;
    for (int i = 0; i < 256; ++i) if (items[i] == 0x0804) ++count;
    while (maximum > 0 && count != 0) {
        int selected = (int)(af_normal_random() * (float)count);
        for (int i = 0; i < 256; ++i) {
            if (items[i] == 0x0804) {
                if (selected <= 0) { items[i] = 0x0861; break; }
                --selected;
            }
        }
        --count;
        --maximum;
    }
}

extern const int af_normal_cedar_max[4];
void af_normal_new_town(void) {
    af_normal_native_fruit();
    if (af_normal_category(0x290A) != 48) return;
    for (int z = 0; z < 3; ++z)
        for (int x = 0; x < 5; ++x)
            af_normal_cedar_block(af_normal_foreground[z*5+x], af_normal_cedar_max[z]);
}
