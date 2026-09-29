/* Shared tree-state rules. Donor tables determine growth/stump records;
   original native families retain their complete original routines. */
#include "scenery_trees.h"
#ifdef AF_V3_TREE_FAMILIES
const TreeRule *tree_family(u32 i) {
    return i?af_v3_tree_carried_rules+i-1:&af_v3_tree_rule;
}
int tree_selected(const TreeRule *r) {
    return r->unused?af_carried_category(r->selected_item)>0:
        af_v3_player_selected_equipment(r->selected_item)>=0;
}
const TreeRule *tree_rule(u32 item) {
    for (u32 i=0;i<TREE_FAMILIES;++i) {
        const TreeRule *r=tree_family(i);
        if ((item-r->first<=r->count || tree_hidden(r,item) || tree_stump(r,item)) && tree_selected(r)) return r;
    }
    return 0;
}
int trees_selected(void) {
    for (u32 i=0;i<TREE_FAMILIES;++i) if (tree_selected(tree_family(i))) return 1;
    return 0;
}
/* The native inventory uses different plant IDs from the donor. Both planting
   paths retain their original placement/animation/consumption code. */
u32 af_v3_tree_plant_seed(u32 item) {
    item&=65535u;
    const TreeRule *r=tree_family(2);
    if (item==r->plant_item && tree_selected(r)) return r->first;
    return item==0x2900u?0x800u:(u16)(item-0x20BCu);
}
u32 af_v3_tree_plant_preview(u32 item) {
    item&=65535u;
    if (item-0x2901u<9u) return 0x68u;
    if (item==0x2900u) return 0x800u;
    const TreeRule *r=tree_family(2);
    return item==r->plant_item && tree_selected(r)?r->first:item;
}
#endif
#ifndef __mips__
extern int af_test_tree_bury(u32,u32,void *,u16 *,u32);
#endif

u32 af_v3_tree_grow(u32 item,int days,int plant) {
    item&=65535u;
    const TreeRule *r=tree_rule(item);
    if (!r || !tree_live(r,item))
        return af_v3_native_tree_grow(item,days,plant);
    u32 index=item-r->first;
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
    item&=65535u;
    const TreeRule *r=tree_rule(item);
    if (!r || (!tree_live(r,item) && !tree_hidden(r,item))) return af_v3_native_tree_stump(item,flag);
    u32 index=item-r->first;
    int hidden=tree_hidden(r,item);
    if ((s16)flag || (!hidden && !index)) return item;
    u32 stage=hidden?4u:(u32)r->growth[index][1];
    return r->stumps[4u-stage];
}

static int bury(u32 item,u32 hole,void *position,u16 *buried,u32 variant) {
    item&=65535u;hole&=65535u;
    for (u32 i=0;i<TREE_FAMILIES;++i) {
        const TreeRule *r=tree_family(i);
        if (item==r->plant_item && (!r->hole || hole==r->hole) && tree_selected(r)) {
            *buried=r->first;return 1;
        }
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
