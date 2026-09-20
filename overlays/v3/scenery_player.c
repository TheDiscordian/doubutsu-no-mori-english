/* Shared player predicates. Queries never rewrite the foreground identity. */
#include "scenery_trees.h"
extern const u32 af_v3_tree_player_masks[2][3];
extern int af_v3_tree_is_bee(u32);
static int mask_has(u32 item,u32 group) {
    u32 bit=item-0x800u;
    return bit<96u && (af_v3_tree_player_masks[group][bit>>5]>>(bit&31)&1u);
}
int af_v3_tree_player_query(u32 item,u32 query) {
    item&=65535;
    if (query==2) return af_v3_tree_is_bee(item);
    if (query>2) return 0;
    int native=mask_has(item,0) || item==0x5e || item==0x5f ||
        item==0x60 || item==0x61 || item==0x69;
    if (native) return query==0 || !mask_has(item,1);
    u32 stage=item-af_v3_tree_rule.first;
    int gold=(stage>0 && stage<af_v3_tree_rule.count) ||
        item-af_v3_tree_rule.hidden_first<af_v3_tree_rule.hidden_count;
    return gold && (query==0 || stage!=1) &&
        af_v3_player_selected_equipment(af_v3_tree_rule.selected_item)>=0;
}
