#include <assert.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/event_acquisition.c"

Category af_test_event_categories[3]={{0x2254,780,0x1758,8,0},
    {0x224C,680,0x1759,8,1},{0x2244,480,0x175A,8,2}};
u8 *af_test_event_owner;
static u8 masks[3];
static u16 saved[22];
static float draw;
static u32 random_calls, original_calls;
static int present=1;
int af_test_event_selected(u32 item) {
    for (u32 k=0;k<3;k++) if (item>=categories[k].first && item<categories[k].first+8u)
        return masks[k]&(1u<<(item-categories[k].first)) ? 91+(int)(item-0x2244u) : -1;
    return -1;
}
float af_test_event_random(void) { ++random_calls; return draw; }
u8 *af_test_event_get_area(u32 event,u32 id) {
    assert(event==11 && id==0);
    return present ? (u8 *)(saved+1) : NULL;
}
void af_test_event_original(void) {
    ++original_calls;
    /* Simulate only the original native initializer's existing twenty bytes. */
    for (u32 i=1;i<=10;i++) saved[i]=(u16)(0x5000u+i);
}
int main(void) {
    struct { u32 before; Stock stock; u32 after; } guarded={0x12345678,{{0},0,0},0x87654321};
    Stock *s=&guarded.stock, zero=*s;
    assert(af_v3_event_stock_init(NULL)==-1);
    assert(af_v3_event_stock_init(s)==0 && !random_calls && !memcmp(s,&zero,sizeof(*s)));
    masks[0]=0xA5; draw=0.5f;
    assert(af_v3_event_stock_init(s)==1 && random_calls==1);
    assert(s->kind==0 && s->count==8 && af_v3_event_stock_count(s,0)==4);
    const int slots[]={0,2,5,7};
    for (u32 i=0;i<4;i++) assert(s->goods[slots[i]]==0x2254+slots[i]);
    assert(af_v3_event_stock_index(s,0,0)==0 && af_v3_event_stock_index(s,0,1)==2);
    assert(af_v3_event_stock_index(s,0,2)==5 && af_v3_event_stock_index(s,0,3)==-1);
    assert(af_v3_event_stock_index(s,6,0)==7 && af_v3_event_stock_index(s,8,0)==-1);
    assert(af_v3_event_stock_count(s,8)==0 && af_v3_event_stock_count(s,~0u)==-1);
    assert(af_v3_event_stock_index(s,~0u,0)==-1 && af_v3_event_stock_index(s,0,~0u)==-1);
    Offer offer={1,2,3,4}, untouched=offer;
    assert(!af_v3_event_stock_quote(s,8,&offer) && !memcmp(&offer,&untouched,sizeof(offer)));
    assert(!af_v3_event_stock_quote(s,1,&offer) && !af_v3_event_stock_quote(s,0,NULL));
    for (u32 i=0;i<4;i++) {
        u32 slot=(u32)slots[i];
        assert(af_v3_event_stock_quote(s,slot,&offer));
        assert(offer.item==0x2254+slot && offer.price==780 && offer.message==0x1758 && offer.slot==slot);
        Stock copy=*s; Offer wrong=offer;
        ++wrong.item; assert(!af_v3_event_stock_commit(s,&wrong));
        wrong=offer; ++wrong.price; assert(!af_v3_event_stock_commit(s,&wrong));
        wrong=offer; ++wrong.message; assert(!af_v3_event_stock_commit(s,&wrong));
        wrong=offer; wrong.slot=65535; assert(!af_v3_event_stock_commit(s,&wrong));
        assert(!af_v3_event_stock_commit(s,NULL) && !memcmp(s,&copy,sizeof(*s)));
        assert(af_v3_event_stock_commit(s,&offer) && !af_v3_event_stock_commit(s,&offer));
        assert(!s->goods[slot] && af_v3_event_stock_count(s,0)==3-(int)i);
        assert(af_v3_event_stock_init(s)==1 && !s->goods[slot] && random_calls==1);
    }
    assert(s->count==8 && af_v3_event_stock_count(s,0)==0);
    assert(af_v3_event_stock_init(s)==1 && random_calls==1); /* No sold-out refill. */
    assert(guarded.before==0x12345678 && guarded.after==0x87654321);
    for (u32 k=0;k<3;k++) {
        *s=zero; masks[0]=masks[1]=masks[2]=255; draw=((float)k+0.5f)/3.0f;
        assert(af_v3_event_stock_init(s)==1 && s->kind==k);
        for (u32 i=0;i<8;i++) {
            assert(af_v3_event_stock_quote(s,i,&offer));
            assert(offer.item==categories[k].first+i && offer.price==categories[k].price);
        }
    }
    /* Source kind two is balloon stock, never the native unlimited-fruit mode. */
    assert(af_v3_event_stock_commit(s,&offer));
    assert(af_v3_event_stock_count(s,0)==7);
    *s=zero; masks[0]=masks[1]=0; masks[2]=0x80; draw=0.0f;
    assert(af_v3_event_stock_init(s)==1 && s->kind==2 && s->goods[7]==0x224B);
    masks[2]=0;
    Stock copy=*s; assert(af_v3_event_stock_init(s)==-1 && af_v3_event_stock_count(s,0)==-1);
    assert(!af_v3_event_stock_quote(s,7,&offer) && !memcmp(s,&copy,sizeof(*s)));
    for (u32 bad=0;bad<4;bad++) {
        *s=zero; if (bad==0) s->goods[1]=0x2255;
        if (bad==1) s->kind=1;
        if (bad==2) s->count=9;
        if (bad==3) { s->count=8;s->kind=3; }
        copy=*s; assert(af_v3_event_stock_init(s)==-1 && !memcmp(s,&copy,sizeof(*s)));
    }
    for (u32 bad=0;bad<3;bad++) {
        *s=zero; masks[0]=1; draw=bad==0 ? -0.1f : bad==1 ? 1.0f : NAN;
        assert(af_v3_event_stock_init(s)==-1 && !memcmp(s,&zero,sizeof(*s)));
    }
    draw=0.0f; categories[1].first=categories[0].first;
    assert(af_v3_event_stock_init(s)==-1); categories[1].first=0x224C;
    saved[0]=0xA55A; saved[21]=0x5AA5;
    af_v3_event_stock_construct(); assert(original_calls==0);
    af_test_event_owner=(u8 *)1;
    af_v3_event_stock_construct(); assert(original_calls==1);
    for (u32 i=1;i<=10;i++) assert(saved[i]==0x5000u+i);
    Stock *tail=(Stock *)(saved+11);
    assert(tail->count==8 && tail->goods[0]==0x2254);
    assert(af_v3_event_stock_quote(tail,0,&offer) && af_v3_event_stock_commit(tail,&offer));
    u16 retained[22]; memcpy(retained,saved,sizeof(saved));
    af_v3_event_stock_construct(); assert(original_calls==2 && !memcmp(saved,retained,sizeof(saved)));
    present=0; af_v3_event_stock_construct(); assert(original_calls==3);
    assert(saved[0]==0xA55A && saved[21]==0x5AA5);
    puts("Event category selection, sparse paging, quotations, consumption, persistent sold-out state, and bounds pass");
}
