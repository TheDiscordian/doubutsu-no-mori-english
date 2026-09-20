#ifndef AF_V3_SCENERY_TREES_H
#define AF_V3_SCENERY_TREES_H
#include "scenery.h"
typedef unsigned short u16;
typedef signed short s16;
typedef struct {
    u16 first, count, hidden_first, hidden_count, selected_item, plant_item, hole, unused;
    s16 growth[6][2];
    u16 stumps[4];
} TreeRule;
_Static_assert(sizeof(TreeRule)==48,"Tree rule layout");
extern const TreeRule af_v3_tree_rule;
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
#endif
