/* Donor hidden contents on imported trees; original acre scheduling stays native. */
#include "scenery_trees.h"
extern const u16 af_v3_tree_content_tables[4][3];
extern float af_scenery_random(void);
extern void af_scenery_native_change(u16 *,u32,u32);

static int content_family(u32 item,int row) {
    if (item==af_v3_tree_content_tables[row][0]) return 0;
    const TreeRule *r=tree_rule(item);
    if (!r || r->unused==1) return -1;
    int family=r->unused==2?1:2;
    return item==af_v3_tree_content_tables[row][family]?family:-1;
}
static int content_row(u16 item) {
    for (int row=1;row<4;++row) if (af_v3_tree_content_tables[row][0]==item) return row;
    return 0;
}
int af_v3_tree_record_content(u8 *record,u32 item,u32 native,int block_x) {
    item=(u16)item;native=(u16)native;
    int row=content_row((u16)native);
    if (item==native || (row && content_family(item,row)>=0)) {
        *record|=(u8)(1u<<((u32)block_x&31u));
        return 1;
    }
    return 0;
}
int af_v3_tree_count_money(u16 *item,void *info) {
    if (content_family(*item,3)>=0) {
        /* Native GrowInfo: money_tree_num at 0x34; preserve wrapping addition. */
        ++*(u32 *)((u8 *)info+0x34);
        return 1;
    }
    return 0;
}
u32 af_v3_tree_count_eligible(u16 *items) {
    u8 count=0;
    if (items) for (u32 i=0;i<256;++i)
        if (content_family(items[i],0)>=0) ++count;
    return count;
}
void af_v3_tree_change_content(u16 *items,u32 target,u32 count) {
    int row=content_row((u16)target);
    if (!row || !trees_selected()) {
        af_scenery_native_change(items,target,count);return;
    }
    int chosen=(int)(af_scenery_random()*(float)(u8)count);
    for (u32 i=0;i<256;++i) {
        int family=content_family(items[i],0);
        if (family<0) continue;
        if (chosen<=0) { items[i]=af_v3_tree_content_tables[row][family];break; }
        --chosen;
    }
}
