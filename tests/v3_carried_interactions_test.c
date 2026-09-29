#include <assert.h>
#include <stdio.h>
#include <string.h>
#include "carried_items.h"
typedef unsigned char u8;
typedef unsigned short u16;
typedef unsigned u32;
#define W(p,o) (*(u32 *)((u8 *)(p)+(o)))
#define H(p,o) (*(u16 *)((u8 *)(p)+(o)))
static u32 inventory[64],player[1024],caught[160],submenu[64],tag[24],menu[32];
static int overlay,enabled=1,slot=4,prior_menu,returned,closed,released,original_release,put_slot,put_item,last_message,prior_message;
u8 *af_test_carried_interaction_active=(u8 *)inventory,af_test_carried_interaction_field;
extern int af_carried_interaction_menu(void *,u32,int),af_carried_net_slot(void *);
extern void af_carried_release(void *,void *),af_carried_net_put(int,u32,void *),af_carried_net_message(u8 *,unsigned);
unsigned af_carried_quantity(unsigned item) {return enabled && item-0x2D28u<5u?item-0x2D27u:0;}
u16 af_carried_with_quantity(u32 item,u32 count) {assert(af_carried_quantity(item));return count && count<=5?0x2D27+count:0;}
int af_carried_prior_action_menu(void *s,u32 item,int i) {(void)s;(void)item;(void)i;return prior_menu;}
void af_carried_prior_insect_message(u8 *p,unsigned m) {(void)p;prior_message=(int)m;}
void af_carried_set_message(unsigned m) {last_message=(int)m;}
void *af_test_carried_interaction_pointer(void *p,u32 at) {
    if(p==submenu && at==0x2C)return &overlay;
    if(p==&overlay && at==0x106D0)return tag;
    if(p==player && at==0xE68)return W(player,0xE68)?caught:NULL;
    assert(0);return NULL;
}
static int get_slot(void *p) {assert(p==(u8 *)tag+8);return slot;}
static int empty_slot(void) {
    for(int i=0;i<15;i++)if(!H(inventory,0x14+i*2) && !(W(inventory,0x34)>>(i*2)&3))return i;
    return -1;
}
static void set_item(void *p,int i,u32 item,int cond) {assert(p==inventory && !cond);H(p,0x14+i*2)=item;}
static int return_tag(void *s,int type,int mode) {assert(s==submenu && !type && !mode);returned++;return 0;}
static void close_menu(void *s,void *m,int flag) {assert(s==submenu && m==menu && flag==1);closed++;}
static void release(int type) {assert(type==40);released++;}
static void native_release(void *s,void *m) {assert(s==submenu && m==menu);original_release++;}
static void put(int i,u32 item,void *pos) {assert(!pos);put_slot=i;put_item=item;H(inventory,0x14+i*2)=item;}
void *af_test_carried_interaction_function(u32 at) {
    switch(at) {
        case 0x8086F910:return get_slot;case 0x800B3780:return empty_slot;
        case 0x800B8B08:return set_item;case 0x8086F4AC:return return_tag;
        case 0x80871760:return close_menu;case 0x800B20A8:return release;
        case 0x808739B0:return native_release;case 0x808B5584:return put;
        default:assert(0);return NULL;
    }
}
static void reset(void) {
    memset(inventory,0,sizeof(inventory));memset(player,0,sizeof(player));memset(caught,0,sizeof(caught));
    W(player,0xF24)=40;W(player,0xE68)=1;enabled=1;
    af_test_carried_interaction_field=0;returned=closed=released=original_release=0;
    put_slot=put_item=last_message=prior_message=-1;
}
int main(void) {
    reset();
    for(int field=0;field<4;field++)for(prior_menu=0;prior_menu<51;prior_menu++) {
        af_test_carried_interaction_field=field;
        int changed=prior_menu==7 || prior_menu==8 || prior_menu==12;
        assert(af_carried_interaction_menu(submenu,0x2D2C,slot)==(changed?(field?8:7):prior_menu));
        W(inventory,0x34)=1u<<(slot*2);
        assert(af_carried_interaction_menu(submenu,0x2D2C,slot)==prior_menu);W(inventory,0x34)=0;
    }
    for(int count=1;count<=5;count++) {
        reset();H(inventory,0x14+slot*2)=0x2D27+count;
        af_carried_release(submenu,menu);
        assert(H(inventory,0x14+slot*2)==(count>1?0x2D26+count:0));
        assert(released==1 && returned==1 && closed==1 && !original_release);
        assert(((u8 *)submenu)[0xDF]==slot && H(submenu,0xE0)==0x2D27+count);
    }
    reset();H(inventory,0x14+slot*2)=0x2D20;af_carried_release(submenu,menu);assert(original_release==1);
    H(inventory,0x14+slot*2)=0x2D28;enabled=0;af_carried_release(submenu,menu);assert(!released);
    for(unsigned held=0;held<=5;held++)for(unsigned incoming=1;incoming<=5;incoming++) {
        reset();for(int i=0;i<15;i++)H(inventory,0x14+i*2)=0x100;
        H(caught,0x21C)=0x2D27+incoming;
        if(held)H(inventory,0x14+slot*2)=0x2D27+held;
        int found=af_carried_net_slot(player);
        assert(found==(held && held+incoming<=5?slot:-1));
        if(found>=0) {
            af_carried_net_put(found,H(caught,0x21C),NULL);
            assert(put_slot==slot && put_item==(int)(0x2D27+held+incoming));
        }
        W(inventory,0x34)=1u<<(slot*2);assert(af_carried_net_slot(player)==-1);
        H(inventory,0x14)=0;assert(af_carried_net_slot(player)==0);
    }
    for(int held=0;held<=5;held++) {
        reset();if(held)H(inventory,0x14+slot*2)=0x2D27+held;
        af_carried_net_message((u8 *)player,123);
        assert(last_message==AF_CARRIED_SPIRIT_MESSAGE_FIRST+held && prior_message==-1);
    }
    reset();W(player,0xF24)=38;af_carried_net_message((u8 *)player,123);assert(prior_message==123);
    af_carried_net_put(0,0x2D26,NULL);assert(put_item==0x2D26 && put_slot==0);
    puts("Carried interactions: complete stacks, protected menus, release, and official message selection pass.");
    return 0;
}
