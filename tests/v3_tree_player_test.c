#include <assert.h>
#include <stdio.h>
#include "../overlays/v3/scenery_player.c"
const TreeRule af_v3_tree_rule={.first=0x863,.count=6,.hidden_first=0x7f,.hidden_count=3,.selected_item=0x223b};
const u32 af_v3_tree_player_masks[2][3]={{3755991006u,259776479u,983040u},{1077952578u,17317952u,65536u}};
static int selected;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return selected?90:-1; }
int af_v3_tree_is_bee(u32 item) { return item==0x5e || (selected && item==0x81); }
int main(void) {
    const u16 first[]={0x801,0x806,0x80e,0x816,0x81e,0x826,0x82e,0x833,0x838,0x850};
    for (selected=0;selected<2;++selected) for (u32 item=0;item<65536;++item) {
        int native=(item>=0x5e && item<=0x61)||item==0x69,small=0;
        for (u32 i=0;i<10;++i) {
            u32 count=i>=1 && i<=5?7:4;
            if (item-first[i]<count) native=1;
            if (item==first[i]) small=1;
        }
        int gold=selected && ((item>=0x864 && item<=0x868)||(item>=0x7f && item<=0x81));
        u32 noisy=item|0xA5000000u;
        assert(af_v3_tree_player_query(noisy,0)==(native||gold));
        assert(af_v3_tree_player_query(noisy,1)==((native&&!small)||(gold&&item!=0x864)));
        assert(af_v3_tree_player_query(noisy,2)==(item==0x5e||(selected&&item==0x81)));
        assert(!af_v3_tree_player_query(noisy,3));
    }
    puts("shared player tree predicates pass");return 0;
}
