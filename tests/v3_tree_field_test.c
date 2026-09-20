#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_field.c"
const TreeRule af_v3_tree_rule={.first=0x863,.count=6,.selected_item=0x223b};
static int selected;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return selected?90:-1; }
int main(void) {
    for (selected=0;selected<2;selected++) for (u32 item=0;item<65536;item++) {
        struct { u16 guard0,cell,guard1; } value={0xa5a5,item,0x5a5a};
        af_v3_tree_clear(&value.cell);
        int clear=item-0x800u<0x3cu || item-0x84fu<5u || (selected&&item-0x863u<6u);
        assert(value.cell==(clear?0:item));assert(value.guard0==0xa5a5 && value.guard1==0x5a5a);
        int gold=selected && (item==0x867 || item==0x868 || item==0x7f || item==0x80);
        assert(af_v3_tree_insect_match(item|0xa5000000,0x804,0x804)==(item==0x804||gold));
        assert(af_v3_tree_insect_match(item,0x845,0x84d)==(item>=0x845&&item<=0x84d));
        assert(af_v3_tree_insect_match(item,0,0)==(item==0));
        assert(!af_v3_tree_insect_match(item,0x805,0x804));
    }
    u16 cells[256],copy[256];
    for (selected=0;selected<2;selected++) for (int z=0;z<16;z++) for (int x=0;x<16;x++) {
        memset(cells,0,sizeof(cells));cells[z*16+x]=0x868;memcpy(copy,cells,sizeof(cells));
        assert(af_v3_tree_insect_scan(0x804,0x804,cells,16,16)==(selected&&x>=2&&x<14&&z>=2&&z<14));
        assert(!memcmp(cells,copy,sizeof(cells)));
    }
    memset(cells,0,sizeof(cells));cells[2*16+2]=0x804;
    selected=0;assert(af_v3_tree_insect_scan(0x804,0x804,cells,16,16));
    assert(!af_v3_tree_insect_scan(0x804,0x804,NULL,16,16));
    for (int size=-4;size<=4;size++) {
        assert(!af_v3_tree_insect_scan(0,0,cells,size,16));
        assert(!af_v3_tree_insect_scan(0,0,cells,16,size));
    }
    assert(!af_v3_tree_insect_scan(0,0,cells,INT_MIN,INT_MIN));
    puts("shared tree field/insect predicates pass");return 0;
}
