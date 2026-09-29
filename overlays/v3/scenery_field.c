/* Shared field clearing and tree-insect eligibility. Real cells stay intact
   during queries; only the existing native clearing callers remove trees. */
#include "scenery_trees.h"

void af_v3_tree_clear(u16 *cell) {
    u32 item=*cell;
    int native=item-0x800u<0x3cu || item-0x84fu<5u;
    const TreeRule *r=tree_rule(item);
    if (native || (r && tree_live(r,item))) *cell=0;
}

int af_v3_tree_insect_match(u32 item,u32 minimum,u32 maximum) {
    item&=65535u;minimum&=65535u;maximum&=65535u;
    if (item>=minimum && item<=maximum) return 1;
    /* Native tree requests use exactly TREE..TREE. Do not broaden flower,
       empty-ground, or any other range into tree habitat. Bee trees exclude. */
    const TreeRule *r=tree_rule(item);
    return minimum==0x804u && maximum==0x804u && r && r->unused!=1 &&
        ((tree_live(r,item) && r->growth[item-r->first][1]==4) ||
         item-r->hidden_first<2u || (r->unused==2 && item==0x82u));
}

int af_v3_tree_insect_scan(u32 minimum,u32 maximum,const u16 *cells,int width,int height) {
    if (!cells || width<=4 || height<=4) return 0;
    for (int z=2;z<height-2;z++) for (int x=2;x<width-2;x++)
        if (af_v3_tree_insect_match(cells[(uptr)z*(u32)width+(u32)x],minimum,maximum)) return 1;
    return 0;
}
