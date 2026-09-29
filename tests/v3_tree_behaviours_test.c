/* The current generated configuration links separately: exercise the same
 * complete family tables as the cartridge, with native services doubled. */
#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_trees.c"
#include "../overlays/v3/scenery_daily.c"
#include "../overlays/v3/scenery_contents.c"
#include "../overlays/v3/scenery_world.c"
#include "../overlays/v3/scenery_interactions.c"
#include "../overlays/v3/scenery_player.c"
#include "../overlays/v3/scenery_field.c"

static u32 selected;
static int fallback,ground_calls;
static float ground_height,random_value;
static TreePosition seen_position;
static u16 acre[256];
int af_test_tree_money_luck;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223B);return selected&1?90:-1; }
int af_carried_category(u32 item) {
    assert(item==0x2807 || item==0x290A);
    return selected&(item==0x2807?2:4)?50:0;
}
u32 af_v3_native_tree_grow(u32 item,int days,int cap) { (void)days;(void)cap;fallback++;return item; }
u32 af_v3_native_tree_stump(u32 item,int flag) { (void)flag;fallback++;return item; }
int af_test_tree_bury(u32 item,u32 hole,void *p,u16 *out,u32 v) {
    (void)item;(void)hole;(void)p;(void)out;assert(v<4);fallback++;return 0;
}
int native_near(u16 *p,GrowInfo *g,int x,int z) { (void)p;(void)g;(void)x;(void)z;fallback++;return 1; }
int native_plant(u16 *p,GrowInfo *g) { (void)p;(void)g;fallback++;return 0; }
void native_set(u16 *b,u16 *p) {
    memset(b,0,32);for (u32 i=0;i<256;i++) if (native_sapling(p[i])) b[i/16]|=(u16)(1u<<(i%16));
}
void native_reset(u16 *b,u8 *n,u8 *o,u16 *p) {
    for (u32 i=0;i<256;i++) if (b[i/16]>>(i%16)&1u) {
        if (p[i]==0x84E)b[i/16]&=(u16)~(1u<<(i%16));
        else if (p[i]-0x800u<5u)++*n;
        else if (p[i])++*o;
    }
}
void native_thin(u16 *p,u16 *b,int n,int o) { (void)p;(void)b;(void)n;(void)o;fallback++; }
float af_scenery_random(void) { return random_value; }
int af_tree_block_position(float *x,float *z,int bx,int bz) { *x=640.0f*bx;*z=640.0f*bz;return 1; }
float af_tree_ground_height(TreePosition p,float offset) {
    assert(offset==0);seen_position=p;ground_calls++;return ground_height;
}
void af_scenery_native_change(u16 *p,u32 target,u32 count) { (void)p;(void)target;(void)count;fallback++; }
int af_v3_tree_column_native(void *c,const TreeUnit *u,int grounded,u32 low,u32 high) {
    (void)c;assert(grounded==1);assert(low==0xFFFF && high==0);return u->item;
}
int af_v3_tree_dig_native(const u16 *p,u32 x,u32 y,u32 z) { (void)p;(void)x;(void)y;(void)z;return -1; }
int af_v3_tree_npc_native(u32 item) { (void)item;return -1; }
const u16 *af_tree_field_units(int x,int z) { assert(x==32 && z==96);return acre; }
void af_test_tree_cut_native(int x,int z,u8 *out,u32 v) {
    assert(x==2 && z==6 && v<4);memset(out,0xA5,256);
}
int af_test_tree_talk(u32 index,u32 variant) { (void)index;assert(variant<4);return -1; }

