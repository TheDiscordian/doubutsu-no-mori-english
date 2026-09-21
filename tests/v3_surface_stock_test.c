#include <assert.h>
#include <string.h>
#include "../overlays/v3/surface_stock.c"
static u32 enabled,last_argument;
static u16 *native_result;
static int calls;
int af_v3_surface_item_type(u32 item) {
    u32 kind=(item>>8)-0x26u,index=(item&255u)-73u;
    return kind<2 && index<5 && (enabled&(1u<<(kind*5+index))) ? 12 : 0;
}
int af_surface_prior_shop_category(u32 arg) {last_argument=arg;return 123;}
u16 *af_surface_prior_stock_list(void *lists,void *priorities,int type) {
    assert(lists==(void *)1 && priorities==(void *)2 && type==3);++calls;
    return native_result;
}
static u16 *run(u16 *list) {native_result=list;return af_v3_surface_stock_list((void *)1,(void *)2,3);}
int main(void) {
    for (int kind=0;kind<2;kind++) {
        u32 base=(u32)(0x26+kind)<<8;
        for (u32 mode=0;mode<3;mode++) {
            enabled=mode==0 ? 0 : mode==1 ? 1023 : (1u<<1)|(1u<<8);
            u16 list[]={base,base+72,base+73,base+74,base+75,base+76,base+77,base+63,0};
            u16 expected[9]={base};u32 n=1;
            for (u32 i=0;i<5;i++) {
                int selected=(enabled>>(kind*5+i))&1;
                if (selected) expected[n++]=(u16)(base+73+i);
                assert(af_v3_surface_shop_category(base+73+i)==(selected?3+kind:-1));
            }
            expected[n++]=(u16)(base+63);expected[n++]=0;
            assert(run(list)==list && !memcmp(list,expected,n*2));
            assert(af_v3_surface_shop_category(base+64)==-1);
            assert(af_v3_surface_shop_category(base+255)==-1);
            assert(af_v3_surface_shop_category(0xABCD0000u+base)==123);
            assert(last_argument==0xABCD0000u+base);
        }
    }
    u16 other[]={0x1000,0x264A,0};assert(run(other)==other && other[1]==0x264A);
    u16 empty[]={0};assert(run(empty)==empty && !run(0));
    u16 mixed[]={0x2600,0x2701,0};assert(!run(mixed) && mixed[0]==0x2600 && mixed[1]==0x2701);
    u16 limit[69];for (int i=0;i<69;i++)limit[i]=0x2600;
    assert(!run(limit));for (int i=0;i<69;i++)assert(limit[i]==0x2600);
    assert(af_v3_surface_shop_category(0x34BF)==123 && last_argument==0x34BF);
    assert(calls==11);
    return 0;
}
