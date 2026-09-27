#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "../overlays/v3/creature_items.c"
u32 af_test_creature_items[128];
static u32 chosen,prior_calls;
int af_creature_profile(u32 index) {return chosen==index;}
int af_creature_prior_name(u8 *p,u32 n,u32 item) {(void)p;(void)n;prior_calls++;return (int)item;}
int af_creature_prior_type(u32 item) {prior_calls++;return (int)item;}
u32 af_creature_prior_price(u32 item) {prior_calls++;return item;}
u16 af_creature_prior_display(u32 item) {prior_calls++;return (u16)(item^0x1000);}
u16 af_creature_prior_pocket(u32 item) {prior_calls++;return (u16)(item^0x1000);}

int main(void) {
    u32 *h=af_test_creature_items;h[0]=0x41464349;h[1]=1;h[2]=17;h[3]=28;
    Creature *rows=(Creature *)(h+4);
    for(u32 i=0;i<17;i++) {
        Creature *r=rows+i;
        r->item=(u16)(i<9?0x2320+i:0x2D20+i-9);
        r->display=(u16)(0x3C98+i*4);r->type=i<9?8:18;r->source=(u8)i;
        r->price=(u16)(400+i*4);memset(r->name,'A'+i,16);
    }
    unsigned char text[20];
    for(u32 i=0;i<17;i++) {
        Creature *r=rows+i;chosen=1024+((r->display&4095)>>2);prior_calls=0;
        assert(!af_v3_creature_room_display(r->item));
        r->ready=1;
        assert(af_v3_creature_room_display(r->item)==r->display);
        assert(af_v3_creature_item_type(r->item)==r->type);
        for(u32 rotation=0;rotation<4;rotation++) {
            u32 display=r->display+rotation;
            assert(af_v3_creature_room_pocket(display)==r->item);
            assert(af_v3_creature_room_display(display)==display);
            assert(af_v3_creature_item_price(display)==r->price);
            assert(af_v3_creature_item_type(display)==10);
            memset(text,0xDE,sizeof(text));
            assert(af_v3_creature_item_name(text+2,16,display)==1);
            assert(!memcmp(text+2,r->name,16));
            assert(text[0]==0xDE && text[1]==0xDE && text[18]==0xDE && text[19]==0xDE);
        }
        assert(af_v3_creature_item_price(r->item)==r->price);
        memset(text,0xDE,sizeof(text));
        assert(!af_v3_creature_item_name(text,15,r->item));
        assert(text[0]==0xDE);
        assert(!af_v3_creature_item_name(0,16,r->item));
        chosen=0;
        assert(!af_v3_creature_room_display(r->item));
        assert(!af_v3_creature_room_pocket(r->display));
        assert(!af_v3_creature_item_type(r->item));
        assert(!af_v3_creature_item_price(r->item));
        assert(!af_v3_creature_item_name(text,16,r->item));
        assert(!prior_calls);r->ready=0;
    }
    /* Invalid extended IDs never index the original 32-entry tables. */
    assert(!af_v3_creature_item_type(0x23FF));assert(!af_v3_creature_item_price(0x2DFF));
    h[2]=18;assert(!af_v3_creature_room_display(0x2328));h[2]=17;
    /* Native herabuna and the original category, clothes, and furniture retain their readers. */
    const u32 native[]={0x2301,0x231F,0x2D1F,0x2400,0x17AC,0x1C2C,0x341A,0x3868};
    for(u32 i=0;i<sizeof(native)/sizeof(*native);i++) {
        u32 item=native[i];prior_calls=0;
        assert(af_v3_creature_item_name(text,16,item)==(int)item);
        assert(af_v3_creature_item_type(item)==(int)item);
        assert(af_v3_creature_item_price(item)==item);
        assert(af_v3_creature_room_display(item)==(item^0x1000));
        assert(af_v3_creature_room_pocket(item)==(item^0x1000));
        assert(prior_calls==5);
    }
    puts("Complete creature parent/room path: pass");
}