static void family_cases(void) {
    const u32 masks[]={0,1,2,4,7};
    for (u32 profile=0;profile<5;profile++) {
        selected=masks[profile];
        for (u32 f=0;f<3;f++) {
            const TreeRule *r=tree_family(f);int enabled=(selected>>f)&1u;
            for (u32 s=0;s<=r->count;s++) {
                u16 item=(u16)(r->first+s);
                assert((tree_rule(item)!=0)==enabled);
                u32 result=af_v3_tree_grow(item,20,4);
                u32 final=r->first+(f==0?(s<4?4:s):r->count-1u);
                assert(result==(enabled && s<r->count?final:item));
                assert(af_v3_tree_grow(item,-1,4)==item);
                assert(af_v3_tree_grow(item,20,0)==item);
                assert(af_v3_tree_stump(item,1)==item);
                u32 stump=enabled && s && s<r->count?r->stumps[4-r->growth[s][1]]:item;
                assert(af_v3_tree_stump(item,0)==stump);
                assert(af_v3_tree_player_query(item,0)==(enabled && s && s<r->count));
                assert(af_v3_tree_player_query(item,1)==(enabled && s>1 && s<r->count));
                assert(af_v3_tree_dig(&item,0,0,0)==(enabled && (!s || s==r->count)?1:-1));
                assert(af_v3_tree_npc(item)==(enabled && !s?1:-1));
                u16 clear=item;af_v3_tree_clear(&clear);
                assert(clear==(enabled && s<r->count?0:item));
            }
            for (u32 s=0;s<4;s++) {
                u16 item=r->stumps[s];assert(af_v3_tree_player_query(item,3)==enabled);
                assert(af_v3_tree_dig(&item,0,0,0)==(enabled?1:-1));
            }
            u16 result=0xCAFE;
            assert(af_v3_tree_bury0(r->plant_item,r->hole,0,&result)==enabled);
            assert(result==(enabled?r->first:0xCAFE));
            if (f==2) {
                assert(af_v3_tree_plant_seed(0x290A)==(enabled?0x85D:0x84E));
                assert(af_v3_tree_plant_preview(0x290A)==(enabled?0x85D:0x290A));
            }
            u32 drop=f==0?0x867:f==1?0x85B:0x78;
            const TreeDropSpan *span=af_v3_tree_drop_table(drop);
            assert(span->end-span->begin==(enabled?21:13));
            if (enabled) {
                TreeUnit unit={.flags=0x1234,.item=(u16)(r->first+2)},before=unit;
                assert(af_v3_tree_column(0,&unit,1,0xFFFF,0)==0x802);
                assert(!memcmp(&unit,&before,sizeof(unit)));
                assert(af_v3_tree_column(0,&unit,1,unit.item,unit.item)==0);
            }
        }
        assert(af_v3_tree_is_bee(0x7A)==!!(selected&4));
        assert(af_v3_tree_is_bee(0x81)==!!(selected&1));
        assert(af_v3_tree_is_bee(0x5E)==1);
        assert(!af_v3_tree_insect_match(0x85B,0x804,0x804));
        assert(af_v3_tree_insect_match(0x861,0x804,0x804)==!!(selected&4));
        assert(!af_v3_tree_insect_match(0x7A,0x804,0x804));
    }
    selected=7;
    assert(af_v3_tree_plant_seed(0x2900)==0x800 && af_v3_tree_plant_preview(0x2900)==0x800);
    for (u32 item=0x2901;item<=0x2909;item++) {
        assert(af_v3_tree_plant_seed(item)==item-0x20BC);
        assert(af_v3_tree_plant_preview(item)==0x68);
    }
    assert(af_v3_tree_plant_preview(0x2807)==0x2807);
    assert(af_v3_tree_grow(0x857,0,4)==0x85B);
    assert(af_v3_tree_grow(0x858,0,4)==0x859);
    assert(af_v3_tree_grow(0x858,1,4)==0x85A);
    assert(af_v3_tree_grow(0x858,2,4)==0x85B);
    for (u32 s=0;s<4;s++)assert(af_v3_tree_stump(0x858+s,0)==0x73);
    assert(af_v3_tree_stump(0x82,0)==0x77);
}

