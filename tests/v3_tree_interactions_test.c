#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_interactions.c"
const TreeRule af_v3_tree_rule={.selected_item=0x223b,.hidden_first=0x7f};
const TreeDrop af_v3_tree_drops[17]={
    {0x80c,0x2800,0x809,3},{0x814,0x2804,0x811,3},{0x81c,0x2803,0x819,3},
    {0x824,0x2802,0x821,3},{0x82c,0x2801,0x829,3},{0x831,0x2100,0x804,3},
    {0x836,0x2101,0x804,3},{0x83b,0x2102,0x804,3},{0x853,0x2103,0x804,3},
    {0x5f,0x1088,0x804,1},{0x5e,0x62,0x804,1},{0x61,0x251c,0x804,1},{0x69,0x2103,0x804,1},
    {0x7f,0x2103,0x868,1},{0x80,0x1088,0x868,1},{0x81,0x62,0x868,1},{0x867,0x223b,0x868,1}};
const u16 af_v3_tree_cuts[8][2]={{0x864,1},{0x865,2},{0x866,3},{0x867,3},{0x868,3},{0x7f,3},{0x80,3},{0x81,3}};
static int selected,native_calls,field_calls,null_field;
static u32 seen_variant;
static u16 cells[256];
int af_test_tree_money_luck;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return selected?90:-1; }
const u16 *af_tree_field_units(int x,int z) { assert(x==32 && z==48);++field_calls;return null_field?NULL:cells; }
void af_test_tree_cut_native(int x,int z,u8 *out,u32 variant) {
    assert(x==2 && z==3);++native_calls;seen_variant=variant;
    for (u32 i=0;i<256;++i) out[i]=(u8)(cells[i]%5);
}
int main(void) {
    struct {u32 a;u8 data[256];u32 b;} guard={.a=0x1234,.b=0x5678};
    for (selected=0;selected<2;++selected) {
        const TreeDropSpan *span=af_v3_tree_drop_table();
        assert(span->begin==af_v3_tree_drops && span->end-span->begin==(selected?17:13));
        for (u32 item=0;item<=65535;++item) {
            assert(af_v3_tree_is_bee(item|0xa5000000)==(item==0x5e || (selected && item==0x81)));
            for (af_test_tree_money_luck=0;af_test_tree_money_luck<2;++af_test_tree_money_luck)
                assert(af_v3_tree_drop_item(item,0xa5a52103)==
                    ((af_test_tree_money_luck && (item==0x69 || (selected && item==0x7f)))?0x2100:0x2103));
        }
        for (u32 first=0;first<65536;first+=256) {
            for (u32 i=0;i<256;++i) cells[i]=(u16)(first+i);
            u16 original[256];memcpy(original,cells,sizeof(cells));native_calls=field_calls=0;
            af_v3_tree_cut0(2,3,guard.data);
            assert(native_calls==1 && field_calls==selected && seen_variant==0);
            for (u32 i=0;i<256;++i) {
                u8 expected=(u8)(cells[i]%5);
                if (selected) for (u32 j=0;j<8;++j)
                    if (cells[i]==af_v3_tree_cuts[j][0]) expected=(u8)af_v3_tree_cuts[j][1];
                assert(guard.data[i]==expected);
            }
            assert(!memcmp(original,cells,sizeof(cells)));
        }
    }
    selected=1;null_field=1;
    af_v3_tree_cut1(2,3,guard.data);assert(seen_variant==1);
    af_v3_tree_cut2(2,3,guard.data);assert(seen_variant==2);
    af_v3_tree_cut3(2,3,guard.data);assert(seen_variant==3);
    for (u32 i=0;i<256;++i) assert(guard.data[i]==cells[i]%5);
    assert(guard.a==0x1234 && guard.b==0x5678);
    puts("shared tree drop/cutting rules pass");return 0;
}
