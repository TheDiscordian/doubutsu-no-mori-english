/* Shared state/planting rules, native fallbacks, and bounded writes. */
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_trees.c"

const TreeRule af_v3_tree_rule={0x863,6,0x7f,3,0x223b,0x2202,0x5d,0,
    {{-1,0},{-1,1},{-1,2},{-1,3},{0,4},{0,4}}, {0x7e,0x7d,0x7c,0x7b}};
static int selected, fallback;
static u32 last_item,last_variant;
static int last_days,last_plant;
static void *last_position;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return selected?90:-1; }
u32 af_v3_native_tree_grow(u32 item,int days,int plant) {
    ++fallback;last_item=item;last_days=days;last_plant=plant;return 0xf001;
}
u32 af_v3_native_tree_stump(u32 item,int flag) {
    ++fallback;last_item=item;last_days=flag;return 0xf002;
}
int af_test_tree_bury(u32 item,u32 hole,void *position,u16 *out,u32 variant) {
    ++fallback;last_item=item;last_plant=(int)hole;last_variant=variant;last_position=position;
    *out=(u16)item;return 0;
}
int main(void) {
    selected=1;
    const int days[]={INT_MIN,-1,0,1,2,3,4,100,INT_MAX};
    for (u32 stage=0;stage<6;++stage) for (unsigned d=0;d<sizeof(days)/sizeof(days[0]);++d)
        for (int cap=-1;cap<=5;++cap) {
            u32 expected=stage;
            if (days[d]>=0) for (int step=0;step<4;++step) {
                if (step>days[d] || expected>=4 || (int)expected+1>cap) break;
                ++expected;
            }
            assert(af_v3_tree_grow(0x863+stage,days[d],cap)==0x863+expected);
        }
    assert(fallback==0);
    const u16 inputs[]={0x863,0x864,0x865,0x866,0x867,0x868,0x7f,0x80,0x81};
    const u16 stumps[]={0x863,0x7b,0x7c,0x7d,0x7e,0x7e,0x7e,0x7e,0x7e};
    for (unsigned i=0;i<sizeof(inputs)/sizeof(inputs[0]);++i) {
        assert(af_v3_tree_stump(inputs[i],0)==stumps[i]);
        assert(af_v3_tree_stump(inputs[i],0x10000)==stumps[i]);
        assert(af_v3_tree_stump(inputs[i],-1)==inputs[i]);
        assert(af_v3_tree_stump(inputs[i],1)==inputs[i]);
    }
    assert(fallback==0);
    for (u32 item=0;item<0x10000;++item) {
        if (item>=0x863 && item<=0x868) continue;
        assert(af_v3_tree_grow(item,2,3)==0xf001);
        assert(last_item==item && last_days==2 && last_plant==3);
        if (item>=0x7f && item<=0x81) continue;
        assert(af_v3_tree_stump(item,7)==0xf002 && last_item==item && last_days==7);
    }
    int (*const bury[4])(u32,u32,void *,u16 *)={af_v3_tree_bury0,af_v3_tree_bury1,af_v3_tree_bury2,af_v3_tree_bury3};
    for (u32 variant=0;variant<4;++variant) for (selected=0;selected<2;++selected)
        for (int shine=0;shine<2;++shine) for (int shovel=0;shovel<2;++shovel) {
            u16 out[]={0xaaaa,0,0xbbbb};float position[]={1,2,3};
            u32 item=shovel?0x2202:0x2800,hole=shine?0x5d:0x3f;
            fallback=0;int expected=selected && shine && shovel;
            assert(bury[variant](item,hole,position,out+1)==expected);
            assert(out[0]==0xaaaa && out[2]==0xbbbb && out[1]==(expected?0x863:item));
            assert(position[0]==1 && position[1]==2 && position[2]==3);
            assert(fallback==!expected);
            if (!expected) assert(last_variant==variant && last_item==item && last_plant==(int)hole && last_position==position);
        }
    selected=0;
    assert(af_v3_tree_grow(0x12340863u,INT_MAX,4)==0xf001 && last_item==0x863 && last_days==INT_MAX);
    assert(af_v3_tree_stump(0x12340864u,0)==0xf002 && last_item==0x864);
    puts("shared tree states pass");return 0;
}