static void daily_cases(void) {
    selected=7;GrowInfo info={.cap=4,.days=1,.block_x=2,.block_z=6,.x=7,.z=8};
    u16 acres[5][256];for (u32 d=0;d<4;d++)info.around[d]=acres[d+1];
    for (u32 f=0;f<3;f++) for (u32 d=0;d<4;d++) for (int edge=0;edge<2;edge++) {
        const TreeRule *r=tree_family(f);info.x=7;info.z=8;
        if (edge) { if (d<2)info.z=d?15:0;else info.x=d==2?0:15; }
        memset(acres,0,sizeof(acres));u16 *p=acres[0]+info.z*16+info.x;*p=r->first;
        *neighbour(p,&info,info.x,info.z,d)=tree_family((f+1)%3)->first+2;
        af_v3_tree_daily_plant(p,&info);assert(*p==r->first+r->count);
    }
    info.x=7;info.z=8;ground_height=100;memset(acres,0,sizeof(acres));
    u16 *p=acres[0]+info.z*16+info.x;
    *p=0x854;assert(af_v3_tree_daily_plant(p,&info)==1 && *p==0x855);
    info.block_z=5;*p=0x854;af_v3_tree_daily_plant(p,&info);assert(*p==0x85C);
    af_v3_tree_daily_plant(p,&info);assert(!*p);
    *p=0x85D;ground_calls=0;af_v3_tree_daily_plant(p,&info);assert(*p==0x85E && ground_calls==1);
    assert(seen_position.x==1580 && seen_position.z==3540 && seen_position.y==0);
    ground_height=99.5f;*p=0x85D;af_v3_tree_daily_plant(p,&info);assert(*p==0x862);
    af_v3_tree_daily_plant(p,&info);assert(!*p);
    ground_height=120;info.days=0;*p=0x85D;af_v3_tree_daily_plant(p,&info);assert(*p==0x85D);
    for (u32 f=0;f<3;f++) {
        const TreeRule *r=tree_family(f);
        info.cap=0;*p=r->first+2;af_v3_tree_daily_plant(p,&info);assert(*p==r->first+r->count);
        info.cap=-1;*p=r->first+2;af_v3_tree_daily_plant(p,&info);assert(!*p);
    }
    struct {u32 a;u16 bits[16];u32 b;} guard={.a=0x12345678,.b=0xABCDEF01};
    memset(acre,0,sizeof(acre));acre[0]=0x800;acre[1]=0x85D;acre[2]=0x854;acre[3]=0x863;
    af_v3_tree_set_info(guard.bits,acre);assert(guard.bits[0]==15);
    u8 normal=0,other=0;af_v3_tree_reset_info(guard.bits,&normal,&other,acre);assert(normal==2 && other==2);
    for (u32 i=4;i<34;i++)acre[i]=0x861;
    random_value=0.75f;af_v3_tree_thin(acre,guard.bits,normal,other);
    assert(acre[0]==0x84E && acre[1]==0x862 && acre[2]==0x854 && acre[3]==0x863);
    assert(guard.bits[0]==12 && guard.a==0x12345678 && guard.b==0xABCDEF01);
    acre[2]=0x85C;normal=other=0;af_v3_tree_reset_info(guard.bits,&normal,&other,acre);
    assert(guard.bits[0]==8 && normal==0 && other==1);
}

static void interaction_cases(void) {
    selected=7;memset(acre,0,sizeof(acre));acre[0]=0x804;acre[1]=0x861;acre[2]=0x868;acre[3]=0x867;acre[4]=0x85B;
    assert(af_v3_tree_count_eligible(acre)==3);
    random_value=0.5f;af_v3_tree_change_content(acre,0x69,3);assert(acre[1]==0x78);
    assert(af_v3_tree_count_eligible(acre)==2 && acre[3]==0x867 && acre[4]==0x85B);
    u8 record=0;assert(af_v3_tree_record_content(&record,0x78,0x69,3)==1 && record==8);
    u32 info[16]={0};af_v3_tree_count_money(acre+1,info);assert(info[0x34/4]==1);
    af_test_tree_money_luck=1;assert(af_v3_tree_drop_item(0x78,0x2103)==0x2100);
    assert(af_v3_tree_drop_item(0x85B,0x2807)==0x2807);
    for (u32 i=0;i<TREE_CUTS;i++)acre[i]=af_v3_tree_cuts[i][0];
    struct {u32 a;u8 data[256];u32 b;} guard={.a=0x12345678,.b=0xABCDEF01};
    af_v3_tree_cut0(2,6,guard.data);
    for (u32 i=0;i<TREE_CUTS;i++)assert(guard.data[i]==af_v3_tree_cuts[i][1]);
    assert(guard.a==0x12345678 && guard.b==0xABCDEF01);
    extern const u32 af_v3_tree_camera_masks[4][3];
    for (u32 v=0;v<4;v++)for (u32 f=0;f<3;f++) {
        selected=1u<<f;
        for (u32 i=0;i<32;i++)assert(talk(af_v3_scenery_config[v].first_index+i,v)==
            (af_v3_tree_camera_masks[v][f]>>i&1u?1:-1));
    }
}
int main(void) {
    family_cases();daily_cases();interaction_cases();
    puts("connected family growth, regional conditions, contents, collision and interactions pass");
    return 0;
}
