#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/scenery_trees.c"
#include "../overlays/v3/scenery_daily.c"

const TreeRule af_v3_tree_rule={0x863,6,0x7f,3,0x223b,0x2202,0x5d,0,
    {{-1,0},{-1,1},{-1,2},{-1,3},{0,4},{0,4}}, {0x7e,0x7d,0x7c,0x7b}};
const TreeDaily af_v3_tree_daily_config={0x80100c5c,0x398,0x910,0x14a0,0x160c,0x1854,0x869,0x84e,32};
static int enabled,near_calls,plant_calls,thin_calls,random_calls;
static float random_value;
int af_v3_player_selected_equipment(u32 item) { assert(item==0x223b);return enabled?90:-1; }
u32 af_v3_native_tree_grow(u32 item,int days,int cap) { (void)days;(void)cap;return item; }
u32 af_v3_native_tree_stump(u32 item,int flag) { (void)flag;return item; }
int af_test_tree_bury(u32 i,u32 h,void *p,u16 *o,u32 v) { (void)i;(void)h;(void)p;(void)o;(void)v;return 0; }
int native_near(u16 *p,GrowInfo *g,int x,int z) { (void)p;(void)g;(void)x;(void)z;++near_calls;return 1; }
int native_plant(u16 *p,GrowInfo *g) { (void)p;(void)g;++plant_calls;return 0; }
void native_thin(u16 *p,u16 *b,int n,int o) { (void)p;(void)b;(void)n;(void)o;++thin_calls; }
void native_set(u16 *b,u16 *p) {
    memset(b,0,32);for (int i=0;i<256;++i) if (native_sapling(p[i])) b[i/16]|=(u16)(1u<<(i%16));
}
void native_reset(u16 *b,u8 *normal,u8 *other,u16 *p) {
    for (int i=0;i<256;++i) if (b[i/16]&(1u<<(i%16))) {
        if (p[i]==0x84e) b[i/16]&=(u16)~(1u<<(i%16));
        else if (p[i]-0x800u<5u) ++*normal;
        else if (p[i]) ++*other;
    }
}
float af_scenery_random(void) { ++random_calls;return random_value; }

int main(void) {
    u16 acres[5][256];GrowInfo info={0};
    for (int i=0;i<4;++i) info.around[i]=acres[i+1];
    enabled=1;
    for (int direction=0;direction<4;++direction) for (int boundary=0;boundary<2;++boundary)
        for (int parity=0;parity<2;++parity) {
            int x=7,z=7+parity;
            if (boundary) {
                if (direction<2) { z=direction?15:0;x=(z^parity)&1; }
                else { x=direction==3?15:0;z=(x^parity)&1; }
            }
            u16 *p=acres[0]+z*16+x;
            for (int current=0;current<2;++current) {
                const u16 neighbours[]={0,0x800,0x801,1,0x863,0x864,0x867,0x868,0x869,0x7b,0x7e,0x7f,0x80,0x81};
                for (unsigned n=0;n<sizeof(neighbours)/sizeof(neighbours[0]);++n) {
                    memset(acres,0,sizeof(acres));*p=current?0x863:0x800;
                    *neighbour(p,&info,x,z,(u32)direction)=neighbours[n];near_calls=0;
                    int value=neighbours[n];
                    int gold_block=value==0x864 || value==0x867 || value==0x868 || (value>=0x7b && value<=0x81) || (value==0x863 && parity);
                    int native_block=value==0x801 || value==1 || (value==0x800 && parity);
                    int blocked=gold_block || (current && native_block);
                    int result=af_v3_tree_near(p,&info,x,z);
                    assert(*p==(blocked?(current?0x869:0x84e):(current?0x863:0x800)));
                    assert(result==(blocked?(current && !parity):1));
                    assert(near_calls==(!current && !blocked));
                }
            }
        }
    memset(acres,0,sizeof(acres));u16 *p=acres[0]+136;
    info.x=8;info.z=8;
    const int days[]={INT_MIN,-1,0,1,2,4,INT_MAX};
    for (int stage=0;stage<7;++stage) for (int cap=-1;cap<=5;++cap)
        for (unsigned d=0;d<sizeof(days)/sizeof(days[0]);++d) {
            *p=(u16)(0x863+stage);info.days=days[d];info.cap=cap;
            int expected=*p;
            if (cap==-1 || stage==6) expected=0;
            else if (!cap) expected=0x869;
            else if (days[d]>0) {
                int next=stage;
                for (int i=0;i<4 && i<days[d] && next<4 && next<cap;++i) ++next;
                expected=0x863+next;
            }
            assert(af_v3_tree_daily_plant(p,&info)==1 && *p==expected);
        }
    enabled=0;*p=0x863;info.cap=4;info.days=4;plant_calls=0;
    assert(af_v3_tree_daily_plant(p,&info)==0 && *p==0x863 && plant_calls==1);
    near_calls=0;assert(af_v3_tree_near(p,&info,8,8)==1 && near_calls==1);
    enabled=1;*p=0x2800;plant_calls=0;
    assert(af_v3_tree_daily_plant(p,&info)==0 && *p==0x2800 && plant_calls==1);

    struct { u16 before[8],bits[16],after[8]; } guarded;
    memset(&guarded,0xa5,sizeof(guarded));memset(acres,0,sizeof(acres));
    acres[0][0]=0x800;acres[0][1]=0x863;acres[0][255]=0x863;
    af_v3_tree_set_info(guarded.bits,acres[0]);
    assert(guarded.bits[0]==3 && guarded.bits[15]==0x8000);
    acres[0][1]=0x869;u8 normal=0,other=0;
    af_v3_tree_reset_info(guarded.bits,&normal,&other,acres[0]);
    assert(normal==1 && other==1 && guarded.bits[0]==1 && guarded.bits[15]==0x8000);
    for (int i=0;i<8;++i) assert(guarded.before[i]==0xa5a5 && guarded.after[i]==0xa5a5);

    /* Count every mature form, retain native-first thinning priority, and use
       the source random choice once per removed sapling. */
    memset(acres,0,sizeof(acres));memset(guarded.bits,0,sizeof(guarded.bits));
    for (int i=0;i<32;++i) acres[0][i]=0x867;
    acres[0][32]=0x800;acres[0][33]=0x864;guarded.bits[2]=3;
    random_value=0;random_calls=0;af_v3_tree_thin(acres[0],guarded.bits,1,1);
    assert(acres[0][32]==0x84e && acres[0][33]==0x869 && guarded.bits[2]==0 && random_calls==2);
    for (int i=0;i<32;++i) assert(acres[0][i]==0x867);
    memset(acres,0,sizeof(acres));memset(guarded.bits,0,sizeof(guarded.bits));
    for (int i=0;i<31;++i) acres[0][i]=(u16)(0x7f+i%3);
    acres[0][31]=0x864;acres[0][32]=0x865;guarded.bits[1]=0x8000;guarded.bits[2]=1;
    random_value=0.75f;random_calls=0;af_v3_tree_thin(acres[0],guarded.bits,0,2);
    assert(acres[0][31]==0x864 && acres[0][32]==0x869 && random_calls==1);
    for (int i=0;i<256;++i) acres[0][i]=0x867;
    memset(guarded.bits,0,sizeof(guarded.bits));guarded.bits[0]=1;random_calls=0;
    af_v3_tree_thin(acres[0],guarded.bits,0,1);assert(random_calls==0); /* source u8 wrap */
    enabled=0;thin_calls=0;af_v3_tree_thin(acres[0],guarded.bits,0,1);assert(thin_calls==1);
    puts("shared daily tree growth pass");return 0;
}
