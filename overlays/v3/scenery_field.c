/* Shared field clearing and tree-insect eligibility. Real cells stay intact
   during queries; only the existing native clearing callers remove trees. */
#include "scenery_trees.h"

void af_v3_tree_clear(u16 *cell) {
    u32 item=*cell;
    int native=item-0x800u<0x3cu || item-0x84fu<5u;
    int gold=item-af_v3_tree_rule.first<af_v3_tree_rule.count &&
        af_v3_player_selected_equipment(af_v3_tree_rule.selected_item)>=0;
    if (native || gold) *cell=0;
}

int af_v3_tree_insect_match(u32 item,u32 minimum,u32 maximum) {
    item&=65535u;minimum&=65535u;maximum&=65535u;
    if (item>=minimum && item<=maximum) return 1;
    /* Native tree requests use exactly TREE..TREE. Do not broaden flower,
       empty-ground, or any other range into tree habitat. Bee trees exclude. */
    return minimum==0x804u && maximum==0x804u &&
        (item==0x867u || item==0x868u || item==0x7fu || item==0x80u) &&
        af_v3_player_selected_equipment(af_v3_tree_rule.selected_item)>=0;
}

int af_v3_tree_insect_scan(u32 minimum,u32 maximum,const u16 *cells,int width,int height) {
    if (!cells || width<=4 || height<=4) return 0;
    for (int z=2;z<height-2;z++) for (int x=2;x<width-2;x++)
        if (af_v3_tree_insect_match(cells[(uptr)z*(u32)width+(u32)x],minimum,maximum)) return 1;
    return 0;
}
