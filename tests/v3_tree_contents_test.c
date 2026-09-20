#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_contents.c"
const TreeRule af_v3_tree_rule={.selected_item=0x223b};
const u16 af_v3_tree_content_tables[4][3]={{0x804,0x861,0x868},
    {0x5e,0x7a,0x81},{0x5f,0x79,0x80},{0x69,0x78,0x7f}};
static int enabled,calls,fallback;
static float random_value;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return enabled?90:-1; }
float af_scenery_random(void) { ++calls;return random_value; }
void af_scenery_native_change(u16 *p,u32 target,u32 count) {
    (void)p;(void)target;(void)count;++fallback;
}
int main(void) {
    struct { u32 a;u16 cells[256];u32 b; } acre={.a=0xcafed00d,.b=0xabbaabba};
    struct { u32 a;u32 words[17];u32 b; } info={.a=0x12345678,.b=0x87654321};
    for (enabled=0;enabled<2;++enabled) {
        for (u32 item=0;item<=65535;++item) {
            u16 value=(u16)item;
            memset(info.words,0xa5,sizeof(info.words));
            int money=item==0x69 || (enabled && item==0x7f);
            assert(af_v3_tree_count_money(&value,info.words)==money);
            assert(info.words[13]==0xa5a5a5a5u+(u32)money && value==item);
            for (int i=0;i<17;++i) if (i!=13) assert(info.words[i]==0xa5a5a5a5);
            for (int row=1;row<4;++row) {
                struct {u8 before,record,after;} flags={0xa5,0x80,0x5a};
                int match=item==af_v3_tree_content_tables[row][0] ||
                    (enabled && item==af_v3_tree_content_tables[row][2]);
                assert(af_v3_tree_record_content(&flags.record,item,af_v3_tree_content_tables[row][0],3)==match);
                assert(flags.record==(match?0x88:0x80) && flags.before==0xa5 && flags.after==0x5a);
            }
        }
        assert(af_v3_tree_count_eligible(0)==0);
        for (int n=0;n<=256;++n) {
            for (int i=0;i<256;++i) acre.cells[i]=i<n?(i&1?0x804:0x868):0x867;
            assert(af_v3_tree_count_eligible(acre.cells)==(u8)(enabled?n:n/2));
        }
    }
    enabled=1;
    for (int row=1;row<4;++row) for (int chosen=0;chosen<4;++chosen) {
        memset(acre.cells,0,sizeof(acre.cells));
        acre.cells[0]=0x867;acre.cells[1]=0x863;acre.cells[2]=0x861;
        const int positions[]={3,17,133,255};
        for (int i=0;i<4;++i) acre.cells[positions[i]]=i&1?0x804:0x868;
        random_value=((float)chosen+0.5f)/4.0f;calls=0;fallback=0;
        af_v3_tree_change_content(acre.cells,af_v3_tree_content_tables[row][0],4);
        for (int i=0;i<4;++i) assert(acre.cells[positions[i]]==(i==chosen?
            af_v3_tree_content_tables[row][i&1?0:2]:(i&1?0x804:0x868)));
        assert(calls==1 && fallback==0 && acre.cells[0]==0x867 && acre.cells[1]==0x863 && acre.cells[2]==0x861);
    }
    u16 before[256];memcpy(before,acre.cells,sizeof(before));
    enabled=0;calls=0;fallback=0;af_v3_tree_change_content(acre.cells,0x5e,4);
    assert(fallback==1 && calls==0 && !memcmp(before,acre.cells,sizeof(before)));
    enabled=1;fallback=0;af_v3_tree_change_content(acre.cells,0x60,4);assert(fallback==1 && calls==0);
    memset(acre.cells,0,sizeof(acre.cells));acre.cells[255]=0x868;random_value=0.8f;calls=0;
    af_v3_tree_change_content(acre.cells,0x69,256); /* Native u8 input wraps to zero. */
    assert(acre.cells[255]==0x7f && calls==1);
    info.words[13]=UINT32_MAX;u16 money=0x7f;assert(af_v3_tree_count_money(&money,info.words)==1 && !info.words[13]);
    assert(acre.a==0xcafed00d && acre.b==0xabbaabba && info.a==0x12345678 && info.b==0x87654321);
    puts("shared daily tree contents pass");return 0;
}
