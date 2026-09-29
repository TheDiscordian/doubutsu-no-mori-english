/* Shared native stationery generation; no per-style creation rules.
 * Background-only callers retain the original selector through its bridge.
 * The original RNG, rarity, exclusions, fallback, and allocation stay intact. */
#include "carried_paper.h"
extern void af_paper_original_select(void *,AFCarryHalf *,int,AFCarryHalf *,int,int,int);
extern int af_paper_original_goods_exist(AFCarryHalf *,int,AFCarryWord);
extern int af_paper_prior_shop_category(AFCarryWord);
extern int af_paper_native_give(void *,AFCarryHalf,int);
extern void af_paper_native_demo(int,int,int);

void af_carried_paper_select(void *game,AFCarryHalf *items,int count,
        AFCarryHalf *existing,int existing_count,int category,int list) {
    af_paper_original_select(game,items,count,existing,existing_count,category,list);
    if(items && count>0 && category==1)
        for(int i=0;i<count;i++)items[i]=af_carried_paper_create_item(items[i]);
}

int af_carried_paper_goods_exist(AFCarryHalf *items,int count,AFCarryWord item) {
    int style=af_carried_paper_style((AFCarryHalf)item);
    if(!af_carried_paper_packs_enabled() || style<0)
        return af_paper_original_goods_exist(items,count,item);
    /* Generated candidates are still singles inside the original selector;
     * saved shop/exclusion entries can already be packs. Compare styles without
     * mutating the caller's existing inventory or introducing another buffer. */
    if(items && count>0)
        for(int i=0;i<count;i++)if(af_carried_paper_style(items[i])==style)return 1;
    return 0;
}

int af_carried_paper_shop_category(AFCarryWord argument) {
    AFCarryWord item=(AFCarryHalf)argument;
    if(af_carried_paper_reserved(item))return af_carried_paper_packs_enabled()?1:-1;
    if(item-0x2040u<4u)return af_carried_paper_style(item)==64?1:-1;
    return af_paper_prior_shop_category(argument);
}

int af_carried_paper_first_job_give(void *player,AFCarryHalf item,int condition) {
    return af_paper_native_give(player,af_carried_paper_create_item(item),condition);
}

void af_carried_paper_first_job_show(int order,int field,int item) {
    af_paper_native_demo(order,field,af_carried_paper_create_item((AFCarryHalf)item));
}
