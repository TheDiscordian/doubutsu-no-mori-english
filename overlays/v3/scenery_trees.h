#ifndef AF_V3_SCENERY_TREES_H
#define AF_V3_SCENERY_TREES_H
#include "scenery.h"
typedef unsigned short u16;
typedef signed short s16;
typedef struct { float x,y,z; } TreePosition;
typedef struct {
    u16 first, count, hidden_first, hidden_count, selected_item, plant_item, hole, unused;
#ifdef AF_V3_TREE_FAMILIES
    s16 growth[8][2];
#else
    s16 growth[6][2];
#endif
    u16 stumps[4];
} TreeRule;
#ifdef AF_V3_TREE_FAMILIES
_Static_assert(sizeof(TreeRule)==56,"Complete tree rule layout");
extern const TreeRule af_v3_tree_carried_rules[2];
#define TREE_FAMILIES 3u
#else
_Static_assert(sizeof(TreeRule)==48,"Tree rule layout");
#define TREE_FAMILIES 1u
#endif
extern const TreeRule af_v3_tree_rule;
#ifdef AF_V3_TREE_FAMILIES
const TreeRule *tree_family(u32);
int tree_selected(const TreeRule *);
const TreeRule *tree_rule(u32);
int trees_selected(void);
#else
static inline const TreeRule *tree_family(u32 i) {
    (void)i;
    return &af_v3_tree_rule;
}
static inline int tree_selected(const TreeRule *r) {
    return af_v3_player_selected_equipment(r->selected_item)>=0;
}
#endif
static inline int tree_live(const TreeRule *r,u32 item) { return item-r->first<r->count; }
static inline int tree_stump(const TreeRule *r,u32 item) { return item-r->stumps[3]<4u; }
static inline int tree_hidden(const TreeRule *r,u32 item) {
    return item-r->hidden_first<r->hidden_count || (r->unused==2 && item==0x82u);
}
#ifndef AF_V3_TREE_FAMILIES
static inline const TreeRule *tree_rule(u32 item) {
    for (u32 i=0;i<TREE_FAMILIES;++i) {
        const TreeRule *r=tree_family(i);
        if ((item-r->first<=r->count || tree_hidden(r,item) || tree_stump(r,item)) && tree_selected(r)) return r;
    }
    return 0;
}
static inline int trees_selected(void) {
    for (u32 i=0;i<TREE_FAMILIES;++i) if (tree_selected(tree_family(i))) return 1;
    return 0;
}
#endif
extern const u32 af_v3_tree_bury_offsets[4];
extern u32 af_v3_native_tree_grow(u32,int,int);
extern u32 af_v3_native_tree_stump(u32,int);
extern u32 af_v3_tree_grow(u32,int,int);
typedef struct {
    u32 slot, near, plant, set_info, reset_info, thin;
    u16 dead, native_dead;
    u32 limit;
} TreeDaily;
_Static_assert(sizeof(TreeDaily)==32,"Daily tree bindings");
extern const TreeDaily af_v3_tree_daily_config;
typedef struct { u16 tree,item,after,count; } TreeDrop;
#ifdef AF_V3_TREE_FAMILIES
extern const TreeDrop af_v3_tree_drops[21];
extern const u16 af_v3_tree_cuts[23][2];
#define TREE_CUTS 23u
#else
extern const TreeDrop af_v3_tree_drops[17];
extern const u16 af_v3_tree_cuts[8][2];
#define TREE_CUTS 8u
#endif
#endif
