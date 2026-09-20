/* Shared tree-state rules. Donor tables determine growth/stump records;
   original native families retain their complete original routines. */
#include "scenery_trees.h"
#ifndef __mips__
extern int af_test_tree_bury(u32,u32,void *,u16 *,u32);
#endif

u32 af_v3_tree_grow(u32 item,int days,int plant) {
    const TreeRule *r=&af_v3_tree_rule;
    item&=65535u;
    u32 index=item-r->first;
    if (index>=r->count || af_v3_player_selected_equipment(r->selected_item)<0)
        return af_v3_native_tree_grow(item,days,plant);
    if (days<0) return item;
    /* A stable final stage never changes on additional elapsed days. Avoid
       looping for centuries when the donor would keep adding zero. */
    for (;;) {
        u32 step=(u32)-r->growth[index][0];
        if (!step || step>=r->count-index || r->growth[index+step][1]>plant) break;
        index+=step;item+=step;
        if (!days) break;
        days--;
    }
    return item;
}

u32 af_v3_tree_stump(u32 item,int flag) {
    const TreeRule *r=&af_v3_tree_rule;
    item&=65535u;
    u32 index=item-r->first;
    int hidden=item-r->hidden_first<r->hidden_count;
    if ((index>=r->count && !hidden) || af_v3_player_selected_equipment(r->selected_item)<0)
        return af_v3_native_tree_stump(item,flag);
    if ((s16)flag || (!hidden && !index)) return item;
    return r->stumps[hidden || index>=4u ? 0u : 4u-index];
}

static int bury(u32 item,u32 hole,void *position,u16 *buried,u32 variant) {
    const TreeRule *r=&af_v3_tree_rule;
    item&=65535u;hole&=65535u;
    if (item==r->plant_item && hole==r->hole && af_v3_player_selected_equipment(r->selected_item)>=0) {
        *buried=r->first;return 1;
    }
#ifdef __mips__
    u8 *owner=scene_owner(af_v3_scenery_config+variant);
    return ((int (*)(u32,u32,void *,u16 *))(owner+af_v3_tree_bury_offsets[variant]))(item,hole,position,buried);
#else
    return af_test_tree_bury(item,hole,position,buried,variant);
#endif
}
#define BURY(n) \
int af_v3_tree_bury##n(u32 a,u32 b,void *c,u16 *d) { return bury(a,b,c,d,n); }
BURY(0) BURY(1) BURY(2) BURY(3)
